import pandas as pd
import numpy as np
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load order items
order_items = pd.read_csv(
    RAW_PATH / "olist_order_items_dataset.csv"
)

# Average selling price per product
product_price = (
    order_items
    .groupby("product_id")["price"]
    .mean()
    .reset_index()
)

np.random.seed(42)

# Cost = 50% to 85% of selling price
cost_factor = np.random.uniform(
    0.50,
    0.85,
    len(product_price)
)

product_price["cost_price"] = (
    product_price["price"] * cost_factor
).round(2)

product_cost_df = product_price[
    ["product_id", "cost_price"]
]

product_cost_df.to_csv(
    PROCESSED_PATH / "product_costs.csv",
    index=False
)

# Campaign Data
campaign_df = pd.DataFrame({
    "campaign_id": ["C001","C002","C003","C004","C005"],
    "campaign_name": [
        "New Year Sale",
        "Summer Sale",
        "Festival Sale",
        "Flash Sale",
        "Weekend Bonanza"
    ],
    "channel": [
        "Email",
        "Google Ads",
        "Social Media",
        "Influencer",
        "SMS"
    ],
    "discount_pct": [
        10,
        15,
        20,
        25,
        5
    ],
    "budget": [
        5000,
        8000,
        12000,
        10000,
        3000
    ]
})

campaign_df.to_csv(
    PROCESSED_PATH / "campaigns.csv",
    index=False
)

print("Marketing datasets recreated successfully!")