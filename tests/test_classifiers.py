import json
from pathlib import Path

import pytest

from office_automation_ml_api.classifiers import (
    LABEL_ORDER,
    KeywordBaseline,
    load_training,
    train_model,
)


def test_load_training_trims_text_and_reads_labels(tmp_path: Path) -> None:
    path = tmp_path / "training.json"
    path.write_text(json.dumps([{"text": "  inspect welds  ", "label": "quality"}]))

    assert load_training(path) == (["inspect welds"], ["quality"])


@pytest.mark.parametrize(
    "records",
    [
        [],
        [{"text": "   ", "label": "quality"}],
        [{"text": "plan work", "label": "other"}],
        ["not an object"],
    ],
)
def test_load_training_rejects_invalid_rows(tmp_path: Path, records: list[object]) -> None:
    path = tmp_path / "training.json"
    path.write_text(json.dumps(records))

    with pytest.raises(ValueError):
        load_training(path)


def test_keyword_baseline_uses_training_word_counts_and_stable_ties() -> None:
    baseline = KeywordBaseline(
        ["inspect weld quality", "schedule planning meeting", "file document record"],
        ["quality", "planning", "documents"],
    )

    assert baseline.predict_one("weld inspection") == "quality"
    assert baseline.predict_one("words not in the data") == LABEL_ORDER[0]


def test_keyword_baseline_rejects_mismatched_training_data() -> None:
    with pytest.raises(ValueError, match="same number"):
        KeywordBaseline(["inspect weld"], [])


def test_tfidf_model_fits_and_predicts_from_training_examples() -> None:
    texts = ["inspect weld", "schedule the work", "file the report"]
    labels = ["quality", "planning", "documents"]

    model = train_model(texts, labels)

    assert model.predict(["inspect weld"]) == ["quality"]


def test_tfidf_model_rejects_mismatched_training_data() -> None:
    with pytest.raises(ValueError, match="same number"):
        train_model(["inspect weld"], [])
