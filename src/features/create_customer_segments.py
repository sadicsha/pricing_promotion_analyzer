import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load data
sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
orders_df = pd.read_csv(RAW_PATH / "olist_orders_dataset.csv")
customers_df = pd.read_csv(RAW_PATH / "olist_customers_dataset.csv")

# Merge sales with orders to get customer_id
merged = sales_df.merge(orders_df[["order_id", "customer_id"]], on="order_id", how="inner")

# Group by customer_id to find average item spend
cust_stats = merged.groupby("customer_id").agg(
    avg_spend=("revenue", "mean")
).reset_index()

# Merge stats into customers dataset
customers_df = customers_df.merge(cust_stats, on="customer_id", how="left")
customers_df["avg_spend"] = customers_df["avg_spend"].fillna(0)

# Segment based on actual average spend thresholds:
# - Big Spenders (Premium): avg_spend >= 170 (High ticket shoppers)
# - Frequent Shoppers (High Value): avg_spend >= 100 and < 170 (Mid-high ticket)
# - Normal Shoppers (Regular): avg_spend >= 50 and < 100 (Mid-low ticket)
# - Rare Shoppers (Occasional): avg_spend < 50 (Low ticket)
def assign_segment(row):
    avg = row["avg_spend"]
    if avg >= 170:
        return "Premium"
    elif avg >= 100:
        return "High Value"
    elif avg >= 50:
        return "Regular"
    else:
        return "Occasional"

customers_df["customer_segment"] = customers_df.apply(assign_segment, axis=1)

# Keep original columns + segment
output_df = customers_df[["customer_id", "customer_unique_id", "customer_segment"]]

# Save
output_df.to_csv(PROCESSED_PATH / "customer_segments.csv", index=False)

print("Behavior-based customer segmentation completed!")
print(output_df["customer_segment"].value_counts())