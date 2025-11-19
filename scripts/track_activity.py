import os
import time
from datetime import datetime
from dotenv import load_dotenv
from scripts.fetch_stations import fetch_and_store

load_dotenv()

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))

def pretty_time():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

if __name__ == "__main__":
    print(f"🚀 VCUB Activity Tracker Started — interval = {POLL_INTERVAL}s")
    print(f"⏱ Start Time: {pretty_time()}\n")

    while True:
        start = time.time()
        print(f"🔄 Fetching at {pretty_time()}...")

        try:
            inserted_count = fetch_and_store(return_count=True)
            # fetch_and_store should return number of stations inserted
            print(f"   ✅ Inserted {inserted_count} station rows.")
        except Exception as e:
            print(f"❌ Error during fetch: {e}")

        duration = round(time.time() - start, 2)
        print(f"⏲️ Fetch duration: {duration}s")

        if duration > 5:
            print("⚠️ Warning: API response took longer than usual.")

        print(f"😴 Sleeping for {POLL_INTERVAL} seconds...\n")
        time.sleep(POLL_INTERVAL)

