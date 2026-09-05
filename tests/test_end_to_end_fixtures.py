from pathlib import Path

from app.graph import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


FIXTURES = Path(__file__).parent / "fixtures"


def _run_fixture(name: str, run_id: str):
    with (FIXTURES / name).open("rb") as file:
        return run_analysis(
            AnalysisRequest(
                run_id=run_id,
                problem_statement="Inspect the supplied dataset",
                source_type=SourceType.UPLOAD,
            ),
            uploaded_file=file,
        )


def test_clean_time_series_has_an_honest_trend_chart() -> None:
    assessment = _run_fixture("clean_time_series.csv", "fixture-time-series")

    chart_types = {spec["type"] for spec in assessment["chart_specs"]}
    assert assessment["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert "line" in chart_types
    assert assessment["cleaning_plan"] == [{"action": "no_changes", "details": "No deterministic cleaning actions are currently required."}]
    final = execute_cleaning(assessment)
    assert final["status"] is RunStatus.COMPLETED


def test_category_dataset_has_a_category_comparison() -> None:
    assessment = _run_fixture("category_focused.csv", "fixture-categories")

    bar_charts = [spec for spec in assessment["chart_specs"] if spec["type"] == "bar"]
    assert assessment["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert bar_charts
    assert bar_charts[0]["x"] == "category"
    assert "line" not in {spec["type"] for spec in assessment["chart_specs"]}


def test_messy_dataset_shows_plan_then_applies_it_after_approval() -> None:
    assessment = _run_fixture("messy_data.csv", "fixture-messy")

    plan_actions = {item["action"] for item in assessment["cleaning_plan"]}
    assert assessment["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert {"normalize_column_names", "trim_text_values", "remove_duplicates", "impute_numeric_median", "impute_categorical_mode"} <= plan_actions
    assert len(assessment["data_records"]) == 5

    final = execute_cleaning(assessment)
    actions = {item["action"] for item in final["transformations"]}
    assert final["status"] is RunStatus.COMPLETED
    assert len(final["data_records"]) == 4
    assert {"normalize_column_names", "trim_text_values", "remove_duplicates", "impute_numeric_median", "impute_categorical_mode"} <= actions
