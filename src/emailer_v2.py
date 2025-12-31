import smtplib
import ssl
import os
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "ai_newsletter_v2.md")

SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_RAW = os.getenv("EMAIL_RECIPIENT", "")
RECIPIENT_LIST = [email.strip() for email in RECIPIENT_RAW.split(',') if email.strip()]

def send_email():
    if not os.path.exists(INPUT_FILE):
        print(f" ❌ File not found: {INPUT_FILE}")
        return

    print(" 📧 Preparing V2 distribution...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    html_content = markdown.markdown(md_text, extensions=['extra'])

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html {{ scroll-behavior: smooth; }}
            body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f4f4f9; color: #1a1a1a; }}
            .container {{ max-width: 650px; margin: 0 auto; background-color: #ffffff; }}
            .header {{ background-color: #003366; color: #ffffff; padding: 40px 30px; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
            .header .meta {{ margin-top: 10px; font-size: 13px; color: #aab7c4; display: flex; justify-content: space-between; }}
            
            /* EXECUTIVE SUMMARY LIST */
            ol {{ padding-left: 20px; color: #003366; font-weight: 700; margin-bottom: 30px; }}
            ol li {{ margin-bottom: 18px; }} /* Nice spacing between items */
            
            /* Headline Link */
            ol a {{ text-decoration: none; color: #003366; font-size: 16px; border-bottom: 1px dotted #ccc; display: inline-block; margin-bottom: 4px; }}
            ol a:hover {{ border-bottom: 1px solid #003366; background-color: #f0f8ff; }}
            
            /* The 1-Sentence Teaser (Grey & Small) */
            .toc-teaser {{ display: block; font-weight: 400; font-size: 13px; color: #666; line-height: 1.4; margin-top: 2px; }}

            .content {{ padding: 30px 30px; }}
            h2 {{ color: #d35400; font-size: 14px; text-transform: uppercase; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 40px; }}
            h3 {{ margin-top: 40px; margin-bottom: 10px; font-size: 18px; font-weight: 700; }}
            h3 a {{ color: #003366; text-decoration: none; }}
            
            ul {{ padding-left: 20px; line-height: 1.6; color: #333; }}
            strong {{ color: #555; font-size: 0.85em; text-transform: uppercase; font-weight: 800; }}
            blockquote {{ margin: 0; padding-left: 15px; border-left: 4px solid #eee; color: #555; font-size: 14px; line-height: 1.6; }}
            
            .footer {{ background-color: #f8f9fa; border-top: 1px solid #e1e4e8; padding: 40px 30px; text-align: center; font-size: 13px; color: #666; }}
            .cta-link {{ display: inline-block; color: #003366; font-weight: bold; text-decoration: underline; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Bapi's Daily AI Intelligence Brief</h1>
                <div class="meta"><span>{datetime.now().strftime("%A, %B %d, %Y")}</span></div>
            </div>
            <div class="content">
                {html_content}
            </div>
            <div class="footer">
                <a href="mailto:{SENDER_EMAIL}?subject=Feedback" class="cta-link">Reply with feedback</a>
                <p>Curated by <strong>Bapi's Local AI Agent</strong></p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Brief (Fixed V2): {datetime.now().strftime('%b %d')}"
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
        print(" ✅ V2 Email Sent!")
    except Exception as e:
        print(f" ❌ Transmission Error: {e}")

if __name__ == "__main__":
    send_email()