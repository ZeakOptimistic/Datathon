from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from forecast_baseline import fit_baseline, predict_dates


FINAL_CONFIG = {
    "revenue_level_method": "recent_yoy_shrink50",
    "ratio_level_method": "ewm30",
    "revenue_scale": 1.122,
    "cogs_scale": 0.878,
}

FINAL_PUBLIC_SCORE = "best current Kaggle submission"
RATIO_MIN = 0.65
RATIO_MAX = 1.05


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(math.sqrt(np.mean((actual - predicted) ** 2)))


def r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = float(np.sum((actual - predicted) ** 2))
    ss_tot = float(np.sum((actual - actual.mean()) ** 2))
    return 1.0 - (ss_res / ss_tot)


def annual_factor(annual_values: pd.Series, method: str, years_ahead: int) -> float:
    if years_ahead == 0:
        return 1.0

    values = annual_values.astype(float)
    yoy = values.pct_change().dropna()
    if yoy.empty:
        return 1.0

    if method == "flat":
        growth = 1.0
    elif method == "recent_yoy_shrink25":
        growth = 1.0 + 0.25 * float(yoy.iloc[-1])
    elif method == "recent_yoy_shrink50":
        growth = 1.0 + 0.50 * float(yoy.iloc[-1])
    elif method == "ewm30":
        growth = 1.0 + float(yoy.ewm(alpha=0.30, adjust=False).mean().iloc[-1])
    else:
        raise ValueError(f"Unknown annual level method: {method}")

    return float(growth**years_ahead)


def predict_seasonal_dow(
    train_df: pd.DataFrame,
    dates: pd.Series,
    target: str,
    level_method: str,
) -> np.ndarray:
    train = train_df[["Date", target]].copy()
    train["year"] = train["Date"].dt.year
    train["month"] = train["Date"].dt.month
    train["day"] = train["Date"].dt.day
    train["dow"] = train["Date"].dt.dayofweek

    annual_mean = train.groupby("year")[target].mean()
    annual_sum = train.groupby("year")[target].sum()
    train["norm_target"] = train[target] / train["year"].map(annual_mean)

    seasonal = (
        train.groupby(["month", "day"], as_index=False)["norm_target"]
        .mean()
        .rename(columns={"norm_target": "seasonal_factor"})
    )
    with_season = train.merge(seasonal, on=["month", "day"], how="left")
    with_season["weekday_residual"] = with_season["norm_target"] / with_season["seasonal_factor"]
    weekday_factor = with_season.groupby("dow")["weekday_residual"].mean()

    future = pd.DataFrame({"Date": pd.to_datetime(dates)})
    future["year"] = future["Date"].dt.year
    future["month"] = future["Date"].dt.month
    future["day"] = future["Date"].dt.day
    future["dow"] = future["Date"].dt.dayofweek
    future = future.merge(seasonal, on=["month", "day"], how="left")
    future["seasonal_factor"] = future["seasonal_factor"].fillna(1.0)
    future["weekday_factor"] = future["dow"].map(weekday_factor).fillna(1.0)

    max_train_year = int(train["year"].max())
    last_annual_mean = float(annual_mean.iloc[-1])
    prediction = []
    for row in future.itertuples(index=False):
        level = last_annual_mean * annual_factor(annual_sum, level_method, int(row.year - max_train_year))
        prediction.append(level * float(row.seasonal_factor) * float(row.weekday_factor))
    return np.asarray(prediction)


def predict_ratio(
    train_df: pd.DataFrame,
    dates: pd.Series,
    level_method: str,
) -> np.ndarray:
    ratio_train = train_df[["Date", "Revenue", "COGS"]].copy()
    ratio_train["COGS_to_Revenue"] = ratio_train["COGS"] / ratio_train["Revenue"]
    ratio_prediction = predict_seasonal_dow(
        ratio_train.rename(columns={"COGS_to_Revenue": "Ratio"}),
        dates=dates,
        target="Ratio",
        level_method=level_method,
    )
    return np.clip(ratio_prediction, RATIO_MIN, RATIO_MAX)


