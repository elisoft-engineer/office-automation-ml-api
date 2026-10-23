from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("job_id", "description", "status", "estimated_hours")
STATUSES = ("open", "in_progress", "done")
PLACEHOLDERS = ("TOTAL_JOBS", "OPEN", "IN_PROGRESS", "DONE", "TOTAL_HOURS", "JOB_ROWS")


@dataclass(frozen=True)
class Job:
    """One validated job record from the input CSV."""

    job_id: str
    description: str
    status: str
    hours: Decimal


def read_jobs(path: Path) -> list[Job]:
    """Read and validate every row before any output document is created."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise ValueError("CSV is missing its header row")
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError("CSV header contains duplicate column names")
            missing = [field for field in FIELDS if field not in reader.fieldnames]
            if missing:
                raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
            jobs: list[Job] = []
            for line, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(f"row {line}: unexpected extra column(s)")
                values = {key: (row.get(key) or "").strip() for key in FIELDS}
                for field in FIELDS:
                    if not values[field]:
                        raise ValueError(f"row {line}: {field} must not be blank")
                status = values["status"]
                if status not in STATUSES:
                    raise ValueError(f"row {line}: status must be one of {', '.join(STATUSES)}")
                try:
                    hours = Decimal(values["estimated_hours"])
                except InvalidOperation as exc:
                    raise ValueError(f"row {line}: estimated_hours must be a number") from exc
                if not hours.is_finite():
                    raise ValueError(f"row {line}: estimated_hours must be finite")
                if hours < 0:
                    raise ValueError(f"row {line}: estimated_hours must be zero or greater")
                jobs.append(Job(values["job_id"], values["description"], status, hours))
            return jobs
    except OSError as exc:
        raise ValueError(f"cannot read CSV '{path}': {exc.strerror or exc}") from exc


def decimal_text(value: Decimal) -> str:
    """Format hours clearly without expanding very large decimal values."""
    if value.is_zero():
        return "0"
    if -6 <= value.adjusted() < 15:
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    # Keep extreme but finite inputs readable without expanding them into billions of digits.
    return format(value, "E")


def officecli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run OfficeCLI and turn missing tools or command failures into clear errors."""
    try:
        return subprocess.run(["officecli", *args], text=True, capture_output=True, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "OfficeCLI is required. Install it and verify with `officecli --version`."
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown OfficeCLI error").strip()
        raise RuntimeError(f"OfficeCLI command failed: {detail}") from exc


def generate(template: Path, csv_path: Path, output: Path) -> None:
    """Validate the CSV, fill the template, and publish the finished document."""
    jobs = read_jobs(csv_path)
    if not template.is_file():
        raise ValueError(f"template does not exist: {template}")
    if output.resolve() == template.resolve():
        raise ValueError("output path must not overwrite the supplied template")
    output.parent.mkdir(parents=True, exist_ok=True)
    counts = {status: sum(job.status == status for job in jobs) for status in STATUSES}
    total_hours = sum((job.hours for job in jobs), start=Decimal("0"))
    # Pipe-separated records remain legible in the template's dedicated detail paragraph.
    rows = (
        "\n".join(
            f"{job.job_id} | {job.description} | {job.status} | {decimal_text(job.hours)} hours"
            for job in jobs
        )
        or "No jobs"
    )

    # Work in a sibling temporary DOCX and atomically publish only after OfficeCLI succeeds.
    with tempfile.TemporaryDirectory(prefix="status-report-", dir=output.parent) as temp_dir:
        draft = Path(temp_dir) / "status_report.docx"
        shutil.copy2(template, draft)
        values = {
            "TOTAL_JOBS": str(len(jobs)),
            "OPEN": str(counts["open"]),
            "IN_PROGRESS": str(counts["in_progress"]),
            "DONE": str(counts["done"]),
            "TOTAL_HOURS": decimal_text(total_hours),
            "JOB_ROWS": rows,
        }
        commands = [
            {
                "command": "set",
                "path": "/",
                "props": {"find": "{{" + name + "}}", "replace": values[name]},
            }
            for name in PLACEHOLDERS
        ]
        batch = officecli("batch", str(draft), "--commands", json.dumps(commands), "--json")
        try:
            receipt = json.loads(batch.stdout)
            results = receipt["data"]["results"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("OfficeCLI returned an unreadable batch receipt") from exc
        if len(results) != len(PLACEHOLDERS) or any(not item.get("success") for item in results):
            raise RuntimeError("OfficeCLI did not apply every placeholder replacement")
        for name, result in zip(PLACEHOLDERS, results, strict=True):
            match = re.search(r"\((\d+) matched\)", result.get("output", ""))
            if match is None or int(match.group(1)) == 0:
                raise RuntimeError(f"OfficeCLI did not find placeholder {{{{{name}}}}}")
        # Verify through OfficeCLI before publishing, including absence of any unresolved token.
        viewed = officecli("view", str(draft), "text").stdout
        unresolved = re.findall(r"\{\{[^{}]+\}\}", viewed)
        if unresolved:
            raise RuntimeError("OfficeCLI left unresolved placeholder(s): " + ", ".join(unresolved))
        os.replace(draft, output)


def main() -> int:
    """Parse command-line options and report user-facing generation errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("materials/jobs.csv"))
    parser.add_argument("--template", type=Path, default=Path("materials/status_template.docx"))
    parser.add_argument("--output", type=Path, default=Path("outputs/status_report.docx"))
    args = parser.parse_args()
    try:
        generate(args.template, args.csv, args.output)
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
