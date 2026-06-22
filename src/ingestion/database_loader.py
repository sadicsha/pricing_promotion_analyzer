import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path


DATABASE_PATH = "sqlite:///database/retail_marketing.db"

engine = create_engine(DATABASE_PATH)

DATA_PATH = Path("data/raw")


customers_df = pd.read_csv(
    DATA_PATH / "olist_customers_dataset.csv"
)

orders_df = pd.read_csv(
    DATA_PATH / "olist_orders_dataset.csv"
)

products_df = pd.read_csv(
    DATA_PATH / "olist_products_dataset.csv"
)

order_items_df = pd.read_csv(
    DATA_PATH / "olist_order_items_dataset.csv"
)

payments_df = pd.read_csv(
    DATA_PATH / "olist_order_payments_dataset.csv"
)


customers_df.to_sql(
    "customers",
    engine,
    if_exists="replace",
    index=False
)

orders_df.to_sql(
    "orders",
    engine,
    if_exists="replace",
    index=False
)

products_df.to_sql(
    "products",
    engine,
    if_exists="replace",
    index=False
)

order_items_df.to_sql(
    "order_items",
    engine,
    if_exists="replace",
    index=False
)

payments_df.to_sql(
    "payments",
    engine,
    if_exists="replace",
    index=False
)

print("All tables loaded successfully!")