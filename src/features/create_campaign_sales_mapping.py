import pandas as pd
import numpy as np
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load orders
orders_df = pd.read_csv(
    RAW_PATH / "olist_orders_dataset.csv"
)

# Load campaigns
campaign_df = pd.read_csv(
    PROCESSED_PATH / "campaigns.csv"
)

np.random.seed(42)

# Assign random campaign to each order
orders_df["campaign_id"] = np.random.choice(
    campaign_df["campaign_id"],
    size=len(orders_df)
)

campaign_mapping = orders_df[
    ["order_id", "campaign_id"]
]

campaign_mapping.to_csv(
    PROCESSED_PATH / "campaign_sales_mapping.csv",
    index=False
)

print("Campaign mapping created successfully!")

print("\nSample Mapping:\n")
print(campaign_mapping.head())