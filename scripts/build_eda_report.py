from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def load_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "sales": pd.read_csv(data_dir / "sales.csv", parse_dates=["Date"]),
        "orders": pd.read_csv(data_dir / "orders.csv", parse_dates=["order_date"]),
        "order_items": pd.read_csv(data_dir / "order_items.csv", low_memory=False),
        "products": pd.read_csv(data_dir / "products.csv"),
        "returns": pd.read_csv(data_dir / "returns.csv", parse_dates=["return_date"]),
        "customers": pd.read_csv(data_dir / "customers.csv", parse_dates=["signup_date"]),
        "geography": pd.read_csv(data_dir / "geography.csv"),
        "inventory": pd.read_csv(data_dir / "inventory.csv", parse_dates=["snapshot_date"]),
        "web_traffic": pd.read_csv(data_dir / "web_traffic.csv", parse_dates=["date"]),
    }


def figure_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": (12, 6),
            "axes.titlesize": 15,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )


def save_monthly_sales_chart(sales: pd.DataFrame, output_dir: Path) -> dict[str, float]:
    monthly = (
        sales.assign(month=sales["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)[["Revenue", "COGS"]]
        .sum()
    )
    monthly["GrossProfit"] = monthly["Revenue"] - monthly["COGS"]
    monthly["GrossMargin"] = monthly["GrossProfit"] / monthly["Revenue"]
    monthly["MonthNumber"] = monthly["month"].dt.month

    avg_month = monthly.groupby("MonthNumber", as_index=False)["Revenue"].mean()
    peak_month_num = int(avg_month.sort_values("Revenue", ascending=False).iloc[0]["MonthNumber"])
    trough_month_num = int(avg_month.sort_values("Revenue", ascending=True).iloc[0]["MonthNumber"])
    peak_month_name = pd.Timestamp(2000, peak_month_num, 1).strftime("%B")
    trough_month_name = pd.Timestamp(2000, trough_month_num, 1).strftime("%B")

    fig, axes = plt.subplots(2, 1, figsize=(13, 9), constrained_layout=True)

    axes[0].plot(monthly["month"], monthly["Revenue"] / 1e6, label="Revenue", linewidth=2.0, color="#1f77b4")
    axes[0].plot(monthly["month"], monthly["COGS"] / 1e6, label="COGS", linewidth=1.8, color="#ff7f0e")
    axes[0].plot(monthly["month"], monthly["GrossProfit"] / 1e6, label="Gross Profit", linewidth=1.8, color="#2ca02c")
    axes[0].set_title("Monthly Revenue, COGS, and Gross Profit")
    axes[0].set_ylabel("VND millions")
    axes[0].legend()

    axes[1].bar(avg_month["MonthNumber"], avg_month["Revenue"] / 1e6, color="#4C78A8")
    axes[1].set_xticks(avg_month["MonthNumber"])
    axes[1].set_xticklabels([pd.Timestamp(2000, int(month), 1).strftime("%b") for month in avg_month["MonthNumber"]])
    axes[1].set_title("Average Revenue by Calendar Month")
    axes[1].set_xlabel("Month")
    axes[1].set_ylabel("Average revenue (VND millions)")

    path = output_dir / "01_monthly_sales_and_seasonality.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "peak_month_num": peak_month_num,
        "trough_month_num": trough_month_num,
        "peak_month_name": peak_month_name,
        "trough_month_name": trough_month_name,
        "peak_month_avg_revenue_m": avg_month["Revenue"].max() / 1e6,
        "trough_month_avg_revenue_m": avg_month["Revenue"].min() / 1e6,
        "latest_gross_margin_pct": monthly.iloc[-12:]["GrossMargin"].mean() * 100.0,
    }


def save_category_chart(order_items: pd.DataFrame, products: pd.DataFrame, output_dir: Path) -> dict[str, str | float]:
    merged = order_items[["order_id", "product_id", "quantity", "unit_price", "discount_amount", "promo_id"]].merge(
        products[["product_id", "category", "segment", "cogs"]], on="product_id", how="left"
    )
    merged["Revenue"] = merged["quantity"] * merged["unit_price"]
    merged["COGS"] = merged["quantity"] * merged["cogs"]
    merged["GrossProfit"] = merged["Revenue"] - merged["COGS"]
    merged["PromoApplied"] = merged["promo_id"].notna()

    category = (
        merged.groupby("category", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            gross_profit=("GrossProfit", "sum"),
            promo_share=("PromoApplied", "mean"),
            distinct_orders=("order_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
    )
    category["gross_margin"] = category["gross_profit"] / category["revenue"]
    category["aov_proxy"] = category["revenue"] / category["distinct_orders"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    axes[0].bar(category["category"], category["revenue"] / 1e9, color="#4C78A8")
    axes[0].set_title("Revenue by Category")
    axes[0].set_ylabel("Revenue (VND billions)")
    axes[0].tick_params(axis="x", rotation=15)

    scatter = axes[1].scatter(
        category["promo_share"] * 100.0,
        category["gross_margin"] * 100.0,
        s=(category["revenue"] / 1e7),
        color="#F58518",
        alpha=0.75,
    )
    for _, row in category.iterrows():
        axes[1].annotate(row["category"], (row["promo_share"] * 100.0, row["gross_margin"] * 100.0), xytext=(6, 4), textcoords="offset points")
    axes[1].set_title("Promo Exposure vs Gross Margin")
    axes[1].set_xlabel("Promo line share (%)")
    axes[1].set_ylabel("Gross margin (%)")

    path = output_dir / "02_category_revenue_margin.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    top_revenue = category.iloc[0]
    top_margin = category.sort_values("gross_margin", ascending=False).iloc[0]
    weakest_margin = category.sort_values("gross_margin", ascending=True).iloc[0]

    return {
        "top_revenue_category": str(top_revenue["category"]),
        "top_revenue_b": float(top_revenue["revenue"] / 1e9),
        "top_margin_category": str(top_margin["category"]),
        "top_margin_pct": float(top_margin["gross_margin"] * 100.0),
        "weakest_margin_category": str(weakest_margin["category"]),
        "weakest_margin_pct": float(weakest_margin["gross_margin"] * 100.0),
    }


def save_return_chart(returns: pd.DataFrame, products: pd.DataFrame, order_items: pd.DataFrame, output_dir: Path) -> dict[str, str | float]:
    merged_returns = returns.merge(products[["product_id", "category", "size"]], on="product_id", how="left")
    by_reason = (
        merged_returns.groupby(["category", "return_reason"], as_index=False)
        .size()
        .rename(columns={"size": "return_records"})
    )
    top_categories = (
        merged_returns["category"].value_counts().head(4).index.tolist()
    )
    plot_reason = by_reason[by_reason["category"].isin(top_categories)].pivot(
        index="category", columns="return_reason", values="return_records"
    ).fillna(0.0)

    returns_by_size = merged_returns["size"].value_counts()
    order_items_by_size = order_items.merge(products[["product_id", "size"]], on="product_id", how="left")["size"].value_counts()
    size_rate = (returns_by_size / order_items_by_size).reindex(["S", "M", "L", "XL"])

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)

    plot_reason.plot(kind="barh", stacked=True, ax=axes[0], colormap="tab20c")
    axes[0].set_title("Return Reasons by Category")
    axes[0].set_xlabel("Return records")
    axes[0].set_ylabel("Category")

    axes[1].bar(size_rate.index, size_rate.values * 100.0, color="#E45756")
    axes[1].set_title("Return Record Rate by Size")
    axes[1].set_ylabel("Return rate (%)")
    axes[1].set_xlabel("Size")

    path = output_dir / "03_returns_by_category_and_size.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    top_reason = (
        merged_returns["return_reason"].value_counts().idxmax()
    )
    top_size = size_rate.sort_values(ascending=False).index[0]

    return {
        "top_reason": str(top_reason),
        "top_reason_share_pct": float(merged_returns["return_reason"].value_counts(normalize=True).max() * 100.0),
        "top_size": str(top_size),
        "top_size_rate_pct": float(size_rate[top_size] * 100.0),
    }


def save_region_customer_chart(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    geography: pd.DataFrame,
    customers: pd.DataFrame,
    output_dir: Path,
) -> dict[str, str | float]:
    items = order_items[["order_id", "quantity", "unit_price"]].copy()
    items["Revenue"] = items["quantity"] * items["unit_price"]
    region = (
        orders[["order_id", "zip"]]
        .merge(geography[["zip", "region"]], on="zip", how="left")
        .merge(items[["order_id", "Revenue"]], on="order_id", how="left")
        .groupby("region", as_index=False)
        .agg(revenue=("Revenue", "sum"), distinct_orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    region["aov_proxy"] = region["revenue"] / region["distinct_orders"]

    order_count = orders.groupby("customer_id").size().rename("orders")
    acquisition = (
        customers[customers["acquisition_channel"].notna()]
        .merge(order_count, on="customer_id", how="left")
        .fillna({"orders": 0})
        .groupby("acquisition_channel", as_index=False)
        .agg(customers=("customer_id", "nunique"), avg_orders=("orders", "mean"))
        .sort_values("avg_orders", ascending=False)
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)

    axes[0].bar(region["region"], region["revenue"] / 1e9, color="#72B7B2")
    axes[0].set_title("Regional Revenue Footprint")
    axes[0].set_ylabel("Revenue (VND billions)")

    bars = axes[1].bar(acquisition["acquisition_channel"], acquisition["avg_orders"], color="#54A24B")
    axes[1].set_title("Average Orders per Customer by Acquisition Channel")
    axes[1].set_ylabel("Avg orders per customer")
    axes[1].tick_params(axis="x", rotation=20)
    for bar, customers_count in zip(bars, acquisition["customers"]):
        axes[1].text(bar.get_x() + bar.get_width() / 2.0, bar.get_height(), f"n={int(customers_count):,}", ha="center", va="bottom", fontsize=9)

    path = output_dir / "04_region_and_acquisition.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    top_region = region.iloc[0]
    top_aov_region = region.sort_values("aov_proxy", ascending=False).iloc[0]
    top_channel = acquisition.iloc[0]

    return {
        "top_region": str(top_region["region"]),
        "top_region_revenue_b": float(top_region["revenue"] / 1e9),
        "top_aov_region": str(top_aov_region["region"]),
        "top_aov_region_value": float(top_aov_region["aov_proxy"]),
        "top_channel": str(top_channel["acquisition_channel"]),
        "top_channel_avg_orders": float(top_channel["avg_orders"]),
    }


def save_traffic_inventory_chart(web_traffic: pd.DataFrame, sales: pd.DataFrame, inventory: pd.DataFrame, output_dir: Path) -> dict[str, float | str]:
    traffic_source = (
        web_traffic.groupby("traffic_source", as_index=False)
        .agg(
            avg_sessions=("sessions", "mean"),
            avg_bounce_rate=("bounce_rate", "mean"),
            avg_duration=("avg_session_duration_sec", "mean"),
        )
        .sort_values("avg_bounce_rate", ascending=True)
    )
    traffic_daily = web_traffic.groupby("date", as_index=False)[["sessions", "unique_visitors", "page_views"]].sum()
    merged_daily = sales.merge(traffic_daily, left_on="Date", right_on="date", how="inner")
    traffic_corr = merged_daily[["Revenue", "sessions", "unique_visitors", "page_views"]].corr().loc["Revenue", "sessions"]

    inventory_category = (
        inventory.groupby("category", as_index=False)
        .agg(
            stockout_rate=("stockout_flag", "mean"),
            overstock_rate=("overstock_flag", "mean"),
            avg_fill_rate=("fill_rate", "mean"),
        )
        .sort_values("stockout_rate", ascending=False)
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)

    sc = axes[0].scatter(
        traffic_source["avg_sessions"],
        traffic_source["avg_bounce_rate"] * 100.0,
        s=traffic_source["avg_duration"] * 1.5,
        color="#B279A2",
        alpha=0.8,
    )
    for _, row in traffic_source.iterrows():
        axes[0].annotate(row["traffic_source"], (row["avg_sessions"], row["avg_bounce_rate"] * 100.0), xytext=(6, 5), textcoords="offset points")
    axes[0].set_title("Traffic Source Quality")
    axes[0].set_xlabel("Average daily sessions")
    axes[0].set_ylabel("Average bounce rate (%)")

    x = range(len(inventory_category))
    width = 0.36
    axes[1].bar([v - width / 2 for v in x], inventory_category["stockout_rate"] * 100.0, width=width, label="Stockout rate", color="#E45756")
    axes[1].bar([v + width / 2 for v in x], inventory_category["overstock_rate"] * 100.0, width=width, label="Overstock rate", color="#4C78A8")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(inventory_category["category"], rotation=15)
    axes[1].set_title("Inventory Risk by Category")
    axes[1].set_ylabel("Flag rate (%)")
    axes[1].legend()

    path = output_dir / "05_traffic_and_inventory.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    best_source = traffic_source.iloc[0]
    worst_inventory = inventory_category.iloc[0]

    return {
        "best_source": str(best_source["traffic_source"]),
        "best_source_bounce_pct": float(best_source["avg_bounce_rate"] * 100.0),
        "traffic_corr": float(traffic_corr),
        "worst_inventory_category": str(worst_inventory["category"]),
        "worst_stockout_pct": float(worst_inventory["stockout_rate"] * 100.0),
        "worst_overstock_pct": float(worst_inventory["overstock_rate"] * 100.0),
    }


def write_report(output_dir: Path, metrics: dict[str, dict[str, str | float]]) -> Path:
    report_path = output_dir / "eda_report.md"

    sales = metrics["sales"]
    category = metrics["category"]
    returns = metrics["returns"]
    region = metrics["region"]
    traffic = metrics["traffic"]

    lines = [
        "# Datathon Round 1 - EDA Report",
        "",
        "This report focuses on business decisions that can improve revenue quality, reduce avoidable returns, and align inventory with demand.",
        "",
        "## 1. Revenue is highly seasonal, with a concentrated peak in late spring to early summer",
        "",
        "![Monthly sales and seasonality](01_monthly_sales_and_seasonality.png)",
        "",
        f"- Average monthly revenue peaks in **{sales['peak_month_name']}** at roughly **{sales['peak_month_avg_revenue_m']:.2f} million VND**, while **{sales['trough_month_name']}** is the weakest month at about **{sales['trough_month_avg_revenue_m']:.2f} million VND**.",
        f"- The trailing 12-month gross margin sits around **{sales['latest_gross_margin_pct']:.2f}%**, which means topline growth still depends on careful discount and cost control.",
        "- Planning implication: inventory, staffing, and marketing should be front-loaded before the April-June peak window.",
        "",
        "## 2. Streetwear is the engine of revenue, but not the engine of margin",
        "",
        "![Category revenue and margin](02_category_revenue_margin.png)",
        "",
        f"- **{category['top_revenue_category']}** is the dominant category with about **{category['top_revenue_b']:.2f} billion VND** in revenue.",
        f"- The strongest gross margin belongs to **{category['top_margin_category']}** at roughly **{category['top_margin_pct']:.2f}%**, while **{category['weakest_margin_category']}** is the weakest at about **{category['weakest_margin_pct']:.2f}%**.",
        "- Promo exposure does not automatically create healthy economics. The portfolio should protect margin in large categories before simply adding more discount volume.",
        "",
        "## 3. Wrong size is the dominant driver of returns across the business",
        "",
        "![Returns by category and size](03_returns_by_category_and_size.png)",
        "",
        f"- The most frequent return reason is **{returns['top_reason']}**, accounting for about **{returns['top_reason_share_pct']:.2f}%** of return records.",
        f"- Size **{returns['top_size']}** has the highest return record rate at roughly **{returns['top_size_rate_pct']:.2f}%**, but all sizes are close enough that the issue looks systemic rather than isolated to one size bucket.",
        "- Action: invest in sizing accuracy first. Better size guides, fit notes, and size recommendation UX should reduce refund leakage faster than product-only interventions.",
        "",
        "## 4. East brings the most revenue, but Central appears to hold stronger order value",
        "",
        "![Region and acquisition](04_region_and_acquisition.png)",
        "",
        f"- **{region['top_region']}** generates the highest total revenue at about **{region['top_region_revenue_b']:.2f} billion VND**.",
        f"- **{region['top_aov_region']}** has the highest average order value proxy at roughly **{region['top_aov_region_value']:.0f} VND per order**.",
        f"- On the customer side, **{region['top_channel']}** brings the highest average orders per customer at around **{region['top_channel_avg_orders']:.2f}**.",
        "- Action: defend East for scale, but use Central-style order composition as a benchmark for upsell and basket-building strategy.",
        "",
        "## 5. The best traffic source is not necessarily the biggest one, and inventory shows chronic imbalance",
        "",
        "![Traffic and inventory](05_traffic_and_inventory.png)",
        "",
        f"- **{traffic['best_source']}** has the lowest average bounce rate at about **{traffic['best_source_bounce_pct']:.3f}%**, which suggests higher visit quality than the rest of the channel mix.",
        f"- Daily sessions and daily revenue are positively related, but only moderately so, with a correlation of about **{traffic['traffic_corr']:.3f}**. Traffic quality matters, not just traffic volume.",
        f"- **{traffic['worst_inventory_category']}** shows the highest stockout flag rate at roughly **{traffic['worst_stockout_pct']:.2f}%**, while overstock remains high at **{traffic['worst_overstock_pct']:.2f}%**.",
        "- Action: inventory policy likely needs refinement. Simultaneously high stockout and overstock rates indicate assortment-level imbalance rather than total inventory shortage alone.",
        "",
        "## Recommended submission framing",
        "",
        "For the presentation deck or notebook, frame the story in four steps:",
        "",
        "1. Revenue is seasonal and concentrated in a predictable peak window.",
        "2. Scale is coming from categories that do not always have the best economics.",
        "3. Returns are heavily driven by fit issues, which are fixable.",
        "4. The company should shift from pure growth to growth quality: better sizing UX, smarter promo control, and region-aware inventory planning.",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a chart pack and markdown report for Datathon Round 1 EDA.")
    parser.add_argument("--data-dir", type=Path, default=Path("dataset"), help="Directory that contains the CSV files.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs") / "eda_report", help="Directory for figures and the markdown report.")
    args = parser.parse_args()

    ensure_output_dir(args.output_dir)
    figure_style()
    data = load_data(args.data_dir)

    metrics = {
        "sales": save_monthly_sales_chart(data["sales"], args.output_dir),
        "category": save_category_chart(data["order_items"], data["products"], args.output_dir),
        "returns": save_return_chart(data["returns"], data["products"], data["order_items"], args.output_dir),
        "region": save_region_customer_chart(data["orders"], data["order_items"], data["geography"], data["customers"], args.output_dir),
        "traffic": save_traffic_inventory_chart(data["web_traffic"], data["sales"], data["inventory"], args.output_dir),
    }
    report_path = write_report(args.output_dir, metrics)

    print(f"Saved EDA report to {report_path}")


if __name__ == "__main__":
    main()
