# File: src/generator.py
import sqlite3
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "newsletter.db")
OUTPUT_FILE = os.path.join(BASE_DIR, "daily_newsletter.md")

def generate_newsletter():
    print("📝 Generating your newsletter...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the top 20 biggest stories (clusters with most articles)
    # This filters out the "noise" and finds the "big news"
    cursor.execute('''
        SELECT title, importance_score, id 
        FROM clusters 
        ORDER BY importance_score DESC 
        LIMIT 20
    ''')
    top_stories = cursor.fetchall()

    # Start writing the Markdown file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Header
        date_str = datetime.now().strftime("%Y-%m-%d")
        f.write(f"# 🤖 AI Newsletter - {date_str}\n")
        f.write(f"**Top Stories form the last 24h**\n\n")
        f.write("---\n\n")

        if not top_stories:
            f.write("No stories found. Try running the fetcher first!\n")
            print("⚠️ No stories found in database.")
            return

        # Loop through stories
        for i, (title, score, cluster_id) in enumerate(top_stories, 1):
            f.write(f"## {i}. {title} \n")
            f.write(f"*(🔥 Trending Score: {score} sources)*\n\n")
            
            # Get the top 3 links for this story
            cursor.execute('''
                SELECT title, link, source_id 
                FROM items 
                WHERE cluster_id = ? 
                LIMIT 3
            ''', (cluster_id,))
            articles = cursor.fetchall()
            
            for art_title, link, source in articles:
                f.write(f"- [{source}] [{art_title}]({link})\n")
            
            f.write("\n")

    conn.close()
    print(f"✅ Newsletter generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_newsletter()