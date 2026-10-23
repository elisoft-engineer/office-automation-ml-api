#!/usr/bin/env python3
"""Run the Task 2 Part A report generator from a source checkout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from office_automation_ml_api.report import main  # noqa: E402

raise SystemExit(main())
