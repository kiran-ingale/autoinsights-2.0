"""Workflow callable contract used by the Streamlit application."""

from __future__ import annotations

from typing import BinaryIO, Protocol

from app.schemas import AnalysisRequest, AnalysisState


class AnalysisRunner(Protocol):
    """Interface the Streamlit application will call to run an analysis."""

    def __call__(
        self,
        request: AnalysisRequest,
        uploaded_file: BinaryIO | None,
    ) -> AnalysisState:
        """Run the workflow and return its final structured state."""
