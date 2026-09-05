"""Persist analysis artifacts and build self-contained HTML reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jinja2 import BaseLoader, Environment, select_autoescape
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.schemas import AnalysisState


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<style>
body{font-family:Arial,sans-serif;color:#172033;line-height:1.55;max-width:1050px;margin:40px auto;padding:0 24px;background:#fff}
h1{font-size:2rem;margin-bottom:0}h2{margin-top:2.2rem;border-bottom:1px solid #dde3ee;padding-bottom:.35rem}h3{margin-top:1.5rem}
.meta,.note{color:#536174}.notice{background:#fff7e6;padding:14px;border-left:4px solid #d97706}.card{background:#f7f9fc;border-radius:8px;padding:16px;margin:12px 0}
table{border-collapse:collapse;width:100%;margin:12px 0}th,td{padding:8px;text-align:left;border-bottom:1px solid #dfe5ef}th{background:#eef3f9}
</style></head><body>
<h1>{{ title }}</h1><p class="meta">{{ phase_label }} · Source: {{ source }} · Records analyzed: {{ profile.row_count }} · Columns: {{ profile.column_count }}</p>
<h2>Executive Summary</h2><ul>{% for item in summary %}<li>{{ item }}</li>{% endfor %}</ul>
<h2>Data Quality</h2>{% if warnings %}<div class="notice"><ul>{% for warning in warnings %}<li>{{ warning }}</li>{% endfor %}</ul></div>{% else %}<p>No data-quality warnings were identified in this {{ phase_label|lower }}.</p>{% endif %}
<h2>Key Findings</h2>{% for insight in insights %}<div class="card"><strong>{{ insight.type|replace('_',' ')|title }}:</strong> {{ insight.text }}</div>{% endfor %}
<h2>Visual Evidence</h2>{% for chart in charts %}<section>{{ chart|safe }}</section>{% endfor %}
<h2>{{ cleaning_heading }}</h2>{% if cleaning_items %}<table><thead><tr><th>Action</th><th>Column</th><th>Rows affected</th><th>Details</th></tr></thead><tbody>{% for item in cleaning_items %}<tr><td>{{ item.action }}</td><td>{{ item.column|default('—') }}</td><td>{{ item.rows_affected|default('—') }}</td><td>{{ item.details|default('Applied deterministically') }}</td></tr>{% endfor %}</tbody></table>{% else %}<p>No cleaning actions were recorded.</p>{% endif %}
<h2>Further Questions</h2><p>Review findings by relevant business segments and validate important relationships with domain knowledge before acting. Correlations describe association, not causation.</p>
<h2>Caveats and Assumptions</h2><p>This report describes only the supplied dataset. Results are exploratory and may change with broader coverage, additional context, or different data-quality rules.</p>
</body></html>"""


def _figure(spec: dict[str, Any], frame: pd.DataFrame) -> go.Figure | None:
    chart_type = spec["type"]
    if chart_type == "histogram" and spec["x"] in frame:
        return px.histogram(frame, x=spec["x"], title=spec["title"], color_discrete_sequence=["#2563eb"])
    if chart_type == "bar" and {spec["x"], spec["y"]} <= set(frame.columns):
        grouped = frame.groupby(spec["x"], dropna=False)[spec["y"]].mean().sort_values(ascending=False).reset_index()
        return px.bar(grouped, x=spec["x"], y=spec["y"], title=spec["title"], color_discrete_sequence=["#2563eb"])
    if chart_type == "heatmap":
        numeric = frame.select_dtypes(include="number")
        if len(numeric.columns) < 2:
            return None
        correlation = numeric.corr().round(2)
        return go.Figure(go.Heatmap(z=correlation.values, x=correlation.columns, y=correlation.index, colorscale="Blues", zmin=-1, zmax=1))
    if chart_type == "scatter" and {spec["x"], spec["y"]} <= set(frame.columns):
        return px.scatter(frame, x=spec["x"], y=spec["y"], title=spec["title"], color_discrete_sequence=["#2563eb"])
    if chart_type == "line" and {spec["x"], spec["y"]} <= set(frame.columns):
        plotted = frame[[spec["x"], spec["y"]]].copy()
        plotted[spec["x"]] = pd.to_datetime(plotted[spec["x"]], errors="coerce", format="mixed")
        plotted = plotted.dropna().sort_values(spec["x"])
        return px.line(plotted, x=spec["x"], y=spec["y"], title=spec["title"], markers=True, color_discrete_sequence=["#2563eb"])
    return None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def persist_and_render_report(state: AnalysisState, phase: Literal["assessment", "final"]) -> str:
    """Save a run snapshot and return the generated report path."""

    paths = state["artifacts"]
    run_dir = Path(paths.root_dir)
    charts_dir = Path(paths.charts_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(exist_ok=True)

    if state["source_csv"]:
        Path(paths.input_csv).write_text(state["source_csv"], encoding="utf-8")
    frame = pd.DataFrame(state["data_records"])
    if phase == "final":
        frame.to_csv(paths.cleaned_csv, index=False)
    _write_json(Path(paths.transformations_json), state.get("transformations", []))
    _write_json(
        Path(paths.metadata_json),
        {
            "phase": phase,
            "request": state["request"].model_dump(mode="json"),
            "profile": state.get("profile", {}),
            "statistics": state.get("statistics", {}),
            "warnings": state["warnings"],
        },
    )

    charts: list[str] = []
    for index, spec in enumerate(state.get("chart_specs", [])):
        figure = _figure(spec, frame)
        if figure is None:
            continue
        figure.update_layout(template="plotly_white", margin={"l": 30, "r": 30, "t": 55, "b": 30})
        charts.append(figure.to_html(full_html=False, include_plotlyjs=True if index == 0 else False))

    source = "bundled synthetic retail sample" if state["request"].source_type.value == "sample" else "user-uploaded CSV"
    is_assessment = phase == "assessment"
    summary = [item["text"] for item in state.get("insights", [])[:3]] or ["The dataset was profiled and is ready for review."]
    environment = Environment(loader=BaseLoader(), autoescape=select_autoescape(default_for_string=True))
    html = environment.from_string(_TEMPLATE).render(
        title="AutoInsights Raw Data Assessment" if is_assessment else "AutoInsights Cleaned Data Report",
        phase_label="Raw-data assessment" if is_assessment else "Cleaned-data analysis",
        source=source,
        profile=state.get("profile", {}),
        summary=summary,
        warnings=state["warnings"],
        insights=state.get("insights", []),
        charts=charts,
        cleaning_heading="Proposed Cleaning Plan" if is_assessment else "Applied Transformations",
        cleaning_items=state.get("cleaning_plan", []) if is_assessment else state.get("transformations", []),
    )
    report_path = run_dir / ("assessment_report.html" if is_assessment else "report.html")
    report_path.write_text(html, encoding="utf-8")
    return str(report_path)
