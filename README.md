# AutoInsights

AutoInsights is an agentic data-analysis application that turns a business question and optional CSV dataset into a reproducible analysis, visualizations, recommendations, and a downloadable report.

This prototype uses Streamlit for the interactive experience and LangGraph to coordinate specialized analysis agents. It intentionally does not include a separate backend service.

## What it does

1. Accepts a problem statement, domain, constraints, and an optional CSV file.
2. Profiles the dataset and flags missing data, duplicates, anomalous values, and schema issues.
3. Cleans data and records each transformation.
4. Performs exploratory analysis and creates interactive charts.
5. Prepares useful features and runs lightweight statistical analysis.
6. Converts findings into plain-language insights and actionable recommendations.
7. Presents results in an interactive Streamlit dashboard, produces an HTML report, and preserves the run artifacts for auditability.

If no dataset is supplied, the system initially supports safe sample-dataset acquisition for demonstration. Extensible data-source adapters can later add approved APIs, UCI, or Kaggle integrations.

## Architecture

```text
Streamlit UI and Dashboard
    |
    | validates input, starts a run, displays progress
    v
LangGraph orchestration
    |
    +--> Intake Agent
    +--> Data Acquisition Agent (only when no upload is available)
    +--> Profiling Agent
    +--> Cleaning Agent
    +--> EDA Agent
    +--> Feature Engineering Agent
    +--> Statistical Analysis Agent
    +--> Insight Agent
    +--> Visualization and Dashboard Agent
    +--> Reporting Agent
    |
    v
Run artifacts: cleaned CSV, charts, transformation log, report
```

## Agent workflow

The graph owns the shared `AnalysisState`, which includes the request, dataset locations, diagnostics, artifacts, messages, and errors. Nodes add structured results to state instead of passing untracked files directly between agents.

The manager logic uses conditional edges to choose the data-acquisition path when a dataset was not uploaded and routes failures to a terminal error state. Every run receives a unique ID and isolated artifact directory.

| Agent | Responsibility | Primary output |
| --- | --- | --- |
| Intake | Validate and normalize the request | Structured analysis request |
| Acquisition | Supply an approved sample dataset when required | Input CSV and source metadata |
| Profiling | Inspect schema, nulls, duplicates, and summary statistics | Data-quality profile |
| Cleaning | Apply deterministic cleaning rules and log changes | Cleaned CSV and transformation log |
| EDA | Find distributions, correlations, and segment patterns | Charts and observations |
| Feature engineering | Encode, scale, and derive model-ready features | Feature dataset summary |
| Statistics | Run relevant descriptive tests and association checks | Statistical findings |
| Insight generation | Translate evidence into decisions and caveats | Recommendations |
| Visualization and dashboard | Select charts and prepare dashboard-ready metric data | Interactive charts and metric model |
| Reporting | Assemble artifacts into an HTML report | Final report path |

## Tech stack

- **Application and dashboard:** Streamlit
- **Orchestration:** LangGraph
- **Data:** pandas, NumPy, scikit-learn
- **Charts and dashboard:** Plotly, Streamlit
- **Reports:** Jinja2 HTML (PDF export can be added as an adapter)
- **Tests:** pytest

## Planned project layout

```text
autoinsights/
├── app/
│   ├── agents/                  # One module per specialist agent
│   ├── graph/                   # LangGraph state, routing, workflow
│   ├── services/                # Files, reports, charts, data utilities
│   ├── schemas/                 # Pydantic request/response models
│   └── config.py
├── frontend/
│   └── streamlit_app.py         # Streamlit UI and dashboard
├── tests/
├── artifacts/                   # Git-ignored per-run outputs
├── .env.example
├── pyproject.toml
└── README.md
```

## Local development

The implementation will use Python 3.11+ and a virtual environment.

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
streamlit run frontend/streamlit_app.py
```

Streamlit invokes the graph in-process and writes every run to its own artifact directory. Status containers and session state display workflow progress without a separate API or job queue.

## Dashboard experience

Each completed run opens on a summary-first dashboard in Streamlit. The dashboard is designed for analysis rather than a static chart gallery:

- **Run overview:** input source, processed rows, data-quality warnings, and latest run status.
- **Key metrics:** dynamically selected KPI cards, such as record count, completeness, numeric averages, or task-specific outcomes.
- **Trends and distributions:** time-series lines when a date column is present, histograms for key numeric fields, and categorical breakdowns.
- **Relationships:** correlation heatmap and scatter plots for the strongest numeric associations.
- **Data explorer:** searchable, filtered view of cleaned data plus download controls.
- **Findings:** evidence-linked observations, recommendations, transformation log, and limitations.

The analysis agents return chart specifications and compact aggregated data to the Streamlit application. Streamlit renders those as native Plotly charts, which keeps the UI responsive and makes filters apply consistently across cards, charts, and tables. The saved HTML report receives static versions of the same validated visuals.

The initial dashboard uses a small number of meaningful global controls: a date range when available, a categorical segment selector when useful, and an option to choose the measure shown. It will not display metrics that cannot be defined or reconciled from the input data.

## Delivery phases

1. **Foundation:** Python package, settings, Streamlit shell, and local artifact storage.
2. **Workflow:** Typed LangGraph state, all agent nodes, conditional routing, and run lifecycle tracking.
3. **Analysis:** CSV upload, profile/clean/EDA/statistics agents, charts, dashboard data, and HTML reporting.
4. **Dashboard:** Streamlit KPI cards, filters, Plotly charts, cleaned-data explorer, and download controls.
5. **Product polish:** Streamlit run progress, artifact downloads, input validation, error display, and tests.
6. **Extensions:** authenticated external sources, LLM-powered narrative generation, model training, PDF export, persistent job storage, and an optional FastAPI API for multi-user or integration scenarios.

## Design principles

- **Reproducible:** persist inputs, cleaned data, transformations, and generated outputs per run.
- **Transparent:** show warnings, assumptions, and source metadata in the report.
- **Safe by default:** do not scrape arbitrary URLs or fetch credentials-protected data automatically.
- **LLM optional:** core analysis remains deterministic; an LLM can enrich insights later without becoming the sole source of evidence.
- **Extensible:** agents are independently testable functions connected through the graph state.
- **Prototype-first:** Streamlit runs the graph directly; add FastAPI only when a separate API, asynchronous jobs, or multi-user scaling is required.

## Initial scope and limits

The first working version targets tabular CSV data that fits in local memory. It is not a replacement for expert statistical review and will surface uncertainty instead of overstating conclusions. File-size limits, allowed extensions, and source approval controls are enforced in the Streamlit application.