def build_final_submission(sales: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    revenue = (
        predict_seasonal_dow(sales, dates, "Revenue", FINAL_CONFIG["revenue_level_method"])
        * FINAL_CONFIG["revenue_scale"]
    )
    cogs_ratio = predict_ratio(sales, dates, FINAL_CONFIG["ratio_level_method"])
    cogs = revenue * cogs_ratio * FINAL_CONFIG["cogs_scale"]

    prediction = pd.DataFrame({"Date": pd.to_datetime(dates), "Revenue": revenue, "COGS": cogs})
    prediction[["Revenue", "COGS"]] = prediction[["Revenue", "COGS"]].round(2)
    return prediction


def build_baseline_submission(train_df: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    prediction = predict_dates(dates, annual, seasonal, growth_rev, growth_cogs, base_year)
    prediction[["Revenue", "COGS"]] = prediction[["Revenue", "COGS"]].round(2)
    return prediction


def metric_row(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {"mae": mae(actual, predicted), "rmse": rmse(actual, predicted), "r2": r2(actual, predicted)}


def evaluate_prediction(
    valid_df: pd.DataFrame,
    prediction: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    return {
        target: metric_row(valid_df[target].to_numpy(), prediction[target].to_numpy())
        for target in ["Revenue", "COGS"]
    }


def evaluate_holdout(sales: pd.DataFrame, holdout_year: int) -> dict[str, dict[str, dict[str, float]]]:
    train_df = sales[sales["Date"].dt.year < holdout_year].copy()
    valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
    dates = valid_df["Date"]

    return {
        "seasonal_growth_baseline": evaluate_prediction(
            valid_df,
            build_baseline_submission(train_df, dates),
        ),
        "final_cv_tuned_submission": evaluate_prediction(
            valid_df,
            build_final_submission(train_df, dates),
        ),
    }


def write_benchmark(
    path: Path,
    results: dict[int, dict[str, dict[str, dict[str, float]]]],
    final_output: Path,
) -> None:
    lines = [
        "# Final Forecast Benchmark",
        "",
        "This benchmark keeps only the final Kaggle submission path used for the cleaned repo.",
        "",
        "Final submission:",
        "",
        f"- Output: `{final_output}`",
        f"- Revenue level: `{FINAL_CONFIG['revenue_level_method']}`",
        f"- Revenue scale: `{FINAL_CONFIG['revenue_scale']}`",
        f"- COGS ratio level: `{FINAL_CONFIG['ratio_level_method']}`",
        f"- COGS scale: `{FINAL_CONFIG['cogs_scale']}`",
        "",
    ]

    for holdout_year, model_results in results.items():
        lines.extend(
            [
                f"## Holdout Year {holdout_year}",
                "",
                "| Model | Target | MAE | RMSE | R2 |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for model_name, target_results in model_results.items():
            for target, metrics in target_results.items():
                lines.append(
                    f"| {model_name} | {target} | {metrics['mae']:.2f} | {metrics['rmse']:.2f} | {metrics['r2']:.4f} |"
                )
        lines.append("")

    lines.extend(
        [
            "## Submission",
            "",
            f"- Submit `{final_output}` or `outputs/submission_best.csv`.",
            "- `outputs/submission_best.csv` is kept as the convenience copy for Kaggle upload.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the final cleaned Kaggle forecasting submission.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "submission_cv_tuned_diag_1122_0878.csv",
    )
    parser.add_argument(
        "--best-output",
        type=Path,
        default=Path("outputs") / "submission_best.csv",
    )
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=Path("outputs") / "forecast_cv_tuned_benchmark.md",
    )
    parser.add_argument("--holdout-years", type=int, nargs="+", default=[2021, 2022])
    parser.add_argument("--no-best-copy", action="store_true")
    args = parser.parse_args()

    sales = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    submission_template = pd.read_csv(args.data_dir / "sample_submission.csv", parse_dates=["Date"])

    output = build_final_submission(sales, submission_template["Date"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False, date_format="%Y-%m-%d")

    if not args.no_best_copy:
        shutil.copyfile(args.output, args.best_output)

    results = {holdout_year: evaluate_holdout(sales, holdout_year) for holdout_year in args.holdout_years}
    write_benchmark(args.benchmark_output, results, args.output)

    print(f"Saved final submission to {args.output}")
    if not args.no_best_copy:
        print(f"Copied final submission to {args.best_output}")
    print(f"Saved final benchmark to {args.benchmark_output}")


if __name__ == "__main__":
    main()
