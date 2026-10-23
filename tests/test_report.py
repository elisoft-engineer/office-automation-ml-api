from decimal import Decimal
from pathlib import Path

import pytest

from office_automation_ml_api.report import decimal_text, read_jobs


def write_csv(path: Path, contents: str) -> Path:
    """Write a CSV fixture and return its path."""
    path.write_text(contents, encoding="utf-8")
    return path


def test_read_jobs_parses_rows_and_decimal_hours(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path / "jobs.csv",
        "job_id,description,status,estimated_hours\nJ-1,Inspect welds,open,2.50\n",
    )

    jobs = read_jobs(path)

    assert len(jobs) == 1
    assert jobs[0].job_id == "J-1"
    assert jobs[0].hours == Decimal("2.50")


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "job_id,description,status\nJ-1,Inspect welds,open\n",
        "job_id,description,status,estimated_hours\nJ-1,,open,2\n",
        "job_id,description,status,estimated_hours\nJ-1,Inspect welds,unknown,2\n",
        "job_id,description,status,estimated_hours\nJ-1,Inspect welds,open,-1\n",
        "job_id,description,status,estimated_hours\nJ-1,Inspect welds,open,nan\n",
    ],
)
def test_read_jobs_rejects_invalid_csv(tmp_path: Path, contents: str) -> None:
    path = write_csv(tmp_path / "jobs.csv", contents)

    with pytest.raises(ValueError):
        read_jobs(path)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("0"), "0"),
        (Decimal("12.500"), "12.5"),
        (Decimal("1E+20"), "1E+20"),
    ],
)
def test_decimal_text_is_readable(value: Decimal, expected: str) -> None:
    assert decimal_text(value) == expected
