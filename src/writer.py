import sqlite3
import ollama
import os
import math
from datetime import datetime
from urllib.parse import urlparse

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "newsletter.db")
OUTPUT_FILE = os.path.join(BASE_DIR, "ai_newsletter.md")

# Model Settings
MODEL_NAME = "llama3.1"
TOP_CLUSTERS = 12 

def get_domain_name(url):
    """Extracts a clean source name from a URL."""
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        if '.' in domain:
            domain = domain.split('.')[0]
        return domain.capitalize()
    except:
        return "Source"

def clean_response(text):
    """Removes conversational filler and pure cleans the text."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        lower_line = line.lower()
        if "here is" in lower_line or "output format" in lower_line or "headline:" in lower_line:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def clean_headline(ai_text, original_title):
    """
    Sanitizes the headline. 
    If AI returns a list or garbage, falls back to original_title.
    """
    if not ai_text:
        return original_title
        
    # 1. Strip quotes
    clean = ai_text.replace('"', '').replace("'", "").replace("*", "").strip()
    
    # 2. Check if it's a list (e.g., "1. Headline") and take the first one
    lines = clean.split('\n')
    first_line = lines[0]
    
    # Remove numbering like "1. " or "#1"
    if first_line[0].isdigit() or first_line.startswith("#"):
        parts = first_line.split(' ', 1)
        if len(parts) > 1:
            first_line = parts[1]

    # 3. SAFETY CHECK: If headline is absurdly long (> 150 chars), 
    # the AI probably hallucinated a list. Use original title instead.
    if len(first_line) > 150:
        return original_title

    return first_line

def generate_story(articles, is_top_story=True):
    """Generates the text for a single story with dual modes."""
    context = ""
    # Main link for the headline
    main_link = articles[0][2] 
    original_title = articles[0][0]
    
    for title, summary, link in articles:
        context += f"- Title: {title}\n  Summary: {summary}\n"

    # MODE 1: DEEP DIVE (For Top 5)
    if is_top_story:
        prompt = f"""
        You are an executive intelligence editor.
        Task: Write a deep-dive news segment.
        
        STRICT RULES:
        1. NO EMOJIS.
        2. Output ONLY the body content. Do NOT output a headline.
        3. Structure:
           **WHAT HAPPENED:** [Max 2 concise bullets]
           **WHY IT MATTERS:** [Max 1 bullet on business impact]
        
        Input Data:
        {context}
        """
        headline_prompt = f"Write exactly ONE professional headline (Bloomberg style) for this story. Do not list options. Output ONLY the text. Input: {context}"
    
    # MODE 2: QUICK HIT (For the rest)
    else:
        prompt = f"""
        You are an executive intelligence editor.
        Task: Write a 1-sentence summary.
        
        STRICT RULES:
        1. NO EMOJIS.
        2. NO BULLET POINTS.
        3. Output ONLY the 1-sentence summary.
        
        Input Data:
        {context}
        """
        headline_prompt = f"Write exactly ONE short factual headline (5-8 words). Do not list options. Output ONLY the text. Input: {context}"

    try:
        # Generate Body
        body_resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        body_text = clean_response(body_resp['message']['content'])
        
        # Generate Headline
        head_resp = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': headline_prompt}])
        raw_headline = head_resp['message']['content']
        
        # USE THE NEW CLEANER
        final_headline = clean_headline(raw_headline, original_title)
        
        return final_headline, body_text, main_link
    except Exception as e:
        print(f" ❌ Error talking to Ollama: {e}")
        return None, None, None

def generate_newsletter():
    print(" ✍️  Analyst is drafting the report...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get Top Clusters
    cursor.execute('''
        SELECT id, title, importance_score 
        FROM clusters 
        ORDER BY importance_score DESC 
        LIMIT ?
    ''', (TOP_CLUSTERS,))
    
    clusters = cursor.fetchall()
    
    if not clusters:
        print(" ⚠️  No data found.")
        conn.close()
        return

    content_blocks = []
    
    # Split into Top 5 and Rest
    top_stories = clusters[:5]
    quick_hits = clusters[5:]

    # --- PROCESS TOP 5 (DEEP DIVES) ---
    content_blocks.append("## 🔥 Top 5 Signals\n\n")
    
    for i, (cluster_id, _, _) in enumerate(top_stories, 1):
        print(f"   - Processing Top Story #{i}")
        cursor.execute('SELECT title, summary, link FROM items WHERE cluster_id = ? LIMIT 5', (cluster_id,))
        articles = cursor.fetchall()
        
        headline, body, link = generate_story(articles, is_top_story=True)
        
        if headline and body:
            # Format: ### #1 [Headline](Link)
            # Added extra newlines to prevent bleeding
            full_block = f"### #{i} [{headline}]({link})\n\n{body}\n\n---\n\n"
            content_blocks.append(full_block)

    # --- PROCESS QUICK HITS (BRIEFS) ---
    if quick_hits:
        content_blocks.append("## ⚡ Quick Hits\n\n")
        
        for i, (cluster_id, _, _) in enumerate(quick_hits, 6):
            print(f"   - Processing Quick Hit #{i}")
            cursor.execute('SELECT title, summary, link FROM items WHERE cluster_id = ? LIMIT 3', (cluster_id,))
            articles = cursor.fetchall()
            
            headline, body, link = generate_story(articles, is_top_story=False)
            
            if headline and body:
                # Format: ### #6 [Headline](Link)
                # Quick hits get a quote block
                full_block = f"### #{i} [{headline}]({link})\n\n> {body}\n\n"
                content_blocks.append(full_block)

    # Calculate Reading Time
    full_text_str = "".join(content_blocks)
    word_count = len(full_text_str.split())
    read_time = math.ceil(word_count / 230) 
    
    # Write File
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Bapi's Daily AI Intelligence Brief\n")
        f.write(f"*{datetime.now().strftime('%A, %B %d, %Y')}* | ⏱️ *{read_time} min read*\n\n")
        f.write("Your daily signal on what’s moving the AI world — curated & ranked.\n\n")
        f.write("---\n\n")
        for block in content_blocks:
            f.write(block)
    
    conn.close()
    print(f" ✅ Report generated: {OUTPUT_FILE} ({read_time} min read)")

if __name__ == "__main__":
    generate_newsletter()