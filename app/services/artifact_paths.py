"""Pure helpers defining the on-disk contract for analysis-run artifacts."""

from __future__ import annotations

from pathlib import Path
import re

from app.schemas import ArtifactPaths


_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def build_artifact_paths(artifacts_root: Path, run_id: str) -> ArtifactPaths:
    """Return canonical output paths without creating or writing any files."""

    if not _SAFE_RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, numbers, underscores, or hyphens")

    run_dir = artifacts_root.resolve() / run_id
    return ArtifactPaths(
        root_dir=str(run_dir),
        input_csv=str(run_dir / "input.csv"),
        cleaned_csv=str(run_dir / "cleaned.csv"),
        transformations_json=str(run_dir / "transformations.json"),
        charts_dir=str(run_dir / "charts"),
        report_html=str(run_dir / "report.html"),
        metadata_json=str(run_dir / "metadata.json"),
    )
