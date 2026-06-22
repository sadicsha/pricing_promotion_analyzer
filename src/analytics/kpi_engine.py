import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/processed")

# Load feature-engineered data
df = pd.read_csv(
    DATA_PATH / "sales_features.csv"
)

# ------------------------
# KPI 1 - Total Revenue
# ------------------------

total_revenue = df["revenue"].sum()

# ------------------------
# KPI 2 - Total Profit
# ------------------------

total_profit = df["gross_profit"].sum()

# ------------------------
# KPI 3 - Average Margin
# ------------------------

avg_margin = df["profit_margin_pct"].mean()

print("\n===== BUSINESS KPIs =====")

print(
    f"Total Revenue: {total_revenue:,.2f}"
)

print(
    f"Total Profit: {total_profit:,.2f}"
)

print(
    f"Average Margin %: {avg_margin:.2f}"
)
print("\nTop 10 Most Profitable Products")

top_products = (
    df.groupby("product_id")["gross_profit"]
      .sum()
      .sort_values(ascending=False)
      .head(10)
)

print(top_products)