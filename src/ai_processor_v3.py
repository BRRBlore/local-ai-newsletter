import sqlite3
import json
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import os

# --- CONFIGURATION ---
DB_PATH = "data/news_v3.db"
MODEL_NAME = 'all-MiniLM-L6-v2'
SIMILARITY_THRESHOLD = 0.5  # Distance threshold for clustering

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_clusters(conn):
    """Ensures the clusters table exists."""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clusters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  summary TEXT,
                  news_ids TEXT)''')
    conn.commit()

def process_and_cluster():
    print(f"[V3] Loading Embedding Model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)
    
    conn = get_db_connection()
    init_db_clusters(conn) # <--- ADDED THIS LINE TO FIX THE ERROR
    c = conn.cursor()
    
    # 1. Clear previous clusters to keep it fresh for the daily run
    c.execute("DELETE FROM clusters")
    c.execute("UPDATE items SET cluster_id = NULL")
    conn.commit()
    
    # 2. Fetch all unclustered items
    items = c.execute("SELECT id, title, description FROM items").fetchall() # Changed summary -> description
    
    if not items:
        print("No items to process.")
        conn.close()
        return

    print(f"Processing {len(items)} items...")
    
    # 3. Generate Embeddings
    # specific fix: Handle empty descriptions by falling back to title
    texts = [item['title'] + ". " + (item['description'] if item['description'] else "") for item in items]
    embeddings = model.encode(texts)
    
    # 4. Perform Clustering
    # Normalize embeddings for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=SIMILARITY_THRESHOLD,
        metric='euclidean',
        linkage='ward'
    )
    cluster_labels = clustering_model.fit_predict(embeddings)
    
    # 5. Group Items by Cluster
    clusters = {}
    for idx, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(items[idx])
        
    # 6. Save Clusters to DB
    print(f"Found {len(clusters)} clusters.")
    for label, cluster_items in clusters.items():
        # Pick the first item's title as the cluster title for now
        cluster_title = cluster_items[0]['title']
        item_ids = [item['id'] for item in cluster_items]
        
        # Save cluster
        c.execute("INSERT INTO clusters (title, news_ids) VALUES (?, ?)", 
                  (cluster_title, json.dumps(item_ids)))
        cluster_db_id = c.lastrowid
        
        # Update items with cluster_id
        for item_id in item_ids:
            c.execute("UPDATE items SET cluster_id = ? WHERE id = ?", (cluster_db_id, item_id))
            
    conn.commit()
    conn.close()
    print("Clustering complete.")

if __name__ == "__main__":
    process_and_cluster()