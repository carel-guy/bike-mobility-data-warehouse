import sqlite3
import pandas as pd
from utils.db import DB_PATH

# 1. Load Data
conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query("""
    SELECT station_id, name, free_bikes, timestamp
    FROM station_activity
    ORDER BY station_id, timestamp
""", conn)

conn.close()

# 2. Clean and Convert Timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# 3. Remove any corrupted rows (rare, but safe)
df = df.dropna(subset=["timestamp"])

# 4. Compute movement
df["movement"] = (
    df.groupby("station_id")["free_bikes"]
      .diff()
      .fillna(0)
      .abs()
)

# 5. Ranking
ranking = (
    df.groupby(["station_id", "name"])["movement"]
      .sum()
      .reset_index()
      .sort_values("movement", ascending=False)
)

# 6. Display Results
print("\n🚴 Top 10 Most Active Stations in Bordeaux:\n")
print(ranking.head(10).to_string(index=False))

print("\n📊 Total Stations Tracked:", ranking.shape[0])
print("📅 Total Rows in Database:", df.shape[0])
