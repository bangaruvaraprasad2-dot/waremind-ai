import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config


class EmailService:
    """
    SMTP Email Dispatcher Service for WareMind AI.
    Handles real SMTP email transmission via Gmail, Mailtrap, or any standard SMTP server.
    Provides graceful console logging fallback when SMTP credentials are not configured.
    """

    @staticmethod
    def send_otp_email(recipient_email: str, otp_code: str) -> dict:
        """
        Dispatches a 6-digit OTP verification email via SMTP.
        """
        smtp_server = Config.SMTP_SERVER
        smtp_port = Config.SMTP_PORT
        smtp_username = Config.SMTP_USERNAME
        smtp_password = Config.SMTP_PASSWORD
        sender_email = Config.SMTP_SENDER_EMAIL or smtp_username or "no-reply@waremind.ai"
        use_tls = Config.SMTP_USE_TLS

        # HTML Email Template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #090b10; margin: 0; padding: 20px; color: #f1f5f9; }}
                .container {{ max-width: 500px; margin: 0 auto; background-color: #111622; border: 1px solid #242d3d; border-radius: 16px; padding: 32px; text-align: center; }}
                .logo {{ font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; margin-bottom: 24px; }}
                .logo span {{ color: #6366f1; }}
                .card {{ background-color: #161c2b; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 24px; margin: 20px 0; }}
                .otp-code {{ font-family: monospace; font-size: 36px; font-weight: 800; color: #10b981; letter-spacing: 6px; margin: 16px 0; }}
                .subtext {{ font-size: 13px; color: #94a3b8; line-height: 1.5; }}
                .footer {{ margin-top: 28px; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">WareMind <span>AI</span></div>
                <h2 style="color: #ffffff; font-size: 20px; margin-bottom: 8px;">Verification Security Code</h2>
                <p class="subtext">Use the following 6-digit One-Time Password (OTP) to complete your sign-in to the WareMind AI Control Tower.</p>

                <div class="card">
                    <div style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Your OTP Code</div>
                    <div class="otp-code">{otp_code}</div>
                    <div style="font-size: 11px; color: #f59e0b;">⏰ Valid for 5 minutes only</div>
                </div>

                <p class="subtext">If you did not request this verification code, please ignore this email.</p>

                <div class="footer">
                    &copy; 2026 WareMind AI Platform · Smart Warehouse Operations & Fulfillment Intelligence
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"WareMind AI Security OTP Code: {otp_code}. Valid for 5 minutes."

        # If SMTP username/password are not set, return graceful demo status
        if not smtp_username or not smtp_password:
            print(f"[SMTP WARNING] SMTP_USERNAME or SMTP_PASSWORD not set in .env. Console fallback code for {recipient_email}: {otp_code}")
            return {
                "sent": False,
                "method": "DEMO_FALLBACK",
                "message": f"SMTP credentials not configured. Console OTP: {otp_code}",
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"WareMind AI Verification Code: {otp_code}"
            msg["From"] = f"WareMind AI <{sender_email}>"
            msg["To"] = recipient_email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            print(f"[SMTP] Connecting to {smtp_server}:{smtp_port} for recipient {recipient_email}...")

            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)

            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
            server.quit()

            print(f"[SMTP SUCCESS] Real OTP Email dispatched successfully to {recipient_email} via {smtp_server}!")
            return {
                "sent": True,
                "method": "SMTP",
                "message": f"6-Digit OTP code dispatched to {recipient_email} via SMTP ({smtp_server}).",
            }

        except Exception as e:
            print(f"[SMTP ERROR] Failed to send email via {smtp_server}: {e}")
            return {
                "sent": False,
                "method": "ERROR_FALLBACK",
                "message": f"SMTP dispatch failed ({str(e)}). Using demo OTP code: {otp_code}",
                "error": str(e),
            }
