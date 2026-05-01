# Datathon Round 1 Code Guide

This workspace includes these runnable scripts:

1. `scripts/solve_mcq.py`
   - Computes all 10 multiple-choice answers directly from the CSV files.
   - Writes a markdown summary to `outputs/mcq_answers.md`.

2. `scripts/make_eda_tables.py`
   - Generates starter tables for the open-ended EDA section.
   - Writes CSV outputs under `outputs/eda/`.

3. `scripts/forecast_baseline.py`
   - Trains a simple seasonal-growth baseline for the forecasting task.
   - Uses `sales.csv` for training and `sample_submission.csv` for the target dates.
   - Writes `outputs/submission_baseline.csv`.

4. `scripts/build_eda_report.py`
   - Generates a presentation-ready markdown report and chart pack for Part 2.
   - Writes figures and a report under `outputs/eda_report/`.

5. `scripts/forecast_benchmark.py`
   - Benchmarks the baseline against an experimental lag-based gradient boosting model.
   - Writes `outputs/forecast_benchmark.md`.

6. `scripts/forecast_blend.py`
   - Creates a fixed-weight blend between the baseline and lag-based model.
   - Writes `outputs/submission_blend.csv`.
   - Keeps the older blended candidate available for comparison.

7. `scripts/forecast_improved.py`
   - Creates the current known-best seasonal + weekday + COGS/Revenue ratio candidate.
   - Writes `outputs/submission_improved.csv`.
   - Copies the currently recommended file to `outputs/submission_best.csv`.
   - Writes `outputs/forecast_improved_benchmark.md`.

8. `scripts/forecast_cv_tuned.py`
   - Builds experimental candidates using historical holdout validation only.
   - Writes `outputs/submission_cv_tuned.csv`.
   - Writes `outputs/submission_cv_recent_2022.csv`.
   - Does not overwrite `outputs/submission_best.csv`.

## Recommended commands

### Part 1: MCQ

```powershell
uv run --with pandas python scripts/solve_mcq.py
```

### Part 2: EDA starter tables

```powershell
uv run --with pandas python scripts/make_eda_tables.py
```

### Part 2: Full chart pack + report

```powershell
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
```

Files produced:

- `outputs/eda/monthly_sales.csv`
- `outputs/eda/category_performance.csv`
- `outputs/eda/region_performance.csv`
- `outputs/eda/returns_by_category.csv`
- `outputs/eda/return_rate_by_size.csv`
- `outputs/eda/promo_summary.csv`
- `outputs/eda/traffic_by_source.csv`
- `outputs/eda/traffic_sales_daily.csv`

Presentation-ready files:

- `outputs/eda_report/eda_report.md`
- `outputs/eda_report/01_monthly_sales_and_seasonality.png`
- `outputs/eda_report/02_category_revenue_margin.png`
- `outputs/eda_report/03_returns_by_category_and_size.png`
- `outputs/eda_report/04_region_and_acquisition.png`
- `outputs/eda_report/05_traffic_and_inventory.png`

Use those tables in a notebook or BI tool to build the visuals and business story.

### Part 3: Forecasting baseline

```powershell
uv run --with pandas python scripts/forecast_baseline.py
```

If you want to validate on a different year:

```powershell
uv run --with pandas python scripts/forecast_baseline.py --holdout-year 2021
```

### Part 3: Benchmark candidate models

```powershell
uv run --with pandas --with scikit-learn python scripts/forecast_benchmark.py
```

This will produce:

- `outputs/forecast_benchmark.md`

### Part 3: Older blended submission

```powershell
uv run --with pandas --with scikit-learn python scripts/forecast_blend.py
```

This will produce:

- `outputs/submission_blend.csv`

### Part 3: Current best improved submission

```powershell
uv run --with pandas --with numpy python scripts/forecast_improved.py
```

This will produce:

- `outputs/submission_improved.csv`
- `outputs/submission_best.csv`
- `outputs/forecast_improved_benchmark.md`

The known public-score `912428.76513` submission is kept at:

- `outputs/submission_public_912428.csv`

It should match `outputs/submission_best.csv` after running `scripts/forecast_improved.py`.

### Part 3: Experimental CV-tuned candidates

```powershell
uv run --with pandas --with numpy python scripts/forecast_cv_tuned.py
```

This will produce:

- `outputs/submission_cv_tuned.csv`
- `outputs/submission_cv_recent_2022.csv`
- `outputs/forecast_cv_tuned_benchmark.md`

Submit `submission_cv_tuned.csv` first if you want to test the next data-driven improvement. Keep `submission_public_912428.csv` as the fallback.

## Suggested EDA storyline

Use the generated tables to cover these four layers:

1. Descriptive
   - Monthly revenue, COGS, gross profit, gross margin.
   - Category and segment performance.

2. Diagnostic
   - Return hotspots by category, size, and reason.
   - Promo-heavy categories versus gross margin.
   - Region performance and average order value proxy.

3. Predictive
   - Trend and seasonality in monthly sales.
   - Traffic versus sales movement by day.

4. Prescriptive
   - Reduce returns in high-risk categories and sizes.
   - Revisit promo mix where discount is high but margin is weak.
   - Prioritize inventory and logistics for the top-revenue regions.

## Important caveat

Q7 in the markdown mentions `sales_train.csv`, but the provided `sales.csv` does not contain any `region` column. The MCQ solver therefore computes regional revenue from transaction tables by joining:

- `orders.zip`
- `geography.region`
- `order_items.quantity * order_items.unit_price`

The top region is the same if revenue is aggregated from `payments.payment_value`, which makes the answer stable despite the schema mismatch in the question text.

## Current recommendation

- Use `scripts/solve_mcq.py` for the multiple-choice section.
- Use `scripts/build_eda_report.py` as the starting point for Part 2, then edit the markdown wording to match your presentation style.
- Use `scripts/forecast_improved.py` for the current best Part 3 submission candidate.
- Keep `outputs/submission_baseline.csv` as the simpler fallback if you prefer the more interpretable model.
