from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

LABEL_ORDER = ("quality", "planning", "documents")
TOKEN = re.compile(r"[a-z0-9]+")


def load_training(path: Path) -> tuple[list[str], list[str]]:
    """Read the training examples and reject blank text or labels the API cannot return."""
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("training data must be a nonempty JSON array")
    texts, labels = [], []
    for index, item in enumerate(records, start=1):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("text"), str)
            or not item["text"].strip()
        ):
            raise ValueError(f"training row {index} must contain nonempty text")
        if item.get("label") not in LABEL_ORDER:
            raise ValueError(f"training row {index} has an unsupported label")
        texts.append(item["text"].strip())
        labels.append(item["label"])
    return texts, labels


class KeywordBaseline:
    """Choose a label by counting how often its words appear in the training data.

    If no words match, or labels receive the same score, ``LABEL_ORDER`` decides.
    """

    def __init__(self, texts: list[str], labels: list[str]) -> None:
        if len(texts) != len(labels):
            raise ValueError("texts and labels must contain the same number of examples")
        if not texts:
            raise ValueError("at least one training example is required")
        if any(label not in LABEL_ORDER for label in labels):
            raise ValueError("training data contains an unsupported label")
        self.term_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for text, label in zip(texts, labels, strict=True):
            self.term_counts[label].update(TOKEN.findall(text.lower()))

    def predict_one(self, text: str) -> str:
        """Return the label with the strongest matching word count."""
        words = set(TOKEN.findall(text.lower()))
        scores = {
            label: sum(self.term_counts[label][word] for word in words) for label in LABEL_ORDER
        }
        return max(LABEL_ORDER, key=lambda label: scores[label])


def train_model(texts: list[str], labels: list[str]) -> Pipeline:
    """Fit the TF-IDF and logistic regression pipeline on the supplied examples."""
    if len(texts) != len(labels):
        raise ValueError("texts and labels must contain the same number of examples")
    if not texts:
        raise ValueError("at least one training example is required")
    if any(label not in LABEL_ORDER for label in labels):
        raise ValueError("training data contains an unsupported label")
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=1000, random_state=17)),
        ]
    )
    model.fit(texts, labels)
    return model
