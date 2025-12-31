import smtplib
import ssl
import os
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "ai_newsletter.md")

SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_RAW = os.getenv("EMAIL_RECIPIENT", "")
RECIPIENT_LIST = [email.strip() for email in RECIPIENT_RAW.split(',') if email.strip()]

def send_email():
    if not os.path.exists(INPUT_FILE):
        print(f" ❌ File not found: {INPUT_FILE}")
        return

    print(" 📧 Preparing distribution...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(md_text, extensions=['extra'])

    # CSS & HTML Template
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Base */
            body {{ font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; color: #1a1a1a; }}
            .container {{ max-width: 650px; margin: 0 auto; background-color: #ffffff; }}
            
            /* Header */
            .header {{ background-color: #003366; color: #ffffff; padding: 40px 30px; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }}
            .header .meta {{ margin-top: 10px; font-size: 13px; color: #aab7c4; display: flex; justify-content: space-between; }}
            .tagline {{ margin-top: 15px; font-size: 15px; color: #e1e4e8; font-style: italic; border-left: 3px solid #3498db; padding-left: 10px; }}
            
            /* Content */
            .content {{ padding: 30px 30px; }}
            
            /* Section Dividers */
            h2 {{ color: #d35400; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 50px; }}
            
            /* Headlines */
            h3 {{ margin-top: 30px; margin-bottom: 10px; font-size: 18px; font-weight: 700; line-height: 1.4; }}
            /* Ensure the link looks like a title */
            h3 a {{ color: #003366; text-decoration: none; border-bottom: 1px solid transparent; }}
            h3 a:hover {{ border-bottom: 1px solid #003366; }}
            
            /* Text & Bullets */
            ul {{ padding-left: 20px; line-height: 1.6; color: #333; margin-top: 5px; }}
            li {{ margin-bottom: 8px; }}
            strong {{ color: #555; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 800; }}
            
            /* Quick Hit Quotes */
            blockquote {{ margin: 0; padding-left: 15px; border-left: 4px solid #eee; color: #555; font-style: normal; font-size: 14px; line-height: 1.6; }}
            
            /* Divider */
            hr {{ border: 0; border-top: 1px solid #f0f0f0; margin: 30px 0; }}

            /* Footer */
            .footer {{ background-color: #f8f9fa; border-top: 1px solid #e1e4e8; padding: 40px 30px; text-align: center; font-size: 13px; color: #666; }}
            .cta-link {{ display: inline-block; color: #003366; font-weight: bold; text-decoration: underline; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bapi's Daily AI Intelligence Brief</h1>
                <div class="meta">
                    <span>{datetime.now().strftime("%A, %B %d, %Y")}</span>
                </div>
                <div class="tagline">Your daily signal on what’s moving the AI world — curated & ranked.</div>
            </div>

            <div class="content">
                {html_content}
            </div>

            <div class="footer">
                <a href="mailto:{SENDER_EMAIL}?subject=Feedback on AI Brief" class="cta-link">Reply with feedback or topics you want covered</a>
                <p>Curated by <strong>Bapi's Local AI Agent</strong></p>
                <p style="font-size: 11px; margin-top: 5px; color: #999;">Generated via Llama 3.1 Architecture</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Brief: {datetime.now().strftime('%b %d')} (Top 5 Signals)"
    msg["From"] = SENDER_EMAIL
    
    msg.attach(MIMEText(full_html, "html"))

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            for recipient in RECIPIENT_LIST:
                if "To" in msg: msg.replace_header("To", recipient)
                else: msg.add_header("To", recipient)
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                print(f"   -> Dispatched to: {recipient}")
        
        print(" ✅ Distribution complete.")

    except Exception as e:
        print(f" ❌ Transmission Error: {e}")

if __name__ == "__main__":
    send_email()