import smtplib
from email.message import EmailMessage
import os
import logging
from dotenv import load_dotenv

# Load env variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Inherit settings from the main.py root logger
logger = logging.getLogger(__name__)

# We normally put these in heavily locked down Configs/Env vars
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "no-reply@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MOCK_EMAIL_MODE = not bool(SMTP_PASSWORD)


def send_confirmation_email(recipient_email: str, booking_details: dict):
    """
    Send an HTML formatted confirmation email outlining the booking.
    Will mock to standard output if no SMTP_PASSWORD is provided.
    """
    subject = f"Booking Confirmation: {booking_details.get('hall')} on {booking_details.get('date')}"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #4f46e5;">Hall Booking Confirmed!</h2>
        <p>Hi {booking_details.get('booked_by', 'there')},</p>
        <p>Your booking has been successfully secured in our system. Here are your reservation details:</p>
        <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #4f46e5; border-radius: 4px;">
            <p><strong>Hall:</strong> {booking_details.get('hall')}</p>
            <p><strong>Date:</strong> {booking_details.get('date')}</p>
            <p><strong>Time:</strong> {booking_details.get('start_time')} - {booking_details.get('end_time')}</p>
            <p><strong>Purpose:</strong> {booking_details.get('purpose')}</p>
        </div>
        <br>
        <p>If you need to change your manual setup or cancel, please contact the administrators via our support number.</p>
        <p>Best regards,<br>Hall Booking Expert System</p>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = recipient_email
    msg.set_content("Your booking has been confirmed.", subtype="plain") # Fallback
    msg.add_alternative(html_content, subtype='html')

    if MOCK_EMAIL_MODE:
        logger.info(f"[MOCK EMAIL DISPATCH] TO: {recipient_email} | SUBJECT: {subject}")
        # Note: We omit logging full HTML body here to keep the bookings.log file clean.
        return

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Dispatch successful: confirmation sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to dispatch email to {recipient_email}: {e}")
