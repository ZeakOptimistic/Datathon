from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


def fit_baseline(train: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, float, float, int]:
    train = train.copy()
    train["year"] = train["Date"].dt.year
    train["month"] = train["Date"].dt.month
    train["day"] = train["Date"].dt.day

    annual = train.groupby("year", as_index=True)[["Revenue", "COGS"]].sum()
    full_years = annual.loc[annual.index.min() + 1 : annual.index.max()]
    yoy_rev = full_years["Revenue"].pct_change().dropna()
    yoy_cogs = full_years["COGS"].pct_change().dropna()
    growth_rev = float((1.0 + yoy_rev).prod() ** (1.0 / len(yoy_rev)))
    growth_cogs = float((1.0 + yoy_cogs).prod() ** (1.0 / len(yoy_cogs)))

    annual_means = train.groupby("year")[["Revenue", "COGS"]].transform("mean")
    train["rev_norm"] = train["Revenue"] / annual_means["Revenue"]
    train["cogs_norm"] = train["COGS"] / annual_means["COGS"]

    seasonal = (
        train.groupby(["month", "day"], as_index=False)[["rev_norm", "cogs_norm"]]
        .mean()
        .sort_values(["month", "day"])
    )
    base_year = int(annual.index.max())

    return annual, seasonal, growth_rev, growth_cogs, base_year


def predict_dates(
    dates: pd.Series,
    annual: pd.DataFrame,
    seasonal: pd.DataFrame,
    growth_rev: float,
    growth_cogs: float,
    base_year: int,
) -> pd.DataFrame:
    prediction = pd.DataFrame({"Date": pd.to_datetime(dates)})
    prediction["year"] = prediction["Date"].dt.year
    prediction["month"] = prediction["Date"].dt.month
    prediction["day"] = prediction["Date"].dt.day
    prediction["years_ahead"] = prediction["year"] - base_year
    prediction = prediction.merge(seasonal, on=["month", "day"], how="left")
    prediction["rev_norm"] = prediction["rev_norm"].fillna(1.0)
    prediction["cogs_norm"] = prediction["cogs_norm"].fillna(1.0)

    base_rev = annual.loc[base_year, "Revenue"] / 365.0
    base_cogs = annual.loc[base_year, "COGS"] / 365.0
    prediction["Revenue"] = base_rev * (growth_rev ** prediction["years_ahead"]) * prediction["rev_norm"]
    prediction["COGS"] = base_cogs * (growth_cogs ** prediction["years_ahead"]) * prediction["cogs_norm"]
    return prediction[["Date", "Revenue", "COGS"]]


def mae(actual: pd.Series, predicted: pd.Series) -> float:
    return float((actual - predicted).abs().mean())


def rmse(actual: pd.Series, predicted: pd.Series) -> float:
    return float(math.sqrt(((actual - predicted) ** 2).mean()))


def r2(actual: pd.Series, predicted: pd.Series) -> float:
    ss_res = float(((actual - predicted) ** 2).sum())
    ss_tot = float(((actual - actual.mean()) ** 2).sum())
    return 1.0 - (ss_res / ss_tot)


def backtest(train: pd.DataFrame, holdout_year: int) -> dict[str, float]:
    history = train[train["Date"].dt.year < holdout_year].copy()
    holdout = train[train["Date"].dt.year == holdout_year].copy()
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(history)
    predicted = predict_dates(holdout["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)
    predicted = holdout[["Date", "Revenue", "COGS"]].merge(predicted, on="Date", suffixes=("_actual", "_pred"))
    return {
        "revenue_mae": mae(predicted["Revenue_actual"], predicted["Revenue_pred"]),
        "revenue_rmse": rmse(predicted["Revenue_actual"], predicted["Revenue_pred"]),
        "revenue_r2": r2(predicted["Revenue_actual"], predicted["Revenue_pred"]),
        "cogs_mae": mae(predicted["COGS_actual"], predicted["COGS_pred"]),
        "cogs_rmse": rmse(predicted["COGS_actual"], predicted["COGS_pred"]),
        "cogs_r2": r2(predicted["COGS_actual"], predicted["COGS_pred"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a simple seasonal-growth forecasting baseline for Round 1.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "submission_baseline.csv",
        help="CSV file for the generated baseline submission.",
    )
    parser.add_argument(
        "--holdout-year",
        type=int,
        default=2022,
        help="Last full year to use as a time-based validation slice.",
    )
    args = parser.parse_args()

    train = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"])
    submission_template = pd.read_csv(args.data_dir / "sample_submission.csv", parse_dates=["Date"])

    metrics = backtest(train, args.holdout_year)
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train)
    prediction = predict_dates(submission_template["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)
    prediction["Revenue"] = prediction["Revenue"].round(2)
    prediction["COGS"] = prediction["COGS"].round(2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    prediction.to_csv(args.output, index=False, date_format="%Y-%m-%d")

    print(f"Saved baseline submission to {args.output}")
    print("Validation metrics:")
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value:.4f}")


if __name__ == "__main__":
    main()
