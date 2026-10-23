#!/usr/bin/env python3
"""Run the Task 2 Part B local API."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import uvicorn  # noqa: E402

uvicorn.run(
    "office_automation_ml_api.api:app",
    app_dir="src",
    host=os.environ.get("HOST", "127.0.0.1"),
    port=int(os.environ.get("PORT", "8000")),
)
