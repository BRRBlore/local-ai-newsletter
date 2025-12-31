# File: src/ai_processor.py
import sqlite3
import os
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "newsletter.db")

# AI Model (Small & Fast)
MODEL_NAME = "all-MiniLM-L6-v2"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def process_clusters():
    print("⏳ Loading AI Model (this happens once)...")
    # This will download ~80MB the first time
    model = SentenceTransformer(MODEL_NAME)
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch unclustered articles
    print("🔍 Fetching articles from database...")
    cursor.execute("SELECT id, title, summary FROM items WHERE cluster_id IS NULL")
    articles = cursor.fetchall()
    
    if not articles:
        print("✅ No new articles to cluster.")
        conn.close()
        return

    ids = [a[0] for a in articles]
    # Combine title + summary for better context
    texts = [f"{a[1]}. {a[2]}" for a in articles]

    print(f"🧠 Generating embeddings for {len(texts)} articles...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # 2. Clustering (Agglomerative is great for news)
    # distance_threshold=1.5 means "if they are distinct enough, start a new story"
    print("✨ Grouping similar stories...")
    clustering = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=1.5, 
        metric='euclidean', 
        linkage='ward'
    )
    cluster_labels = clustering.fit_predict(embeddings)

    # 3. Save Cluster IDs back to Items table
    print("💾 Saving cluster assignments...")
    updates = []
    for article_id, label in zip(ids, cluster_labels):
        updates.append((int(label), article_id))

    cursor.executemany("UPDATE items SET cluster_id = ? WHERE id = ?", updates)
    
    # 4. Generate Cluster Summaries (The "Stories")
    unique_labels = set(cluster_labels)
    print(f"📊 Found {len(unique_labels)} unique stories from {len(articles)} articles.")
    
    # Clear old clusters for this demo (optional)
    # cursor.execute("DELETE FROM clusters") 

    for label in unique_labels:
        # Get all articles in this cluster
        indices = [i for i, x in enumerate(cluster_labels) if x == label]
        cluster_articles = [articles[i] for i in indices]
        
        # Pick the most representative title (simply the first one for now)
        main_title = cluster_articles[0][1] 
        day_key = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute('''
            INSERT INTO clusters (day_key, title, importance_score)
            VALUES (?, ?, ?)
        ''', (day_key, main_title, len(cluster_articles)))

    conn.commit()
    conn.close()
    print("✅ Clustering Complete!")

if __name__ == "__main__":
    process_clusters()