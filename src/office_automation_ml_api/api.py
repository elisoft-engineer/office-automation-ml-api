import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator

from . import __version__
from .classifiers import load_training, train_model

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = Path(os.environ.get("TRAIN_DATA", PROJECT_ROOT / "materials/api_train.json"))
texts, labels = load_training(TRAIN_PATH)
MODEL_NAME = "tfidf-logistic-regression"
classifier = train_model(texts, labels)
app = FastAPI(title="Office Automation ML API", version=__version__)


class PredictRequest(BaseModel):
    """Text to classify, with no extra fields or blank input allowed."""

    model_config = ConfigDict(extra="forbid")
    text: str

    @field_validator("text")
    @classmethod
    def require_nonblank_text(cls, value: str) -> str:
        """Trim surrounding whitespace and reject text with no content."""
        value = value.strip()
        if not value:
            raise ValueError("text must be a nonempty string")
        return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    """Return a consistent client error when a request does not match the schema."""
    return JSONResponse(
        status_code=400, content={"error": "request must be an object with nonempty string text"}
    )


@app.post("/predict")
async def predict(payload: PredictRequest) -> dict[str, str]:
    """Classify the submitted text and return the selected model's name."""
    label = str(classifier.predict([payload.text])[0])
    return {"label": label, "model": MODEL_NAME}
