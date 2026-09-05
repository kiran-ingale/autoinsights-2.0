# AutoInsights Prototype Implementation Plan

## Objective

Deliver a local Streamlit prototype where a user uploads a CSV, describes an analysis goal, runs a LangGraph multi-agent workflow, explores interactive visualizations, and downloads an HTML report.

## Scope

### Included

- CSV upload with file-size and schema validation
- Streamlit input form, progress display, dashboard, data explorer, and downloads
- LangGraph workflow for intake, profiling, cleaning, EDA, feature preparation, statistics, insights, visualization, and reporting
- Per-run artifacts: input data, cleaned data, transformation log, charts, and HTML report
- Sample data option when no CSV is uploaded
- Automated tests for the graph, core data services, and report creation

### Excluded from the prototype

- FastAPI or a separate backend service
- Authentication, multi-user access, background queues, and database persistence
- Arbitrary web scraping and credential-protected source integrations
- Model training, production deployment, and PDF export

## Team ownership

| Workstream | Owner | Main areas | Depends on |
| --- | --- | --- | --- |
| Agent workflow | Person 1 | `app/graph/`, `app/agents/`, shared state, data analysis | Shared contracts approved first |
| Streamlit dashboard | Person 2 | `frontend/streamlit_app.py`, UI components, dashboard rendering | Shared state contract and mock results |
| Artifacts and quality | Person 3 | `app/services/`, reports, sample data, tests, Git integration | Shared contracts and outputs from Persons 1–2 |

## Shared contracts

Person 1 creates these first and treats them as the interface between all workstreams.

```text
AnalysisRequest
  run_id, problem_statement, domain, constraints, source_type

AnalysisState
  request, artifact_dir, input_path, cleaned_path, dataframe_metadata,
  profile, transformations, observations, statistics, insights,
  chart_specs, report_path, warnings, errors, status

run_analysis(request, uploaded_file) -> AnalysisState
```

Rules:

- Each agent returns structured state updates; agents do not rely on UI objects.
- Every file belongs under `artifacts/<run_id>/`.
- Charts are passed as serializable Plotly JSON specifications or explicitly named artifact files.
- Errors are recorded in `state.errors` and shown to users without exposing stack traces.

## Milestones

### Milestone 0 — Project foundation

**Owner:** Person 3  
**Goal:** Create a clean, runnable skeleton.

- Add `app/`, `frontend/`, `tests/`, and `artifacts/` directories.
- Add package initialization files and `.gitignore` for `.venv/`, `artifacts/`, `__pycache__/`, and `.env`.
- Validate `requirements.txt` installation in a virtual environment.
- Add sample CSV data and artifact-directory helper.

**Done when:** `streamlit run frontend/streamlit_app.py` starts and shows a placeholder page.

### Milestone 1 — Workflow and data pipeline

**Owner:** Person 1  
**Goal:** Build a deterministic LangGraph workflow that accepts a CSV and returns usable structured results.

- Define Pydantic request models and `AnalysisState`.
- Build LangGraph nodes in this order:
  1. Intake and validation
  2. Sample data acquisition when no upload exists
  3. Data profiling
  4. Cleaning with transformation log
  5. EDA and chart specifications
  6. Feature preparation
  7. Descriptive statistics and correlations
  8. Insight generation
  9. Reporting handoff
- Add conditional routing for uploaded versus sample data and for terminal failures.
- Save cleaned CSV and transformation log.

**Done when:** A test CSV completes the graph and returns profile, insights, chart specs, and paths to saved artifacts.

### Milestone 2 — Dashboard and user experience

**Owner:** Person 2  
**Goal:** Make the results easy to understand and explore.

- Create input fields for question, domain, constraints, and CSV upload.
- Add a “Use sample data” option.
- Run the graph in-process and show agent progress with `st.status`.
- Render completed results in dashboard sections:
  - Run summary and data-quality warnings
  - KPI cards
  - Distribution and categorical charts
  - Time-series chart when an eligible date column exists
  - Correlation heatmap when enough numeric fields exist
  - Cleaned-data explorer with filters and CSV download
  - Insights, recommendations, transformations, and limitations
- Render friendly validation and failure messages.

**Done when:** A user can complete an end-to-end run from a browser with an uploaded sample CSV.

### Milestone 3 — Reports, QA, and integration

**Owner:** Person 3  
**Goal:** Produce an auditable deliverable and ensure the prototype is reliable.

- Build a Jinja2 HTML report from `AnalysisState`.
- Include request metadata, source information, quality warnings, transformations, visualizations, findings, and limitations.
- Add download links for cleaned CSV and report.
- Write tests for artifact storage, report rendering, malformed CSV handling, and a complete sample-data run.
- Merge workstreams and resolve interface differences.

**Done when:** A run produces a self-contained HTML report and the test suite passes.

### Milestone 4 — Demo readiness

**Owners:** All

- Test three datasets: sales/time-series, customer/category, and messy data with nulls/duplicates.
- Confirm every dashboard chart is meaningful for the available columns; hide unsupported charts.
- Confirm artifacts are isolated by run ID.
- Update README with final setup and demo instructions.
- Prepare one short demo script: upload → run → explore → download.

**Done when:** A fresh clone can install dependencies, launch Streamlit, and complete the demo without manual code changes.

## Suggested schedule

| Day | Person 1 | Person 2 | Person 3 |
| --- | --- | --- | --- |
| 1 | State contract and graph skeleton | UI shell using mock state | Folder structure, `.gitignore`, sample data |
| 2 | Profiling, cleaning, EDA nodes | Upload, validation, run controls | Artifact service and report template |
| 3 | Statistics and insight nodes | KPI cards, charts, data explorer | Tests and report integration |
| 4 | Graph tests and bug fixes | UX and error-state polish | Merge, end-to-end QA, README |

## Git workflow

Create a branch per workstream:

```powershell
git checkout -b feature/agent-workflow
git checkout -b feature/streamlit-dashboard
git checkout -b feature/reporting-quality
```

- Keep commits small and scoped, for example `feat: add profiling agent`.
- Do not edit the shared state contract without notifying the other two people.
- Merge Person 1’s contract first, then Person 2 and Person 3 work.
- Before merging a pull request, run `pytest` and a manual Streamlit smoke test.

## Definition of done

The prototype is complete when it can:

1. Accept a CSV or selected sample dataset.
2. Run the LangGraph workflow without an external backend.
3. Show profiling, cleaning actions, interactive dashboard charts, and evidence-based insights.
4. Let the user explore and download cleaned data.
5. Generate a readable HTML report stored with the run artifacts.
6. Handle invalid files and analysis errors gracefully.
7. Pass the agreed automated tests and a three-dataset manual smoke test.
