# Office Automation and ML API

This repository contains a validated Word status report generator and a local text-classification API. The implementation follows a supplied assessment specification; all business data is synthetic.

## Requirements

- Python 3.11 or newer
- Poetry 2.x
- Node.js 14+ and OfficeCLI `@officecli/officecli` 1.0.158 (DOCX editing CLI; verified for this project)

The Python environment is managed by Poetry. Create it and install dependencies with:

```bash
poetry env use python3.14
poetry install
```

Install OfficeCLI using the official npm package, then verify it:

```bash
npm install --global @officecli/officecli@1.0.158
officecli --version
```

OfficeCLI reads and edits the provided Word template. The report code itself uses Python's standard library for CSV parsing and validation.

## Part A — status report

Run from the repository root:

```bash
poetry run python scripts/generate_report.py
```

This reads `materials/jobs.csv` and `materials/status_template.docx`, then writes `outputs/status_report.docx`. The command validates all rows before creating a draft. It works on a template copy, asks OfficeCLI to replace each placeholder, checks the result with OfficeCLI, and publishes the finished document atomically. Invalid input prints a row-specific error and does not create or replace the report.

To use a different CSV or output location:

```bash
poetry run python scripts/generate_report.py --csv examples/csv/zero_hours.csv --output outputs/zero_hours.docx
```

The validator requires `job_id`, `description`, `status`, and `estimated_hours`. Status is one of `open`, `in_progress`, or `done`. Hours must be finite and nonnegative; zero is valid. A header-only CSV produces zero counts and zero hours. Job details appear as pipe-separated lines in the template's details section.

## Part B — classifier API

Start the service in one terminal:

```bash
poetry run python scripts/run_api.py
```

The API trains a TF-IDF plus logistic-regression pipeline from `materials/api_train.json` at startup, before accepting requests. It listens on `localhost:8000` by default; set `HOST` or `PORT` to change the bind address. The interactive API documentation is available at `http://localhost:8000/docs`. A valid request returns both the predicted label and model name:

```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Inspect a weld defect"}'
```

Missing, blank, non-string text and non-object request bodies return HTTP 400 with a clear JSON error. No external API or API key is needed.

## Reproduce the checks and evaluation

With OfficeCLI on `PATH`, run the Part A supplied cases (including repeatability):

```bash
poetry run python scripts/check_report.py
```

With the API running, run the Part B evaluation:

```bash
poetry run python scripts/evaluate_api.py
```

If the API uses a non-default address, set `API_URL` when running the evaluator, for example `API_URL=http://localhost:8765 poetry run python scripts/evaluate_api.py`.

Run the unit tests and code checks with:

```bash
poetry run pytest
poetry run ruff format --check src scripts tests
poetry run ruff check src scripts tests
poetry run mypy
```

The API tests send requests through httpx directly to the in-process FastAPI app, using `http://localhost:8000` as the test base URL. They do not need a separate server. For the end-to-end evaluator, start the service in one terminal with `poetry run python scripts/run_api.py`, then run `poetry run python scripts/evaluate_api.py` in another terminal. The evaluator expects the service at `http://localhost:8000` by default.

The evaluation compares a corpus-derived keyword baseline with the fixed TF-IDF/logistic-regression model on all six records in `examples/api_test.json`, then exercises every case in `examples/api_invalid.json`. It writes the complete prediction-level results and timing to `results/api_evaluation.json`. The mean endpoint time includes the HTTP round trip, request parsing, and prediction. It excludes model fitting/loading, which is completed before the server starts. No test labels are used for fitting or tuning.

The keyword baseline counts training-set token occurrences by label, adds those counts for the tokens in each request, and selects the highest score. Ties and requests with no training-token matches use the fixed order `quality`, `planning`, `documents`.

The supplied labeled test set has only six examples. Its accuracy is a check against the assessment examples, not a reliable estimate of performance on real shipyard requests. The training examples are also very small and synthetic; the model has no context beyond learned unigram and bigram patterns.

In the recorded run, the baseline and trained model each classified all six supplied examples correctly. Both scored 6/6, so this evaluation provides no evidence that the trained model is better than the simpler baseline. The API averaged 13.206 ms per request on the local run, excluding model fitting at startup; all seven supplied invalid inputs returned HTTP 400. Part A passed all 13 supplied checks. Full results are in `results/`.

## Project layout

```text
materials/      supplied CSV, training data, and DOCX template
examples/       supplied valid/invalid evaluation inputs
src/            report generator, classifiers, and API
scripts/        repeatable entry points and evaluation runners
results/        sample report and recorded check/evaluation output
outputs/        default working reports (ignored by Git)
```

## Approach, time, and assistance

The implementation validates the full report input before output creation, uses a temporary copy plus atomic replacement, and keeps both task parts runnable locally. The classifier and baseline are both derived only from the supplied training JSON. Evaluation reports each prediction, failures, accuracy out of six, and API timing method.

Time spent and final observed results are recorded in `REPORT.md` after running the supplied checks. AI assistance was used to inspect the requirements, shape the implementation, and review the evaluation workflow; all reported results are generated by the checked-in scripts.

## License

This project is distributed under the BSD 3-Clause License. See [LICENSE](LICENSE).
