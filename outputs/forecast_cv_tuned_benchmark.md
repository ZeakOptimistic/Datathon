# Final Forecast Benchmark

This benchmark keeps only the final Kaggle submission path used for the cleaned repo.

Final submission:

- Output: `outputs/submission_cv_tuned_diag_1122_0878.csv`
- Revenue level: `recent_yoy_shrink50`
- Revenue scale: `1.122`
- COGS ratio level: `ewm30`
- COGS scale: `0.878`

## Holdout Year 2021

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 530578.01 | 768466.68 | 0.7809 |
| seasonal_growth_baseline | COGS | 502552.95 | 731985.73 | 0.7394 |
| final_cv_tuned_submission | Revenue | 597932.08 | 788048.65 | 0.7696 |
| final_cv_tuned_submission | COGS | 440323.07 | 632193.32 | 0.8056 |

## Holdout Year 2022

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 698524.32 | 943421.67 | 0.6823 |
| seasonal_growth_baseline | COGS | 580407.79 | 780488.87 | 0.7137 |
| final_cv_tuned_submission | Revenue | 576541.27 | 777955.32 | 0.7840 |
| final_cv_tuned_submission | COGS | 502217.23 | 673984.85 | 0.7865 |

## Submission

- Submit `outputs/submission_cv_tuned_diag_1122_0878.csv` or `outputs/submission_best.csv`.
- `outputs/submission_best.csv` is kept as the convenience copy for Kaggle upload.
