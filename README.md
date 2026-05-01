# Datathon 2026 Round 1

Workspace for **Datathon 2026 - The Gridbreaker, Round 1**. The repo contains reproducible scripts and lightweight reports for:

1. Multiple-choice data questions
2. EDA / business analysis
3. Daily `Revenue` and `COGS` forecasting for Kaggle submission

## Current Kaggle Submission

Use:

```text
outputs/submission_best.csv
```

This file is the restored known public-score candidate:

```text
Public score: 912428.76513
Backup file: outputs/submission_public_912428.csv
```

`outputs/submission_best.csv`, `outputs/submission_improved.csv`, and `outputs/submission_public_912428.csv` should match after running the current forecasting script.

## Repository Layout

```text
dataset/                         Raw CSV files used by the scripts
scripts/                         Reproducible Part 1/2/3 scripts
outputs/                         Generated reports, figures, and submissions
PROJECT_ONBOARDING_REPORT.md      High-level project status
ROUND1_CODE_GUIDE.md              Script-by-script run guide
datathon-2026-round1-de-thi-vong-1.md  Markdown version of the problem statement
docs/DATA.md                      Dataset setup notes
```

## Setup

This project uses `uv run --with ...` so a permanent virtual environment is optional.

Check that the raw CSV files exist:

```bash
ls dataset/*.csv
```

See [docs/DATA.md](docs/DATA.md) for the expected files.

## Common Commands

Part 1:

```bash
uv run --with pandas python scripts/solve_mcq.py
```

Part 2:

```bash
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
```

Part 3 current submission:

```bash
uv run --with pandas --with numpy python scripts/forecast_improved.py
```

Optional benchmark:

```bash
uv run --with pandas --with scikit-learn python scripts/forecast_benchmark.py
```

## Important Notes

- Raw `dataset/*.csv` files are included so the project can be cloned and rerun directly.
- The original PDF statement is ignored; use the markdown statement in this repo.
- `outputs/submission_public_912428.csv` is the backup of the best known public-score submission.
- `scripts/forecast_improved.py` is the generator that should recreate the current `submission_best.csv`.
