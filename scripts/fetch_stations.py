import os
import requests
from datetime import datetime, timezone
from utils.db import create_table, get_connection
from utils.logging_config import setup_logger
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CITYBIKES_BASE_URL")
NETWORK_ID = os.getenv("NETWORK_ID")

API_URL = f"{BASE_URL}/v2/networks/{NETWORK_ID}"

logger = setup_logger("fetch_logger")

logger.info(f"Fetching VCUB station data from {API_URL}...")


def fetch_and_store(return_count=False):
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"API Request failed: {e}")
        raise

    stations = response.json()["network"]["stations"]
    logger.info(f"API returned {len(stations)} stations")

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
        inserted += 1

    conn.commit()
    conn.close()

    logger.info(f"Inserted {inserted} rows into SQLite")

    if return_count:
        return inserted


if __name__ == "__main__":
    create_table()
    fetch_and_store()
