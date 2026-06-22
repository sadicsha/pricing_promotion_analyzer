import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load datasets
sales_df = pd.read_csv(
    PROCESSED_PATH / "sales_features.csv"
)

campaign_mapping = pd.read_csv(
    PROCESSED_PATH / "campaign_sales_mapping.csv"
)

campaigns_df = pd.read_csv(
    PROCESSED_PATH / "campaigns.csv"
)

# Merge sales with campaign mapping
merged_df = sales_df.merge(
    campaign_mapping,
    on="order_id",
    how="left"
)

# Campaign level summary
campaign_performance = (
    merged_df
    .groupby("campaign_id")
    .agg({
        "revenue": "sum",
        "gross_profit": "sum"
    })
    .reset_index()
)

# Add campaign details
campaign_performance = campaign_performance.merge(
    campaigns_df,
    on="campaign_id",
    how="left"
)

# ROI Calculation
campaign_performance["roi_pct"] = (
    (
        campaign_performance["gross_profit"]
        - campaign_performance["budget"]
    )
    /
    campaign_performance["budget"]
) * 100

# Sort by ROI
campaign_performance = campaign_performance.sort_values(
    by="roi_pct",
    ascending=False
)

print("\n===== CAMPAIGN ROI ANALYSIS =====\n")

print(
    campaign_performance[
        [
            "campaign_name",
            "discount_pct",
            "budget",
            "revenue",
            "gross_profit",
            "roi_pct"
        ]
    ]
)

# Best campaign
best_campaign = campaign_performance.iloc[0]

print("\n===== RECOMMENDATION =====\n")

print(
    f"Repeat '{best_campaign['campaign_name']}' "
    f"because it generated the highest ROI "
    f"of {best_campaign['roi_pct']:.2f}%."
)