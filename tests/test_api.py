import asyncio

import httpx
from httpx import ASGITransport, AsyncClient

from office_automation_ml_api.api import app


def post(path: str, **kwargs: object) -> httpx.Response:
    """Send an HTTP request through the app without opening a local socket."""

    async def send() -> httpx.Response:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
            return await client.post(path, **kwargs)

    return asyncio.run(send())


def test_predict_returns_a_label_and_model_name() -> None:
    response = post("/predict", json={"text": "inspect the weld quality"})

    assert response.status_code == 200
    assert response.json() == {
        "label": "quality",
        "model": "tfidf-logistic-regression",
    }


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
