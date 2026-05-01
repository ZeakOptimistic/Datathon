from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from forecast_baseline import fit_baseline, predict_dates
from forecast_benchmark import evaluate_baseline, recursive_predict_lag_model

DEFAULT_REVENUE_BASELINE_WEIGHT = 0.85
DEFAULT_COGS_BASELINE_WEIGHT = 0.55


def blend_series(base_pred: np.ndarray, lag_pred: np.ndarray, baseline_weight: float) -> np.ndarray:
    return baseline_weight * base_pred + (1.0 - baseline_weight) * lag_pred


def evaluate_blend(train_df: pd.DataFrame, valid_df: pd.DataFrame, target: str, baseline_weight: float) -> dict[str, float]:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    baseline_prediction = predict_dates(valid_df["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)
    base_pred = baseline_prediction[target].to_numpy()
    lag_pred = recursive_predict_lag_model(train_df, valid_df["Date"], target)
    blended = blend_series(base_pred, lag_pred, baseline_weight)
    actual = valid_df[target].to_numpy()

    mae = float(np.mean(np.abs(actual - blended)))
    rmse = float(np.sqrt(np.mean((actual - blended) ** 2)))
    r2 = float(1.0 - np.sum((actual - blended) ** 2) / np.sum((actual - actual.mean()) ** 2))
    return {"mae": mae, "rmse": rmse, "r2": r2}


def build_blend_submission(
    sales: pd.DataFrame,
    submission_template: pd.DataFrame,
    revenue_baseline_weight: float,
    cogs_baseline_weight: float,
) -> pd.DataFrame:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(sales)
    baseline_prediction = predict_dates(submission_template["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)

    lag_revenue = recursive_predict_lag_model(sales, submission_template["Date"], "Revenue")
    lag_cogs = recursive_predict_lag_model(sales, submission_template["Date"], "COGS")

    blended = pd.DataFrame({"Date": submission_template["Date"]})
    blended["Revenue"] = blend_series(baseline_prediction["Revenue"].to_numpy(), lag_revenue, revenue_baseline_weight)
    blended["COGS"] = blend_series(baseline_prediction["COGS"].to_numpy(), lag_cogs, cogs_baseline_weight)
    blended["Revenue"] = blended["Revenue"].round(2)
    blended["COGS"] = blended["COGS"].round(2)
    return blended


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a blended submission from the seasonal baseline and lag-based model.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "submission_blend.csv",
        help="CSV file for the blended submission.",
    )
    parser.add_argument(
        "--best-output",
        type=Path,
        default=Path("outputs") / "submission_best.csv",
        help="Path to update when --copy-to-best is explicitly set.",
    )
    parser.add_argument(
        "--copy-to-best",
        action="store_true",
        help="Copy the blend output to submission_best.csv. Disabled by default because forecast_improved.py is the current best candidate.",
    )
    parser.add_argument(
        "--revenue-baseline-weight",
        type=float,
        default=DEFAULT_REVENUE_BASELINE_WEIGHT,
        help="Weight assigned to the baseline model for Revenue.",
    )
    parser.add_argument(
        "--cogs-baseline-weight",
        type=float,
        default=DEFAULT_COGS_BASELINE_WEIGHT,
        help="Weight assigned to the baseline model for COGS.",
    )
    parser.add_argument(
        "--holdout-years",
        type=int,
        nargs="+",
        default=[2021, 2022],
        help="Holdout years used to report validation metrics for the fixed blend.",
    )
    args = parser.parse_args()

    sales = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    submission_template = pd.read_csv(args.data_dir / "sample_submission.csv", parse_dates=["Date"])

    output_df = build_blend_submission(
        sales=sales,
        submission_template=submission_template,
        revenue_baseline_weight=args.revenue_baseline_weight,
        cogs_baseline_weight=args.cogs_baseline_weight,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.output, index=False, date_format="%Y-%m-%d")

    print(f"Saved blended submission to {args.output}")
    if args.copy_to_best:
        shutil.copyfile(args.output, args.best_output)
        print(f"Copied blended submission to {args.best_output}")
    else:
        print("Did not update submission_best.csv; forecast_improved.py is the current recommended generator.")
    print("Blend weights:")
    print(f"  Revenue baseline weight: {args.revenue_baseline_weight:.2f}")
    print(f"  COGS baseline weight: {args.cogs_baseline_weight:.2f}")
    print("Validation metrics:")

    for holdout_year in args.holdout_years:
        train_df = sales[sales["Date"].dt.year < holdout_year].copy()
        valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
        baseline_rev = evaluate_baseline(train_df, valid_df, "Revenue")
        baseline_cogs = evaluate_baseline(train_df, valid_df, "COGS")
        blend_rev = evaluate_blend(train_df, valid_df, "Revenue", args.revenue_baseline_weight)
        blend_cogs = evaluate_blend(train_df, valid_df, "COGS", args.cogs_baseline_weight)

        print(f"  Holdout {holdout_year}:")
        print(f"    Baseline Revenue MAE={baseline_rev['mae']:.2f} | Blend Revenue MAE={blend_rev['mae']:.2f}")
        print(f"    Baseline COGS    MAE={baseline_cogs['mae']:.2f} | Blend COGS    MAE={blend_cogs['mae']:.2f}")


if __name__ == "__main__":
    main()
