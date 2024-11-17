import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import logging
import time
from typing import Dict, List, Optional
from app.utils.config import get_config
from app.models.subscription import Subscription
from app.utils.logger import setup_logger

class EmailService:
    def __init__(self, config=None):
        """
        Initialize email service with SMTP configuration
        
        Args:
            config (dict, optional): SMTP and email configuration
        """
        self.config = config or get_config()
        self.logger = setup_logger('email_service')
        self.email_queue: List[Dict] = []
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.rate_limit_delay = 1  # seconds between emails

    def _create_smtp_connection(self):
        """
        Create a secure SMTP connection
        
        Returns:
            smtplib.SMTP_SSL: Secure SMTP connection
        """
        try:
            context = ssl.create_default_context()
            smtp_connection = smtplib.SMTP_SSL(
                self.config['SMTP_HOST'], 
                self.config['SMTP_PORT'], 
                context=context
            )
            smtp_connection.login(
                self.config['SMTP_USERNAME'], 
                self.config['SMTP_PASSWORD']
            )
            return smtp_connection
        except Exception as e:
            self.logger.error(f"SMTP Connection Error: {e}")
            raise

    def render_template(self, template_name: str, context: Dict) -> str:
        """
        Render an email template with given context
        
        Args:
            template_name (str): Name of the template
            context (dict): Template rendering context
        
        Returns:
            str: Rendered HTML template
        """
        try:
            with open(f'app/templates/emails/{template_name}.html', 'r') as f:
                template = Template(f.read())
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"Template Rendering Error: {e}")
            raise

    def send_email(
        self, 
        recipient: str, 
        subject: str, 
        template_name: str, 
        context: Dict,
        subscription: Optional[Subscription] = None
    ) -> bool:
        """
        Send an email with subscription-aware templating
        
        Args:
            recipient (str): Email recipient
            subject (str): Email subject
            template_name (str): Email template name
            context (dict): Template rendering context
            subscription (Subscription, optional): User subscription details
        
        Returns:
            bool: Email sending status
        """
        try:
            # Apply subscription-specific context modifications
            if subscription:
                context['subscription_level'] = subscription.tier
                context['is_premium'] = subscription.is_premium()

            html_content = self.render_template(template_name, context)

            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.config['SMTP_SENDER']
            message['To'] = recipient

            message.attach(MIMEText(html_content, 'html'))

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            with self._create_smtp_connection() as smtp:
                smtp.send_message(message)
                self.logger.info(f"Email sent to {recipient}")
                return True

        except Exception as e:
            self.logger.error(f"Email Sending Error: {e}")
            return False

    def queue_email(self, email_details: Dict):
        """
        Queue an email for later processing
        
        Args:
            email_details (dict): Email sending details
        """
        self.email_queue.append(email_details)

    def process_email_queue(self):
        """
        Process queued emails with retry mechanism
        """
        while self.email_queue:
            email = self.email_queue.pop(0)
            retries = 0
            
            while retries < self.max_retries:
                try:
                    success = self.send_email(
                        recipient=email['recipient'],
                        subject=email['subject'],
                        template_name=email['template_name'],
                        context=email['context'],
                        subscription=email.get('subscription')
                    )
                    
                    if success:
                        break
                    
                    retries += 1
                    time.sleep(self.retry_delay * (2 ** retries))
                
                except Exception as e:
                    self.logger.error(f"Queue Processing Error: {e}")
                    break

            if retries == self.max_retries:
                self.logger.error(f"Failed to send email after {self.max_retries} attempts")

# Singleton instance for easy import and use
email_service = EmailService()
