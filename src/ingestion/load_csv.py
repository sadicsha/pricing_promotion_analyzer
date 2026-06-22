import pandas as pd
from pathlib import Path


DATA_PATH = Path("data/raw")


def load_dataset(file_name):
    """
    Load a CSV dataset and return a DataFrame.
    """

    file_path = DATA_PATH / file_name

    df = pd.read_csv(file_path)

    print("\n" + "=" * 60)
    print(f"Dataset: {file_name}")
    print("=" * 60)

    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn Names:")
    print(df.columns.tolist())

    print("\nFirst 5 Records:")
    print(df.head())

    return df


if __name__ == "__main__":

    customers_df = load_dataset("olist_customers_dataset.csv")

    orders_df = load_dataset("olist_orders_dataset.csv")

    products_df = load_dataset("olist_products_dataset.csv")

    order_items_df = load_dataset("olist_order_items_dataset.csv")

    payments_df = load_dataset("olist_order_payments_dataset.csv")