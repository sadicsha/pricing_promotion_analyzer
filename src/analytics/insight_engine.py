import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

products_df = pd.read_csv(
    RAW_PATH / "olist_products_dataset.csv"
)

translation_df = pd.read_csv(
    RAW_PATH / "product_category_name_translation.csv"
)

merged_df = sales_df.merge(
    products_df[
        ["product_id", "product_category_name"]
    ],
    on="product_id",
    how="left"
)

merged_df = merged_df.merge(
    translation_df,
    on="product_category_name",
    how="left"
)

category_summary = (
    merged_df
    .groupby("product_category_name_english")
    .agg({
        "revenue": "sum",
        "gross_profit": "sum"
    })
    .reset_index()
)

top_revenue = category_summary.loc[
    category_summary["revenue"].idxmax()
]

top_profit = category_summary.loc[
    category_summary["gross_profit"].idxmax()
]

print("\n===== MARKETING INSIGHTS =====\n")

print(
    f"Highest Revenue Category: "
    f"{top_revenue['product_category_name_english']}"
)

print(
    f"Revenue Generated: "
    f"{top_revenue['revenue']:,.2f}"
)

print()

print(
    f"Highest Profit Category: "
    f"{top_profit['product_category_name_english']}"
)

print(
    f"Profit Generated: "
    f"{top_profit['gross_profit']:,.2f}"
)

print("\nRecommendation:")

print(
    f"Increase promotional focus on "
    f"{top_profit['product_category_name_english']} "
    f"because it generates the highest profit."
)