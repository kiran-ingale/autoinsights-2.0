from io import BytesIO

from app.graph.workflow import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


def test_sample_run_profiles_and_cleans_data() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="core-sample-run",
            problem_statement="Summarize sales data",
            source_type=SourceType.SAMPLE,
        )
    )

    assert state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert state["profile"]["row_count"] == 12
    assert state["profile"]["column_count"] == 8
    assert len(state["data_records"]) == 12
    assert "order_date" in state["dataframe_metadata"]["original_columns"]
    completed = execute_cleaning(state)
    assert completed["status"] is RunStatus.COMPLETED
    assert "order_date" in completed["dataframe_metadata"]["cleaned_columns"]


def test_cleaning_removes_duplicates_and_imputes_missing_values() -> None:
    csv = b" City ,Revenue\n North ,100\nNorth,100\nSouth,\n"
    state = run_analysis(
        AnalysisRequest(
            run_id="messy-upload-run",
            problem_statement="Check data quality",
            source_type=SourceType.UPLOAD,
        ),
        uploaded_file=BytesIO(csv),
    )

    plan_actions = [item["action"] for item in state["cleaning_plan"]]
    assert state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert len(state["data_records"]) == 3
    assert "remove_duplicates" in plan_actions
    completed = execute_cleaning(state)
    actions = [item["action"] for item in completed["transformations"]]
    assert completed["status"] is RunStatus.COMPLETED
    assert len(completed["data_records"]) == 2
    assert "normalize_column_names" in actions
    assert "trim_text_values" in actions
    assert "remove_duplicates" in actions
    assert "impute_numeric_median" in actions


def test_missing_upload_stops_with_a_friendly_error() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="missing-upload-run",
            problem_statement="Check data quality",
            source_type=SourceType.UPLOAD,
        )
    )

    assert state["status"] is RunStatus.FAILED
    assert state["errors"] == ["Please upload a non-empty CSV file."]
