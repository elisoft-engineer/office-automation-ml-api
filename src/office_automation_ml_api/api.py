"""Local HTTP inference API."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

from .classifiers import load_training, train_model

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = Path(os.environ.get("TRAIN_DATA", PROJECT_ROOT / "materials/api_train.json"))
texts, labels = load_training(TRAIN_PATH)
MODEL_NAME = "tfidf-logistic-regression"
classifier = train_model(texts, labels)
app = FastAPI(title="Office Automation ML API", version="1.0.0")


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str

    @field_validator("text")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must be a nonempty string")
        return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "request must be an object with nonempty string text"})


@app.post("/predict")
async def predict(payload: PredictRequest) -> dict[str, str]:
    label = classifier.predict([payload.text])[0]
    return {"label": label, "model": MODEL_NAME}
