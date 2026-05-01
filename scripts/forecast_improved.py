from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from forecast_baseline import fit_baseline, predict_dates

DEFAULT_REVENUE_LEVEL_METHOD = "recent_yoy_shrink25"
DEFAULT_RATIO_LEVEL_METHOD = "ewm30"
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
    elif method == "geo_all":
        full_years = values.loc[values.index.min() + 1 :]
        full_yoy = full_years.pct_change().dropna()
        if full_yoy.empty:
            return 1.0
        growth = float((1.0 + full_yoy).prod() ** (1.0 / len(full_yoy)))
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


def predict_improved(
    train_df: pd.DataFrame,
    dates: pd.Series,
    revenue_level_method: str = DEFAULT_REVENUE_LEVEL_METHOD,
    ratio_level_method: str = DEFAULT_RATIO_LEVEL_METHOD,
) -> pd.DataFrame:
    revenue = predict_seasonal_dow(train_df, dates, "Revenue", revenue_level_method)
    cogs_ratio = predict_ratio(train_df, dates, ratio_level_method)

    prediction = pd.DataFrame({"Date": pd.to_datetime(dates)})
    prediction["Revenue"] = revenue
    prediction["COGS"] = revenue * cogs_ratio
    return prediction


def predict_current_baseline(train_df: pd.DataFrame, dates: pd.Series, target: str) -> np.ndarray:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    prediction = predict_dates(dates, annual, seasonal, growth_rev, growth_cogs, base_year)
    return prediction[target].to_numpy()


def metric_row(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "r2": r2(actual, predicted),
    }


def evaluate_holdout(
    sales: pd.DataFrame,
    holdout_year: int,
    revenue_level_method: str,
    ratio_level_method: str,
) -> dict[str, dict[str, dict[str, float]]]:
    train_df = sales[sales["Date"].dt.year < holdout_year].copy()
    valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
    improved = predict_improved(
        train_df,
        valid_df["Date"],
        revenue_level_method=revenue_level_method,
        ratio_level_method=ratio_level_method,
    )

    return {
        "seasonal_growth_baseline": {
            "Revenue": metric_row(
                valid_df["Revenue"].to_numpy(),
                predict_current_baseline(train_df, valid_df["Date"], "Revenue"),
            ),
            "COGS": metric_row(
                valid_df["COGS"].to_numpy(),
                predict_current_baseline(train_df, valid_df["Date"], "COGS"),
            ),
        },
        "improved_seasonal_dow_ratio": {
            "Revenue": metric_row(valid_df["Revenue"].to_numpy(), improved["Revenue"].to_numpy()),
            "COGS": metric_row(valid_df["COGS"].to_numpy(), improved["COGS"].to_numpy()),
        },
    }


def write_benchmark(
    output_path: Path,
    results: dict[int, dict[str, dict[str, dict[str, float]]]],
    revenue_level_method: str,
    ratio_level_method: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Improved Forecast Benchmark",
        "",
        "This benchmark compares the original seasonal-growth baseline with the improved submission candidate.",
        "",
        "Improved model:",
        "",
        f"- Revenue level: `{revenue_level_method}`",
        f"- COGS: predicted as `Revenue * seasonal COGS/Revenue ratio`, ratio level `{ratio_level_method}`",
        "- Calendar signal: month/day seasonality plus weekday residual adjustment",
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
            "## Submission Recommendation",
            "",
            "- Use `outputs/submission_best.csv` for the current known-best Kaggle submission.",
            "- `outputs/submission_public_912428.csv` preserves the same public-score submission as a backup.",
            "- Keep `outputs/submission_baseline.csv` as a conservative fallback because it matches the official sample-style seasonal baseline.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an improved Part 3 forecasting submission.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "submission_improved.csv",
        help="CSV file for the improved submission.",
    )
    parser.add_argument(
        "--best-output",
        type=Path,
        default=Path("outputs") / "submission_best.csv",
        help="Convenience copy of the currently recommended submission.",
    )
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=Path("outputs") / "forecast_improved_benchmark.md",
        help="Markdown file for the improved benchmark summary.",
    )
    parser.add_argument("--revenue-level-method", default=DEFAULT_REVENUE_LEVEL_METHOD)
    parser.add_argument("--ratio-level-method", default=DEFAULT_RATIO_LEVEL_METHOD)
    parser.add_argument("--holdout-years", type=int, nargs="+", default=[2021, 2022])
    parser.add_argument("--no-best-copy", action="store_true", help="Do not copy the improved file to submission_best.csv.")
    args = parser.parse_args()

    sales = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    submission_template = pd.read_csv(args.data_dir / "sample_submission.csv", parse_dates=["Date"])

    output_df = predict_improved(
        sales,
        submission_template["Date"],
        revenue_level_method=args.revenue_level_method,
        ratio_level_method=args.ratio_level_method,
    )
    output_df["Revenue"] = output_df["Revenue"].round(2)
    output_df["COGS"] = output_df["COGS"].round(2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    if not args.no_best_copy:
        shutil.copyfile(args.output, args.best_output)

    results = {
        holdout_year: evaluate_holdout(
            sales,
            holdout_year,
            revenue_level_method=args.revenue_level_method,
            ratio_level_method=args.ratio_level_method,
        )
        for holdout_year in args.holdout_years
    }
    write_benchmark(
        args.benchmark_output,
        results,
        args.revenue_level_method,
        args.ratio_level_method,
    )

    print(f"Saved improved submission to {args.output}")
    if not args.no_best_copy:
        print(f"Copied improved submission to {args.best_output}")
    print(f"Saved improved benchmark to {args.benchmark_output}")
    for holdout_year, holdout_results in results.items():
        print(f"Holdout {holdout_year}:")
        for target in ["Revenue", "COGS"]:
            baseline_metrics = holdout_results["seasonal_growth_baseline"][target]
            improved_metrics = holdout_results["improved_seasonal_dow_ratio"][target]
            print(
                f"  {target}: baseline MAE={baseline_metrics['mae']:.2f}, "
                f"improved MAE={improved_metrics['mae']:.2f}; "
                f"baseline RMSE={baseline_metrics['rmse']:.2f}, improved RMSE={improved_metrics['rmse']:.2f}"
            )


if __name__ == "__main__":
    main()
