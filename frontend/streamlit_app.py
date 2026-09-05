import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


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
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    st.session_state.setdefault("page", "home")
    st.session_state.setdefault("analysis_result", None)
    st.session_state.setdefault("uploaded_df", None)
    st.session_state.setdefault("question", "")
    st.session_state.setdefault("source_name", "Sample dataset")
    st.session_state.setdefault("history", [])


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
    nav_button("Insights", "insights", ":material/monitoring:", st.session_state.analysis_result is None)
    nav_button("Process", "process", ":material/account_tree:", st.session_state.uploaded_df is None)
    nav_button("History", "history", ":material/history:", len(st.session_state.history) == 0)
    st.sidebar.divider()
    st.sidebar.caption("Prototype navigation")
    st.sidebar.info("Run analysis from Home. The app opens Process first, then the Insights dashboard.")


def save_history_entry(result):
    entry = {
        "run_id": result["run_id"],
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "question": result["question"],
        "source": st.session_state.source_name,
        "rows": result["rows_after"],
        "columns": result["columns"],
        "completeness": result["completeness"],
        "missing_values": result["missing_total"],
        "duplicates_removed": result["duplicate_count"],
        "result": result,
    }
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:12]


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
                    df = pd.read_csv(uploaded_file)
                    source_name = uploaded_file.name
                else:
                    df = sample_dataset()
                    source_name = "Built-in sample dataset"
            except Exception:
                st.error("This CSV could not be read. Please check the file format and try again.")
                return

            if df.empty:
                st.error("The dataset is empty. Please upload a CSV with at least one row.")
                return

            st.session_state.question = question
            st.session_state.uploaded_df = df
            st.session_state.source_name = source_name
            st.session_state.analysis_result = None
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

    df = st.session_state.uploaded_df
    question = st.session_state.question

    if df is None:
        st.warning("No dataset found. Please start from the Home page.")
        return

    steps = [
        ("Intake", "Read prompt and validate the dataset request."),
        ("Profiling", "Inspect rows, columns, types, missing values, and duplicates."),
        ("Cleaning", "Handle duplicate rows, missing values, and simple type issues."),
        ("EDA", "Explore distributions, categories, trends, and relationships."),
        ("Statistics", "Calculate summaries and correlation signals."),
        ("Insights", "Translate analysis evidence into plain-language findings."),
        ("Dashboard", "Prepare KPIs, charts, tables, and downloads."),
    ]

    left, right = st.columns([0.72, 1.28], gap="large")
    progress = st.progress(0)

    with left:
        step_area = st.empty()

    with right:
        summary_area = st.empty()

    for index, (name, description) in enumerate(steps, start=1):
        with step_area.container():
            for item_index, (item_name, item_description) in enumerate(steps, start=1):
                if item_index < index:
                    pill = '<span class="status-pill good-pill">Completed</span>'
                    card_class = "step-card"
                elif item_index == index:
                    pill = '<span class="status-pill">Running</span>'
                    card_class = "step-card step-active"
                else:
                    pill = '<span class="status-pill warn-pill">Pending</span>'
                    card_class = "step-card"

                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <strong>{item_name}</strong> {pill}<br>
                        <span class="muted">{item_description}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with summary_area.container():
            st.subheader(f"{name} is running")
            if name == "Profiling":
                st.dataframe(df.head(8), hide_index=True, width="stretch")
            elif name == "Cleaning":
                missing_preview = df.isna().sum().reset_index()
                missing_preview.columns = ["Column", "Missing values"]
                st.dataframe(missing_preview, hide_index=True, width="stretch")
            else:
                st.write(description)

        progress.progress(index / len(steps))
        time.sleep(0.7)

    st.session_state.analysis_result = analyze_dataset(df, question)
    save_history_entry(st.session_state.analysis_result)
    st.success("Analysis complete. Opening the Insights dashboard...")
    time.sleep(0.8)
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


def insights_page():
    result = st.session_state.analysis_result
    if result is None:
        st.warning("No completed analysis yet. Please run analysis from the Home page.")
        return

    df = result["cleaned_df"]
    st.markdown('<div class="hero-title">Insights</div>', unsafe_allow_html=True)
    st.caption(f'{result["question"]} | {st.session_state.source_name} | {result["run_id"]}')

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
        st.subheader("Transformation log")
        for item in result["transformations"]:
            st.write(f"- {item}")
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

        report_html = build_report_html(result)
        st.download_button(
            "Download HTML report",
            data=report_html,
            file_name="autoinsights_report.html",
            mime="text/html",
            width="stretch",
        )


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

    total_runs = len(history)
    total_rows = sum(entry["rows"] for entry in history)
    avg_completeness = round(sum(entry["completeness"] for entry in history) / total_runs, 1)
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
                "Rows": entry["rows"],
                "Columns": entry["columns"],
                "Completeness": f'{entry["completeness"]}%',
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
                st.session_state.analysis_result = selected_entry["result"]
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
            "Completeness": [entry["completeness"] for entry in reversed(history)],
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
