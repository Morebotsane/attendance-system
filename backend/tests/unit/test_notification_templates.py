"""
Unit tests for notification message templates
"""
import pytest
from app.templates.notifications import NotificationTemplates, format_phone_number


class TestNotificationTemplates:
    """Test message template generation"""
    
    @pytest.fixture
    def templates(self):
        return NotificationTemplates()
    
    def test_check_in_success_template(self, templates):
        """Test check-in success notification"""
        result = templates.check_in_success(
            employee_name="John Doe",
            time="08:30"
        )
        
        assert "email_subject" in result
        assert "sms" in result
        assert "email_body" in result
        assert "email_html" in result
        assert "John Doe" in result["sms"]
        assert "08:30" in result["sms"]
        assert "Check-in" in result["email_subject"]
    
    def test_check_out_success_template(self, templates):
        """Test check-out success notification"""
        result = templates.check_out_success(
            employee_name="John Doe",
            time="17:30",
            hours_worked=8.5
        )
        
        assert "email_subject" in result
        assert "sms" in result
        assert "John Doe" in result["sms"]
        assert "17:30" in result["sms"]
        assert "8.5" in result["sms"]
        assert "Check-out" in result["email_subject"]
    
    def test_format_phone_number_lesotho(self):
        """Test Lesotho phone number formatting"""
        assert format_phone_number("58359036") == "+26658359036"
        assert format_phone_number("26658359036") == "+26658359036"
        assert format_phone_number("+26658359036") == "+26658359036"
    
    def test_format_phone_number_international(self):
        """Test international phone numbers"""
        assert format_phone_number("+15551234567") == "+15551234567"
        assert format_phone_number("+447700900123") == "+447700900123"
