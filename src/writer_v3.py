import sqlite3
import requests
import json
import os
import re  # <--- NEW: Added for the "Digital Scissor"
from datetime import datetime

# --- CONFIGURATION ---
DB_PATH = "data/news_v3.db"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"
OUTPUT_HTML = "newsletter_v3.html"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query_ollama(prompt):
    """Sends a prompt to the local Ollama instance."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # ZERO temperature for maximum strictness
            "num_predict": 2048
        }
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return ""

def generate_section_content(section_name, items):
    """Generates HTML content for a specific section using the LLM."""
    if not items:
        return "<p>No significant updates today.</p>"
    
    # --- LOGIC STEP 1: DEDUPLICATE ---
    seen_urls = set()
    unique_items = []
    
    for item in items:
        if item['link'] in seen_urls: 
            continue
        seen_urls.add(item['link'])
        unique_items.append(item)
    
    # --- LOGIC STEP 2: THE "TOP 5" HARD SLICE ---
    top_items = unique_items[:5]

    # Prepare data string for the AI
    data_str = ""
    for item in top_items:
        # Truncate & Clean Description
        desc = item['description'][:300].replace("\n", " ").strip()
        data_str += f"SOURCE_ITEM:\n- HEADLINE: {item['title']}\n- TARGET_URL: {item['link']}\n- CONTEXT: {desc}\n\n"

    # --- LOGIC STEP 3: FEW-SHOT PROMPT ---
    example_block = """
    ### EXAMPLE INPUT ###
    SOURCE_ITEM:
    - HEADLINE: New Python Features
    - TARGET_URL: https://python.org/new
    - CONTEXT: Python 3.12 is faster.

    ### EXAMPLE OUTPUT ###
    <li><strong>New Python Features</strong>: Python 3.12 is faster. <a href="https://python.org/new" style="color:#28a745; font-weight:bold;">[View Source]</a></li>
    """

    # Define Styles per section
    if section_name == "Executive Brief":
        style_color = "#0056b3"
    elif section_name == "Builder's Corner":
        style_color = "#28a745"
    elif section_name == "Learning Lab":
        style_color = "#6f42c1"
    else:
        style_color = "#333333"

    prompt = f"""
    You are a strictly automated HTML formatter.
    INSTRUCTIONS:
    1. Convert each SOURCE_ITEM into a single HTML <li> line.
    2. You MUST include the <a href="TARGET_URL"> tag using the exact URL provided.
    3. Format: <li><strong>HEADLINE</strong>: CONTEXT. <a href="TARGET_URL" style="color:{style_color}; font-weight:bold;">[Link]</a></li>
    4. Do not output conversational text. Start directly with the HTML tags.
    
    {example_block}

    ### REAL INPUT DATA (Process these {len(top_items)} items) ###
    {data_str}
    """

    print(f"Generating content for: {section_name} ({len(top_items)} items)...")
    response = query_ollama(prompt)
    
    # --- LOGIC STEP 4: THE DIGITAL SCISSOR (REGEX CLEANING) ---
    # This finds the first occurrence of "<li" and ignores everything before it.
    match = re.search(r"<li", response, re.IGNORECASE)
    if match:
        response = response[match.start():]
    else:
        # Fallback: If no <li> found, it might be an empty response or error
        pass

    return response

def fetch_clustered_news():
    """Fetches raw news items from DB. We fetch 15 to allow for deduplication."""
    conn = get_db_connection()
    
    brief_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%TechCrunch%' OR source LIKE '%Verge%' OR source LIKE '%OpenAI%' ORDER BY published DESC LIMIT 15").fetchall()
    
    builder_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%LocalLLaMA%' OR title LIKE '%GitHub%' ORDER BY published DESC LIMIT 15").fetchall()
    
    learning_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%Arxiv%' OR source LIKE '%YouTube%' ORDER BY published DESC LIMIT 15").fetchall()
    
    conn.close()
    return brief_items, builder_items, learning_items

def build_html(brief_html, builder_html, learning_html):
    """Assembles the final HTML email."""
    date_str = datetime.now().strftime("%B %d, %Y")
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #0056b3; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; border-bottom: 2px solid #28a745; padding-bottom: 5px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 15px; }}
            a {{ text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            
            /* --- FOOTER STYLE (Big Blue) --- */
            .footer {{ 
                margin-top: 50px; 
                text-align: center; 
                border-top: 2px solid #eee; 
                padding-top: 20px;
                color: #0056b3; 
                font-size: 1.5em; 
                font-weight: bold; 
            }}
        </style>
    </head>
    <body>
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="margin-bottom: 5px;">Bapi's AI Builder's Daily</h1>
            <p style="color: #666; margin-top: 0;">{date_str}</p>
        </div>

        <h2>Executive Brief</h2>
        <ul>{brief_html}</ul>

        <h2>Builder's Corner (Repos & Tools)</h2>
        <ul>{builder_html}</ul>

        <h2>Learning Lab (R&D & Videos)</h2>
        <ul>{learning_html}</ul>

        <div class="footer">
            Generated by Bapi's Local AI Pipeline
        </div>
    </body>
    </html>
    """
    return html_template

def main():
    print("Fetching data from DB...")
    brief_raw, builder_raw, learn_raw = fetch_clustered_news()
    
    brief_content = generate_section_content("Executive Brief", brief_raw)
    builder_content = generate_section_content("Builder's Corner", builder_raw)
    learn_content = generate_section_content("Learning Lab", learn_raw)
    
    full_html = build_html(brief_content, builder_content, learn_content)
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"Newsletter generated: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()