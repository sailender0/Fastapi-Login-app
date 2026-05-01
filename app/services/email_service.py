import smtplib
from email.message import EmailMessage
import logging
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings

# GMAIL CONFIGURATION
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

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
        
        
async def send_mfa_email(email: str, code: str):
    message = MessageSchema(
        subject="Your Login Verification Code",
        recipients=[email],
        body=f"Your verification code is: {code}. It expires in 5 minutes.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)