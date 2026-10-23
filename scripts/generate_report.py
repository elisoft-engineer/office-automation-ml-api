import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from office_automation_ml_api.report import main  # noqa: E402


def run() -> int:
    """Run the report command with this checkout's source package."""
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
