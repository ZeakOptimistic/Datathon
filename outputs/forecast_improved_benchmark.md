# Improved Forecast Benchmark

This benchmark compares the original seasonal-growth baseline with the improved submission candidate.

Improved model:

- Revenue level: `recent_yoy_shrink25`
- COGS: predicted as `Revenue * seasonal COGS/Revenue ratio`, ratio level `ewm30`
- Calendar signal: month/day seasonality plus weekday residual adjustment

## Holdout Year 2021

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 530578.01 | 768466.68 | 0.7809 |
| seasonal_growth_baseline | COGS | 502552.95 | 731985.73 | 0.7394 |
| improved_seasonal_dow_ratio | Revenue | 516242.35 | 730548.26 | 0.8020 |
| improved_seasonal_dow_ratio | COGS | 450897.52 | 630723.40 | 0.8065 |

## Holdout Year 2022

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 698524.32 | 943421.67 | 0.6823 |
| seasonal_growth_baseline | COGS | 580407.79 | 780488.87 | 0.7137 |
| improved_seasonal_dow_ratio | Revenue | 621547.03 | 839123.13 | 0.7487 |
| improved_seasonal_dow_ratio | COGS | 500029.93 | 674981.31 | 0.7858 |

## Submission Recommendation

- Use `outputs/submission_best.csv` for the current known-best Kaggle submission.
- `outputs/submission_public_912428.csv` preserves the same public-score submission as a backup.
- Keep `outputs/submission_baseline.csv` as a conservative fallback because it matches the official sample-style seasonal baseline.
