from app.agents.chat import ChatIntent, dispatch_intent, handle_chat_message
from app.graph import run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


def test_chat_without_key_requests_configuration(monkeypatch) -> None:
    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "")

    result, state = handle_chat_message("What did you find?", None)

    assert result.action == "configuration_required"
    assert state is None


def test_execute_cleaning_intent_calls_the_approved_workflow() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="chat-cleaning-run",
            problem_statement="Analyze sales",
            source_type=SourceType.SAMPLE,
        )
    )

    result, updated = dispatch_intent(
        ChatIntent(action="execute_cleaning", response="Run cleaning."),
        state,
    )

    assert result.state_changed is True
    assert updated is not None
    assert updated["status"] is RunStatus.COMPLETED


def test_router_cannot_execute_cleaning_before_a_run_exists() -> None:
    result, state = dispatch_intent(ChatIntent(action="execute_cleaning", response="Run it."), None)

    assert result.state_changed is False
    assert state is None


def test_network_failure_uses_local_cleaning_fallback(monkeypatch) -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="chat-network-fallback-run",
            problem_statement="Analyze sales",
            source_type=SourceType.SAMPLE,
        )
    )

    def raise_dns_error(*args, **kwargs):
        raise OSError(11001, "getaddrinfo failed")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "configured")
    monkeypatch.setattr("app.agents.chat.route_with_mistral", raise_dns_error)
    result, updated = handle_chat_message("Execute the cleaning", state)

    assert result.state_changed is True
    assert updated is not None
    assert updated["status"] is RunStatus.COMPLETED


def test_rate_limit_uses_a_local_summary(monkeypatch) -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="chat-rate-limit-run",
            problem_statement="Analyze sales",
            source_type=SourceType.SAMPLE,
        )
    )

    def raise_rate_limit(*args, **kwargs):
        raise RuntimeError("API error occurred: Status 429. Body: rate limit exceeded")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "configured")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "")
    monkeypatch.setattr("app.agents.chat.route_with_mistral", raise_rate_limit)
    result, updated = handle_chat_message("What are the findings?", state)

    assert result.action == "offline_fallback"
    assert "rate-limited" in result.response
    assert updated is state


def test_groq_is_used_when_mistral_fails(monkeypatch) -> None:
    def raise_rate_limit(*args, **kwargs):
        raise RuntimeError("Status 429 rate limited")

    def groq_response(*args, **kwargs):
        return ChatIntent(action="answer_question", response="Groq answered the request.")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "groq-key")
    monkeypatch.setattr("app.agents.chat.route_with_mistral", raise_rate_limit)
    monkeypatch.setattr("app.agents.chat.route_with_groq", groq_response)

    result, state = handle_chat_message("What did you find?", None)

    assert result.response == "Groq answered the request."
    assert result.action == "answer_question"
    assert state is None


def test_connection_error_uses_local_fallback(monkeypatch) -> None:
    def raise_connection_error(*args, **kwargs):
        raise RuntimeError("Connection error.")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "")
    monkeypatch.setattr("app.agents.chat.route_with_mistral", raise_connection_error)

    result, state = handle_chat_message("What are the findings?", None)

    assert result.action == "offline_fallback"
    assert "No analysis run is available" in result.response
    assert state is None


def test_missing_groq_model_uses_local_fallback(monkeypatch) -> None:
    def raise_model_error(*args, **kwargs):
        raise RuntimeError("model_not_found: The model does not exist or you do not have access")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "groq-key")
    monkeypatch.setattr("app.agents.chat.route_with_groq", raise_model_error)

    result, state = handle_chat_message("What are the findings?", None)

    assert result.action == "offline_fallback"
    assert "selected model is unavailable" in result.response
    assert state is None


def test_selected_provider_routes_to_its_selected_model(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    def mistral_response(message, state, model=None):
        captured["model"] = model
        return ChatIntent(action="answer_question", response="Mistral answered.")

    monkeypatch.setattr("app.agents.chat.MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setattr("app.agents.chat.GROQ_API_KEY", "groq-key")
    monkeypatch.setattr("app.agents.chat.route_with_mistral", mistral_response)

    result, _ = handle_chat_message("Explain this", None, provider="mistral", model="mistral-large-latest")

    assert result.response == "Mistral answered."
    assert captured["model"] == "mistral-large-latest"
