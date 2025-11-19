import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "activity.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name="bike_logger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate log handlers
    if logger.hasHandlers():
        return logger

    # --- File Handler with Rotation ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5_000_000,   # 5 MB
        backupCount=5         # keep 5 old log files
    )
    file_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # --- Terminal Handler ---
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
