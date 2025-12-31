import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join("data", "news_v3.db")
RETENTION_DAYS = 7

def run_maintenance():
    if not os.path.exists(DB_PATH):
        print(f"[Maintenance] DB not found. Skipping.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=RETENTION_DAYS)).strftime('%Y-%m-%d')

    print(f"[Maintenance] Pruning data older than {cutoff}...")
    try:
        cursor.execute("DELETE FROM items WHERE published_date < ?", (cutoff,))
        del_items = cursor.rowcount
        
        cursor.execute("DELETE FROM clusters WHERE created_at < ?", (cutoff,))
        del_clusters = cursor.rowcount

        conn.commit()
        cursor.execute("VACUUM") # Reclaim disk space
        print(f"[Success] Removed {del_items} items, {del_clusters} clusters.")
    except Exception as e:
        print(f"[Error] {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_maintenance()