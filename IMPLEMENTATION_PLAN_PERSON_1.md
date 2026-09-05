# Implementation Plan Person 1

## Role

Own the LangGraph agent workflow and deterministic data-analysis pipeline.

## Goal

Expose one stable function that receives an analysis request and optional CSV, then returns a complete structured analysis state that the Streamlit UI and reporting layer can consume.

## Owned areas

```text
app/graph/
app/agents/
app/schemas/
tests/test_graph.py
tests/test_agents.py
```

Do not edit Streamlit page layout, report templates, or artifact storage implementation except where the shared contract requires it.

## Deliverables

1. `AnalysisRequest` Pydantic model.
2. Typed `AnalysisState` shared by all agents.
3. LangGraph workflow with conditional routing.
4. Agent nodes for intake, acquisition, profiling, cleaning, EDA, feature preparation, statistics, insights, and visualization metadata.
5. Unit and end-to-end graph tests.

## Implementation tasks

### 1. Define the shared contract first

Create models that include:

```text
run_id, problem_statement, domain, constraints, source_type,
input_path, artifact_dir, cleaned_path, profile, transformations,
observations, statistics, insights, chart_specs, warnings, errors,
status, report_path
```

Share this proposal before building agent logic. Person 2 depends on chart-spec and insight fields; Person 3 depends on artifact paths and report-ready fields.

### 2. Build the graph

Create `run_analysis(request, uploaded_file) -> AnalysisState`.

Graph path:

```text
intake -> upload available?
  yes -> profiling
  no  -> sample acquisition -> profiling
profiling -> cleaning -> EDA -> feature preparation -> statistics
-> insights -> visualization metadata -> reporting handoff -> complete
```

Route unrecoverable errors to a terminal failure state. Add progress messages after every node so the UI can communicate what is happening.

### 3. Build agent nodes

- **Intake:** validate request fields and CSV readability.
- **Acquisition:** select an approved local sample dataset when no file exists.
- **Profiling:** schema, row/column counts, null rates, duplicate count, numeric summary, and warnings.
- **Cleaning:** remove exact duplicates, standardize column names, handle safely imputable nulls, and log each change.
- **EDA:** distributions, categorical counts, date detection, correlations, and initial observations.
- **Feature preparation:** identify numeric/categorical/date fields and propose usable transformations without overwriting the cleaned dataset.
- **Statistics:** descriptive values and meaningful numeric associations; do not make unsupported causal claims.
- **Insights:** generate evidence-linked findings, recommendations, and limitations from prior state.
- **Visualization metadata:** select only charts supported by the actual data and return serializable Plotly figure specifications.

### 4. Tests

- Small valid CSV completes successfully.
- No upload uses sample data.
- Invalid or empty CSV reaches a friendly error state.
- Messy CSV logs duplicates and null-related transformations.
- Chart specs contain only supported chart types.

## Handoff to Person 2

Provide:

- Exact import path and signature for `run_analysis`.
- A representative saved `AnalysisState` fixture or mock JSON.
- Field definitions for `profile`, `chart_specs`, `insights`, `warnings`, and `status`.

## Handoff to Person 3

Provide:

- All artifact-path fields and expected file formats.
- Transformation-log schema.
- Report-ready structured sections: request, source, profile, observations, statistics, insights, limitations, and chart references.

## Acceptance criteria

- The graph completes for both uploaded and sample data.
- Every state change is serializable and auditable.
- Agents never depend on Streamlit objects.
- Bad inputs produce clear state errors rather than uncaught exceptions.
- Automated graph tests pass.
