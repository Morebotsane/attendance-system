"""
Unit tests for email service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.email_service import email_service


class TestEmailService:
    """Test email service with SMTP"""
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Test body",
            html_body="<h1>Test HTML</h1>"
        )
        
        assert result["success"] is True
    
    @patch('app.services.email_service.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Mock SMTP failure
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP failed")
        
        result = email_service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Test body"
        )
        
        assert result["success"] is False
        assert "error" in result
