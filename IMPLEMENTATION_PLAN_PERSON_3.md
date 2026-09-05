# Implementation Plan Person 3

## Role

Own artifact management, sample data, HTML reporting, testing infrastructure, and integration quality.

## Goal

Ensure every analysis run produces well-organized, downloadable, reproducible artifacts and that the combined prototype is reliable from installation through demo.

## Owned areas

```text
app/services/
app/templates/
data/sample/
tests/test_services.py
tests/test_reports.py
.gitignore
```

You coordinate integration but do not rewrite Person 1’s graph behavior or Person 2’s UI layout without agreement.

## Deliverables

1. Per-run artifact storage service.
2. Approved local sample dataset and metadata.
3. Jinja2 HTML report generator.
4. Download helpers for the Streamlit app.
5. Tests, test fixtures, integration checks, and final documentation updates.

## Implementation tasks

### 1. Establish artifact conventions

Create a per-run layout:

```text
artifacts/<run_id>/
├── input.csv
├── cleaned.csv
├── transformations.json
├── charts/
├── report.html
└── metadata.json
```

Provide helpers to create safe run IDs, create directories, save uploads, write JSON atomically, and resolve files only inside the run directory.

### 2. Provide sample data

- Add a small, redistributable CSV suited to charts and data-cleaning demonstrations.
- Include source/description metadata.
- Make it easy for Person 1’s acquisition agent to select.

### 3. Build the HTML report

The report should include:

- Problem statement, domain, and source metadata
- Dataset profile and quality warnings
- Cleaning transformation log
- Charts or chart references generated from the workflow
- Observations, statistical findings, recommendations, and limitations
- Run identifier and generation time

Use Jinja2 with escaped user-provided text. Make output self-contained where practical and ensure it opens from disk.

### 4. Test and integrate

- Test artifact paths cannot escape `artifacts/<run_id>/`.
- Test report generation using Person 1’s analysis-state fixture.
- Test corrupted/empty source files through the relevant service boundary.
- Run the complete application with Person 2’s UI and Person 1’s graph.
- Validate three datasets: clean time series, category-focused data, and messy data with nulls/duplicates.

### 5. Repository hygiene

- Ensure `.gitignore` excludes `.venv/`, `artifacts/`, `__pycache__/`, `.env`, and test-cache files.
- Keep `requirements.txt` aligned with imports.
- Update README only after final integration decisions are agreed.

## Handoff requirements

Give Person 1 artifact helper import paths plus exact expected output paths. Give Person 2 safe file-download helpers and the `report_path` convention.

## Acceptance criteria

- Each run has a unique isolated artifact directory.
- Input, cleaned data, transformations, and report are recoverable by run ID.
- HTML report opens locally and contains complete, correctly escaped analysis content.
- Test suite passes from a fresh environment.
- End-to-end manual demo works for all three test datasets.
