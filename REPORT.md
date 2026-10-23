# Office Automation and ML API — implementation note

## Approach

Part A validates the complete CSV before touching the destination. It checks the four required fields, accepted status values, and finite nonnegative decimal-hour values. It copies the supplied template to a temporary sibling file, uses OfficeCLI for placeholder replacement and read-back, and atomically publishes the completed document. Header-only input and zero hours are supported.

Part B trains a TF-IDF unigram/bigram pipeline with logistic regression from `materials/api_train.json`. The comparison baseline builds token-frequency votes from that same training file. Neither method is tuned against `examples/api_test.json`. The HTTP API rejects invalid input with status 400.

## Evaluation

All 13 Part A checks passed, including all valid and invalid CSV examples and repeatability across two generated reports. The API evaluation scored 6/6 for both the keyword baseline and TF-IDF/logistic-regression model. All seven invalid API examples returned HTTP 400; there were no prediction-request failures. Mean response time was 13.206 ms for six local HTTP requests. It includes request parsing and prediction, and excludes model fitting at server startup.

The run used Python 3.14.4, FastAPI 0.161.1, Pydantic 2.14.1, scikit-learn 1.9.1, Uvicorn 0.54.0, and OfficeCLI 1.0.158. Prediction-level details are in `results/api_evaluation.json`; report case details are in `results/report_checks.json`.

## Limitations

Only twelve short synthetic training examples and six test examples are provided. The evaluation cannot establish generalization to real requests, class balance or vocabulary drift. The mean timing measures a local HTTP round trip and does not include startup-time training.

## Time and assistance

- Assistant implementation and verification time in this session: approximately 50 minutes. Add any independent review or follow-up work to the total you report.
- AI assistance: used for requirements analysis, implementation planning, and review. All code and outcomes are checked in this repository and reproducible with its commands.
