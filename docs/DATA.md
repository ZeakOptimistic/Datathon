# Data Setup

Raw competition files are expected under `dataset/` and are included in this workspace so the scripts can be rerun directly after cloning.

Expected CSV files:

```text
customers.csv
geography.csv
inventory.csv
order_items.csv
orders.csv
payments.csv
products.csv
promotions.csv
returns.csv
reviews.csv
sales.csv
sample_submission.csv
shipments.csv
web_traffic.csv
```

Validation command:

```bash
python3 - <<'PY'
from pathlib import Path

required = {
    "customers.csv",
    "geography.csv",
    "inventory.csv",
    "order_items.csv",
    "orders.csv",
    "payments.csv",
    "products.csv",
    "promotions.csv",
    "returns.csv",
    "reviews.csv",
    "sales.csv",
    "sample_submission.csv",
    "shipments.csv",
    "web_traffic.csv",
}

found = {p.name for p in Path("dataset").glob("*.csv")}
missing = sorted(required - found)

if missing:
    print("Missing files:")
    for name in missing:
        print(f"- {name}")
    raise SystemExit(1)

print("All expected dataset files are present.")
PY
```

The generated outputs are also small enough to keep in git for review. Regenerate them with the commands in `README.md` or `ROUND1_CODE_GUIDE.md`.
