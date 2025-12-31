import sqlite3
import requests
import json
import os
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
            "temperature": 0.3 # Low temp = more obedient/consistent
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
    
    # Prepare the data for the prompt
    data_str = ""
    for item in items:
        data_str += f"- Title: {item['title']}\n  Link: {item['link']}\n  Summary: {item['description']}\n\n"

    # --- PROMPT ENGINEERING (V3.3 STRICT MODE) ---
    if section_name == "Executive Brief":
        prompt = f"""
        You are a strict HTML formatter. Summarize these top AI news stories into a list.
        
        STRICT OUTPUT RULES:
        1. Return ONLY valid HTML <li> tags.
        2. NO introductory text (e.g., "Here is the list"). NO markdown (e.g., **bold**).
        3. Format: <li><strong>Title</strong>: One sentence summary. <a href="LINK_URL" style="text-decoration:none; color:#0056b3;">Read more</a></li>
        4. Focus on Major LLM releases, Strategy, or Policy.

        News Items:
        {data_str}
        """
    elif section_name == "Builder's Corner":
        # THIS WAS THE PROBLEM AREA. INCREASED STRICTNESS.
        prompt = f"""
        You are a strict HTML formatting engine. Convert these tools/repos into a bulleted HTML list.
        
        CRITICAL RULES (DO NOT BREAK):
        1. Output ONLY HTML <li> tags. 
        2. DO NOT START with "Here are..." or "Sure!". START DIRECTLY with <li>.
        3. DO NOT use Markdown. Use <strong> for bolding.
        4. Format: <li><strong>Title</strong>: Technical description. <a href="LINK_URL" style="text-decoration:none; color:#28a745; font-weight:bold;">View Repo</a></li>
        5. Filter for the top 5 most useful tools for developers.

        Input Data:
        {data_str}
        """
    elif section_name == "Learning Lab":
        prompt = f"""
        You are a strict HTML formatter. Curate the top 5 'Must Watch/Read' items.
        
        STRICT OUTPUT RULES:
        1. Return ONLY valid HTML <li> tags. NO conversational filler.
        2. Format: <li><strong>[Type] Title</strong>: Description. <a href="LINK_URL" style="text-decoration:none; color:#6f42c1; font-weight:bold;">View Source</a></li>
        3. 'Type' should be [Paper], [Video], or [Guide].

        Research/Videos:
        {data_str}
        """
    else:
        return "<p>Content generation error.</p>"

    print(f"Generating content for: {section_name}...")
    response = query_ollama(prompt)
    
    # POST-PROCESSING SAFETY NET
    # If the LLM still chats, we strip everything before the first <li>
    if "<li>" in response:
        response = response[response.find("<li>"):]
    if "</li>" in response:
        response = response[:response.rfind("</li>")+5]
        
    return response

def fetch_clustered_news():
    conn = get_db_connection()
    
    # 1. Executive Brief
    brief_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%TechCrunch%' OR source LIKE '%Verge%' OR source LIKE '%OpenAI%' ORDER BY published DESC LIMIT 8").fetchall()
    
    # 2. Builder's Corner
    builder_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%LocalLLaMA%' OR title LIKE '%GitHub%' ORDER BY published DESC LIMIT 10").fetchall()
    
    # 3. Learning Lab
    learning_items = conn.execute("SELECT title, link, description FROM items WHERE source LIKE '%Arxiv%' OR source LIKE '%YouTube%' ORDER BY published DESC LIMIT 8").fetchall()
    
    conn.close()
    return brief_items, builder_items, learning_items

def build_html(brief_html, builder_html, learning_html):
    date_str = datetime.now().strftime("%B %d, %Y")
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #0056b3; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; border-bottom: 2px solid #28a745; padding-bottom: 5px; display: inline-block; }}
            h2.brief {{ border-color: #0056b3; }}
            h2.builder {{ border-color: #28a745; }}
            h2.learn {{ border-color: #6f42c1; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 15px; }}
            .footer {{ margin-top: 50px; font-size: 0.8em; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="margin-bottom: 5px;">Bapi's AI Builder's Daily</h1>
            <p style="color: #666; margin-top: 0;">{date_str} | News, Tools, and Skills for the Modern AI Practitioner</p>
        </div>

        <h2 class="brief">Executive Brief</h2>
        <p><em>Top AI news headlines, prioritizing Major LLM releases, Strategy, or Policy:</em></p>
        <ul>
            {brief_html}
        </ul>

        <h2 class="builder">Builder's Corner (Repos & Tools)</h2>
        <p><em>Top-picked GitHub repositories and tools for building AI Agents & Local LLMs:</em></p>
        <ul>
            {builder_html}
        </ul>

        <h2 class="learn">Learning Lab (R&D & Videos)</h2>
        <p><em>Must Watch/Read items for an advanced engineer:</em></p>
        <ul>
            {learning_html}
        </ul>

        <div class="footer">
            Generated by Bapi's Local AI Pipeline (V3.3)
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