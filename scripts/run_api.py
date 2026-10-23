import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import uvicorn  # noqa: E402


def main() -> None:
    """Start the API at the configured host and port."""
    uvicorn.run(
        "office_automation_ml_api.api:app",
        app_dir="src",
        host=os.environ.get("HOST", "localhost"),
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
