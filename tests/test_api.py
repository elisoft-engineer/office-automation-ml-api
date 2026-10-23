import asyncio
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

import office_automation_ml_api as package
from office_automation_ml_api import __version__
from office_automation_ml_api.api import app


def post(
    path: str,
    *,
    json: Any = None,
    content: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Send an HTTP request through the app without opening a local socket."""

    async def send() -> httpx.Response:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
            return await client.post(path, json=json, content=content, headers=headers)

    return asyncio.run(send())


def test_predict_returns_a_label_and_model_name() -> None:
    response = post("/predict", json={"text": "inspect the weld quality"})

    assert response.status_code == 200
    assert response.json() == {
        "label": "quality",
        "model": "tfidf-logistic-regression",
    }


def test_api_docs_use_the_package_version() -> None:
    assert app.version == version("office-automation-ml-api") == __version__


def test_package_version_uses_poetry_metadata_in_a_source_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_distribution(_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(package, "version", missing_distribution)

    assert package._get_version() == __version__


def test_predict_trims_surrounding_whitespace() -> None:
    response = post("/predict", json={"text": "  inspect weld quality  "})

    assert response.status_code == 200


def test_predict_rejects_blank_text() -> None:
    response = post("/predict", json={"text": "  "})

    assert response.status_code == 400
    assert "error" in response.json()


def test_predict_rejects_missing_text() -> None:
    response = post("/predict", json={})

    assert response.status_code == 400
    assert "error" in response.json()


def test_predict_rejects_non_string_text() -> None:
    response = post("/predict", json={"text": 42})

    assert response.status_code == 400


def test_predict_rejects_non_object_body() -> None:
    response = post("/predict", json=[])

    assert response.status_code == 400
    assert "error" in response.json()


def test_predict_rejects_unknown_fields() -> None:
    response = post("/predict", json={"text": "inspect weld", "debug": True})

    assert response.status_code == 400


def test_predict_rejects_malformed_json() -> None:
    response = post(
        "/predict",
        content="{",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
