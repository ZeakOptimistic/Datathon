from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class MCQAnswer:
    question: str
    value: str
    answer: str
    note: str | None = None


def nearest_numeric_option(value: float, options: dict[str, float]) -> str:
    return min(options, key=lambda key: abs(value - options[key]))


def choose_label_option(value: str, options: dict[str, str]) -> str:
    normalized = {option_value.lower(): option_key for option_key, option_value in options.items()}
    return normalized[value.lower()]


def save_markdown(answers: list[MCQAnswer], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Round 1 MCQ Answers",
        "",
        "| Question | Measured value | Selected option | Note |",
        "|---|---:|---|---|",
    ]
    for answer in answers:
        note = answer.note or ""
        lines.append(f"| {answer.question} | {answer.value} | {answer.answer} | {note} |")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def solve_mcq(data_dir: Path) -> list[MCQAnswer]:
    answers: list[MCQAnswer] = []

    orders = pd.read_csv(data_dir / "orders.csv", usecols=["order_id", "customer_id", "order_date", "zip", "order_status", "payment_method"], parse_dates=["order_date"])
    order_items = pd.read_csv(data_dir / "order_items.csv", usecols=["order_id", "product_id", "quantity", "unit_price", "discount_amount", "promo_id"])
    products = pd.read_csv(data_dir / "products.csv", usecols=["product_id", "category", "segment", "size", "price", "cogs"])
    returns = pd.read_csv(data_dir / "returns.csv", usecols=["product_id", "return_reason", "return_quantity", "refund_amount"])
    customers = pd.read_csv(data_dir / "customers.csv", usecols=["customer_id", "age_group"])
    geography = pd.read_csv(data_dir / "geography.csv", usecols=["zip", "region"])
    payments = pd.read_csv(data_dir / "payments.csv", usecols=["order_id", "payment_value", "installments"])
    web_traffic = pd.read_csv(data_dir / "web_traffic.csv", usecols=["traffic_source", "bounce_rate"])

    # Q1
    order_dates = orders[["customer_id", "order_date"]].sort_values(["customer_id", "order_date"])
    customer_order_counts = order_dates.groupby("customer_id").size()
    multi_order_ids = customer_order_counts[customer_order_counts > 1].index
    inter_order_gap_days = (
        order_dates[order_dates["customer_id"].isin(multi_order_ids)]
        .groupby("customer_id")["order_date"]
        .diff()
        .dt.days
        .dropna()
    )
    q1_value = float(inter_order_gap_days.median())
    q1_choice = nearest_numeric_option(q1_value, {"A": 30.0, "B": 90.0, "C": 180.0, "D": 365.0})
    answers.append(MCQAnswer("Q1", f"{q1_value:.0f} days", q1_choice))

    # Q2
    products["margin_ratio"] = (products["price"] - products["cogs"]) / products["price"]
    q2_segment = products.groupby("segment")["margin_ratio"].mean().sort_values(ascending=False).index[0]
    q2_choice = choose_label_option(q2_segment, {"A": "Premium", "B": "Performance", "C": "Activewear", "D": "Standard"})
    answers.append(MCQAnswer("Q2", q2_segment, q2_choice))

    # Q3
    q3_reason = (
        returns.merge(products[["product_id", "category"]], on="product_id", how="left")
        .loc[lambda frame: frame["category"] == "Streetwear", "return_reason"]
        .value_counts()
        .index[0]
    )
    q3_choice = choose_label_option(
        q3_reason,
        {"A": "defective", "B": "wrong_size", "C": "changed_mind", "D": "not_as_described"},
    )
    answers.append(MCQAnswer("Q3", q3_reason, q3_choice))

    # Q4
    q4_source = web_traffic.groupby("traffic_source")["bounce_rate"].mean().sort_values().index[0]
    q4_choice = choose_label_option(
        q4_source,
        {"A": "organic_search", "B": "paid_search", "C": "email_campaign", "D": "social_media"},
    )
    answers.append(MCQAnswer("Q4", q4_source, q4_choice))

    # Q5
    q5_pct = float(order_items["promo_id"].notna().mean() * 100.0)
    q5_choice = nearest_numeric_option(q5_pct, {"A": 12.0, "B": 25.0, "C": 39.0, "D": 54.0})
    answers.append(MCQAnswer("Q5", f"{q5_pct:.2f}%", q5_choice))

    # Q6
    order_count_per_customer = orders.groupby("customer_id").size().rename("order_count")
    age_group_frame = (
        customers[customers["age_group"].notna()]
        .merge(order_count_per_customer, on="customer_id", how="left")
        .fillna({"order_count": 0})
    )
    q6_group = (
        age_group_frame.groupby("age_group")
        .agg(total_orders=("order_count", "sum"), customers=("customer_id", "nunique"))
        .assign(avg_orders_per_customer=lambda frame: frame["total_orders"] / frame["customers"])
        .sort_values("avg_orders_per_customer", ascending=False)
        .index[0]
    )
    q6_choice = choose_label_option(q6_group, {"A": "55+", "B": "25-34", "C": "35-44", "D": "45-54"})
    answers.append(MCQAnswer("Q6", q6_group, q6_choice))

    # Q7
    order_items["line_revenue"] = order_items["quantity"] * order_items["unit_price"]
    region_revenue_lines = (
        orders[["order_id", "zip"]]
        .merge(geography, on="zip", how="left")
        .merge(order_items[["order_id", "line_revenue"]], on="order_id", how="left")
        .groupby("region")["line_revenue"]
        .sum()
        .sort_values(ascending=False)
    )
    region_revenue_payments = (
        orders[["order_id", "zip"]]
        .merge(geography, on="zip", how="left")
        .merge(payments, on="order_id", how="left")
        .groupby("region")["payment_value"]
        .sum()
        .sort_values(ascending=False)
    )
    q7_region = region_revenue_lines.index[0]
    q7_choice = choose_label_option(q7_region, {"A": "West", "B": "Central", "C": "East"})
    q7_note = "sales.csv has no region, so this uses transaction revenue by shipping zip; payment-based aggregation gives the same top region."
    if region_revenue_payments.index[0] != q7_region:
        q7_note = "Top region depends on revenue definition. Review the dataset schema mismatch in the question."
    answers.append(MCQAnswer("Q7", q7_region, q7_choice, q7_note))

    # Q8
    q8_method = orders.loc[orders["order_status"] == "cancelled", "payment_method"].value_counts().index[0]
    q8_choice = choose_label_option(
        q8_method,
        {"A": "credit_card", "B": "cod", "C": "paypal", "D": "bank_transfer"},
    )
    answers.append(MCQAnswer("Q8", q8_method, q8_choice))

    # Q9
    returns_by_size = returns.merge(products[["product_id", "size"]], on="product_id", how="left")["size"].value_counts()
    order_item_rows_by_size = order_items.merge(products[["product_id", "size"]], on="product_id", how="left")["size"].value_counts()
    q9_rate = (returns_by_size / order_item_rows_by_size).reindex(["S", "M", "L", "XL"])
    q9_size = q9_rate.sort_values(ascending=False).index[0]
    q9_choice = choose_label_option(q9_size, {"A": "S", "B": "M", "C": "L", "D": "XL"})
    answers.append(MCQAnswer("Q9", f"{q9_size} ({q9_rate[q9_size]:.4%})", q9_choice))

    # Q10
    q10_installments = int(payments.groupby("installments")["payment_value"].mean().sort_values(ascending=False).index[0])
    q10_choice = choose_label_option(str(q10_installments), {"A": "1", "B": "3", "C": "6", "D": "12"})
    answers.append(MCQAnswer("Q10", f"{q10_installments} installments", q10_choice))

    return answers


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve the Datathon Round 1 MCQ section from the provided CSV files.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument("--output", type=Path, default=Path("outputs") / "mcq_answers.md", help="Markdown file to save the answers.")
    args = parser.parse_args()

    answers = solve_mcq(args.data_dir)
    save_markdown(answers, args.output)

    print("Computed MCQ answers:")
    for answer in answers:
        suffix = f" | note: {answer.note}" if answer.note else ""
        print(f"{answer.question}: {answer.answer} | value={answer.value}{suffix}")
    print(f"\nSaved markdown summary to {args.output}")


if __name__ == "__main__":
    main()
