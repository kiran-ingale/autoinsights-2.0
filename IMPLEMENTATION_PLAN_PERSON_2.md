# Implementation Plan Person 2

## Role

Own the Streamlit user experience and interactive analysis dashboard.

## Goal

Let a user upload a CSV or select sample data, submit an analysis question, follow the workflow progress, explore its visualizations, and download the generated outputs.

## Owned areas

```text
frontend/streamlit_app.py
frontend/components/
frontend/styles/
tests/test_frontend_smoke.py
```

Do not modify agent logic or report rendering. Consume the shared graph interface and state contract supplied by Person 1.

## Deliverables

1. Streamlit application shell and input form.
2. In-process workflow execution with visible progress.
3. Dashboard for KPI cards, charts, data exploration, findings, and downloads.
4. Input validation and friendly error states.
5. Basic smoke test or documented manual verification steps.

## Implementation tasks

### 1. Build the input experience

Include:

- Problem statement text area
- Optional domain and constraints inputs
- CSV uploader limited to an agreed safe size
- “Use sample data” option
- Run button disabled until request rules are satisfied

Store the latest completed state in `st.session_state` so filters and tab changes do not rerun analysis.

### 2. Integrate the graph

- Call Person 1’s `run_analysis(request, uploaded_file)` directly.
- Use `st.status` or an equivalent status component to show graph messages.
- Render failure state from `state.errors`; never show a raw traceback to the user.
- Show source and run ID once complete.

Use a mock state fixture until the graph is merged so dashboard development can proceed independently.

### 3. Build the dashboard

Organize the default view from summary to detail:

1. Run summary: source, rows, columns, completion state, warnings.
2. KPI cards: record count, completeness, duplicates removed, and relevant dynamic metrics.
3. Charts: render the validated Plotly specs from `state.chart_specs`.
4. Data explorer: filtered cleaned-data table and CSV download.
5. Findings: observations, recommendations, limitations, and transformation log.
6. Report download: display only when `state.report_path` exists.

Use only meaningful controls: date range if a date field exists and one high-value category filter if it meaningfully applies. Hide unavailable visuals instead of inserting empty placeholders.

### 4. UX checks

- Wide layout with readable chart sizes.
- Clear empty state before a run.
- Spinner/status while graph executes.
- Helpful error message for unsupported or malformed files.
- No dashboard section assumes a field exists without checking it.

## Handoff requirements

Ask Person 1 to provide a fixture with at least one numeric, date, and categorical field. Ask Person 3 for stable artifact paths and download-helper functions.

## Acceptance criteria

- A user can submit a CSV and question without needing an API server.
- Graph progress and errors are visible and understandable.
- Charts, KPIs, insights, and cleaned data display correctly from a completed state.
- Downloads work for cleaned CSV and report when available.
- The page handles a run with limited or no numeric data gracefully.
