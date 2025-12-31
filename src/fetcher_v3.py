import feedparser
import sqlite3
import os
from datetime import datetime
from time import mktime

# --- CONFIGURATION ---
DB_PATH = "data/news_v3.db"

# A mix of Tech, Dev Tools, and AI Research feeds
RSS_FEEDS = [
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/artificial-intelligence/index.xml"),
    ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
    ("LocalLLaMA Reddit", "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day"),
    ("LangChain Blog", "https://blog.langchain.dev/rss/"),
    ("Arxiv AI (CS.AI)", "http://export.arxiv.org/rss/cs.ai"),
    ("Two Minute Papers", "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg"), # Example YouTube
    ("Andrej Karpathy", "https://www.youtube.com/feeds/videos.xml?channel_id=UCHgNeSOydGs48gyG3nDLkEg")
]

def init_db():
    """Initialize the database with the CORRECT schema including description."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Dropping old table if exists ensures we get the new schema
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  link TEXT,
                  description TEXT,
                  published TEXT,
                  source TEXT,
                  cluster_id INTEGER)''')
    conn.commit()
    return conn

def parse_date(entry):
    """Standardizes date formats."""
    if hasattr(entry, 'published_parsed'):
        dt = datetime.fromtimestamp(mktime(entry.published_parsed))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_feeds():
    conn = init_db()
    c = conn.cursor()
    
    new_count = 0
    
    for source_name, url in RSS_FEEDS:
        print(f"Fetching {source_name}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Limit to top 5 per feed to keep it fast
                title = entry.title
                link = entry.link
                
                # Try to find the best description/summary content
                description = ""
                if hasattr(entry, 'summary'):
                    description = entry.summary
                elif hasattr(entry, 'description'):
                    description = entry.description
                
                published = parse_date(entry)
                
                # Check for duplicates
                c.execute("SELECT id FROM items WHERE link = ?", (link,))
                if c.fetchone() is None:
                    c.execute("INSERT INTO items (title, link, description, published, source) VALUES (?, ?, ?, ?, ?)",
                              (title, link, description, published, source_name))
                    new_count += 1
        except Exception as e:
            print(f"Error fetching {source_name}: {e}")

    conn.commit()
    conn.close()
    print(f"Success. Added {new_count} new items to DB.")

if __name__ == "__main__":
    fetch_feeds()