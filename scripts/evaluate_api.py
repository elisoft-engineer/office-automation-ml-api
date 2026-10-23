import json
import os
import sys
import time
from importlib.metadata import version
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from office_automation_ml_api.classifiers import KeywordBaseline, load_training  # noqa: E402

BASE_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")


def post(payload: object) -> tuple[int, dict, float]:
    """Send one prediction request and return its status, body, and elapsed time."""
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        BASE_URL + "/predict", data=data, headers={"Content-Type": "application/json"}
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=5) as response:
            status, body = response.status, json.loads(response.read())
    except HTTPError as exc:
        status, body = exc.code, json.loads(exc.read())
    elapsed_ms = (time.perf_counter() - started) * 1000
    return status, body, elapsed_ms


def main() -> int:
    """Compare the API predictions with the examples and keyword baseline."""
    records = json.loads((ROOT / "examples/api_test.json").read_text(encoding="utf-8"))
    train_texts, train_labels = load_training(ROOT / "materials/api_train.json")
    baseline = KeywordBaseline(train_texts, train_labels)
    results = []
    endpoint_times = []
    for record in records:
        expected = record["label"]
        baseline_prediction = baseline.predict_one(record["text"])
        status, body, elapsed_ms = post({"text": record["text"]})
        if status == 200 and isinstance(body.get("label"), str):
            prediction = body["label"]
            endpoint_times.append(elapsed_ms)
        else:
            prediction = None
        results.append(
            {
                "text": record["text"],
                "expected": expected,
                "keyword_prediction": baseline_prediction,
                "keyword_correct": baseline_prediction == expected,
                "model_prediction": prediction,
                "model_correct": prediction == expected,
                "http_status": status,
                "response_ms": round(elapsed_ms, 3),
            }
        )

    invalid_results = []
    for case in json.loads((ROOT / "examples/api_invalid.json").read_text(encoding="utf-8")):
        status, body, _ = post(case["body"])
        invalid_results.append(
            {
                "case": case["case"],
                "expected_status": case["expected_status"],
                "actual_status": status,
                "response": body,
            }
        )
    failures = sum(row["http_status"] != 200 for row in results)
    invalid_failures = sum(
        row["actual_status"] != row["expected_status"] for row in invalid_results
    )
    report = {
        "model": "tfidf-logistic-regression",
        "scikit_learn_version": sklearn.__version__,
        "dependency_versions": {
            package: version(package)
            for package in ("fastapi", "pydantic", "scikit-learn", "uvicorn")
        },
        "python_version": sys.version.split()[0],
        "keyword_baseline": (
            "Training-data word counts, with a fixed order for ties and no matches."
        ),
        "training_examples": len(train_texts),
        "test_examples": len(records),
        "keyword_correct": f"{sum(r['keyword_correct'] for r in results)}/{len(records)}",
        "model_correct": f"{sum(r['model_correct'] for r in results)}/{len(records)}",
        "mean_api_response_ms": round(sum(endpoint_times) / len(endpoint_times), 3)
        if endpoint_times
        else None,
        "timing_scope": (
            "HTTP round trip, request parsing, and prediction. Model fitting and loading happen "
            "before the server starts and are not included."
        ),
        "prediction_failures": failures,
        "invalid_input_cases": invalid_results,
        "invalid_input_failures": invalid_failures,
        "predictions": results,
    }
    output = ROOT / "results/api_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures or invalid_failures:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (URLError, TimeoutError) as exc:
        print(
            f"Cannot reach API at {BASE_URL}: {exc}. "
            "Start it with `poetry run python scripts/run_api.py`.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
