# File: src/fetcher.py
import feedparser
import sqlite3
import yaml
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "newsletter.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "sources.yaml")

def load_config():
    """Load the list of RSS feeds from sources.yaml"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file not found at: {CONFIG_PATH}")
        return {"sources": []}
        
    # FIX: Added encoding="utf-8" to handle emojis properly
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_to_db(articles):
    """Save a list of articles to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    new_count = 0
    for art in articles:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO items (title, link, summary, published_at, source_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (art['title'], art['link'], art['summary'], art['published'], art['source']))
            
            if cursor.rowcount > 0:
                new_count += 1
        except Exception as e:
            print(f"Error saving {art['title']}: {e}")

    conn.commit()
    conn.close()
    return new_count

def fetch_feeds():
    """Main function to fetch and save feeds"""
    config = load_config()
    sources = config.get('sources', [])
    
    if not sources:
        print("⚠️ No sources found in config/sources.yaml")
        return

    all_articles = []
    print(f"🚀 Starting fetch for {len(sources)} sources...")

    for source in sources:
        print(f"   - Fetching: {source['name']}...")
        try:
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                print(f"     ⚠️ No entries found for {source['name']}")
                continue

            for entry in feed.entries:
                title = entry.get('title', 'No Title')
                link = entry.get('link', '')
                summary = entry.get('summary', '') or entry.get('description', '')
                published = entry.get('published', datetime.now().isoformat())

                all_articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published': published,
                    'source': source['name']
                })
        except Exception as e:
            print(f"     ❌ Error fetching {source['name']}: {e}")

    print(f"📥 Downloaded {len(all_articles)} raw articles.")
    
    # Save to DB
    added = save_to_db(all_articles)
    print(f"✅ Saved {added} NEW articles to the database.")

if __name__ == "__main__":
    fetch_feeds()