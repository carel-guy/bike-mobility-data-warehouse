import os
import requests
from datetime import datetime, timezone
from utils.db import create_table, get_connection
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CITYBIKES_BASE_URL")
NETWORK_ID = os.getenv("NETWORK_ID")

API_URL = f"{BASE_URL}/v2/networks/{NETWORK_ID}"

print(f"⏳ Fetching VCUB station data from {API_URL}...")


def fetch_and_store(return_count=False):
    # Fetch data
    response = requests.get(API_URL)
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        response.raise_for_status()

    stations = response.json()["network"]["stations"]

    conn = get_connection()
    cur = conn.cursor()

    inserted = 0

    for st in stations:
        cur.execute("""
            INSERT INTO station_activity
            (station_id, name, free_bikes, empty_slots, latitude, longitude, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            st["id"],
            st["name"],
            st["free_bikes"],
            st["empty_slots"],
            st["latitude"],
            st["longitude"],
            datetime.now(timezone.utc).isoformat()
        ))
        
        inserted += 1  # count inserted rows

    conn.commit()
    conn.close()

    print(f"✅ Fetched and stored {inserted} stations.")

    if return_count:
        return inserted


if __name__ == "__main__":
    create_table()
    fetch_and_store()
