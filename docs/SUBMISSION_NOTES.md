# Submission Notes

## Current Kaggle File

Submit either file below; they are generated to the same content by the final forecasting script:

```text
outputs/submission_best.csv
outputs/submission_cv_tuned_diag_1122_0878.csv
```

`submission_cv_tuned_diag_1122_0878.csv` is the best current Kaggle result reported by the team.

## Reproduce

Run:

```bash
uv run --with pandas --with numpy python scripts/forecast_cv_tuned.py
```

This writes:

```text
outputs/submission_cv_tuned_diag_1122_0878.csv
outputs/submission_best.csv
outputs/forecast_cv_tuned_benchmark.md
```

## Model Summary

- Revenue uses normalized month/day seasonality plus weekday adjustment.
- Annual Revenue level uses recent YoY shrinkage.
- COGS is predicted as `Revenue * seasonal COGS/Revenue ratio`.
- Final scales are `Revenue = 1.122` and `COGS = 0.878`.
