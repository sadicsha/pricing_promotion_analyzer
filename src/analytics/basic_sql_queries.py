from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    "sqlite:///database/retail_marketing.db"
)

# Query 1
query1 = """
SELECT COUNT(*) AS total_orders
FROM orders
"""
result1 = pd.read_sql(query1, engine)

print("\nTOTAL ORDERS")
print(result1)

# Query 2
query2 = """
SELECT
    ROUND(SUM(payment_value),2) AS total_revenue
FROM payments
"""

result2 = pd.read_sql(query2, engine)

print("\nTOTAwL REVENUE")
print(result2)