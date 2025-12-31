-- src / writer.py

import sqlite3
import ollama
from datetime import datetime
from urllib.parse import urlparse

# Configuration
DB_PATH = "data/newsletter.db"
OUTPUT_FILE = "ai_newsletter.md"
MODEL_NAME = "llama3.1"
TOP_CLUSTERS = 12  # Fetch more stories since we are categorizing them

# Defined Categories
CATEGORIES = {
    "MODELS": "🚀 Models & Architecture",
    "BUSINESS": "💰 Industry & Investments",
    "RESEARCH": "🔬 Research & Papers",
    "TOOLS": "🛠️ Tools & Frameworks",
    "OTHER": "🌐 General AI News"
}

def get_domain_name(url):
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        if '.' in domain: domain = domain.split('.')[0]
        return domain.capitalize()
    except: return "Source"

def get_top_clusters_with_articles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT cluster_id, COUNT(*) as count 
    FROM items WHERE cluster_id != -1 
    GROUP BY cluster_id ORDER BY count DESC LIMIT ?
    """
    cursor.execute(query, (TOP_CLUSTERS,))
    clusters = cursor.fetchall()
    
    results = []
    for cluster_id, count in clusters:
        cursor.execute("SELECT title, summary, link FROM items WHERE cluster_id = ?", (cluster_id,))
        results.append({"cluster_id": cluster_id, "articles": cursor.fetchall()})
    conn.close()
    return results

def generate_summary_and_category(articles):
    context = ""
    links = []
    for title, summary, link in articles:
        context += f"- Title: {title}\n  Summary: {summary}\n"
        links.append(link)
        
    prompt = f"""
    You are an expert AI editor.
    
    Task:
    1. CATEGORIZE this story into EXACTLY ONE of these: [MODELS, BUSINESS, RESEARCH, TOOLS, OTHER].
    2. HEADLINE: Catchy, no emoji.
    3. SUMMARY: 2 short bullet points.
    4. IMPACT: 1 sentence on why it matters.

    Source Articles:
    {context}
    
    Output Format:
    Category: [One of the categories above]
    Headline: [Your Headline]
    Summary:
    - [Bullet 1]
    - [Bullet 2]
    **Impact:** [Impact sentence]
    """

    try:
        response = ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        return content, links
    except Exception as e:
        print(f"Ollama Error: {e}")
        return None, links

def main():
    print(f"🚀 Starting AI Writer (Categorized Edition)...")
    clusters = get_top_clusters_with_articles()
    
    # Bucket for sorting stories
    grouped_stories = {key: [] for key in CATEGORIES.keys()}
    
    for i, story in enumerate(clusters):
        print(f"[{i+1}/{len(clusters)}] Processing & Classifying...")
        llm_output, links = generate_summary_and_category(story['articles'])
        
        if llm_output:
            # 1. Extract Category
            lines = llm_output.split('\n')
            category = "OTHER"
            clean_body = []
            
            for line in lines:
                if line.strip().upper().startswith("CATEGORY:"):
                    # Extract "BUSINESS" from "Category: BUSINESS"
                    raw_cat = line.split(":", 1)[1].strip().upper()
                    # Clean up if LLM adds extra punctuation
                    raw_cat = raw_cat.replace(".", "").replace("*", "")
                    if raw_cat in CATEGORIES:
                        category = raw_cat
                else:
                    clean_body.append(line)
            
            # 2. Format Sources
            seen_domains = set()
            unique_links = []
            for link in links:
                domain = get_domain_name(link)
                if domain not in seen_domains:
                    unique_links.append(f"[{domain}]({link})")
                    seen_domains.add(domain)
            
            final_text = "\n".join(clean_body).replace("Headline:", "###")
            final_text += f"\n**Sources:** {' | '.join(unique_links[:3])}\n"
            
            grouped_stories[category].append(final_text)

    # Generate Markdown with Headers
    markdown_output = f"# 🤖 Daily AI Newsletter\nDate: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for cat_key, story_list in grouped_stories.items():
        if story_list:
            markdown_output += f"## {CATEGORIES[cat_key]}\n\n"
            markdown_output += "---\n".join(story_list)
            markdown_output += "\n\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown_output)
        
    print(f"✅ Categorized Newsletter generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()