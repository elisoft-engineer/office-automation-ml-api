# Office Automation and ML API

This project completes Task 2, Parts A and B: building a Word status report from job data and classifying incoming work requests through a local API. All business data is synthetic.

## Requirements

- Python 3.14 or newer
- Poetry 2.x
- Node.js and OfficeCLI `@officecli/officecli` (DOCX editing CLI)

The Python environment is managed by Poetry. Create it and install dependencies with:

```bash
poetry env use python3.14
poetry install
```

Install OfficeCLI using the official npm package, then verify it:

```bash
npm install --global @officecli/officecli
officecli --version
```

OfficeCLI reads and edits the provided Word template. The report code itself uses Python's standard library for CSV parsing and validation.

## Part A: status report

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

## Part B: classifier API

Start the service in one terminal:

```bash
poetry run python scripts/run_api.py
```

The API trains a TF-IDF plus logistic-regression pipeline from `materials/api_train.json` at startup, before accepting requests. It listens on `localhost:8000` by default; set `HOST` or `PORT` to change the bind address. Set `TRAIN_DATA` to use a different training JSON file. The interactive API documentation is available at `http://localhost:8000/docs`. A valid request returns both the predicted label and model name:

```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"text":"Inspect a weld defect"}'
```

Missing, blank, non-string text and non-object request bodies return HTTP 400 with a clear JSON error. No external API or API key is needed.

## Reproduce the checks and evaluation

OfficeCLI is required for the report command and these Part A checks. After installing it, confirm `officecli --version` works in the same terminal so the command is on `PATH`. The report command reads the source template with OfficeCLI, checks its placeholders, and edits a copy. The pytest unit tests cover CSV parsing without OfficeCLI; the checks below exercise the actual Word template:

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

The keyword baseline counts each request's words in the training examples by label, then returns the label with the most matches. If labels tie or no words match, it picks `quality`, `planning`, and `documents` in that order.

The test set has only six examples, so its accuracy is a check against these examples rather than a reliable estimate of performance on real requests. The training set is also small and synthetic, and the model only learns unigram and bigram patterns.

In the latest run, both the baseline and the trained model classified all six examples correctly. Since both scored 6/6, the result does not show that the trained model is better than the baseline. The API averaged 11.592 ms per request, excluding model fitting at startup. All seven invalid requests returned HTTP 400, and all 13 Part A checks passed. Full results are in `results/`.

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

Both parts run locally. The report command checks the full CSV before writing and only replaces the output after the edited document passes a read-back check. The classifier and keyword baseline use the supplied training data, and the evaluation prints each prediction, failures, accuracy out of six, and the timing method. `REPORT.md` records the results, limitations, time spent, and tools used.

## License

This project is distributed under the BSD 3-Clause License. See [LICENSE](LICENSE).
