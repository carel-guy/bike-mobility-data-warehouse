import sqlite3

DB_PATH = "data/bike_data.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_table():
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

    print("Table created successfully.")