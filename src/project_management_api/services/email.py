import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from project_management_api.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """
    Sends an email using configured SMTP settings.
    Falls back gracefully to logging in development / testing environments.
    """
    # 1. In development or test, log to console if SMTP is not configured
    if settings.environment in ["development", "testing"] and (not settings.smtp_host or settings.smtp_host == "localhost"):
        logger.info(
            f"[EMAIL SERVICE - {settings.environment.upper()}] To: {to_email} | Subject: {subject}\n"
            f"Content:\n{text_content}\n"
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.emails_from_name} <{settings.emails_from_email}>"
        msg["To"] = to_email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.emails_from_email, to_email, msg.as_string())

        logger.info(f"Email successfully delivered to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        return False


def send_verification_email(to_email: str, full_name: str, otp: str) -> bool:
    """Dispatches an email verification OTP message."""
    subject = f"Verify your email - {settings.app_name}"
    text_content = (
        f"Hi {full_name},\n\n"
        f"Thank you for registering with {settings.app_name}.\n"
        f"Your verification code is: {otp}\n\n"
        f"This code will expire in {settings.otp_expire_minutes} minutes.\n"
        f"If you did not create an account, you can safely ignore this email.\n\n"
        f"Best regards,\nThe {settings.app_name} Team"
    )
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #2b6cb0;">Verify Your Email Address</h2>
          <p>Hi <strong>{full_name}</strong>,</p>
          <p>Thank you for signing up for <strong>{settings.app_name}</strong>. Please use the verification code below to confirm your email address:</p>
          <div style="background-color: #f7fafc; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0;">
            <span style="font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #2d3748;">{otp}</span>
          </div>
          <p style="color: #718096; font-size: 14px;">This code will expire in <strong>{settings.otp_expire_minutes} minutes</strong>. For security, never share this code with anyone.</p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <p style="color: #a0aec0; font-size: 12px;">If you did not request this email, please ignore it.</p>
        </div>
      </body>
    </html>
    """
    return send_email(to_email=to_email, subject=subject, html_content=html_content, text_content=text_content)


def send_password_reset_email(to_email: str, full_name: str, otp: str) -> bool:
    """Dispatches a password reset OTP message."""
    subject = f"Password Reset Request - {settings.app_name}"
    text_content = (
        f"Hi {full_name},\n\n"
        f"We received a request to reset your password for {settings.app_name}.\n"
        f"Your password reset code is: {otp}\n\n"
        f"This code will expire in {settings.otp_expire_minutes} minutes.\n"
        f"If you did not request a password reset, please ignore this email. Your password will remain unchanged.\n\n"
        f"Best regards,\nThe {settings.app_name} Team"
    )
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #c53030;">Password Reset Request</h2>
          <p>Hi <strong>{full_name}</strong>,</p>
          <p>We received a request to reset your password for <strong>{settings.app_name}</strong>. Please enter the verification code below:</p>
          <div style="background-color: #fff5f5; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; border: 1px solid #feb2b2;">
            <span style="font-size: 28px; font-weight: bold; letter-spacing: 6px; color: #9b2c2c;">{otp}</span>
          </div>
          <p style="color: #718096; font-size: 14px;">This code will expire in <strong>{settings.otp_expire_minutes} minutes</strong>. If you did not request a password reset, you can safely ignore this email.</p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <p style="color: #a0aec0; font-size: 12px;">For security reasons, never share this code with anyone.</p>
        </div>
      </body>
    </html>
    """
    return send_email(to_email=to_email, subject=subject, html_content=html_content, text_content=text_content)
