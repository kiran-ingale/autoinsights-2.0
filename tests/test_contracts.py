from pathlib import Path

import pytest

from app.schemas import AnalysisRequest, SourceType
from app.services import build_artifact_paths


def test_request_trims_user_text() -> None:
    request = AnalysisRequest(
        run_id="run-001",
        problem_statement="  Find sales trends  ",
        domain="  retail ",
        source_type=SourceType.SAMPLE,
    )

    assert request.problem_statement == "Find sales trends"
    assert request.domain == "retail"


def test_artifact_paths_use_the_run_directory() -> None:
    paths = build_artifact_paths(Path("artifacts"), "run_001")

    assert Path(paths.root_dir).name == "run_001"
    assert Path(paths.input_csv).name == "input.csv"
    assert Path(paths.report_html).name == "report.html"


def test_artifact_paths_reject_unsafe_run_ids() -> None:
    with pytest.raises(ValueError):
        build_artifact_paths(Path("artifacts"), "../../outside")
