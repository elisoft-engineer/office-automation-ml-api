"""Office report automation and text classification API."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _get_version() -> str:
    """Read the installed version, or use Poetry metadata in a source checkout."""
    try:
        return version("office-automation-ml-api")
    except PackageNotFoundError:
        project_file = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with project_file.open("rb") as file:
            project = tomllib.load(file)
        return project["project"]["version"]


__version__ = _get_version()
