"""
Unit tests for email service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.email_service import EmailService


class TestEmailService:
    """Test email service with SMTP"""
    
    @patch('app.services.email_service.smtplib.SMTP')
    @patch.object(EmailService, '__init__', lambda x: None)
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Create service with mocked attributes
        service = EmailService()
        service.smtp_host = "smtp.gmail.com"
        service.smtp_port = 587
        service.smtp_user = "test@gmail.com"
        service.smtp_password = "test_password"
        service.from_email = "test@gmail.com"
        service.from_name = "Test"
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            html_body="<h1>Test HTML</h1>"
        )
        
        assert result["success"] is True
        assert mock_server.starttls.called
        assert mock_server.login.called
        assert mock_server.send_message.called
    
    @patch('app.services.email_service.smtplib.SMTP')
    @patch.object(EmailService, '__init__', lambda x: None)
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Create service with mocked attributes
        service = EmailService()
        service.smtp_host = "smtp.gmail.com"
        service.smtp_port = 587
        service.smtp_user = "test@gmail.com"
        service.smtp_password = "test_password"
        service.from_email = "test@gmail.com"
        service.from_name = "Test"
        
        # Mock SMTP failure
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP failed")
        
        result = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result["success"] is False
        assert "error" in result
