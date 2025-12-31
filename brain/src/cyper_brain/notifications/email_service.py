"""
Email Notification Service

Implements email delivery for scan alerts, payment notifications, etc.
Using SendGrid for reliable delivery.
Following TDD - tests in test_email_notifications.py
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from jinja2 import Template

# SendGrid import
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
except ImportError:
    SendGridAPIClient = None  # Allow tests to run without SendGrid

logger = logging.getLogger(__name__)


class EmailDeliveryFailed(Exception):
    """Raised when email delivery fails"""
    pass


class EmailTemplate(Enum):
    """Email template definitions"""
    
    SCAN_COMPLETE = "scan_complete"
    CRITICAL_FINDING = "critical_finding"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    TRIAL_ENDING = "trial_ending"
    TRIAL_EXPIRED = "trial_expired"
    
    def render(self, **kwargs) -> str:
        """Render template with data"""
        templates = {
            "scan_complete": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Scan Complete: {{ target }}</h2>
                    <p>Your security scan has finished.</p>
                    <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                        <strong>Findings:</strong> {{ findings_count }}<br>
                        {% if critical_count %}
                        <span style="color: #d32f2f;"><strong>Critical:</strong> {{ critical_count }}</span><br>
                        {% endif %}
                    </div>
                    <p><a href="{{ scan_url }}" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Report</a></p>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        <a href="{{ unsubscribe_url }}">Unsubscribe</a> from scan notifications
                    </p>
                </body>
                </html>
            """,
            "critical_finding": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="background: #d32f2f; color: white; padding: 15px;">
                        <h2 style="margin: 0;">🚨 CRITICAL Security Finding Detected</h2>
                    </div>
                    <div style="padding: 20px;">
                        <h3>{{ title }}</h3>
                        <p><strong>Severity:</strong> <span style="color: #d32f2f;">{{ severity|upper }}</span></p>
                        <p><strong>CVSS Score:</strong> {{ cvss_score }}/10</p>
                        <p><strong>Affected Target:</strong> {{ target }}</p>
                        <div style="background: #fff3cd; padding: 15px; margin: 20px 0;">
                            <strong>Recommendation:</strong><br>
                            {{ recommendation }}
                        </div>
                        <p><a href="{{ finding_url }}" style="background: #d32f2f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">View Details</a></p>
                    </div>
                </body>
                </html>
            """,
            "payment_success": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Payment Received - Thank You!</h2>
                    <p>Your payment has been processed successfully.</p>
                    <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                        <strong>Amount:</strong> ${{ amount }}<br>
                        <strong>Plan:</strong> {{ plan }}<br>
                        <strong>Period:</strong> {{ period }}
                    </div>
                    <p><a href="{{ invoice_url }}">Download Invoice</a></p>
                </body>
                </html>
            """,
            "payment_failed": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Payment Failed - Action Required</h2>
                    <p>We were unable to process your payment.</p>
                    <div style="background: #ffebee; padding: 15px; margin: 20px 0;">
                        <strong>Reason:</strong> {{ reason }}
                    </div>
                    <p>Please update your payment method to continue using Pro features.</p>
                    <p><a href="{{ update_payment_url }}" style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Update Payment Method</a></p>
                </body>
                </html>
            """,
            "trial_ending": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Your Trial is Ending Soon</h2>
                    <p>You have <strong>{{ days_remaining }} days</strong> left in your free trial.</p>
                    <p>Upgrade now to continue enjoying Pro features:</p>
                    <ul>
                        <li>1,000 scans per month</li>
                        <li>Advanced reports</li>
                        <li>Priority support</li>
                    </ul>
                    <p><a href="{{ upgrade_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Upgrade to Pro - $99/month</a></p>
                </body>
                </html>
            """,
            "trial_expired": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>Your Trial Has Expired</h2>
                    <p>Your free trial has ended. You've been moved to the Free plan.</p>
                    <p><strong>Free Plan Limits:</strong></p>
                    <ul>
                        <li>100 scans per month</li>
                        <li>Basic reports</li>
                    </ul>
                    <p>Upgrade to Pro to unlock more scans and features:</p>
                    <p><a href="{{ upgrade_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Upgrade Now</a></p>
                </body>
                </html>
            """
        }
        
        template_str = templates.get(self.value, "")
        template = Template(template_str)
        return template.render(**kwargs)


class EmailService:
    """
    Email notification service
    
    Handles all email delivery using SendGrid.
    """
    
    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        """
        Initialize email service
        
        Args:
            api_key: SendGrid API key (or from SENDGRID_API_KEY env)
            from_email: Sender email address
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@cypersecurity.com")
        
        if SendGridAPIClient and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            logger.warning("SendGrid not configured - emails will be logged only")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> Dict:
        """
        Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email content
            from_email: Override sender email
        
        Returns:
            Dict with status and details
        
        Raises:
            EmailDeliveryFailed: If delivery fails
        """
        try:
            if not self.client:
                # Log only mode (for development/testing)
                logger.info(f"EMAIL: To={to}, Subject={subject}")
                return {"status": "sent", "to": to, "mode": "log_only"}
            
            message = Mail(
                from_email=from_email or self.from_email,
                to_emails=to,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            logger.info(f"Email sent to {to}: {subject}")
            
            return {
                "status": "sent",
                "to": to,
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise EmailDeliveryFailed(f"Email delivery failed: {e}")
    
    def notify_scan_complete(self, user_email: str, scan_data: Dict):
        """Send scan completion notification"""
        # Check if user is subscribed
        if not self.is_subscribed(user_email, "scan_notifications"):
            logger.info(f"User {user_email} unsubscribed from scan notifications")
            return
        
        html = EmailTemplate.SCAN_COMPLETE.render(
            target=scan_data.get("target", "Unknown"),
            findings_count=scan_data.get("findings_count", 0),
            critical_count=scan_data.get("critical_count", 0),
            scan_url=scan_data.get("scan_url", "#"),
            unsubscribe_url=self._get_unsubscribe_url(user_email, "scan_notifications")
        )
        
        self.send_email(
            to=user_email,
            subject=f"Scan Complete: {scan_data.get('target')}",
            html_content=html
        )
    
    def notify_critical_finding(self, user_email: str, finding: Dict):
        """Send alert for critical vulnerability"""
        # Only send for critical severity
        if finding.get("severity") != "critical":
            return
        
        html = EmailTemplate.CRITICAL_FINDING.render(
            title=finding.get("title", "Security Finding"),
            severity=finding.get("severity", "critical"),
            cvss_score=finding.get("cvss_score", "N/A"),
            target=finding.get("target", "Unknown"),
            recommendation=finding.get("recommendation", "Review the finding details"),
            finding_url=finding.get("url", "#")
        )
        
        self.send_email(
            to=user_email,
            subject=f"🚨 CRITICAL: {finding.get('title')}",
            html_content=html
        )
    
    def notify_payment_success(self, user_email: str, payment_data: Dict):
        """Send payment receipt"""
        amount_cents = payment_data.get("amount", 0)
        amount_dollars = amount_cents / 100
        
        html = EmailTemplate.PAYMENT_SUCCESS.render(
            amount=f"{amount_dollars:.2f}",
            plan=payment_data.get("plan", "Pro"),
            period="Monthly",
            invoice_url=payment_data.get("invoice_url", "#")
        )
        
        self.send_email(
            to=user_email,
            subject="Payment Received - Thank You!",
            html_content=html
        )
    
    def notify_payment_failed(self, user_email: str, reason: str = ""):
        """Send payment failure notification"""
        html = EmailTemplate.PAYMENT_FAILED.render(
            reason=reason or "Card declined",
            update_payment_url="https://app.cypersecurity.com/settings/billing"
        )
        
        self.send_email(
            to=user_email,
            subject="Payment Failed - Action Required",
            html_content=html
        )
    
    def notify_trial_ending(self, user_email: str, days_remaining: int):
        """Send trial ending reminder"""
        html = EmailTemplate.TRIAL_ENDING.render(
            days_remaining=days_remaining,
            upgrade_url="https://app.cypersecurity.com/upgrade"
        )
        
        self.send_email(
            to=user_email,
            subject=f"Your trial ends in {days_remaining} days",
            html_content=html
        )
    
    def notify_trial_expired(self, user_email: str):
        """Send trial expiration notification"""
        html = EmailTemplate.TRIAL_EXPIRED.render(
            upgrade_url="https://app.cypersecurity.com/upgrade"
        )
        
        self.send_email(
            to=user_email,
            subject="Your trial has expired",
            html_content=html
        )
    
    def send_batch(self, recipients: List[str], subject: str, html_content: str):
        """Send email to multiple recipients"""
        for recipient in recipients:
            try:
                self.send_email(recipient, subject, html_content)
            except EmailDeliveryFailed as e:
                logger.error(f"Failed to send to {recipient}: {e}")
                continue
    
    def unsubscribe(self, user_id: str, email_type: str):
        """Mark user as unsubscribed from email type"""
        # In real implementation, update database
        # db.update_email_preferences(user_id, email_type, subscribed=False)
        logger.info(f"User {user_id} unsubscribed from {email_type}")
    
    def is_subscribed(self, user_email: str, email_type: str) -> bool:
        """Check if user is subscribed to email type"""
        # In real implementation, check database
        # return db.get_email_preference(user_email, email_type)
        return True  # Default to subscribed
    
    def _get_unsubscribe_url(self, user_email: str, email_type: str) -> str:
        """Generate unsubscribe URL"""
        # In production, generate secure token
        return f"https://app.cypersecurity.com/unsubscribe?email={user_email}&type={email_type}"
