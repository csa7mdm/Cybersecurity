"""
TDD Tests for Email Notification Service

Testing email delivery for:
- Scan completion
- Critical findings
- Payment failures
- Trial expiration
"""

import pytest
from unittest.mock import Mock, patch, call
from cyper_brain.notifications.email_service import (
    EmailService,
    EmailTemplate,
    EmailDeliveryFailed
)


class TestEmailDelivery:
    """Test basic email sending"""
    
    @patch('sendgrid.SendGridAPIClient')
    def test_send_email_success(self, mock_sendgrid):
        """Should send email successfully"""
        mock_client = Mock()
        mock_sendgrid.return_value = mock_client
        mock_client.send.return_value = Mock(status_code=202)
        
        service = EmailService(api_key="test_key")
        
        result = service.send_email(
            to="user@example.com",
            subject="Test Email",
            html_content="<p>Test</p>"
        )
        
        assert result["status"] == "sent"
        assert result["to"] == "user@example.com"
        mock_client.send.assert_called_once()
    
    @patch('sendgrid.SendGridAPIClient')
    def test_send_email_failure(self, mock_sendgrid):
        """Should handle email delivery failure"""
        mock_client = Mock()
        mock_sendgrid.return_value = mock_client
        mock_client.send.side_effect = Exception("API Error")
        
        service = EmailService(api_key="test_key")
        
        with pytest.raises(EmailDeliveryFailed):
            service.send_email(
                to="invalid@example.com",
                subject="Test",
                html_content="Test"
            )


class TestScanCompletionEmails:
    """Test scan completion notifications"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_scan_complete_notification(self, mock_send):
        """Should send email when scan completes"""
        service = EmailService(api_key="test_key")
        
        scan_data = {
            "id": "scan_123",
            "target": "example.com",
            "open_ports": [80, 443],
            "status": "completed"
        }
        
        service.notify_scan_complete(
            user_email="user@example.com",
            scan_data=scan_data
        )
        
        # Verify email was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        
        assert call_args[1]["to"] == "user@example.com"
        assert "Scan Complete" in call_args[1]["subject"]
        assert "example.com" in call_args[1]["html_content"]
    
    @patch.object(EmailService, 'send_email')
    def test_scan_complete_includes_findings_summary(self, mock_send):
        """Should include findings count in email"""
        service = EmailService(api_key="test_key")
        
        scan_data = {
            "id": "scan_123",
            "target": "example.com",
            "findings_count": 5,
            "critical_count": 2
        }
        
        service.notify_scan_complete(
            user_email="user@example.com",
            scan_data=scan_data
        )
        
        html_content = mock_send.call_args[1]["html_content"]
        assert "5" in html_content  # findings count
        assert "2" in html_content  # critical count


class TestCriticalFindingAlerts:
    """Test critical vulnerability alerts"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_critical_finding_alert(self, mock_send):
        """Should send immediate alert for critical findings"""
        service = EmailService(api_key="test_key")
        
        finding = {
            "severity": "critical",
            "title": "SQL Injection Vulnerability",
            "cvss_score": 9.8,
            "target": "api.example.com"
        }
        
        service.notify_critical_finding(
            user_email="user@example.com",
            finding=finding
        )
        
        call_args = mock_send.call_args
        assert "CRITICAL" in call_args[1]["subject"].upper()
        assert "SQL Injection" in call_args[1]["html_content"]
        assert "9.8" in call_args[1]["html_content"]
    
    @patch.object(EmailService, 'send_email')
    def test_only_send_for_critical_severity(self, mock_send):
        """Should only send alerts for critical severity"""
        service = EmailService(api_key="test_key")
        
        # Low severity finding
        finding = {
            "severity": "low",
            "title": "Minor Issue"
        }
        
        service.notify_critical_finding(
            user_email="user@example.com",
            finding=finding
        )
        
        # Should not send email for low severity
        mock_send.assert_not_called()


class TestPaymentNotifications:
    """Test payment-related emails"""
    
    @patch.object(EmailService, 'send_email')
    def test_payment_success_email(self, mock_send):
        """Should send receipt for successful payment"""
        service = EmailService(api_key="test_key")
        
        payment_data = {
            "amount": 9900,  # $99.00
            "plan": "Pro",
            "invoice_url": "https://invoice.example.com"
        }
        
        service.notify_payment_success(
            user_email="user@example.com",
            payment_data=payment_data
        )
        
        call_args = mock_send.call_args
        assert "Payment Received" in call_args[1]["subject"]
        assert "$99" in call_args[1]["html_content"]
        assert "invoice.example.com" in call_args[1]["html_content"]
    
    @patch.object(EmailService, 'send_email')
    def test_payment_failed_email(self, mock_send):
        """Should notify user of payment failure"""
        service = EmailService(api_key="test_key")
        
        service.notify_payment_failed(
            user_email="user@example.com",
            reason="Card declined"
        )
        
        call_args = mock_send.call_args
        assert "Payment Failed" in call_args[1]["subject"]
        assert "Card declined" in call_args[1]["html_content"]
        assert "update" in call_args[1]["html_content"].lower()


