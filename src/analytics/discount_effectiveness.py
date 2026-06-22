import pandas as pd
from pathlib import Path

PROCESSED_PATH = Path("data/processed")

sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

campaign_mapping = pd.read_csv(
    PROCESSED_PATH / "campaign_sales_mapping.csv"
)

campaigns_df = pd.read_csv(
    PROCESSED_PATH / "campaigns.csv"
)

# Join campaign info
merged_df = sales_df.merge(
    campaign_mapping,
    on="order_id",
    how="left"
)

merged_df = merged_df.merge(
    campaigns_df[
        [
            "campaign_id",
            "campaign_name",
            "discount_pct"
        ]
    ],
    on="campaign_id",
    how="left"
)

# Discount analysis
discount_summary = (
    merged_df
    .groupby("discount_pct")
    .agg({
        "revenue": "sum",
        "gross_profit": "sum"
    })
    .reset_index()
)

discount_summary["profit_margin_pct"] = (
    discount_summary["gross_profit"]
    /
    discount_summary["revenue"]
) * 100

discount_summary = discount_summary.sort_values(
    by="gross_profit",
    ascending=False
)

print("\n===== DISCOUNT EFFECTIVENESS =====\n")
print(discount_summary)

best_discount = discount_summary.iloc[0]

print("\n===== RECOMMENDATION =====\n")

print(
    f"Recommended Discount: "
    f"{best_discount['discount_pct']}%"
)

print(
    f"This discount generated the highest profit "
    f"of {best_discount['gross_profit']:,.2f}"
)