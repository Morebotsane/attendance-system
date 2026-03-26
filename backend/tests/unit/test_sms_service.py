"""
Unit tests for SMS service with dual provider support
"""
import pytest
from unittest.mock import Mock, patch
from app.services.sms_service import sms_service


class TestSMSService:
    """Test SMS service with Africa's Talking and Twilio"""
    
    @patch('app.services.sms_service.sms_service.at_sms')
    @patch('app.services.sms_service.sms_service.twilio_client')
    def test_send_sms_twilio_success(self, mock_twilio, mock_at):
        """Test successful SMS via Twilio"""
        # Mock Twilio response
        mock_message = Mock()
        mock_message.sid = "SM_test123"
        mock_message.status = "queued"
        mock_twilio.messages.create.return_value = mock_message
        
        result = sms_service.send_sms("+26612345678", "Test message", provider="twilio")
        
        assert result["success"] is True
        assert result["provider"] == "twilio"
        assert result["message_id"] == "SM_test123"
    
    def test_format_phone_number(self):
        """Test phone number formatting"""
        from app.templates.notifications import format_phone_number
        
        # Test Lesotho number
        assert format_phone_number("58359036") == "+26658359036"
        assert format_phone_number("26658359036") == "+26658359036"
        assert format_phone_number("+26658359036") == "+26658359036"
        
        # Test already formatted
        assert format_phone_number("+1234567890") == "+1234567890"
