"""
Email sender module for sending trading alerts.
Handles SMTP email configuration and sending.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Any, Optional

from collect.config_handler import config_handler

logger = logging.getLogger(__name__)


class EmailSender:
    """Email sender for trading alerts."""
    
    def __init__(self, smtp_item: str = "smtp.qq.com"):
        """
        Initialize email sender with SMTP configuration.
        
        Args:
            smtp_item: Configuration item for SMTP settings (default: "smtp.qq.com")
        """
        self.smtp_item = smtp_item
        self.smtp_config = config_handler.get_config_dict(smtp_item)
        
        if not self.smtp_config:
            logger.warning(f"No SMTP configuration found for {smtp_item}")
    
    def _get_smtp_config(self) -> Optional[Dict[str, str]]:
        """
        Get SMTP configuration from MongoDB.
        
        Returns:
            Dictionary with 'account', 'authCode', 'host', 'port' or None
        """
        config = config_handler.get_config_dict(self.smtp_item)
        
        if not config:
            logger.error(f"SMTP configuration not found: {self.smtp_item}")
            return None
        
        required_keys = ['account', 'authCode']
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required SMTP config key: {key}")
                return None
        
        # Set default values
        smtp_config = {
            'account': config['account'],
            'authCode': config['authCode'],
            'host': config.get('host', 'smtp.qq.com'),
            'port': config.get('port', '587')
        }
        
        return smtp_config
    
    def send_email(self, to_email: str, subject: str, content: str, is_html: bool = False) -> bool:
        """
        Send email to specified recipient.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (plain text or HTML)
            is_html: Whether content is HTML format
            
        Returns:
            bool: True if send successful, False otherwise
        """
        try:
            smtp_config = self._get_smtp_config()
            if not smtp_config:
                return False
            
            account = smtp_config['account']
            auth_code = smtp_config['authCode']
            host = smtp_config['host']
            port = int(smtp_config['port'])
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = formataddr(("Technical Analysis Helper", account))
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach content
            msg.attach(MIMEText(content, 'html' if is_html else 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(host, port) as server:
                server.starttls()  # Enable TLS
                server.login(account, auth_code)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_trading_alert(self, to_email: str, prediction_data: Dict[str, Any], confidence_threshold: float = 0.6) -> bool:
        """
        Send trading alert email based on prediction data.
        
        Args:
            to_email: Recipient email address
            prediction_data: Prediction data from predict_price_movement()
            confidence_threshold: Minimum confidence to send alert (default: 0.6)
            
        Returns:
            bool: True if sent, False if confidence too low or send failed
        """
        try:
            prediction = prediction_data.get('prediction')
            prediction_label = prediction_data.get('prediction_label')
            probabilities = prediction_data.get('probabilities', {})
            timestamp = prediction_data.get('timestamp')
            
            if not prediction or not probabilities:
                logger.warning("Invalid prediction data")
                return False
            
            # Calculate confidence
            confidence = probabilities.get(str(prediction), 0)
            
            # Check if confidence meets threshold
            if confidence < confidence_threshold:
                logger.info(f"Confidence {confidence:.2%} below threshold {confidence_threshold:.2%}, skipping email")
                return False
            
            # Format timestamp
            if timestamp:
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_time = "Unknown"
            
            # Create email content (HTML format)
            subject = f"交易提醒: {prediction_label} (置信度: {confidence:.1%})"
            
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }}
                    .header {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .prediction {{
                        font-size: 24px;
                        font-weight: bold;
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .confidence {{
                        text-align: center;
                        font-size: 18px;
                        color: #4CAF50;
                        margin: 10px 0;
                    }}
                    .details {{
                        background-color: #f9f9f9;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .timestamp {{
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>交易提醒</h2>
                    </div>
                    <div class="prediction">
                        {prediction_label}
                    </div>
                    <div class="confidence">
                        置信度: {confidence:.1%}
                    </div>
                    <div class="details">
                        <h3>预测详情</h3>
                        <p><strong>预测类别:</strong> {prediction}</p>
                        <p><strong>预测标签:</strong> {prediction_label}</p>
                        <p><strong>置信度:</strong> {confidence:.2%}</p>
                        <h4>所有类别概率:</h4>
                        <ul>
            """
            
            for class_id, prob in probabilities.items():
                html_content += f"<li>类别 {class_id}: {prob:.2%}</li>"
            
            html_content += f"""
                        </ul>
                    </div>
                    <div class="timestamp">
                        时间: {formatted_time}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            return self.send_email(to_email, subject, html_content, is_html=True)
            
        except Exception as e:
            logger.error(f"Failed to send trading alert: {e}")
            return False


# Global instance
email_sender = EmailSender()
