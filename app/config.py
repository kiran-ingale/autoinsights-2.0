"""Central configuration for the local AutoInsights prototype."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / os.getenv("AUTOINSIGHTS_ARTIFACTS_DIR", "artifacts")
MAX_UPLOAD_MB = int(os.getenv("AUTOINSIGHTS_MAX_UPLOAD_MB", "25"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
