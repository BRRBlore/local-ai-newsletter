-- src/emailer.py


import smtplib
import ssl
import os
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
recipients_raw = os.getenv("EMAIL_RECIPIENT", "")
RECIPIENT_LIST = [email.strip() for email in recipients_raw.split(',') if email.strip()]

FILE_PATH = "ai_newsletter.md"

def send_email():
    if not os.path.exists(FILE_PATH): return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_raw = markdown.markdown(md_content)

    print(f"📧 Connecting to Gmail...")
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            for recipient in RECIPIENT_LIST:
                print(f"   -> Sending to: {recipient}...")
                message = MIMEMultipart("alternative")
                message["Subject"] = f"Bapi's AI Brief - {datetime.now().strftime('%Y-%m-%d')}"
                message["From"] = SENDER_EMAIL
                message["To"] = recipient

                html_body = f"""
                <html>
                  <head>
                    <style>
                        body {{ font-family: 'Segoe UI', sans-serif; background-color: #f4f4f9; color: #333; }}
                        .container {{ max-width: 600px; margin: 20px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background-color: #2c3e50; color: #fff; padding: 25px; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 24px; }}
                        .content {{ padding: 25px; }}
                        
                        /* CATEGORY HEADERS (H2) */
                        h2 {{ 
                            background-color: #eaf2f8; 
                            color: #2980b9; 
                            padding: 10px; 
                            border-radius: 5px; 
                            font-size: 18px; 
                            margin-top: 30px; 
                            border-left: 5px solid #2980b9;
                        }}

                        /* STORY HEADLINES (H3) */
                        h3 {{ color: #2c3e50; font-size: 16px; margin-top: 20px; }}
                        
                        ul {{ padding-left: 20px; color: #555; }}
                        li {{ margin-bottom: 5px; line-height: 1.5; font-size: 14px; }}
                        a {{ color: #e74c3c; text-decoration: none; font-weight: bold; font-size: 12px; }}
                        
                        .footer {{ background-color: #ecf0f1; text-align: center; padding: 15px; font-size: 12px; color: #7f8c8d; }}
                    </style>
                  </head>
                  <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 Bapi's Daily AI Brief</h1>
                            <p style="margin:5px 0 0 0; font-size: 14px; opacity: 0.8;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
                        </div>
                        <div class="content">{html_raw}</div>
                        <div class="footer"><p>Curated by Bapi's Local AI Agent</p></div>
                    </div>
                  </body>
                </html>
                """
                message.attach(MIMEText(html_body, "html"))
                server.sendmail(SENDER_EMAIL, recipient, message.as_string())
        print("✅ All emails sent!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    send_email()