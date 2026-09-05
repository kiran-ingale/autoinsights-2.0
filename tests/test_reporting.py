from pathlib import Path

from app.graph import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, SourceType


def test_raw_and_cleaned_reports_are_persisted() -> None:
    assessment = run_analysis(
        AnalysisRequest(
            run_id="report-artifact-run",
            problem_statement="Analyze the retail sample",
            source_type=SourceType.SAMPLE,
        )
    )
    assessment_path = Path(assessment["assessment_report_path"])
    assert assessment_path.name == "assessment_report.html"
    assert assessment_path.is_file()
    assert "Proposed Cleaning Plan" in assessment_path.read_text(encoding="utf-8")
    assert Path(assessment["artifacts"].input_csv).is_file()
    assert assessment["input_path"] == assessment["artifacts"].input_csv

    final = execute_cleaning(assessment)
    final_path = Path(final["report_path"])
    assert final_path.name == "report.html"
    assert final_path.is_file()
    assert "Applied Transformations" in final_path.read_text(encoding="utf-8")
    assert Path(final["artifacts"].cleaned_csv).is_file()
    assert Path(final["artifacts"].transformations_json).is_file()
    assert Path(final["artifacts"].metadata_json).is_file()
    assert final["cleaned_path"] == final["artifacts"].cleaned_csv
