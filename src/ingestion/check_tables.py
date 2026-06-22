from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    "sqlite:///database/retail_marketing.db"
)

query = """
SELECT name
FROM sqlite_master
WHERE type='table'
"""

tables = pd.read_sql(query, engine)

print(tables)