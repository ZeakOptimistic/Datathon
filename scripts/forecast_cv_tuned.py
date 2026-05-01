from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from forecast_baseline import fit_baseline, predict_dates
from forecast_improved import predict_ratio, predict_seasonal_dow

CONFIGS = {
    "cv_tuned_candidate": {
        "revenue_level_method": "recent_yoy_shrink50",
        "ratio_level_method": "ewm30",
        "revenue_scale": 1.05,
        "cogs_scale": 0.95,
    },
    "cv_recent_2022_candidate": {
        "revenue_level_method": "flat",
        "ratio_level_method": "recent_yoy_shrink50",
        "revenue_scale": 1.08,
        "cogs_scale": 0.95,
    },
}


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(math.sqrt(np.mean((actual - predicted) ** 2)))


def r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = float(np.sum((actual - predicted) ** 2))
    ss_tot = float(np.sum((actual - actual.mean()) ** 2))
    return 1.0 - (ss_res / ss_tot)


def build_config_submission(sales: pd.DataFrame, dates: pd.Series, config: dict[str, float | str]) -> pd.DataFrame:
    revenue = (
        predict_seasonal_dow(sales, dates, "Revenue", str(config["revenue_level_method"]))
        * float(config["revenue_scale"])
    )
    cogs_ratio = predict_ratio(sales, dates, str(config["ratio_level_method"]))
    cogs = revenue * cogs_ratio * float(config["cogs_scale"])
    prediction = pd.DataFrame({"Date": pd.to_datetime(dates), "Revenue": revenue, "COGS": cogs})
    prediction[["Revenue", "COGS"]] = prediction[["Revenue", "COGS"]].round(2)
    return prediction


def build_cv_tuned_submission(sales: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    return build_config_submission(sales, dates, CONFIGS["cv_tuned_candidate"])


def build_known_best_submission(sales: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    revenue = predict_seasonal_dow(sales, dates, "Revenue", "recent_yoy_shrink25")
    cogs_ratio = predict_ratio(sales, dates, "ewm30")
    prediction = pd.DataFrame({"Date": pd.to_datetime(dates), "Revenue": revenue, "COGS": revenue * cogs_ratio})
    prediction[["Revenue", "COGS"]] = prediction[["Revenue", "COGS"]].round(2)
    return prediction


def build_baseline_submission(train_df: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    prediction = predict_dates(dates, annual, seasonal, growth_rev, growth_cogs, base_year)
    prediction[["Revenue", "COGS"]] = prediction[["Revenue", "COGS"]].round(2)
    return prediction


def metric_row(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {"mae": mae(actual, predicted), "rmse": rmse(actual, predicted), "r2": r2(actual, predicted)}


def evaluate_model(
    sales: pd.DataFrame,
    holdout_year: int,
    model_name: str,
    prediction: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
    return {
        target: metric_row(valid_df[target].to_numpy(), prediction[target].to_numpy())
        for target in ["Revenue", "COGS"]
    }


def evaluate_holdout(sales: pd.DataFrame, holdout_year: int) -> dict[str, dict[str, dict[str, float]]]:
    train_df = sales[sales["Date"].dt.year < holdout_year].copy()
    valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
    dates = valid_df["Date"]
    baseline = build_baseline_submission(train_df, dates)
    known_best = build_known_best_submission(train_df, dates)
    cv_tuned = build_config_submission(train_df, dates, CONFIGS["cv_tuned_candidate"])
    cv_recent = build_config_submission(train_df, dates, CONFIGS["cv_recent_2022_candidate"])
    return {
        "seasonal_growth_baseline": evaluate_model(sales, holdout_year, "baseline", baseline),
        "known_best_public_912_config": evaluate_model(sales, holdout_year, "known_best", known_best),
        "cv_tuned_candidate": evaluate_model(sales, holdout_year, "cv_tuned", cv_tuned),
        "cv_recent_2022_candidate": evaluate_model(sales, holdout_year, "cv_recent", cv_recent),
    }


def write_benchmark(path: Path, results: dict[int, dict[str, dict[str, dict[str, float]]]]) -> None:
    lines = [
        "# CV Tuned Forecast Benchmark",
        "",
        "This benchmark uses historical holdout years only. It does not use leaderboard scores.",
        "",
        "Primary candidate config:",
        "",
        f"- Revenue level: `{CONFIGS['cv_tuned_candidate']['revenue_level_method']}`",
        f"- Revenue scale: `{CONFIGS['cv_tuned_candidate']['revenue_scale']}`",
        f"- COGS ratio level: `{CONFIGS['cv_tuned_candidate']['ratio_level_method']}`",
        f"- COGS scale: `{CONFIGS['cv_tuned_candidate']['cogs_scale']}`",
        "",
        "Recent-year alternate config:",
        "",
        f"- Revenue level: `{CONFIGS['cv_recent_2022_candidate']['revenue_level_method']}`",
        f"- Revenue scale: `{CONFIGS['cv_recent_2022_candidate']['revenue_scale']}`",
        f"- COGS ratio level: `{CONFIGS['cv_recent_2022_candidate']['ratio_level_method']}`",
        f"- COGS scale: `{CONFIGS['cv_recent_2022_candidate']['cogs_scale']}`",
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
            "- Submit `outputs/submission_cv_tuned.csv` as the next data-driven trial.",
            "- If it is worse than the public 912 backup, try `outputs/submission_cv_recent_2022.csv` only as a secondary trial.",
            "- Keep `outputs/submission_public_912428.csv` as the known-best fallback.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a CV-tuned data-driven forecasting submission.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"))
    parser.add_argument("--output", type=Path, default=Path("outputs") / "submission_cv_tuned.csv")
    parser.add_argument(
        "--recent-output",
        type=Path,
        default=Path("outputs") / "submission_cv_recent_2022.csv",
    )
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=Path("outputs") / "forecast_cv_tuned_benchmark.md",
    )
    parser.add_argument("--holdout-years", type=int, nargs="+", default=[2021, 2022])
    args = parser.parse_args()

    sales = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    submission_template = pd.read_csv(args.data_dir / "sample_submission.csv", parse_dates=["Date"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = build_config_submission(sales, submission_template["Date"], CONFIGS["cv_tuned_candidate"])
    output.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    recent_output = build_config_submission(sales, submission_template["Date"], CONFIGS["cv_recent_2022_candidate"])
    recent_output.to_csv(args.recent_output, index=False, date_format="%Y-%m-%d")

    results = {holdout_year: evaluate_holdout(sales, holdout_year) for holdout_year in args.holdout_years}
    write_benchmark(args.benchmark_output, results)

    print(f"Saved CV-tuned submission to {args.output}")
    print(f"Saved recent-year alternate submission to {args.recent_output}")
    print(f"Saved CV-tuned benchmark to {args.benchmark_output}")
    for holdout_year, holdout_results in results.items():
        print(f"Holdout {holdout_year}:")
        for target in ["Revenue", "COGS"]:
            known = holdout_results["known_best_public_912_config"][target]
            tuned = holdout_results["cv_tuned_candidate"][target]
            print(
                f"  {target}: known-best RMSE={known['rmse']:.2f}, "
                f"CV-tuned RMSE={tuned['rmse']:.2f}; "
                f"known-best MAE={known['mae']:.2f}, CV-tuned MAE={tuned['mae']:.2f}"
            )


if __name__ == "__main__":
    main()
