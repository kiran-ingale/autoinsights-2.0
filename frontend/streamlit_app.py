"""Streamlit entry point for the AutoInsights prototype."""

from __future__ import annotations

from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st


# Allow `streamlit run frontend/streamlit_app.py` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import GROQ_MODEL, MAX_UPLOAD_MB, MISTRAL_MODEL
from app.agents.chat import handle_chat_message
from app.graph import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType
from frontend.dashboard import render_dashboard


st.set_page_config(page_title="AutoInsights", page_icon="📊", layout="wide")


def _start_run(
    problem_statement: str,
    domain: str,
    constraints: str,
    uploaded_file: object | None,
    use_sample_data: bool,
) -> None:
    """Validate the form and retain the final graph state in the session."""

    if len(problem_statement.strip()) < 3:
        st.error("Enter a question with at least three characters.")
        return
    if not use_sample_data and uploaded_file is None:
        st.error("Upload a CSV file or select the included sample data.")
        return

    source_type = SourceType.SAMPLE if use_sample_data else SourceType.UPLOAD
    request = AnalysisRequest(
        run_id=f"run-{uuid4().hex[:12]}",
        problem_statement=problem_statement,
        domain=domain or None,
        constraints=constraints or None,
        source_type=source_type,
    )

    with st.status("Running AutoInsights workflow...", expanded=True) as status:
        state = run_analysis(request, uploaded_file=uploaded_file)  # type: ignore[arg-type]
        for event in state["progress"]:
            if event["level"] == "error":
                st.error(f"{event['agent']}: {event['message']}")
            elif event["level"] == "warning":
                st.warning(f"{event['agent']}: {event['message']}")
            else:
                st.write(f"{event['agent']}: {event['message']}")
        if state["status"] is RunStatus.COMPLETED:
            status.update(label="Analysis workflow complete", state="complete")
        elif state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL:
            status.update(label="Raw-data assessment complete — cleaning approval required", state="complete")
        else:
            status.update(label="Analysis workflow stopped", state="error")

    st.session_state.analysis_state = state


def _show_run_summary() -> None:
    """Display the raw or cleaned dashboard for the current workflow state."""

    state = st.session_state.get("analysis_state")
    if not state:
        st.info("Submit a question and data source to start an analysis run.")
        return
    if state["status"] is RunStatus.FAILED:
        st.error("The analysis could not be completed.")
        for error in state["errors"]:
            st.write(f"- {error}")
        return

    if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL:
        st.info("Raw-data assessment complete. Review the cleaning plan, then choose whether to apply it.")
    else:
        st.success(f"Run `{state['request'].run_id}` completed after approved cleaning.")
    if state["warnings"]:
        st.subheader("Data-quality notices")
        for warning in state["warnings"]:
            st.warning(warning)
    render_dashboard(state)

    report_path = state.get("assessment_report_path") if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL else state.get("report_path")
    if report_path and Path(report_path).is_file():
        st.download_button(
            "Download current HTML report",
            data=Path(report_path).read_bytes(),
            file_name=Path(report_path).name,
            mime="text/html",
        )

    if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL:
        st.subheader("Proposed cleaning plan")
        st.caption("No transformations have been applied yet. The dashboard above reflects the original data.")
        st.dataframe(state.get("cleaning_plan", []), use_container_width=True, hide_index=True)
        if st.button("Execute cleaning and refresh analysis", type="primary"):
            with st.status("Applying approved cleaning and refreshing the analysis...", expanded=True) as status:
                updated_state = execute_cleaning(state)
                for event in updated_state["progress"][len(state["progress"]) :]:
                    st.write(f"{event['agent']}: {event['message']}")
                status.update(label="Cleaning and final analysis complete", state="complete")
            st.session_state.analysis_state = updated_state
            st.rerun()


def _render_chat() -> None:
    """Render the Mistral-assisted chat entry point and retain conversation history."""

    st.divider()
    st.subheader("Ask AutoInsights")
    st.caption("Ask about findings, charts, data quality, cleaning, or reports. The assistant can execute only supported analysis actions.")
    with st.sidebar:
        with st.expander("Chat model settings"):
            provider_label = st.selectbox("Provider", ["Auto", "Mistral", "Groq"], help="Auto tries Mistral first, then Groq.")
            if provider_label == "Mistral":
                selected_model = st.text_input("Mistral model", value=MISTRAL_MODEL)
            elif provider_label == "Groq":
                selected_model = st.text_input("Groq model", value=GROQ_MODEL)
            else:
                selected_model = ""
    history = st.session_state.setdefault("chat_history", [])
    for item in history:
        with st.chat_message(item["role"]):
            st.write(item["content"])

    message = st.chat_input("Ask about this analysis or request a supported action")
    if not message:
        return
    history.append({"role": "user", "content": message})
    with st.chat_message("user"):
        st.write(message)
    with st.chat_message("assistant"):
        result, updated_state = handle_chat_message(
            message,
            st.session_state.get("analysis_state"),
            provider=provider_label.lower(),
            model=selected_model or None,
        )
        st.write(result.response)
    history.append({"role": "assistant", "content": result.response})
    if result.state_changed:
        st.session_state.analysis_state = updated_state
        st.rerun()


st.title("AutoInsights")
st.caption("Agentic data analysis prototype powered by Streamlit and LangGraph")

with st.form("analysis_request", clear_on_submit=False):
    problem_statement = st.text_area(
        "What would you like to learn from your data?",
        placeholder="Example: Identify the factors associated with monthly sales.",
    )
    left, right = st.columns(2)
    domain = left.text_input("Domain (optional)", placeholder="Example: retail")
    constraints = right.text_input("Constraints (optional)", placeholder="Example: focus on revenue")
    uploaded_file = st.file_uploader(
        "Upload a CSV file",
        type=["csv"],
        help=f"Maximum upload size: {MAX_UPLOAD_MB} MB.",
    )
    use_sample_data = st.checkbox("Use the included retail sales sample data instead")
    submitted = st.form_submit_button("Start analysis", type="primary")

if submitted:
    _start_run(problem_statement, domain, constraints, uploaded_file, use_sample_data)

_show_run_summary()
_render_chat()
