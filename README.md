# Datathon 2026 Round 1

Workspace for **Datathon 2026 - The Gridbreaker, Round 1**. The repo contains reproducible code and lightweight outputs for:

1. Multiple-choice data questions
2. EDA / business analysis
3. Daily `Revenue` and `COGS` forecasting for Kaggle submission

## Current Kaggle Submission

Use:

```text
outputs/submission_best.csv
```

This is a convenience copy of:

```text
outputs/submission_cv_tuned_diag_1122_0878.csv
```

## Repository Layout

```text
dataset/                         Raw CSV files used by the scripts
scripts/                         Reproducible Part 1/2/3 scripts
outputs/                         Generated reports, figures, and final submissions
docs/                            Short project notes
PROJECT_ONBOARDING_REPORT.md      High-level project status
ROUND1_CODE_GUIDE.md              Script-by-script run guide
datathon-2026-round1-de-thi-vong-1.md  Markdown version of the problem statement
```

## Setup

This project uses `uv run --with ...` so a permanent virtual environment is optional.

Check that the raw CSV files exist:

```bash
ls dataset/*.csv
```

## Common Commands

Part 1:

```bash
uv run --with pandas python scripts/solve_mcq.py
```

Part 2:

```bash
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
```

Part 3 final submission:

```bash
uv run --with pandas --with numpy python scripts/forecast_cv_tuned.py
```

This creates:

- `outputs/submission_cv_tuned_diag_1122_0878.csv`
- `outputs/submission_best.csv`
- `outputs/forecast_cv_tuned_benchmark.md`

## Important Notes

- Raw `dataset/*.csv` files are included so the project can be cloned and rerun directly.
- The original PDF statement is ignored; use the markdown statement in this repo.
- `outputs/submission_best.csv` is the file to upload to Kaggle.
