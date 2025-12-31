import sqlite3
import os

# New DB Name for V3
DB_NAME = "news_v3.db"
DB_PATH = os.path.join("data", DB_NAME)

def init_db():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables with the new 'category' column
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            published_date TEXT,
            source TEXT,
            category TEXT,  -- New Column for V3 (News, Builder, Learning)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # We also update the clusters table to track category
    c.execute('''
        CREATE TABLE IF NOT EXISTS clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id TEXT,
            cluster_id INTEGER,
            title TEXT,
            summary TEXT,
            urls TEXT,
            category TEXT, -- New Column
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[V3] Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()