import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load datasets
sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

products_df = pd.read_csv(
    RAW_PATH / "olist_products_dataset.csv"
)

translation_df = pd.read_csv(
    RAW_PATH / "product_category_name_translation.csv"
)

# Merge sales + products
merged_df = sales_df.merge(
    products_df[
        ["product_id", "product_category_name"]
    ],
    on="product_id",
    how="left"
)

# Translate Portuguese categories to English
merged_df = merged_df.merge(
    translation_df,
    on="product_category_name",
    how="left"
)

# Revenue by category
revenue_by_category = (
    merged_df.groupby(
        "product_category_name_english"
    )["revenue"]
    .sum()
    .sort_values(
        ascending=False
    )
    .head(10)
)

print("\nTOP 10 CATEGORIES BY REVENUE\n")
print(revenue_by_category)

# Profit by category
profit_by_category = (
    merged_df.groupby(
        "product_category_name_english"
    )["gross_profit"]
    .sum()
    .sort_values(
        ascending=False
    )
    .head(10)
)

print("\nTOP 10 CATEGORIES BY PROFIT\n")
print(profit_by_category)