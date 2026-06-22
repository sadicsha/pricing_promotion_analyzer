import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load data
order_items = pd.read_csv(
    RAW_PATH / "olist_order_items_dataset.csv"
)

product_costs = pd.read_csv(
    PROCESSED_PATH / "product_costs.csv"
)

# Merge
merged_df = order_items.merge(
    product_costs,
    on="product_id",
    how="left"
)

# Revenue
merged_df["revenue"] = merged_df["price"]

# Gross Profit
merged_df["gross_profit"] = (
    merged_df["revenue"]
    - merged_df["cost_price"]
)

# Margin %
merged_df["profit_margin_pct"] = (
    merged_df["gross_profit"]
    / merged_df["revenue"]
) * 100

# Save
merged_df.to_csv(
    PROCESSED_PATH / "sales_features.csv",
    index=False
)

print("Feature engineering completed!")
print(merged_df.head())

print("\nRevenue Statistics")
print(merged_df["revenue"].describe())

print("\nCost Statistics")
print(merged_df["cost_price"].describe())

print("\nProfit Statistics")
print(merged_df["gross_profit"].describe())