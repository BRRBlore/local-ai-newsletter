import os

def create_structure():
    # 1. Define Directories
    folders = [
        "config",
        "data",
        "src",
        "logs",
        "tests"
    ]
    
    print("🏗️  Building Professional Folder Structure...")
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        # Add an empty .gitkeep so empty folders are tracked
        with open(os.path.join(folder, ".gitkeep"), "w") as f:
            pass
        print(f"   📂 /{folder}")

    # 2. Create __init__.py in src (Makes it a Python Package)
    with open("src/__init__.py", "w") as f:
        pass
    print("   📄 src/__init__.py")

    # 3. Create .gitignore (Security)
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
.venv/

# Secrets
.env

# Data
data/*.db
data/*.sqlite

# Logs
logs/*.log
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    print("   🛑 .gitignore created")

    # 4. Create Config File
    config_content = """sources:
  - name: "The Rundown AI"
    url: "https://www.therundown.ai/feed"
    trust_score: 10
    type: "rss"
    max_items: 10
    enabled: true

  - name: "Ben's Bites"
    url: "https://bensbites.beehiiv.com/feed"
    trust_score: 9
    type: "rss"
    max_items: 10
    enabled: true
"""
    with open("config/sources.yaml", "w") as f:
        f.write(config_content)
    print("   ⚙️  config/sources.yaml created")
    
    # 5. Create Secrets File
    with open(".env", "w") as f:
        f.write("EMAIL_USER=your_email@gmail.com\nEMAIL_PASS=your_app_password")
    print("   🔒 .env created")

    print("\n✅ Structure Complete!")

if __name__ == "__main__":
    create_structure()