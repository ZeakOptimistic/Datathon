# Datathon Round 1 Code Guide

This workspace keeps the runnable path for all three exercises and removes obsolete Kaggle trial files.

## Scripts

1. `scripts/solve_mcq.py`
   - Computes all 10 multiple-choice answers from the CSV files.
   - Writes `outputs/mcq_answers.md`.

2. `scripts/make_eda_tables.py`
   - Generates starter EDA tables under `outputs/eda/`.

3. `scripts/build_eda_report.py`
   - Generates the Part 2 chart pack and report.
   - Writes `outputs/eda_report/eda_report.md` and PNG figures.

4. `scripts/forecast_baseline.py`
   - Keeps a simple seasonal baseline for comparison.
   - Writes `outputs/submission_baseline.csv`.

5. `scripts/forecast_benchmark.py`
   - Benchmarks baseline-style forecasting experiments.
   - Writes `outputs/forecast_benchmark.md`.

6. `scripts/forecast_cv_tuned.py`
   - Generates the final Kaggle submission.
   - Writes `outputs/submission_cv_tuned_diag_1122_0878.csv`.
   - Copies the same file to `outputs/submission_best.csv`.
   - Writes `outputs/forecast_cv_tuned_benchmark.md`.

## Commands

### Part 1: MCQ

```powershell
uv run --with pandas python scripts/solve_mcq.py
```

### Part 2: EDA report

```powershell
uv run --with pandas --with matplotlib python scripts/build_eda_report.py
```

### Part 3: Final Kaggle submission

```powershell
uv run --with pandas --with numpy python scripts/forecast_cv_tuned.py
```

Submit:

```text
outputs/submission_best.csv
```

Equivalent named final file:

```text
outputs/submission_cv_tuned_diag_1122_0878.csv
```

## Key Outputs

- `outputs/mcq_answers.md`
- `outputs/eda_report/eda_report.md`
- `outputs/submission_best.csv`
- `outputs/submission_cv_tuned_diag_1122_0878.csv`
- `outputs/forecast_cv_tuned_benchmark.md`

## Important Caveat

Q7 in the markdown mentions `sales_train.csv`, but the provided `sales.csv` does not contain a `region` column. The MCQ solver computes regional revenue from transaction tables by joining:

- `orders.zip`
- `geography.region`
- `order_items.quantity * order_items.unit_price`

Payment-based aggregation gives the same top region, so the answer is stable despite the schema mismatch.
