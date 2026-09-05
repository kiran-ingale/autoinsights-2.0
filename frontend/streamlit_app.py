"""Temporary Streamlit shell for the AutoInsights prototype."""

from pathlib import Path
import sys

import streamlit as st


# Allow `streamlit run frontend/streamlit_app.py` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import MAX_UPLOAD_MB


st.set_page_config(page_title="AutoInsights", page_icon="📊", layout="wide")

st.title("AutoInsights")
st.caption("Agentic data analysis prototype powered by Streamlit and LangGraph")

st.info(
    "Project setup is complete. The analysis workflow and dashboard will be added next."
)

with st.form("analysis_request", clear_on_submit=False):
    problem_statement = st.text_area(
        "What would you like to learn from your data?",
        placeholder="Example: Identify the factors associated with monthly sales.",
    )
    uploaded_file = st.file_uploader(
        "Upload a CSV file (optional)",
        type=["csv"],
        help=f"Maximum upload size: {MAX_UPLOAD_MB} MB.",
    )
    use_sample_data = st.checkbox("Use the included sample data instead")
    submitted = st.form_submit_button("Start analysis", disabled=True)

if submitted:
    st.warning("The LangGraph workflow has not been connected yet.")

st.subheader("Next milestones")
st.write(
    "Define the shared analysis state, build the LangGraph workflow, then connect "
    "this form to the interactive dashboard."
)
