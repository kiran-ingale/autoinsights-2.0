from app.graph import run_analysis
from app.schemas import AnalysisRequest, RunStatus, SourceType


def test_sample_run_produces_analytical_results_and_chart_specs() -> None:
    state = run_analysis(
        AnalysisRequest(
            run_id="analysis-sample-run",
            problem_statement="Analyze retail revenue",
            source_type=SourceType.SAMPLE,
        )
    )

    chart_types = {spec["type"] for spec in state["chart_specs"]}
    assert state["status"] is RunStatus.COMPLETED
    assert state["observations"]
    assert state["statistics"]["strongest_correlation"] is not None
    assert state["insights"]
    assert {"histogram", "bar", "heatmap", "scatter", "line"} <= chart_types
    assert state["dataframe_metadata"]["feature_recommendations"]


def test_sparse_data_omits_unsupported_scatter_and_trend_charts() -> None:
    from io import BytesIO

    state = run_analysis(
        AnalysisRequest(
            run_id="sparse-analysis-run",
            problem_statement="Analyze a small dataset",
            source_type=SourceType.UPLOAD,
        ),
        uploaded_file=BytesIO(b"date,revenue,units\n2026-01-01,100,2\n2026-02-01,120,3\n"),
    )

    chart_types = {spec["type"] for spec in state["chart_specs"]}
    assert "scatter" not in chart_types
    assert "line" not in chart_types
