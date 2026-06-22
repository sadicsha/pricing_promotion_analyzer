import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load data
sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

products_df = pd.read_csv(
    RAW_PATH / "olist_products_dataset.csv"
)

translation_df = pd.read_csv(
    RAW_PATH / "product_category_name_translation.csv"
)

# Merge category information
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

# Category summary
category_summary = (
    merged_df.groupby(
        "product_category_name_english"
    )
    .agg({
        "revenue": "sum",
        "gross_profit": "sum",
        "profit_margin_pct": "mean"
    })
    .reset_index()
)

# Benchmarks
avg_revenue = category_summary["revenue"].mean()
avg_profit = category_summary["gross_profit"].mean()

recommendations = []

for _, row in category_summary.iterrows():

    category = row["product_category_name_english"]

    revenue = row["revenue"]

    profit = row["gross_profit"]

    margin = row["profit_margin_pct"]

    if revenue > avg_revenue and profit > avg_profit:

        recommendation = (
            "Increase promotion budget"
        )

    elif revenue > avg_revenue and profit < avg_profit:

        recommendation = (
            "Reduce discounts and improve margins"
        )

    elif revenue < avg_revenue and profit < avg_profit:

        recommendation = (
            "Review category strategy"
        )

    else:

        recommendation = (
            "Test targeted promotions"
        )

    recommendations.append(
        [
            category,
            revenue,
            profit,
            margin,
            recommendation
        ]
    )

recommendation_df = pd.DataFrame(
    recommendations,
    columns=[
        "category",
        "revenue",
        "profit",
        "margin_pct",
        "recommendation"
    ]
)

recommendation_df = recommendation_df.sort_values(
    by="profit",
    ascending=False
)

print("\n===== PROMOTION RECOMMENDATIONS =====\n")

print(
    recommendation_df[
        [
            "category",
            "profit",
            "recommendation"
        ]
    ]
    .head(15)
)