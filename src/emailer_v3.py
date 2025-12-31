import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from pathlib import Path

# --- ROBUST CONFIGURATION ---
# Get the absolute path to the folder where this script lives (src/)
script_dir = Path(__file__).resolve().parent
# Go up one level to the project root to find .env
env_path = script_dir.parent / '.env'

# Force load the specific .env file
load_dotenv(dotenv_path=env_path)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
# Handles multiple recipients (comma-separated list in .env)
# Using 'get' with a default ensures .split() doesn't crash if variable is missing
recipients_str = os.getenv("EMAIL_RECIPIENT", "")
RECIPIENTS = recipients_str.split(",") if recipients_str else []

# HTML file is also in the project root (parent of script_dir)
HTML_FILE = script_dir.parent / "newsletter_v3.html"

def send_emails():
    # Debug print to help us verify path (will show in log)
    print(f"[INFO] Looking for .env at: {env_path}")
    
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECIPIENTS:
        print("[ERROR] Missing email configuration in .env")
        print(f"      Found User: {SENDER_EMAIL}") # Debug helper
        return

    # Check if HTML exists
    if not HTML_FILE.exists():
        print(f"[ERROR] HTML file not found: {HTML_FILE}")
        return

    # Read the HTML content
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    print("[INFO] Starting Email Service...")

    try:
        # Connect to Gmail Server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("[INFO] Login Successful.")

        for recipient in RECIPIENTS:
            recipient = recipient.strip()
            if not recipient:
                continue
                
            # Create the email
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient
            msg["Subject"] = "Bapi's AI Builder's Daily"

            # Attach HTML content
            msg.attach(MIMEText(html_content, "html"))

            # Send
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
            print(f"   ...Sending to {recipient}")

        server.quit()
        print(f"[SUCCESS] Sent to {len(RECIPIENTS)} recipients.")

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

if __name__ == "__main__":
    send_emails()