import sqlite3
import ollama
import os
import math
from datetime import datetime
from urllib.parse import urlparse
import re

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "newsletter.db")
OUTPUT_FILE = os.path.join(BASE_DIR, "ai_newsletter_v2.md")
MODEL_NAME = "llama3.1"
TOP_CLUSTERS = 12 

def clean_response(text):
    """Clean unwanted conversational text."""
    if not text: return ""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        lower_line = line.lower()
        if "here is" in lower_line or "output format" in lower_line or "headline:" in lower_line: continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()

def clean_headline(ai_text, original_title):
    """
    Aggressively strips numbers, quotes, and prefixes to leave JUST the text.
    Example: '1. The Big News' -> 'The Big News'
    """
    if not ai_text: return original_title
    
    # 1. remove bold/italic markers
    clean = ai_text.replace('*', '').replace('"', '').replace("'", "").strip()
    
    # 2. Split into lines and take the first real line
    lines = [L for L in clean.split('\n') if L.strip()]
    if not lines: return original_title
    first_line = lines[0]
    
    # 3. Remove leading numbering (1., #1, 1:, etc) using Regex
    # Matches "1.", "1 ", "#1 ", "Category: "
    first_line = re.sub(r'^[\d#]+\.?\s*', '', first_line)
    first_line = re.sub(r'^Category:\s*', '', first_line, flags=re.IGNORECASE)
    
    if len(first_line) > 150: return original_title
    return first_line.strip()

def force_one_sentence(text):
    """
    Forces text to be exactly one sentence.
    """
    if not text: return ""
    # Split by period, but keep the period.
    sentences = text.split('.')
    if sentences:
        return sentences[0].strip() + "."
    return text

def generate_story(articles, is_top_story=True):
    context = ""
    main_link = articles[0][2] 
    original_title = articles[0][0]
    
    for title, summary, link in articles:
        context += f"- Title: {title}\n  Summary: {summary}\n"

    # MODE 1: DEEP DIVE (Top 5)
    if is_top_story:
        # Body Prompt
        prompt_body = f"""You are an executive editor. Task: Write a deep-dive segment. STRICT RULES: NO EMOJIS. Structure: **WHAT HAPPENED:** [Max 2 bullets] **WHY IT MATTERS:** [Max 1 bullet impact] Input: {context}"""
        
        # Teaser Prompt (We will also Python-truncate this)
        prompt_teaser = f"""Write exactly ONE sentence summary (under 20 words). Input: {context}"""
        
        # Headline Prompt
        prompt_headline = f"Write ONE professional headline (Bloomberg style). No numbering. Input: {context}"
        
        try:
            body_text = clean_response(ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt_body}])['message']['content'])
            
            raw_teaser = clean_response(ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt_teaser}])['message']['content'])
            final_teaser = force_one_sentence(raw_teaser)
            
            raw_head = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt_headline}])['message']['content']
            final_headline = clean_headline(raw_head, original_title)
            
            return final_headline, body_text, final_teaser, main_link
        except: return None, None, None, None

    # MODE 2: QUICK HIT (Rest)
    else:
        prompt = f"""Write a 1-sentence summary. NO BULLETS. Input: {context}"""
        prompt_headline = f"Write ONE short factual headline. No numbering. Input: {context}"
        
        try:
            body_text = clean_response(ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])['message']['content'])
            # For quick hits, the body IS the teaser
            final_teaser = force_one_sentence(body_text)
            
            raw_head = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt_headline}])['message']['content']
            final_headline = clean_headline(raw_head, original_title)
            
            return final_headline, body_text, final_teaser, main_link
        except: return None, None, None, None

def generate_newsletter():
    print(" ✍️  Drafting V2 Report (Fixed Teasers & Numbering)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, importance_score FROM clusters ORDER BY importance_score DESC LIMIT ?', (TOP_CLUSTERS,))
    clusters = cursor.fetchall()
    
    if not clusters:
        conn.close()
        return

    toc_lines = []
    body_blocks = []
    
    top_stories = clusters[:5]
    quick_hits = clusters[5:]

    # PROCESS TOP 5
    body_blocks.append("## 🔥 Deep Dive Analysis\n\n")
    for i, (cluster_id, _, _) in enumerate(top_stories, 1):
        print(f"   - Processing Top Story #{i}")
        cursor.execute('SELECT title, summary, link FROM items WHERE cluster_id = ? LIMIT 5', (cluster_id,))
        articles = cursor.fetchall()
        headline, body, teaser, link = generate_story(articles, is_top_story=True)
        
        if headline and body:
            # EXECUTIVE SUMMARY LIST ITEM
            # This is the "Clickable Highlight" you requested
            toc_lines.append(f"{i}. [{headline}](#story-{i})\n   <span class='toc-teaser'>{teaser}</span>")
            
            # FULL DETAILS
            body_blocks.append(f'<a name="story-{i}"></a>\n### #{i} [{headline}]({link})\n\n{body}\n\n---\n\n')

    # PROCESS QUICK HITS
    if quick_hits:
        body_blocks.append("## ⚡ Quick Hits\n\n")
        for i, (cluster_id, _, _) in enumerate(quick_hits, 6):
            print(f"   - Processing Quick Hit #{i}")
            cursor.execute('SELECT title, summary, link FROM items WHERE cluster_id = ? LIMIT 3', (cluster_id,))
            articles = cursor.fetchall()
            headline, body, teaser, link = generate_story(articles, is_top_story=False)
            
            if headline and body:
                # Add to Executive Summary too
                toc_lines.append(f"{i}. [{headline}](#story-{i})\n   <span class='toc-teaser'>{teaser}</span>")
                
                body_blocks.append(f'<a name="story-{i}"></a>\n### #{i} [{headline}]({link})\n\n> {body}\n\n')

    # ASSEMBLE
    final_md = f"# Bapi's Daily AI Intelligence Brief\n*{datetime.now().strftime('%A, %B %d, %Y')}*\n\n"
    final_md += "## 📋 Executive Summary\n\n"
    for line in toc_lines: final_md += line + "\n\n"
    final_md += "\n---\n\n"
    for block in body_blocks: final_md += block

    # Read time
    word_count = len(final_md.split())
    read_time = math.ceil(word_count / 230) 
    final_md = final_md.replace(f"*{datetime.now().strftime('%A, %B %d, %Y')}*", f"*{datetime.now().strftime('%A, %B %d, %Y')}* | ⏱️ *{read_time} min read*")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f: f.write(final_md)
    conn.close()
    print(f" ✅ V2 Report generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_newsletter()