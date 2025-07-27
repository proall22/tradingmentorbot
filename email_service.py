import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from config import EMAIL_USER, EMAIL_PASSWORD

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.email_user = EMAIL_USER
        self.email_password = EMAIL_PASSWORD
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587  # Changed from 465 to 587
    
    def send_email(self, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Fixed SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, user_name, user_email):
        subject = "Welcome to Trading Mentor Bot! 🎉"
        body = f"""
Dear {user_name},

Welcome to Trading Mentor Bot! We're excited to have you join our community of traders.

You've successfully registered and can now access our services:
• Mentorship programs
• Master classes
• VIP signals
• One-to-one coaching

To get started, simply return to the bot and choose your preferred service.

If you have any questions, feel free to reach out to our support team.

Best regards,
Trading Mentor Team
        """
        return self.send_email(user_email, subject, body)
    
    def send_payment_confirmation(self, user_name, user_email, service, duration, amount):
        subject = f"Payment Confirmation - {service}"
        body = f"""
Dear {user_name},

Your payment has been confirmed! Here are the details:

Service: {service}
Duration: {duration} month(s)
Amount: ${amount}

Your subscription is now active and you have full access to the service.

Thank you for choosing Trading Mentor Bot!

Best regards,
Trading Mentor Team
        """
        return self.send_email(user_email, subject, body)
    
    def send_expiry_warning(self, user_name, user_email, service, days_left):
        subject = f"Subscription Expiring Soon - {service}"
        body = f"""
Dear {user_name},

Your {service} subscription will expire in {days_left} day(s).

To continue enjoying our services, please renew your subscription before it expires.

Return to the bot to renew: [Bot Link]

Best regards,
Trading Mentor Team
        """
        return self.send_email(user_email, subject, body)
    
    def send_admin_notification(self, admin_email, subject, message):
        return self.send_email(admin_email, f"[Admin] {subject}", message)
    
    def send_new_payment_alert(self, admin_email, user_name, service, amount, payment_method):
        subject = "New Payment Requires Approval"
        body = f"""
New payment received:

User: {user_name}
Service: {service}
Amount: ${amount}
Payment Method: {payment_method}

Please review and approve in the admin panel.
        """
        return self.send_admin_notification(admin_email, subject, body)

# Global email service instance
email_service = EmailService()
