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
    msg = EmailMessage()
    msg.set_content(f"Hi {username},\n\nYour account has been successfully created!")
    msg["Subject"] = "Welcome to Our App!"
    # Use settings instead of string literals
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = email

    try:
        # Using settings for host and port as well
        with smtplib.SMTP_SSL(settings.MAIL_SERVER, 465) as smtp:
            smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            smtp.send_message(msg)
        logging.info(f"REAL EMAIL SENT to {email}")
    except Exception as e:
        # Keep the try-except so a mail failure doesn't stop the user registration
        logging.error(f"REAL EMAIL FAILED for {email}: {str(e)}")
        
        
async def send_mfa_email(email: str, code: str):
    message = MessageSchema(
        subject="Your Login Verification Code",
        recipients=[email],
        body=f"Your verification code is: {code}. It expires in 5 minutes.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_reset_email(email_to: str, reset_link: str):
    html = f"""
    <html>
        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #4f46e5; text-align: center;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>We received a request to reset your password. Click the button below to choose a new one. This link will expire in 15 minutes.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #4f46e5; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                       Reset My Password
                    </a>
                </div>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #6b7280; font-size: 12px;">{reset_link}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">If you did not request this, please ignore this email.</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="FastAPI Auth - Password Reset",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)