"""Mistral-backed chat routing for the supported AutoInsights actions."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.config import GROQ_API_KEY, GROQ_MODEL, MISTRAL_API_KEY, MISTRAL_MODEL
from app.graph import execute_cleaning
from app.schemas import AnalysisState, RunStatus


class ChatIntent(BaseModel):
    """A safe local action selected by the Mistral routing prompt."""

    action: Literal["answer_question", "explain_results", "execute_cleaning", "show_report", "unsupported"]
    response: str = Field(min_length=1, max_length=2_000)


class ChatResult(BaseModel):
    """Response returned to Streamlit after routing and optional action execution."""

    response: str
    action: str
    state_changed: bool = False


def _state_context(state: AnalysisState | None) -> dict[str, Any]:
    if state is None:
        return {"run_available": False}
    return {
        "run_available": True,
        "status": state["status"].value,
        "question": state["request"].problem_statement,
        "profile": state.get("profile", {}),
        "warnings": state["warnings"],
        "observations": state.get("observations", []),
        "statistics": state.get("statistics", {}),
        "insights": state.get("insights", []),
        "cleaning_plan": state.get("cleaning_plan", []),
        "transformations": state.get("transformations", []),
        "report_available": bool(state.get("report_path") or state.get("assessment_report_path")),
    }


def _parse_intent(content: object) -> ChatIntent:
    """Extract one JSON object even when a model returns Markdown fences."""

    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
    text = str(content).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("The model did not return a routing object.")
    return ChatIntent.model_validate_json(match.group(0))


def _system_prompt() -> str:
    return """You are the AutoInsights chat router. You may answer questions about the current analysis and select only these actions:
- answer_question: answer a general or data-analysis question using the supplied context.
- explain_results: explain findings, charts, warnings, or cleaning choices.
- execute_cleaning: select only when the user explicitly asks to apply, run, or execute cleaning and status is awaiting_cleaning_approval.
- show_report: select only when the user asks for the current report.
- unsupported: use for requests that require arbitrary system commands, external actions, raw-data access, or capabilities not provided by AutoInsights.
Never claim to have executed an action; execution is handled locally. Return only JSON with action and response. Keep the response concise and do not invent facts beyond the supplied context."""


def _messages(message: str, state: AnalysisState | None) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": json.dumps({"message": message, "analysis_context": _state_context(state)})},
    ]


def route_with_mistral(message: str, state: AnalysisState | None, model: str | None = None) -> ChatIntent:
    """Ask Mistral to choose a supported action and draft a concise answer."""

    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY is not configured.")
    from mistralai import Mistral

    client = Mistral(api_key=MISTRAL_API_KEY)
    completion = client.chat.complete(
        model=model or MISTRAL_MODEL,
        messages=_messages(message, state),
    )
    return _parse_intent(completion.choices[0].message.content)


def route_with_groq(message: str, state: AnalysisState | None, model: str | None = None) -> ChatIntent:
    """Ask Groq to route the same allow-listed AutoInsights actions."""

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(model=model or GROQ_MODEL, messages=_messages(message, state))
    return _parse_intent(completion.choices[0].message.content)


def dispatch_intent(intent: ChatIntent, state: AnalysisState | None) -> tuple[ChatResult, AnalysisState | None]:
    """Invoke only local, allow-listed actions selected by the router."""

    if intent.action == "execute_cleaning":
        if state is None:
            return ChatResult(response="Start an analysis first, then review its cleaning plan.", action=intent.action), state
        if state["status"] is not RunStatus.AWAITING_CLEANING_APPROVAL:
            return ChatResult(response="Cleaning is not awaiting approval for the current run.", action=intent.action), state
        updated = execute_cleaning(state)
        return ChatResult(response="Cleaning completed. I refreshed the analysis, dashboard, and final report.", action=intent.action, state_changed=True), updated
    if intent.action == "show_report":
        return ChatResult(response="The current HTML report is available through the download button below the dashboard.", action=intent.action), state
    return ChatResult(response=intent.response, action=intent.action), state


def _offline_fallback(message: str, state: AnalysisState | None) -> tuple[ChatResult, AnalysisState | None]:
    """Answer supported requests locally when an external provider is unavailable."""

    request = message.lower()
    if any(term in request for term in ("clean", "apply", "execute")):
        return dispatch_intent(ChatIntent(action="execute_cleaning", response="Execute the approved cleaning plan."), state)
    if "report" in request or "download" in request:
        return dispatch_intent(ChatIntent(action="show_report", response="Show the current report."), state)
    if state is None:
        return (
            ChatResult(
                response="No analysis run is available yet. Upload data or use the sample data to start.",
                action="offline_fallback",
            ),
            state,
        )
    if any(term in request for term in ("cleaning", "quality", "missing", "duplicate")):
        plan = state.get("cleaning_plan") or state.get("transformations", [])
        details = "; ".join(item.get("action", "") for item in plan) or "No cleaning actions were recorded."
        return ChatResult(response=f"Available data-quality actions: {details}.", action="offline_fallback"), state
    insights = state.get("insights", [])
    summary = " ".join(item.get("text", "") for item in insights[:2])
    return ChatResult(
        response=(f"Current analysis summary: {summary}" if summary else "Review the dashboard and report for the current results."),
        action="offline_fallback",
    ), state


def handle_chat_message(
    message: str,
    state: AnalysisState | None,
    provider: Literal["auto", "mistral", "groq"] = "auto",
    model: str | None = None,
) -> tuple[ChatResult, AnalysisState | None]:
    """Route one user message through Mistral and dispatch its safe local action."""

    mistral_enabled = provider in {"auto", "mistral"} and bool(MISTRAL_API_KEY)
    groq_enabled = provider in {"auto", "groq"} and bool(GROQ_API_KEY)
    if not mistral_enabled and not groq_enabled:
        return (
            ChatResult(
                response=f"No configured API key is available for the selected {provider} provider.",
                action="configuration_required",
            ),
            state,
        )
    try:
        intent = route_with_mistral(message, state, model) if mistral_enabled else route_with_groq(message, state, model)
        return dispatch_intent(intent, state)
    except Exception as error:
        if provider == "auto" and groq_enabled and mistral_enabled:
            try:
                return dispatch_intent(route_with_groq(message, state, model), state)
            except Exception as groq_error:
                error = groq_error
        error_text = str(error).lower()
        if (
            "getaddrinfo failed" in error_text
            or "connection error" in error_text
            or "connecterror" in error_text
            or "timeout" in error_text
            or isinstance(error, OSError)
        ):
            result, updated_state = _offline_fallback(message, state)
            return result, updated_state
        if "rate limit" in error_text or "status 429" in error_text or "rate_limited" in error_text:
            result, updated_state = _offline_fallback(message, state)
            if result.action == "offline_fallback":
                result.response = f"Mistral is rate-limited. {result.response} Try again in a moment for a full AI response."
            return result, updated_state
        if "model_not_found" in error_text or "does not exist or you do not have access" in error_text:
            result, updated_state = _offline_fallback(message, state)
            if result.action == "offline_fallback":
                result.response = (
                    "The selected model is unavailable to this API key. Choose a model enabled for "
                    "that provider in Chat model settings, or update its value in `.env` and restart "
                    f"Streamlit. {result.response}"
                )
            return result, updated_state
        return ChatResult(response=f"I could not process that chat request: {error}", action="error"), state
