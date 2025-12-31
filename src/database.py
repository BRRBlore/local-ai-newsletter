# File: src/database.py
import sqlite3
import os
from datetime import datetime

# Define paths
DB_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_FOLDER, "newsletter.db")

def init_db():
    """Initialize the SQLite database with required tables."""
    # Ensure data folder exists
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Raw Items Table (RSS Feeds)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        title TEXT,
        link TEXT UNIQUE,
        published_at TIMESTAMP,
        summary TEXT,
        content TEXT,
        embedding BLOB,
        cluster_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Clusters Table (Grouped Stories)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_key TEXT,  -- e.g., "2023-10-27"
        title TEXT,
        summary TEXT,
        category TEXT,
        importance_score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. Subscribers Table (Emails)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        is_active BOOLEAN DEFAULT 1,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database ready at: {DB_PATH}")

if __name__ == "__main__":
    init_db()