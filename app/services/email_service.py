import smtplib
from email.message import EmailMessage
import logging

async def send_welcome_email(email: str, username: str):
    # GMAIL CONFIGURATION
    SENDER_EMAIL = "sailu.reddy2001@gmail.com" 
    SENDER_PASSWORD = "REMOVED_SECRET" 

    msg = EmailMessage()
    msg.set_content(f"Hi {username},\n\nYour account has been successfully created!")
    msg["Subject"] = "Welcome to Our App!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = email

    try:
        # Using standard SMTP for Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logging.info(f"REAL EMAIL SENT to {email}")
    except Exception as e:
        logging.error(f"REAL EMAIL FAILED: {str(e)}")