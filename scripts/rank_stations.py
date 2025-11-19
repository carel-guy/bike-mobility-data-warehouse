import sqlite3
import pandas as pd
from utils.db import DB_PATH

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query("""
    SELECT station_id, name, free_bikes, timestamp
    FROM station_activity
""", conn)
conn.close()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["station_id", "timestamp"])

df["movement"] = df.groupby("station_id")["free_bikes"].diff().abs()

ranking = (
    df.groupby(["station_id", "name"])["movement"]
    .sum()
    .reset_index()
    .sort_values("movement", ascending=False)
)

print("\n🚴 Top Most Active Stations in Bordeaux:\n")
print(ranking.head(10))
