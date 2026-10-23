# Office Automation and ML API

## Approach

Part A validates the complete CSV before touching the destination. It checks the four required fields, accepted status values, and finite nonnegative decimal-hour values. It copies the supplied template to a temporary sibling file, uses OfficeCLI for placeholder replacement and read-back, and atomically publishes the completed document. Header-only input and zero hours are supported.

Part B trains a TF-IDF unigram/bigram pipeline with logistic regression from `materials/api_train.json`. The comparison baseline builds token-frequency votes from that same training file. Neither method is tuned against `examples/api_test.json`. The HTTP API rejects invalid input with status 400.

## Evaluation

All 13 Part A checks passed, including valid and invalid CSV examples and repeatability across two reports. Both the keyword baseline and TF-IDF/logistic-regression model scored 6/6. All seven invalid API examples returned HTTP 400, with no prediction-request failures. The six local HTTP requests averaged 11.592 ms each. Timing includes request parsing and prediction, but not model fitting at startup.

The run used Python 3.14.4, FastAPI 0.161.1, Pydantic 2.14.1, scikit-learn 1.9.1, Uvicorn 0.54.0, and OfficeCLI 1.0.158. Prediction-level details are in `results/api_evaluation.json`; report case details are in `results/report_checks.json`.

## Limitations

Only twelve short synthetic training examples and six test examples are provided. That is too little data to say how the model would handle real requests, especially if they use different wording. The response time measures a local HTTP request after startup; it does not include model training or loading.

## Time and tools used

- Time spent: about 8 hours.
- Help used: I used an AI assistant for a few design discussions and to review parts of the tests.
