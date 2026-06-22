import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load datasets
sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

orders_df = pd.read_csv(
    RAW_PATH / "olist_orders_dataset.csv"
)

customers_df = pd.read_csv(
    PROCESSED_PATH / "customer_segments.csv"
)

# Merge order -> customer
merged_df = sales_df.merge(
    orders_df[
        ["order_id", "customer_id"]
    ],
    on="order_id",
    how="left"
)

# Merge customer segments
merged_df = merged_df.merge(
    customers_df[
        ["customer_id", "customer_segment"]
    ],
    on="customer_id",
    how="left"
)

# Segment summary
segment_summary = (
    merged_df
    .groupby("customer_segment")
    .agg({
        "revenue": "sum",
        "gross_profit": "sum",
        "profit_margin_pct": "mean"
    })
    .round(2)
)

print("\n===== SEGMENT PROFITABILITY =====\n")
print(segment_summary)

# Most profitable segment
best_segment = (
    segment_summary["gross_profit"]
    .idxmax()
)

print("\nRecommendation:")
print(
    f"Focus marketing efforts on "
    f"{best_segment} customers "
    f"because they generate the highest profit."
)