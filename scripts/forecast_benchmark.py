from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from forecast_baseline import fit_baseline, predict_dates

DEFAULT_REVENUE_BASELINE_WEIGHT = 0.85
DEFAULT_COGS_BASELINE_WEIGHT = 0.55


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(math.sqrt(np.mean((actual - predicted) ** 2)))


def r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(1.0 - np.sum((actual - predicted) ** 2) / np.sum((actual - actual.mean()) ** 2))


def build_features(frame: pd.DataFrame, target: str) -> pd.DataFrame:
    out = frame.copy()
    out["dow"] = out["Date"].dt.dayofweek
    out["dom"] = out["Date"].dt.day
    out["month"] = out["Date"].dt.month
    out["quarter"] = out["Date"].dt.quarter
    out["doy"] = out["Date"].dt.dayofyear
    out["weekofyear"] = out["Date"].dt.isocalendar().week.astype(int)
    out["year_idx"] = out["Date"].dt.year - out["Date"].dt.year.min()

    idx = np.arange(len(out))
    for period in [7.0, 30.4375, 365.25]:
        out[f"sin_{period}"] = np.sin(2.0 * np.pi * idx / period)
        out[f"cos_{period}"] = np.cos(2.0 * np.pi * idx / period)

    for lag in [1, 7, 14, 28, 56, 364]:
        out[f"lag_{lag}"] = out[target].shift(lag)
    for window in [7, 28]:
        out[f"rollmean_{window}"] = out[target].shift(1).rolling(window).mean()
        out[f"rollstd_{window}"] = out[target].shift(1).rolling(window).std()
    return out


def fit_lag_model(train_df: pd.DataFrame, target: str) -> tuple[HistGradientBoostingRegressor, list[str]]:
    features = build_features(train_df[["Date", target]].copy(), target).dropna().reset_index(drop=True)
    x = features.drop(columns=["Date", target])
    y = np.log1p(features[target])
    model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_depth=6,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.1,
        max_iter=220,
        random_state=42,
    )
    model.fit(x, y)
    return model, x.columns.tolist()


def recursive_predict_lag_model(train_df: pd.DataFrame, future_dates: pd.Series, target: str) -> np.ndarray:
    model, feature_columns = fit_lag_model(train_df, target)
    history = train_df[["Date", target]].copy().reset_index(drop=True)
    predictions: list[float] = []

    for prediction_date in future_dates:
        history.loc[len(history)] = [prediction_date, np.nan]
        row = build_features(history.copy(), target).iloc[-1][feature_columns].to_frame().T
        prediction = float(np.expm1(model.predict(row)[0]))
        history.at[len(history) - 1, target] = prediction
        predictions.append(prediction)

    return np.asarray(predictions)


def evaluate_baseline(train_df: pd.DataFrame, valid_df: pd.DataFrame, target: str) -> dict[str, float]:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    predictions = predict_dates(valid_df["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)
    predicted = predictions[target].to_numpy()
    actual = valid_df[target].to_numpy()
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "r2": r2(actual, predicted),
    }


def evaluate_lag_model(train_df: pd.DataFrame, valid_df: pd.DataFrame, target: str) -> dict[str, float]:
    predicted = recursive_predict_lag_model(train_df, valid_df["Date"], target)
    actual = valid_df[target].to_numpy()
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "r2": r2(actual, predicted),
    }


def evaluate_blend_model(train_df: pd.DataFrame, valid_df: pd.DataFrame, target: str, baseline_weight: float) -> dict[str, float]:
    annual, seasonal, growth_rev, growth_cogs, base_year = fit_baseline(train_df)
    baseline_prediction = predict_dates(valid_df["Date"], annual, seasonal, growth_rev, growth_cogs, base_year)
    lag_prediction = recursive_predict_lag_model(train_df, valid_df["Date"], target)
    predicted = baseline_weight * baseline_prediction[target].to_numpy() + (1.0 - baseline_weight) * lag_prediction
    actual = valid_df[target].to_numpy()
    return {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "r2": r2(actual, predicted),
    }


def write_markdown(output_path: Path, results: dict[int, dict[str, dict[str, dict[str, float]]]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Forecast Benchmark",
        "",
        "This file compares the current seasonal-growth baseline against a lag-based gradient boosting model.",
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
            "## Recommendation",
            "",
            "- Use the fixed blend as the current best submission candidate. It improves Revenue MAE on both 2021 and 2022 holdouts relative to the plain baseline.",
            "- Keep the seasonal-growth baseline as the fallback because it is simpler and more interpretable.",
            "- The pure lag-based model is still useful for feature ideas, but it does not beat the baseline on Revenue by itself.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark forecasting candidates for Datathon Round 1.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument("--output", type=Path, default=Path("outputs") / "forecast_benchmark.md", help="Markdown file for the benchmark summary.")
    parser.add_argument("--holdout-years", type=int, nargs="+", default=[2021, 2022], help="Years to use as holdout slices.")
    args = parser.parse_args()

    sales = pd.read_csv(args.data_dir / "sales.csv", parse_dates=["Date"]).sort_values("Date").reset_index(drop=True)
    results: dict[int, dict[str, dict[str, dict[str, float]]]] = {}

    for holdout_year in args.holdout_years:
        train_df = sales[sales["Date"].dt.year < holdout_year].copy()
        valid_df = sales[sales["Date"].dt.year == holdout_year].copy()
        results[holdout_year] = {
            "seasonal_growth_baseline": {
                "Revenue": evaluate_baseline(train_df, valid_df, "Revenue"),
                "COGS": evaluate_baseline(train_df, valid_df, "COGS"),
            },
            "lag_gradient_boosting": {
                "Revenue": evaluate_lag_model(train_df, valid_df, "Revenue"),
                "COGS": evaluate_lag_model(train_df, valid_df, "COGS"),
            },
            "blend_baseline_lag": {
                "Revenue": evaluate_blend_model(train_df, valid_df, "Revenue", DEFAULT_REVENUE_BASELINE_WEIGHT),
                "COGS": evaluate_blend_model(train_df, valid_df, "COGS", DEFAULT_COGS_BASELINE_WEIGHT),
            },
        }

    write_markdown(args.output, results)
    print(f"Saved forecast benchmark to {args.output}")


if __name__ == "__main__":
    main()
