import os
import time
from datetime import datetime
from dotenv import load_dotenv
from scripts.fetch_stations import fetch_and_store
from utils.logging_config import setup_logger

load_dotenv()

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 300))
logger = setup_logger("tracker_logger")

def pretty_time():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


if __name__ == "__main__":
    logger.info(f"VCUB Tracker Started — interval = {POLL_INTERVAL}s")

    while True:
        start_time = time.time()
        logger.info(f"Fetching new snapshot at {pretty_time()}")

        try:
            count = fetch_and_store(return_count=True)
            logger.info(f"Inserted {count} rows")
        except Exception as e:
            logger.error(f"Error fetching data: {e}")

        duration = round(time.time() - start_time, 2)
        logger.info(f"Fetch duration: {duration}s")

        logger.info(f"Sleeping for {POLL_INTERVAL} seconds...\n")
        time.sleep(POLL_INTERVAL)
