import sqlite3
import os

# Absolute path to /data/bike_data.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "bike_data.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_table():
    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS station_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT,
            name TEXT,
            free_bikes INTEGER,
            empty_slots INTEGER,
            latitude REAL,
            longitude REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Table created successfully at:", DB_PATH)