class TestTrialNotifications:
    """Test trial period notifications"""
    
    @patch.object(EmailService, 'send_email')
    def test_trial_ending_reminder(self, mock_send):
        """Should send reminder 3 days before trial ends"""
        service = EmailService(api_key="test_key")
        
        service.notify_trial_ending(
            user_email="user@example.com",
            days_remaining=3
        )
        
        call_args = mock_send.call_args
        assert "trial" in call_args[1]["subject"].lower()
        assert "3 days" in call_args[1]["html_content"]
    
    @patch.object(EmailService, 'send_email')
    def test_trial_expired_notification(self, mock_send):
        """Should notify when trial expires"""
        service = EmailService(api_key="test_key")
        
        service.notify_trial_expired(
            user_email="user@example.com"
        )
        
        call_args = mock_send.call_args
        assert "expired" in call_args[1]["subject"].lower()
        assert "upgrade" in call_args[1]["html_content"].lower()


class TestEmailTemplates:
    """Test email template rendering"""
    
    def test_render_scan_complete_template(self):
        """Should render scan complete template with data"""
        template = EmailTemplate.SCAN_COMPLETE
        
        html = template.render(
            scan_id="scan_123",
            target="example.com",
            findings_count=5,
            scan_url="https://app.example.com/scans/123"
        )
        
        assert "example.com" in html
        assert "5" in html
        assert "app.example.com/scans/123" in html
    
    def test_render_critical_finding_template(self):
        """Should render critical finding template"""
        template = EmailTemplate.CRITICAL_FINDING
        
        html = template.render(
            severity="critical",
            title="SQL Injection",
            cvss_score=9.8,
            recommendation="Sanitize user input"
        )
        
        assert "SQL Injection" in html
        assert "9.8" in html
        assert "Sanitize" in html


class TestUnsubscribe:
    """Test email unsubscribe functionality"""
    
    def test_include_unsubscribe_link(self):
        """Should include unsubscribe link in all emails"""
        service = EmailService(api_key="test_key")
        
        with patch.object(service, 'send_email') as mock_send:
            service.notify_scan_complete(
                user_email="user@example.com",
                scan_data={"id": "scan_123", "target": "example.com"}
            )
            
            html = mock_send.call_args[1]["html_content"]
            assert "unsubscribe" in html.lower()
    
    @patch('cyper_brain.notifications.email_service.db')
    def test_unsubscribe_user(self, mock_db):
        """Should mark user as unsubscribed"""
        service = EmailService(api_key="test_key")
        
        service.unsubscribe(user_id="user_123", email_type="scan_notifications")
        
        mock_db.update_email_preferences.assert_called_once_with(
            user_id="user_123",
            email_type="scan_notifications",
            subscribed=False
        )
    
    @patch.object(EmailService, 'send_email')
    def test_respect_unsubscribe_preferences(self, mock_send):
        """Should not send if user unsubscribed"""
        service = EmailService(api_key="test_key")
        
        # Mock user as unsubscribed
        with patch.object(service, 'is_subscribed', return_value=False):
            service.notify_scan_complete(
                user_email="user@example.com",
                scan_data={"id": "scan_123"}
            )
            
            # Should not send email
            mock_send.assert_not_called()


class TestBatchEmails:
    """Test sending emails in batches"""
    
    @patch.object(EmailService, 'send_email')
    def test_send_batch_emails(self, mock_send):
        """Should send emails to multiple recipients"""
        service = EmailService(api_key="test_key")
        
        recipients = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]
        
        service.send_batch(
            recipients=recipients,
            subject="Test Batch",
            html_content="<p>Test</p>"
        )
        
        assert mock_send.call_count == 3


# Fixtures
@pytest.fixture
def sample_scan_data():
    """Sample scan data for testing"""
    return {
        "id": "scan_123",
        "target": "example.com",
        "status": "completed",
        "open_ports": [80, 443],
        "findings_count": 5,
        "critical_count": 2,
        "high_count": 1,
        "scan_url": "https://app.example.com/scans/123"
    }


@pytest.fixture
def sample_finding():
    """Sample critical finding for testing"""
    return {
        "severity": "critical",
        "title": "SQL Injection Vulnerability",
        "cvss_score": 9.8,
        "cve_id": "CVE-2024-1234",
        "target": "api.example.com",
        "recommendation": "Sanitize all user inputs"
    }
