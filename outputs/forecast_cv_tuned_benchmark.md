# CV Tuned Forecast Benchmark

This benchmark uses historical holdout years only. It does not use leaderboard scores.

Primary candidate config:

- Revenue level: `recent_yoy_shrink50`
- Revenue scale: `1.05`
- COGS ratio level: `ewm30`
- COGS scale: `0.95`

Recent-year alternate config:

- Revenue level: `flat`
- Revenue scale: `1.08`
- COGS ratio level: `recent_yoy_shrink50`
- COGS scale: `0.95`

## Holdout Year 2021

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 530578.01 | 768466.68 | 0.7809 |
| seasonal_growth_baseline | COGS | 502552.95 | 731985.73 | 0.7394 |
| known_best_public_912_config | Revenue | 516242.35 | 730548.26 | 0.8020 |
| known_best_public_912_config | COGS | 450897.52 | 630723.40 | 0.8065 |
| cv_tuned_candidate | Revenue | 528376.71 | 733557.31 | 0.8004 |
| cv_tuned_candidate | COGS | 442606.77 | 629935.97 | 0.8070 |
| cv_recent_2022_candidate | Revenue | 596095.11 | 786359.77 | 0.7706 |
| cv_recent_2022_candidate | COGS | 444089.22 | 654163.34 | 0.7919 |

## Holdout Year 2022

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 698524.32 | 943421.67 | 0.6823 |
| seasonal_growth_baseline | COGS | 580407.79 | 780488.87 | 0.7137 |
| known_best_public_912_config | Revenue | 621547.03 | 839123.13 | 0.7487 |
| known_best_public_912_config | COGS | 500029.93 | 674981.31 | 0.7858 |
| cv_tuned_candidate | Revenue | 591493.25 | 793745.66 | 0.7751 |
| cv_tuned_candidate | COGS | 500490.23 | 674220.10 | 0.7863 |
| cv_recent_2022_candidate | Revenue | 579309.35 | 777409.90 | 0.7843 |
| cv_recent_2022_candidate | COGS | 501637.47 | 678566.10 | 0.7836 |

## Submission

- Submit `outputs/submission_cv_tuned.csv` as the next data-driven trial.
- If it is worse than the public 912 backup, try `outputs/submission_cv_recent_2022.csv` only as a secondary trial.
- Keep `outputs/submission_public_912428.csv` as the known-best fallback.
