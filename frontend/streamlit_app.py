from io import BytesIO
from pathlib import Path
import sys
from datetime import datetime
from uuid import uuid4

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.chat import handle_chat_message
from app.config import GROQ_MODEL, MISTRAL_MODEL
from app.graph import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


st.set_page_config(
    page_title="AutoInsights",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --panel: #111823;
            --panel-soft: #151d2a;
            --border: #2a3443;
            --text-soft: #a9b4c3;
            --blue: #1677ff;
            --teal: #16c7b7;
            --amber: #f59e0b;
        }

        .stApp {
            background: radial-gradient(circle at top left, #111827 0, #080c13 42%, #05070b 100%);
            color: #f8fafc;
        }

        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stHeader"],
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {
            background: #05070b !important;
        }

        [data-testid="stHeader"] {
            border-bottom: 1px solid #111827;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #171b26 0%, #101620 100%);
            border-right: 1px solid var(--border);
        }

        div[data-testid="stSidebarHeader"] {
            height: 1.5rem;
        }

        .main .block-container {
            max-width: 1280px;
            padding-top: 3rem;
        }

        .hero-title {
            font-size: 3.1rem;
            font-weight: 800;
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }

        .muted {
            color: var(--text-soft);
        }

        .panel {
            background: linear-gradient(180deg, rgba(17, 24, 35, 0.96), rgba(12, 18, 28, 0.96));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.15rem;
            box-shadow: 0 16px 45px rgba(0, 0, 0, 0.18);
        }

        .preview-card {
            background: #101722;
            border: 1px solid #253041;
            border-radius: 8px;
            padding: 0.9rem;
            min-height: 112px;
        }

        .step-card {
            background: #101722;
            border: 1px solid #253041;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.7rem;
        }

        .step-active {
            border-color: var(--blue);
            box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.3);
        }

        .status-pill {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            font-size: 0.75rem;
            color: #dbeafe;
            background: rgba(22, 119, 255, 0.18);
            border: 1px solid rgba(22, 119, 255, 0.3);
        }

        .good-pill {
            color: #bbf7d0;
            background: rgba(34, 197, 94, 0.14);
            border-color: rgba(34, 197, 94, 0.35);
        }

        .warn-pill {
            color: #fde68a;
            background: rgba(245, 158, 11, 0.14);
            border-color: rgba(245, 158, 11, 0.35);
        }

        div[data-testid="stMetric"] {
            background: #101722;
            border: 1px solid #253041;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
        }

        div[data-testid="stMetric"] label {
            color: var(--text-soft);
        }

        div[data-testid="stMetricValue"],
        div[data-testid="stMetricDelta"] {
            color: #f8fafc;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input,
        div[data-testid="stSelectbox"] input {
            background: #101722 !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
        }

        div[data-testid="stTextArea"] textarea::placeholder,
        div[data-testid="stTextInput"] input::placeholder {
            color: #94a3b8 !important;
            opacity: 1;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background: #101722 !important;
            border: 1px dashed #475569 !important;
        }

        div[data-testid="stFileUploaderDropzone"] button {
            background: #1677ff !important;
            border: 1px solid #60a5fa !important;
            color: #ffffff !important;
            font-weight: 700;
        }

        div[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploaderDropzone"] small,
        div[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploaderDropzone"] svg {
            color: #cbd5e1 !important;
            fill: currentColor;
        }

        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] span,
        label {
            color: #e2e8f0 !important;
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 8px;
            border: 1px solid #334155;
            background: #151d2a;
            color: #f8fafc;
        }

        .stButton > button[kind="primary"], .stFormSubmitButton > button {
            background: linear-gradient(90deg, #0f6fff, #168fff);
            border: 0;
            color: #ffffff;
            font-weight: 700;
        }

        /* File uploader uses a separate Streamlit component tree. */
        div[data-testid="stFileUploader"] button,
        div[data-testid="stFileUploaderDropzone"] button,
        button[kind="secondary"]:has(svg[data-testid="stFileUploaderDropzoneUploadIcon"]) {
            background: #1677ff !important;
            border: 1px solid #60a5fa !important;
            color: #ffffff !important;
            opacity: 1 !important;
        }

        div[data-testid="stFileUploader"] button span,
        div[data-testid="stFileUploader"] button p,
        div[data-testid="stFileUploader"] button svg {
            color: #ffffff !important;
            fill: currentColor !important;
        }

        /* Chat input and messages are not rendered as stTextArea widgets. */
        div[data-testid="stChatInput"],
        div[data-testid="stChatInput"] > div {
            background: #101722 !important;
            border-color: #475569 !important;
        }

        div[data-testid="stChatInput"] textarea {
            background: #101722 !important;
            color: #f8fafc !important;
            caret-color: #f8fafc !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #cbd5e1 !important;
            opacity: 1 !important;
        }

        div[data-testid="stChatInput"] button {
            background: #1677ff !important;
            color: #ffffff !important;
            border: 0 !important;
            opacity: 1 !important;
        }

        div[data-testid="stChatMessage"] {
            background: #101722;
            border: 1px solid #2f3b4d;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin: 0.7rem 0;
        }

        div[data-testid="stChatMessage"] p,
        div[data-testid="stChatMessage"] span,
        div[data-testid="stChatMessage"] div {
            color: #e2e8f0 !important;
        }

        /* Streamlit applies muted default text tokens inside the sidebar. */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] small,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #e2e8f0 !important;
            opacity: 1 !important;
        }

        section[data-testid="stSidebar"] [data-testid="stAlert"] p,
        section[data-testid="stSidebar"] [data-testid="stAlert"] div {
            color: #bfdbfe !important;
        }

        /* Tabs and select controls otherwise retain light-theme muted tokens. */
        button[data-baseweb="tab"] {
            color: #cbd5e1 !important;
            font-weight: 600;
            opacity: 1 !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom-color: #1677ff !important;
        }

        button[data-baseweb="tab"]:hover {
            color: #ffffff !important;
            background: #162033 !important;
        }

        div[data-baseweb="select"] > div {
            background: #101722 !important;
            color: #f8fafc !important;
            border-color: #64748b !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {
            color: #f8fafc !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    st.session_state.setdefault("page", "home")
    st.session_state.setdefault("analysis_state", None)
    st.session_state.setdefault("uploaded_df", None)
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("source_name", "Sample dataset")
    st.session_state.setdefault("upload_bytes", None)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("chat_history", [])


def sample_dataset():
    return pd.DataFrame(
        {
            "month": pd.date_range("2026-01-01", periods=12, freq="ME"),
            "category": [
                "Technology",
                "Office Supplies",
                "Furniture",
                "Technology",
                "Office Supplies",
                "Furniture",
                "Technology",
                "Office Supplies",
                "Furniture",
                "Technology",
                "Office Supplies",
                "Furniture",
            ],
            "region": ["West", "East", "South", "North"] * 3,
            "revenue": [120000, 96000, 76000, 132000, 104000, 82000, 142000, 99000, 87000, 161000, 124000, 94000],
            "orders": [420, 350, 280, 455, 390, 310, 470, 365, 335, 520, 430, 340],
            "profit": [24000, 17000, 11200, 28600, 20500, 12400, 31500, 18400, 13900, 38400, 24400, 15100],
            "discount": [0.08, 0.11, 0.2, 0.07, 0.13, 0.21, 0.05, 0.12, 0.18, 0.06, 0.1, 0.23],
            "customer_segment": ["Enterprise", "SMB", "Startup", None, "Enterprise", "SMB", "Enterprise", "SMB", "Startup", "Enterprise", "SMB", "Startup"],
        }
    )


def prepare_dataframe(df):
    prepared = df.copy()
    for column in prepared.columns:
        if prepared[column].dtype == "object":
            converted = pd.to_datetime(prepared[column], errors="coerce")
            if converted.notna().sum() >= max(2, len(prepared) * 0.6):
                prepared[column] = converted
    return prepared


def analyze_dataset(df, question):
    df = prepare_dataframe(df)
    rows_before = len(df)
    cols = len(df.columns)
    missing_total = int(df.isna().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    completeness = 100 if rows_before == 0 or cols == 0 else round((1 - missing_total / (rows_before * cols)) * 100, 1)

    cleaned_df = df.drop_duplicates().copy()

    transformations = []
    if duplicate_count:
        transformations.append(f"Removed {duplicate_count} duplicate rows.")

    for column in cleaned_df.columns:
        missing_count = int(cleaned_df[column].isna().sum())
        if missing_count == 0:
            continue
        if pd.api.types.is_numeric_dtype(cleaned_df[column]):
            cleaned_df[column] = cleaned_df[column].fillna(cleaned_df[column].median())
            transformations.append(f"Filled {missing_count} missing numeric values in {column} using the median.")
        elif pd.api.types.is_datetime64_any_dtype(cleaned_df[column]):
            transformations.append(f"Kept {missing_count} missing date values in {column} for transparency.")
        else:
            cleaned_df[column] = cleaned_df[column].fillna("Unknown")
            transformations.append(f"Filled {missing_count} missing values in {column} using Unknown.")

    if not transformations:
        transformations.append("No cleaning changes were required.")

    numeric_cols = cleaned_df.select_dtypes(include="number").columns.tolist()
    categorical_cols = cleaned_df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = cleaned_df.select_dtypes(include=["datetime64"]).columns.tolist()

    missing_table = (
        df.isna()
        .sum()
        .reset_index()
        .rename(columns={"index": "Column", 0: "Missing values"})
    )
    missing_table["Missing %"] = (
        missing_table["Missing values"] / max(len(df), 1) * 100
    ).round(2)
    missing_table = missing_table.sort_values("Missing values", ascending=False)

    insights = [
        f"The dataset has {rows_before:,} rows and {cols:,} columns before cleaning.",
        f"Overall completeness is {completeness}%, with {missing_total:,} missing values detected.",
        f"{duplicate_count:,} duplicate rows were found and removed.",
    ]

    recommendations = [
        "Review columns with missing values before making business decisions from them.",
        "Use the strongest category and trend patterns as starting points for deeper analysis.",
        "Validate unusual values with the data owner before treating them as true outliers.",
    ]

    if numeric_cols:
        main_metric = numeric_cols[0]
        insights.append(f"The average {main_metric} is {cleaned_df[main_metric].mean():,.2f}.")

    if categorical_cols and numeric_cols:
        cat = categorical_cols[0]
        num = numeric_cols[0]
        top_group = cleaned_df.groupby(cat, dropna=False)[num].sum().sort_values(ascending=False).head(1)
        if not top_group.empty:
            insights.append(f"{top_group.index[0]} contributes the highest total {num}.")
            recommendations.append(f"Investigate what makes {top_group.index[0]} perform strongly and replicate it where possible.")

    if "missing" in question.lower() or missing_total:
        insights.append("Missing-value details are available in the Data quality section.")

    numeric_summary = cleaned_df[numeric_cols].describe().transpose().round(2) if numeric_cols else pd.DataFrame()

    column_profile = pd.DataFrame(
        {
            "Column": cleaned_df.columns,
            "Type": [str(cleaned_df[column].dtype) for column in cleaned_df.columns],
            "Unique values": [int(cleaned_df[column].nunique(dropna=True)) for column in cleaned_df.columns],
            "Missing values": [int(df[column].isna().sum()) for column in cleaned_df.columns],
            "Missing %": [round(float(df[column].isna().mean() * 100), 2) for column in cleaned_df.columns],
        }
    )

    outlier_rows = []
    for column in numeric_cols:
        series = cleaned_df[column].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            count = 0
            lower = q1
            upper = q3
        else:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            count = int(((series < lower) | (series > upper)).sum())
        outlier_rows.append(
            {
                "Column": column,
                "Outliers": count,
                "Lower bound": round(float(lower), 2),
                "Upper bound": round(float(upper), 2),
            }
        )
    outlier_table = pd.DataFrame(outlier_rows)

    top_categories = {}
    for column in categorical_cols[:4]:
        top_categories[column] = (
            cleaned_df[column]
            .value_counts(dropna=False)
            .head(8)
            .rename_axis(column)
            .reset_index(name="Count")
        )

    correlation_pairs = pd.DataFrame()
    if len(numeric_cols) >= 2:
        corr = cleaned_df[numeric_cols].corr().abs()
        pairs = []
        for left_index, left in enumerate(numeric_cols):
            for right in numeric_cols[left_index + 1:]:
                pairs.append(
                    {
                        "Metric 1": left,
                        "Metric 2": right,
                        "Correlation": round(float(corr.loc[left, right]), 3),
                    }
                )
        correlation_pairs = pd.DataFrame(pairs).sort_values("Correlation", ascending=False)

    if not outlier_table.empty and int(outlier_table["Outliers"].sum()) > 0:
        insights.append("Potential outliers were detected in numeric columns; review the Outliers section before final decisions.")

    if not correlation_pairs.empty:
        strongest = correlation_pairs.iloc[0]
        insights.append(
            f"The strongest numeric relationship is between {strongest['Metric 1']} and {strongest['Metric 2']}."
        )

    return {
        "run_id": datetime.now().strftime("run-%Y%m%d-%H%M%S"),
        "question": question,
        "rows_before": rows_before,
        "rows_after": len(cleaned_df),
        "columns": cols,
        "missing_total": missing_total,
        "completeness": completeness,
        "duplicate_count": duplicate_count,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "date_cols": date_cols,
        "cleaned_df": cleaned_df,
        "missing_table": missing_table,
        "numeric_summary": numeric_summary,
        "column_profile": column_profile,
        "outlier_table": outlier_table,
        "top_categories": top_categories,
        "correlation_pairs": correlation_pairs,
        "transformations": transformations,
        "insights": insights,
        "recommendations": recommendations,
        "limitations": [
            "This prototype uses lightweight deterministic analysis.",
            "Business conclusions should be reviewed with domain context.",
            "Only CSV-style tabular data that fits in memory is supported right now.",
        ],
    }


def nav_button(label, page, icon, disabled=False):
    active = st.session_state.page == page
    button_label = f"{icon}  {label}"
    if st.sidebar.button(button_label, width="stretch", disabled=disabled, type="primary" if active else "secondary"):
        st.session_state.page = page
        st.rerun()


def sidebar_nav():
    st.sidebar.markdown("## AutoInsights")
    st.sidebar.caption("AI data analysis workspace")
    st.sidebar.divider()
    nav_button("Home", "home", ":material/home:")
    nav_button("Insights", "insights", ":material/monitoring:", st.session_state.analysis_state is None)
    nav_button("History", "history", ":material/history:", len(st.session_state.history) == 0)


def save_history_entry(state):
    profile = state.get("profile", {})
    entry = {
        "run_id": state["request"].run_id,
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "question": state["request"].problem_statement,
        "source": st.session_state.source_name,
        "rows": profile.get("row_count", 0),
        "columns": profile.get("column_count", 0),
        "missing_values": sum("missing" in warning.lower() for warning in state.get("warnings", [])),
        "duplicates_removed": profile.get("duplicate_rows", 0),
        "state": state,
    }
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:12]


def replace_history_state(state):
    """Keep the matching in-session history entry aligned after approved cleaning."""

    for entry in st.session_state.history:
        if entry["run_id"] == state["request"].run_id:
            entry["state"] = state
            return


def visible_chat_response(response: str) -> str:
    """Remove the obsolete provider-outage prefix from messages saved before the UI update."""

    prefixes = (
        "The configured AI providers are unreachable. Mistral is unreachable. ",
        "The configured AI providers are unreachable. ",
        "Mistral is unreachable. ",
    )
    for prefix in prefixes:
        if response.startswith(prefix):
            return response[len(prefix) :]
    return response


def home_page():
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown('<div class="hero-title">AutoInsights</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="muted">Ask a question about your dataset and get a complete analysis dashboard.</p>',
            unsafe_allow_html=True,
        )

        with st.form("analysis_form", border=True):
            st.subheader("Ask anything about your dataset")
            question = st.text_area(
                "Business question",
                placeholder="Example: Give me the analytics of this dataset and show missing values.",
                height=130,
            )
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
            use_sample = st.checkbox("Use sample data")
            submitted = st.form_submit_button("Run analysis", width="stretch")

        if submitted:
            if not question.strip():
                st.error("Please enter a business question.")
                return

            if uploaded_file is None and not use_sample:
                st.error("Please upload a CSV or choose sample data.")
                return

            try:
                if uploaded_file is not None:
                    upload_bytes = uploaded_file.getvalue()
                    pd.read_csv(BytesIO(upload_bytes), nrows=5)
                    source_name = uploaded_file.name
                else:
                    upload_bytes = None
                    source_name = "Retail Sales Demo Data"
            except Exception:
                st.error("This CSV could not be read. Please check the file format and try again.")
                return

            st.session_state.question = question
            st.session_state.uploaded_df = True
            st.session_state.upload_bytes = upload_bytes
            st.session_state.source_name = source_name
            st.session_state.analysis_state = None
            st.session_state.chat_history = []
            st.session_state.page = "process"
            st.rerun()

        st.info("Enter a prompt and upload a CSV or choose sample data.")

    with right:
        st.subheader("Dashboard preview")
        st.caption("This is the type of analysis AutoInsights will prepare after the process completes.")
        with st.container(horizontal=True):
            st.metric("Records", "12.5k", "+8.7%", border=True)
            st.metric("Completeness", "97.8%", "+1.4%", border=True)
            st.metric("Issues found", "23", "-6", border=True)

        chart_data = pd.DataFrame(
            {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "Revenue": [82, 93, 88, 105, 112, 126],
            }
        )
        fig = px.line(chart_data, x="Month", y="Revenue", markers=True, title="Preview trend")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            """
            <div class="panel">
                <strong>What the app will show</strong><br>
                <span class="muted">Data quality, cleaning, charts, insights, recommendations, and downloads.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def process_page():
    st.markdown('<div class="hero-title">Process</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="muted">AutoInsights shows each analysis step before opening the finished dashboard.</p>',
        unsafe_allow_html=True,
    )

    question = st.session_state.question

    if not question:
        st.warning("No dataset found. Please start from the Home page.")
        return

    steps = [
        ("Intake", "Read prompt and validate the dataset request."),
        ("Profiling", "Inspect rows, columns, types, missing values, and duplicates."),
        ("Cleaning plan", "Identify deterministic cleaning actions without changing the data."),
        ("EDA", "Explore distributions, categories, trends, and relationships."),
        ("Statistics", "Calculate summaries and correlation signals."),
        ("Insights", "Translate analysis evidence into plain-language findings."),
        ("Dashboard", "Prepare KPIs, charts, tables, and downloads."),
    ]

    if st.session_state.analysis_state is None:
        source_type = SourceType.UPLOAD if st.session_state.upload_bytes is not None else SourceType.SAMPLE
        request = AnalysisRequest(
            run_id=f"run-{uuid4().hex[:10]}",
            problem_statement=question,
            source_type=source_type,
        )
        with st.status("Running the LangGraph assessment workflow...", expanded=True) as status:
            uploaded = BytesIO(st.session_state.upload_bytes) if source_type is SourceType.UPLOAD else None
            state = run_analysis(request, uploaded)
            for event in state["progress"]:
                st.write(f"{event['agent']}: {event['message']}")
            if state["status"] is RunStatus.FAILED:
                status.update(label="Analysis could not be completed", state="error")
            else:
                status.update(label="Raw-data assessment complete", state="complete")
        st.session_state.analysis_state = state
        if state["status"] is not RunStatus.FAILED:
            save_history_entry(state)

    state = st.session_state.analysis_state
    if state["status"] is RunStatus.FAILED:
        for error in state["errors"]:
            st.error(error)
        if st.button("Return home"):
            st.session_state.page = "home"
            st.rerun()
        return

    st.success("Assessment complete. Review the raw-data dashboard and proposed cleaning plan next.")
    st.session_state.page = "insights"
    st.rerun()


def render_chart_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig


def dashboard_result_from_state(state):
    """Adapt agent-produced state for the presentation-only dashboard components."""

    frame = pd.DataFrame(state.get("data_records", []))
    profile = state.get("profile", {})
    metadata = state.get("dataframe_metadata", {})
    numeric_cols = [column for column in metadata.get("numeric_columns", []) if column in frame]
    categorical_cols = [column for column in metadata.get("categorical_columns", []) if column in frame]
    date_cols = [column for column in metadata.get("date_columns", []) if column in frame]
    missing = frame.isna().sum()
    missing_table = pd.DataFrame(
        {
            "Column": missing.index,
            "Missing values": missing.values,
            "Missing %": (missing.values / max(len(frame), 1) * 100).round(2),
        }
    ).sort_values("Missing values", ascending=False)
    column_profile = pd.DataFrame(profile.get("columns", [])).rename(
        columns={"name": "Column", "dtype": "Type", "null_percent": "Missing %"}
    )
    if not column_profile.empty:
        column_profile["Unique values"] = [int(frame[column].nunique(dropna=True)) for column in column_profile["Column"]]
        column_profile["Missing values"] = [int(frame[column].isna().sum()) for column in column_profile["Column"]]

    outliers = []
    for column in numeric_cols:
        series = frame[column].dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers.append({"Column": column, "Outliers": int(((series < lower) | (series > upper)).sum()), "Lower bound": round(float(lower), 2), "Upper bound": round(float(upper), 2)})

    correlations = state.get("statistics", {}).get("correlations", {})
    pairs = []
    for index, left in enumerate(numeric_cols):
        for right in numeric_cols[index + 1 :]:
            value = correlations.get(left, {}).get(right)
            if value is not None:
                pairs.append({"Metric 1": left, "Metric 2": right, "Correlation": value})
    top_categories = {
        column: frame[column].value_counts(dropna=False).head(8).rename_axis(column).reset_index(name="Count")
        for column in categorical_cols[:4]
    }
    transformations = state.get("transformations", [])
    return {
        "run_id": state["request"].run_id,
        "question": state["request"].problem_statement,
        "rows_before": profile.get("row_count", len(frame)),
        "rows_after": len(frame),
        "columns": profile.get("column_count", len(frame.columns)),
        "missing_total": int(missing.sum()),
        "completeness": round((1 - missing.sum() / max(len(frame) * max(len(frame.columns), 1), 1)) * 100, 1),
        "duplicate_count": profile.get("duplicate_rows", 0),
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "date_cols": date_cols,
        "cleaned_df": frame,
        "missing_table": missing_table,
        "numeric_summary": frame[numeric_cols].describe().transpose().round(2) if numeric_cols else pd.DataFrame(),
        "column_profile": column_profile,
        "outlier_table": pd.DataFrame(outliers),
        "top_categories": top_categories,
        "correlation_pairs": pd.DataFrame(pairs).sort_values("Correlation", ascending=False) if pairs else pd.DataFrame(),
        "transformations": transformations,
        "insights": [item["text"] for item in state.get("insights", []) if item.get("type") != "recommendation"],
        "recommendations": [item["text"] for item in state.get("insights", []) if item.get("type") == "recommendation"],
    }


def insights_page():
    state = st.session_state.analysis_state
    if state is None:
        st.warning("No completed analysis yet. Please run analysis from the Home page.")
        return

    result = dashboard_result_from_state(state)

    df = result["cleaned_df"]
    st.markdown('<div class="hero-title">Insights</div>', unsafe_allow_html=True)
    st.caption(f'{result["question"]} | {st.session_state.source_name} | {result["run_id"]}')
    if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL:
        st.info("Raw-data assessment only — the charts and metrics below have not been cleaned. Review the plan before approving transformations.")
    else:
        st.success("Approved cleaning has completed. This dashboard reflects the cleaned dataset.")

    with st.container(horizontal=True):
        st.metric("Rows", f'{result["rows_after"]:,}', f'{result["rows_after"] - result["rows_before"]:,}', border=True)
        st.metric("Columns", f'{result["columns"]:,}', border=True)
        st.metric("Completeness", f'{result["completeness"]}%', border=True)
        st.metric("Missing values", f'{result["missing_total"]:,}', border=True)
        st.metric("Duplicates removed", f'{result["duplicate_count"]:,}', border=True)

    top_left, top_right = st.columns([0.95, 1.05], gap="large")

    with top_left:
        with st.container(border=True):
            st.subheader("Key insights")
            for insight in result["insights"]:
                st.write(f"- {insight}")

        with st.container(border=True):
            st.subheader("Recommendations")
            for recommendation in result["recommendations"]:
                st.write(f"- {recommendation}")

    with top_right:
        with st.container(border=True):
            st.subheader("Missing values overview")
            st.dataframe(result["missing_table"], hide_index=True, width="stretch")

    tab_charts, tab_deep_charts, tab_quality, tab_outliers, tab_cleaning, tab_data, tab_downloads = st.tabs(
        ["Charts", "More charts", "Data quality", "Outliers", "Cleaning log", "Data explorer", "Downloads"]
    )

    numeric_cols = result["numeric_cols"]
    categorical_cols = result["categorical_cols"]
    date_cols = result["date_cols"]

    with tab_charts:
        chart_col_1, chart_col_2 = st.columns(2, gap="large")

        with chart_col_1:
            if categorical_cols and numeric_cols:
                grouped = df.groupby(categorical_cols[0], as_index=False)[numeric_cols[0]].sum()
                fig = px.bar(grouped, x=categorical_cols[0], y=numeric_cols[0], title=f"{numeric_cols[0]} by {categorical_cols[0]}")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            elif numeric_cols:
                fig = px.histogram(df, x=numeric_cols[0], title=f"Distribution of {numeric_cols[0]}")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("No numeric columns found for chart generation.")

        with chart_col_2:
            if date_cols and numeric_cols:
                trend = df.groupby(date_cols[0], as_index=False)[numeric_cols[0]].sum()
                fig = px.line(trend, x=date_cols[0], y=numeric_cols[0], markers=True, title=f"{numeric_cols[0]} trend")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            elif len(numeric_cols) >= 2:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], color=categorical_cols[0] if categorical_cols else None, title=f"{numeric_cols[0]} vs {numeric_cols[1]}")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("Upload a dataset with date or multiple numeric columns for more charts.")

        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr()
            fig = px.imshow(corr, text_auto=True, title="Correlation heatmap", color_continuous_scale="RdBu_r")
            st.plotly_chart(render_chart_theme(fig), width="stretch")

    with tab_deep_charts:
        st.subheader("Additional visual analysis")
        chart_col_1, chart_col_2 = st.columns(2, gap="large")

        with chart_col_1:
            if numeric_cols:
                selected_numeric = st.selectbox("Select numeric measure", numeric_cols, key="extra_numeric")
                fig = px.box(df, y=selected_numeric, points="all", title=f"Outlier spread for {selected_numeric}")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("No numeric columns are available for box plot analysis.")

        with chart_col_2:
            if categorical_cols:
                selected_category = st.selectbox("Select category", categorical_cols, key="extra_category")
                counts = df[selected_category].value_counts(dropna=False).head(10).reset_index()
                counts.columns = [selected_category, "Count"]
                fig = px.pie(counts, names=selected_category, values="Count", title=f"{selected_category} share")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("No categorical columns are available for category share analysis.")

        second_col_1, second_col_2 = st.columns(2, gap="large")

        with second_col_1:
            if date_cols and numeric_cols:
                selected_date = st.selectbox("Select date field", date_cols, key="extra_date")
                selected_measure = st.selectbox("Select trend measure", numeric_cols, key="extra_trend_measure")
                trend_df = df.groupby(selected_date, as_index=False)[selected_measure].sum()
                fig = px.area(trend_df, x=selected_date, y=selected_measure, title=f"{selected_measure} area trend")
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("Add a date column and numeric column to see area trend analysis.")

        with second_col_2:
            if categorical_cols and numeric_cols:
                selected_category_for_rank = st.selectbox("Rank category by measure", categorical_cols, key="rank_category")
                selected_rank_measure = st.selectbox("Ranking measure", numeric_cols, key="rank_measure")
                ranking = (
                    df.groupby(selected_category_for_rank, as_index=False)[selected_rank_measure]
                    .sum()
                    .sort_values(selected_rank_measure, ascending=False)
                    .head(10)
                )
                fig = px.bar(
                    ranking,
                    x=selected_rank_measure,
                    y=selected_category_for_rank,
                    orientation="h",
                    title=f"Top {selected_category_for_rank} by {selected_rank_measure}",
                )
                st.plotly_chart(render_chart_theme(fig), width="stretch")
            else:
                st.info("Add category and numeric columns to see ranking analysis.")

        if len(numeric_cols) >= 3:
            st.subheader("Bubble relationship")
            x_axis = st.selectbox("Bubble X axis", numeric_cols, key="bubble_x")
            y_axis_options = [column for column in numeric_cols if column != x_axis] or numeric_cols
            y_axis = st.selectbox("Bubble Y axis", y_axis_options, key="bubble_y")
            size_options = [column for column in numeric_cols if column not in {x_axis, y_axis}] or numeric_cols
            size_axis = st.selectbox("Bubble size", size_options, key="bubble_size")
            fig = px.scatter(
                df,
                x=x_axis,
                y=y_axis,
                size=size_axis,
                color=categorical_cols[0] if categorical_cols else None,
                title=f"{x_axis} vs {y_axis}, sized by {size_axis}",
            )
            st.plotly_chart(render_chart_theme(fig), width="stretch")

    with tab_quality:
        st.subheader("Column profile")
        st.dataframe(result["column_profile"], hide_index=True, width="stretch")

        st.subheader("Numeric summary")
        if result["numeric_summary"].empty:
            st.info("No numeric summary is available for this dataset.")
        else:
            st.dataframe(result["numeric_summary"], width="stretch")

        st.subheader("Missing values")
        st.dataframe(result["missing_table"], hide_index=True, width="stretch")

        if result["top_categories"]:
            st.subheader("Top values by category")
            for column, category_df in result["top_categories"].items():
                with st.expander(f"Top values in {column}"):
                    st.dataframe(category_df, hide_index=True, width="stretch")

        if not result["correlation_pairs"].empty:
            st.subheader("Strongest numeric relationships")
            st.dataframe(result["correlation_pairs"].head(10), hide_index=True, width="stretch")

    with tab_outliers:
        st.subheader("Outlier scan")
        if result["outlier_table"].empty:
            st.info("No numeric columns were available for outlier scanning.")
        else:
            st.dataframe(result["outlier_table"], hide_index=True, width="stretch")
            total_outliers = int(result["outlier_table"]["Outliers"].sum())
            if total_outliers:
                st.warning(f"Detected {total_outliers:,} potential outlier values using the IQR rule.")
            else:
                st.success("No potential outliers were detected with the IQR rule.")

    with tab_cleaning:
        if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL:
            st.subheader("Proposed cleaning plan")
            st.caption("No changes have been made. Approving this plan reruns profiling, analysis, visualizations, and reporting on cleaned data.")
            st.dataframe(state.get("cleaning_plan", []), hide_index=True, width="stretch")
            if st.button("Approve cleaning and refresh analysis", type="primary", width="stretch"):
                with st.status("Applying the approved plan and regenerating the dashboard...", expanded=True) as status:
                    updated_state = execute_cleaning(state)
                    for event in updated_state["progress"][len(state["progress"]) :]:
                        st.write(f"{event['agent']}: {event['message']}")
                    status.update(label="Cleaned analysis complete", state="complete")
                st.session_state.analysis_state = updated_state
                replace_history_state(updated_state)
                st.rerun()
        else:
            st.subheader("Transformation log")
            st.dataframe(result["transformations"], hide_index=True, width="stretch")
            st.info(f'Rows before cleaning: {result["rows_before"]:,} | Rows after cleaning: {result["rows_after"]:,}')

    with tab_data:
        st.subheader("Cleaned data")
        filter_col_1, filter_col_2 = st.columns(2, gap="medium")
        with filter_col_1:
            search = st.text_input("Search cleaned data", placeholder="Type any value to filter rows")
        with filter_col_2:
            selected_column = st.selectbox("Inspect column", ["All columns"] + list(df.columns), key="inspect_column")

        if selected_column != "All columns":
            st.write(f"Showing details for `{selected_column}`")
            st.table(
                {
                    "Type": str(df[selected_column].dtype),
                    "Unique values": int(df[selected_column].nunique(dropna=True)),
                    "Missing after cleaning": int(df[selected_column].isna().sum()),
                }
            )

        display_df = df
        if search:
            mask = df.astype(str).apply(lambda column: column.str.contains(search, case=False, na=False)).any(axis=1)
            display_df = df[mask]
        st.dataframe(display_df, hide_index=True, width="stretch")

    with tab_downloads:
        st.subheader("Download outputs")
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download cleaned CSV",
            data=csv_data,
            file_name="cleaned_data.csv",
            mime="text/csv",
            width="stretch",
        )

        report_path = state.get("assessment_report_path") if state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL else state.get("report_path")
        if report_path and Path(report_path).is_file():
            st.download_button(
                "Download HTML report",
                data=Path(report_path).read_bytes(),
                file_name=Path(report_path).name,
                mime="text/html",
                width="stretch",
            )

    st.divider()
    st.subheader("Ask AutoInsights")
    st.caption("Ask about the current report, data quality, findings, charts, or request supported actions such as executing the proposed cleaning plan.")
    with st.sidebar:
        st.divider()
        st.subheader("Chat settings")
        st.caption("Choose the AI provider and model for analysis questions.")
        provider = st.selectbox("Provider", ["Groq", "Mistral"], help="Groq is selected by default.")
        selected_model = st.text_input(
            "Model ID",
            value=GROQ_MODEL if provider == "Groq" else MISTRAL_MODEL,
            key=f"chat_model_{provider.lower()}",
        )
        st.divider()
        st.caption("Prototype navigation")
        st.info("Run analysis from Home. The app opens the workflow first, then the Insights dashboard.")
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.write(visible_chat_response(item["content"]))
    message = st.chat_input("Ask about this analysis")
    if message:
        st.session_state.chat_history.append({"role": "user", "content": message})
        with st.chat_message("user"):
            st.write(message)
        with st.chat_message("assistant"):
            response, updated_state = handle_chat_message(
                message, state, provider=provider.lower(), model=selected_model or None
            )
            clean_response = visible_chat_response(response.response)
            st.write(clean_response)
        st.session_state.chat_history.append({"role": "assistant", "content": clean_response})
        if response.state_changed:
            st.session_state.analysis_state = updated_state
            replace_history_state(updated_state)
            st.rerun()


def history_page():
    st.markdown('<div class="hero-title">History</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="muted">Review previous analysis runs, compare quality signals, and reopen a dashboard.</p>',
        unsafe_allow_html=True,
    )

    history = st.session_state.history
    if not history:
        st.info("No analysis history yet. Run an analysis from the Home page first.")
        return

    summaries = {entry["run_id"]: dashboard_result_from_state(entry["state"]) for entry in history}
    total_runs = len(history)
    total_rows = sum(summaries[entry["run_id"]]["rows_after"] for entry in history)
    avg_completeness = round(sum(summaries[entry["run_id"]]["completeness"] for entry in history) / total_runs, 1)
    total_missing = sum(entry["missing_values"] for entry in history)

    with st.container(horizontal=True):
        st.metric("Total runs", f"{total_runs:,}", border=True)
        st.metric("Rows analyzed", f"{total_rows:,}", border=True)
        st.metric("Avg completeness", f"{avg_completeness}%", border=True)
        st.metric("Missing values found", f"{total_missing:,}", border=True)

    history_df = pd.DataFrame(
        [
            {
                "Run ID": entry["run_id"],
                "Created": entry["created_at"],
                "Source": entry["source"],
                "Question": entry["question"],
                "Rows": summaries[entry["run_id"]]["rows_after"],
                "Columns": summaries[entry["run_id"]]["columns"],
                "Completeness": f'{summaries[entry["run_id"]]["completeness"]}%',
                "Missing": entry["missing_values"],
                "Duplicates removed": entry["duplicates_removed"],
            }
            for entry in history
        ]
    )

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        with st.container(border=True):
            st.subheader("Analysis runs")
            st.dataframe(history_df, hide_index=True, width="stretch")

    with right:
        with st.container(border=True):
            st.subheader("Open previous dashboard")
            selected_run = st.selectbox(
                "Select run",
                [entry["run_id"] for entry in history],
                format_func=lambda run_id: next(
                    f"{entry['created_at']} - {entry['source']}" for entry in history if entry["run_id"] == run_id
                ),
            )

            selected_entry = next(entry for entry in history if entry["run_id"] == selected_run)
            st.write(f"**Question:** {selected_entry['question']}")
            st.write(f"**Source:** {selected_entry['source']}")
            st.write(f"**Rows:** {selected_entry['rows']:,}")
            st.write(f"**Missing values:** {selected_entry['missing_values']:,}")

            if st.button("Open in Insights", width="stretch", type="primary"):
                st.session_state.analysis_state = selected_entry["state"]
                st.session_state.question = selected_entry["question"]
                st.session_state.source_name = selected_entry["source"]
                st.session_state.page = "insights"
                st.rerun()

            if st.button("Clear history", width="stretch"):
                st.session_state.history = []
                st.session_state.page = "home"
                st.rerun()

    st.subheader("History analysis")
    trend_df = pd.DataFrame(
        {
            "Run": list(range(1, total_runs + 1)),
            "Completeness": [summaries[entry["run_id"]]["completeness"] for entry in reversed(history)],
            "Missing values": [entry["missing_values"] for entry in reversed(history)],
            "Rows": [entry["rows"] for entry in reversed(history)],
        }
    )

    chart_col_1, chart_col_2 = st.columns(2, gap="large")
    with chart_col_1:
        fig = px.line(trend_df, x="Run", y="Completeness", markers=True, title="Completeness across runs")
        st.plotly_chart(render_chart_theme(fig), width="stretch")

    with chart_col_2:
        fig = px.bar(trend_df, x="Run", y="Missing values", title="Missing values found by run")
        st.plotly_chart(render_chart_theme(fig), width="stretch")


def build_report_html(result):
    insight_items = "".join(f"<li>{item}</li>" for item in result["insights"])
    recommendation_items = "".join(f"<li>{item}</li>" for item in result["recommendations"])
    cleaning_items = "".join(f"<li>{item}</li>" for item in result["transformations"])
    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>AutoInsights report</title>
        <style>
            body {{ background: #0b0f17; color: #e5e7eb; font-family: Arial, sans-serif; padding: 32px; }}
            section {{ border: 1px solid #273244; border-radius: 8px; padding: 18px; margin-bottom: 18px; background: #111827; }}
            h1, h2 {{ color: #ffffff; }}
            .metric {{ display: inline-block; min-width: 150px; margin: 8px; padding: 12px; background: #0f172a; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <h1>AutoInsights report</h1>
        <p>{result["question"]}</p>
        <section>
            <h2>Summary</h2>
            <div class="metric">Rows: {result["rows_after"]:,}</div>
            <div class="metric">Columns: {result["columns"]:,}</div>
            <div class="metric">Completeness: {result["completeness"]}%</div>
            <div class="metric">Missing values: {result["missing_total"]:,}</div>
        </section>
        <section><h2>Insights</h2><ul>{insight_items}</ul></section>
        <section><h2>Recommendations</h2><ul>{recommendation_items}</ul></section>
        <section><h2>Cleaning log</h2><ul>{cleaning_items}</ul></section>
    </body>
    </html>
    """


init_state()
apply_theme()
sidebar_nav()

if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "process":
    process_page()
elif st.session_state.page == "insights":
    insights_page()
elif st.session_state.page == "history":
    history_page()
