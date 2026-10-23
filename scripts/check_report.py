#!/usr/bin/env python3
"""Run the supplied Part A cases, checking atomic failures and repeatability."""

import json
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from office_automation_ml_api.report import STATUSES, decimal_text, generate, read_jobs  # noqa: E402


def cli_text(path: Path) -> str:
    proc = subprocess.run(["officecli", "view", str(path), "text"], text=True,
                          capture_output=True, check=True)
    return proc.stdout


def verify_report(path: Path, source: Path) -> tuple[bool, str]:
    visible = cli_text(path)
    normalized = " ".join(visible.split())
    jobs = read_jobs(source)
    counts = {status: sum(job.status == status for job in jobs) for status in STATUSES}
    expected_values = [
        f"Total jobs: {len(jobs)}",
        f"Open: {counts['open']}",
        f"In progress: {counts['in_progress']}",
        f"Done: {counts['done']}",
        f"Estimated hours: {decimal_text(sum((job.hours for job in jobs), start=Decimal('0')))}",
        "Synthetic assessment input.",
    ]
    for value in expected_values:
        if value not in normalized:
            return False, f"report is missing expected content: {value}"
    if "{{" in visible or "}}" in visible:
        return False, "report contains an unresolved placeholder"
    for job in jobs:
        row = f"{job.job_id} | {job.description} | {job.status} | {decimal_text(job.hours)} hours"
        if " ".join(row.split()) not in normalized:
            return False, f"report is missing job row: {job.job_id}"
    if not jobs and "No jobs" not in normalized:
        return False, "header-only input should produce a visible zero-row summary"
    return True, "report content matches the input"


def main() -> int:
    checks = json.loads((ROOT / "examples/checks.json").read_text(encoding="utf-8"))
    valid_names = {"materials/jobs.csv", "examples/csv/header_only.csv", "examples/csv/zero_hours.csv"}
    results = []
    with tempfile.TemporaryDirectory(prefix="task2-check-") as temporary:
        temp = Path(temporary)
        for index, case in enumerate(checks):
            source = ROOT / case["input"]
            output = temp / f"case-{index}.docx"
            if case["input"] in valid_names:
                generate(ROOT / "materials/status_template.docx", source, output)
                passed, detail = verify_report(output, source)
                results.append({"input": case["input"], "passed": output.is_file() and passed,
                                "output_created": output.is_file(), "detail": detail})
            else:
                try:
                    generate(ROOT / "materials/status_template.docx", source, output)
                    error = None
                except ValueError as exc:
                    error = str(exc)
                passed = error is not None and not output.exists()
                results.append({"input": case["input"], "passed": passed,
                                "output_created": output.exists(), "error": error})
        # Generate the default report twice and compare OfficeCLI-visible content.
        first, second = temp / "first.docx", temp / "second.docx"
        generate(ROOT / "materials/status_template.docx", ROOT / "materials/jobs.csv", first)
        generate(ROOT / "materials/status_template.docx", ROOT / "materials/jobs.csv", second)
        deterministic = cli_text(first) == cli_text(second)
        results.append({"check": "repeatability", "passed": deterministic})

    summary = {"checks_passed": sum(bool(row["passed"]) for row in results),
               "checks_total": len(results), "results": results}
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "report_checks.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["checks_passed"] == summary["checks_total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
