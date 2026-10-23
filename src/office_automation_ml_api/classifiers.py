"""Training-data-only keyword baseline and TF-IDF logistic regression model."""

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
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("training data must be a nonempty JSON array")
    texts, labels = [], []
    for index, item in enumerate(records, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError(f"training row {index} must contain nonempty text")
        if item.get("label") not in LABEL_ORDER:
            raise ValueError(f"training row {index} has an unsupported label")
        texts.append(item["text"].strip())
        labels.append(item["label"])
    return texts, labels


class KeywordBaseline:
    """Sum training-corpus token counts per label; ties/no hits use fixed LABEL_ORDER."""

    def __init__(self, texts: list[str], labels: list[str]) -> None:
        self.term_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for text, label in zip(texts, labels):
            self.term_counts[label].update(TOKEN.findall(text.lower()))

    def predict_one(self, text: str) -> str:
        words = set(TOKEN.findall(text.lower()))
        scores = {
            label: sum(self.term_counts[label][word] for word in words)
            for label in LABEL_ORDER
        }
        return max(LABEL_ORDER, key=lambda label: scores[label])


def train_model(texts: list[str], labels: list[str]) -> Pipeline:
    """Fit the fixed TF-IDF/logistic-regression pipeline on training data only."""
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
        ("classifier", LogisticRegression(max_iter=1000, random_state=17)),
    ])
    model.fit(texts, labels)
    return model
