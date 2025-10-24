"""
Notifier subsystem for alerts
"""

import requests
import logging
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class Notifier:
    """Notification handler"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def notify(self, router_name: str, action: str, details: Dict[str, Any], notification_type: str = 'all'):
        """Send notification"""
        message = self._format_message(router_name, action, details)

        if notification_type in ('telegram', 'all'):
            self._send_telegram(message)

        if notification_type in ('email', 'all'):
            self._send_email(message)

        if notification_type in ('webhook', 'all'):
            self._send_webhook(router_name, action, details)

    def _format_message(self, router_name: str, action: str, details: Dict[str, Any]) -> str:
        """Format notification message"""
        return f"Router {router_name}: {action}\nDetails: {details}"

    def _send_telegram(self, message: str):
        """Send Telegram message"""
        try:
            token = self.config.get('telegram_token')
            chat_id = self.config.get('telegram_chat_id')
            if not token or not chat_id:
                return

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def _send_email(self, message: str):
        """Send email notification"""
        try:
            smtp_server = self.config.get('smtp_server')
            smtp_port = self.config.get('smtp_port', 587)
            smtp_user = self.config.get('smtp_user')
            smtp_pass = self.config.get('smtp_password')
            to_email = self.config.get('alert_email')

            if not all([smtp_server, smtp_user, smtp_pass, to_email]):
                return

            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = "MikroTik DDoS Alert"

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()

            logger.info("Email notification sent")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def _send_webhook(self, router_name: str, action: str, details: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                return

            payload = {
                'router': router_name,
                'action': action,
                'details': details,
                'timestamp': details.get('timestamp')
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Webhook notification sent")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")