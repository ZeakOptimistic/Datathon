# Forecast Benchmark

This file compares the current seasonal-growth baseline against a lag-based gradient boosting model.

## Holdout Year 2021

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 530578.01 | 768466.68 | 0.7809 |
| seasonal_growth_baseline | COGS | 502552.95 | 731985.73 | 0.7394 |
| lag_gradient_boosting | Revenue | 681207.10 | 1029351.04 | 0.6069 |
| lag_gradient_boosting | COGS | 556656.51 | 837291.37 | 0.6591 |
| blend_baseline_lag | Revenue | 525495.70 | 770490.24 | 0.7798 |
| blend_baseline_lag | COGS | 489453.75 | 730219.94 | 0.7407 |

## Holdout Year 2022

| Model | Target | MAE | RMSE | R2 |
|---|---|---:|---:|---:|
| seasonal_growth_baseline | Revenue | 698524.32 | 943421.67 | 0.6823 |
| seasonal_growth_baseline | COGS | 580407.79 | 780488.87 | 0.7137 |
| lag_gradient_boosting | Revenue | 741797.57 | 1056105.18 | 0.6019 |
| lag_gradient_boosting | COGS | 547859.43 | 743005.47 | 0.7405 |
| blend_baseline_lag | Revenue | 693496.07 | 939612.63 | 0.6849 |
| blend_baseline_lag | COGS | 536408.58 | 722232.14 | 0.7548 |

## Recommendation

- Use the fixed blend as the current best submission candidate. It improves Revenue MAE on both 2021 and 2022 holdouts relative to the plain baseline.
- Keep the seasonal-growth baseline as the fallback because it is simpler and more interpretable.
- The pure lag-based model is still useful for feature ideas, but it does not beat the baseline on Revenue by itself.
