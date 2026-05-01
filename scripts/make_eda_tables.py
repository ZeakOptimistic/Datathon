from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def build_monthly_sales(data_dir: Path) -> pd.DataFrame:
    sales = pd.read_csv(data_dir / "sales.csv", parse_dates=["Date"])
    monthly = (
        sales.assign(month=lambda frame: frame["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)[["Revenue", "COGS"]]
        .sum()
    )
    monthly["GrossProfit"] = monthly["Revenue"] - monthly["COGS"]
    monthly["GrossMargin"] = monthly["GrossProfit"] / monthly["Revenue"]
    return monthly


def build_category_performance(data_dir: Path) -> pd.DataFrame:
    order_items = pd.read_csv(
        data_dir / "order_items.csv",
        usecols=["order_id", "product_id", "quantity", "unit_price", "discount_amount", "promo_id"],
    )
    products = pd.read_csv(data_dir / "products.csv", usecols=["product_id", "category", "segment", "cogs"])
    merged = order_items.merge(products, on="product_id", how="left")
    merged["Revenue"] = merged["quantity"] * merged["unit_price"]
    merged["COGS"] = merged["quantity"] * merged["cogs"]
    merged["GrossProfit"] = merged["Revenue"] - merged["COGS"]
    merged["HasPromo"] = merged["promo_id"].notna().astype(int)
    grouped = (
        merged.groupby(["category", "segment"], as_index=False)
        .agg(
            order_lines=("order_id", "size"),
            distinct_orders=("order_id", "nunique"),
            units=("quantity", "sum"),
            revenue=("Revenue", "sum"),
            cogs=("COGS", "sum"),
            gross_profit=("GrossProfit", "sum"),
            total_discount=("discount_amount", "sum"),
            promo_line_share=("HasPromo", "mean"),
        )
        .sort_values("revenue", ascending=False)
    )
    grouped["gross_margin"] = grouped["gross_profit"] / grouped["revenue"]
    grouped["aov_proxy"] = grouped["revenue"] / grouped["distinct_orders"]
    return grouped


def build_region_performance(data_dir: Path) -> pd.DataFrame:
    orders = pd.read_csv(data_dir / "orders.csv", usecols=["order_id", "zip", "device_type", "order_source"])
    geography = pd.read_csv(data_dir / "geography.csv", usecols=["zip", "region", "city"])
    order_items = pd.read_csv(data_dir / "order_items.csv", usecols=["order_id", "quantity", "unit_price"])
    order_items["Revenue"] = order_items["quantity"] * order_items["unit_price"]
    merged = orders.merge(geography, on="zip", how="left").merge(order_items[["order_id", "Revenue"]], on="order_id", how="left")
    region = (
        merged.groupby("region", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            distinct_orders=("order_id", "nunique"),
            avg_line_revenue=("Revenue", "mean"),
        )
        .sort_values("revenue", ascending=False)
    )
    region["aov_proxy"] = region["revenue"] / region["distinct_orders"]
    return region


def build_return_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    returns = pd.read_csv(
        data_dir / "returns.csv",
        usecols=["order_id", "product_id", "return_reason", "return_quantity", "refund_amount"],
    )
    products = pd.read_csv(data_dir / "products.csv", usecols=["product_id", "category", "size"])
    order_items = pd.read_csv(data_dir / "order_items.csv", usecols=["product_id"])

    merged_returns = returns.merge(products, on="product_id", how="left")
    by_category = (
        merged_returns.groupby("category", as_index=False)
        .agg(
            return_records=("order_id", "size"),
            return_units=("return_quantity", "sum"),
            refund_amount=("refund_amount", "sum"),
        )
        .sort_values("return_records", ascending=False)
    )

    returns_by_size = merged_returns["size"].value_counts()
    order_lines_by_size = order_items.merge(products[["product_id", "size"]], on="product_id", how="left")["size"].value_counts()
    by_size = (
        pd.DataFrame({"return_records": returns_by_size, "order_item_rows": order_lines_by_size})
        .fillna(0)
        .reset_index(names="size")
        .sort_values("size")
    )
    by_size["return_record_rate"] = by_size["return_records"] / by_size["order_item_rows"]

    return by_category, by_size


def build_promo_table(data_dir: Path) -> pd.DataFrame:
    order_items = pd.read_csv(data_dir / "order_items.csv", usecols=["order_id", "promo_id", "quantity", "unit_price", "discount_amount"])
    promotions = pd.read_csv(data_dir / "promotions.csv", usecols=["promo_id", "promo_type", "promo_channel", "stackable_flag", "applicable_category"])
    order_items["Revenue"] = order_items["quantity"] * order_items["unit_price"]
    merged = order_items.merge(promotions, on="promo_id", how="left")
    merged["promo_bucket"] = merged["promo_id"].notna().map({True: "with_promo", False: "without_promo"})
    summary = (
        merged.groupby(["promo_bucket", "promo_type", "promo_channel"], dropna=False, as_index=False)
        .agg(
            order_lines=("order_id", "size"),
            distinct_orders=("order_id", "nunique"),
            revenue=("Revenue", "sum"),
            total_discount=("discount_amount", "sum"),
        )
        .sort_values(["promo_bucket", "revenue"], ascending=[True, False])
    )
    return summary


def build_traffic_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    traffic = pd.read_csv(data_dir / "web_traffic.csv", parse_dates=["date"])
    sales = pd.read_csv(data_dir / "sales.csv", parse_dates=["Date"])

    by_source = (
        traffic.groupby("traffic_source", as_index=False)
        .agg(
            days=("date", "size"),
            sessions=("sessions", "mean"),
            unique_visitors=("unique_visitors", "mean"),
            page_views=("page_views", "mean"),
            bounce_rate=("bounce_rate", "mean"),
            avg_session_duration_sec=("avg_session_duration_sec", "mean"),
        )
        .sort_values("sessions", ascending=False)
    )

    daily_join = traffic.groupby("date", as_index=False)[["sessions", "unique_visitors", "page_views"]].sum().merge(
        sales.rename(columns={"Date": "date"}), on="date", how="inner"
    )
    daily_join["Revenue_per_session"] = daily_join["Revenue"] / daily_join["sessions"]
    return by_source, daily_join


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate starter tables for the Datathon Round 1 EDA section.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "eda", help="Directory for the generated CSV tables.")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir)

    build_monthly_sales(args.data_dir).to_csv(args.output_dir / "monthly_sales.csv", index=False)
    build_category_performance(args.data_dir).to_csv(args.output_dir / "category_performance.csv", index=False)
    build_region_performance(args.data_dir).to_csv(args.output_dir / "region_performance.csv", index=False)
    return_by_category, return_by_size = build_return_tables(args.data_dir)
    return_by_category.to_csv(args.output_dir / "returns_by_category.csv", index=False)
    return_by_size.to_csv(args.output_dir / "return_rate_by_size.csv", index=False)
    build_promo_table(args.data_dir).to_csv(args.output_dir / "promo_summary.csv", index=False)
    traffic_by_source, traffic_sales_daily = build_traffic_tables(args.data_dir)
    traffic_by_source.to_csv(args.output_dir / "traffic_by_source.csv", index=False)
    traffic_sales_daily.to_csv(args.output_dir / "traffic_sales_daily.csv", index=False)

    print(f"Saved starter EDA tables to {args.output_dir}")


if __name__ == "__main__":
    main()
