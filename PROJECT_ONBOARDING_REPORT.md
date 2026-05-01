# Project Onboarding Report

## Status

The repo is cleaned for GitHub push. It keeps the reproducible path for all three Round 1 exercises:

1. Part 1 MCQ answers
2. Part 2 EDA report and chart pack
3. Part 3 final Kaggle forecasting submission

## Current Kaggle Submission

Use:

```text
outputs/submission_best.csv
```

This file is generated from the same content as:

```text
outputs/submission_cv_tuned_diag_1122_0878.csv
```

The generator is:

```text
scripts/forecast_cv_tuned.py
```

## Main Commands

Part 1:

```powershell
uv run --with pandas python scripts/solve_mcq.py
```

Part 2:

```powershell
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
```

Part 3:

```powershell
uv run --with pandas --with numpy python scripts/forecast_cv_tuned.py
```

## Files To Read First

- `README.md`
- `ROUND1_CODE_GUIDE.md`
- `docs/SUBMISSION_NOTES.md`
- `datathon-2026-round1-de-thi-vong-1.md`

## Key Outputs

- `outputs/mcq_answers.md`
- `outputs/eda_report/eda_report.md`
- `outputs/submission_best.csv`
- `outputs/submission_cv_tuned_diag_1122_0878.csv`
- `outputs/forecast_cv_tuned_benchmark.md`

## Notes

- Raw dataset CSV files are included so the project can be cloned and rerun directly.
- Obsolete Kaggle trial submissions, failed public-calibrated files, and analog-blend experiment files were removed from the cleaned repo state.
- `outputs/submission_best.csv` is the recommended upload file.
