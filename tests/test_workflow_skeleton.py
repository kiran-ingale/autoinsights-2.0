from io import BytesIO
from pathlib import Path

from app.graph.workflow import execute_cleaning, run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


def test_sample_request_traverses_the_workflow() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="sample-run",
            problem_statement="Find sales patterns",
            source_type=SourceType.SAMPLE,
        )
    )

    agents = [event["agent"] for event in state["progress"]]
    assert state["status"] is RunStatus.AWAITING_CLEANING_APPROVAL
    assert "Data Acquisition Agent" in agents
    assert "Data Profiling Agent" in agents
    assert agents[-1] == "Reporting Agent"
    assert Path(state["assessment_report_path"]).is_file()

    completed = execute_cleaning(state)
    assert completed["status"] is RunStatus.COMPLETED
    assert completed["progress"][-1]["agent"] == "Reporting Agent"
    assert Path(completed["report_path"]).is_file()


def test_upload_request_uses_the_upload_branch() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="upload-run",
            problem_statement="Find sales patterns",
            source_type=SourceType.UPLOAD,
        ),
        uploaded_file=BytesIO(b"region,revenue\nNorth,100\nSouth,200\n"),
    )

    agents = [event["agent"] for event in state["progress"]]
    assert "Uploaded Data Source" in agents
    assert "Data Acquisition Agent" not in agents
