"""
SMS Service with dual provider support (Africa's Talking + Twilio fallback)
"""
from typing import Dict, Any, Optional
import logging
from app.core.config import settings
import africastalking
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        # Africa's Talking configuration
        self.at_username = getattr(settings, "AFRICAS_TALKING_USERNAME", "sandbox")
        self.at_api_key = getattr(settings, "AFRICAS_TALKING_API_KEY", "")
        
        # Twilio configuration (backup)
        self.twilio_account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.twilio_phone = getattr(settings, "TWILIO_PHONE_NUMBER", "")
        
        # Initialize Africa's Talking
        if self.at_api_key:
            try:
                africastalking.initialize(self.at_username, self.at_api_key)
                self.at_sms = africastalking.SMS
                logger.info("Africa's Talking initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Africa's Talking: {e}")
                self.at_sms = None
        else:
            self.at_sms = None
            logger.warning("Africa's Talking not configured")
        
        # Initialize Twilio
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
                self.twilio_client = None
        else:
            self.twilio_client = None
            logger.warning("Twilio not configured")
    
    def send_sms(
        self,
        phone_number: str,
        message: str,
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """
        Send SMS with automatic provider fallback
        
        Args:
            phone_number: Phone number in E.164 format (e.g., +26612345678)
            message: SMS message content (max 160 chars recommended)
            provider: "africas_talking", "twilio", or "auto"
        
        Returns:
            Dict with status, provider used, and message details
        """
        # Validate phone number format
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        
        # Try providers based on preference
        if provider == "auto" or provider == "africas_talking":
            result = self._send_via_africas_talking(phone_number, message)
            if result["success"]:
                return result
            
            # Fallback to Twilio if Africa's Talking fails
            if provider == "auto":
                logger.warning("Africa's Talking failed, falling back to Twilio")
                return self._send_via_twilio(phone_number, message)
            else:
                return result
        
        elif provider == "twilio":
            return self._send_via_twilio(phone_number, message)
        
        else:
            return {
                "success": False,
                "provider": "none",
                "error": f"Invalid provider: {provider}"
            }
    
    def _send_via_africas_talking(
        self,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS via Africa's Talking"""
        if not self.at_sms:
            return {
                "success": False,
                "provider": "africas_talking",
                "error": "Africa's Talking not configured"
            }
        
        try:
            # Send SMS
            response = self.at_sms.send(message, [phone_number])
            
            logger.info(f"Africa's Talking response: {response}")
            
            # Parse response
            if response['SMSMessageData']['Recipients']:
                recipient = response['SMSMessageData']['Recipients'][0]
                
                if recipient['status'] == 'Success':
                    return {
                        "success": True,
                        "provider": "africas_talking",
                        "message_id": recipient.get('messageId'),
                        "cost": recipient.get('cost'),
                        "phone": phone_number
                    }
                else:
                    return {
                        "success": False,
                        "provider": "africas_talking",
                        "error": recipient.get('status'),
                        "phone": phone_number
                    }
            else:
                return {
                    "success": False,
                    "provider": "africas_talking",
                    "error": "No recipients in response"
                }
        
        except Exception as e:
            logger.error(f"Africa's Talking SMS failed: {str(e)}")
            return {
                "success": False,
                "provider": "africas_talking",
                "error": str(e)
            }
    
    def _send_via_twilio(
        self,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """Send SMS via Twilio (backup)"""
        if not self.twilio_client:
            return {
                "success": False,
                "provider": "twilio",
                "error": "Twilio not configured"
            }
        
        try:
            # Send SMS
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone_number
            )
            
            logger.info(f"Twilio message sent: {message_obj.sid}")
            
            return {
                "success": True,
                "provider": "twilio",
                "message_id": message_obj.sid,
                "status": message_obj.status,
                "phone": phone_number
            }
        
        except TwilioRestException as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return {
                "success": False,
                "provider": "twilio",
                "error": str(e),
                "code": e.code
            }
        
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return {
                "success": False,
                "provider": "twilio",
                "error": str(e)
            }
    
    def get_balance(self, provider: str = "africas_talking") -> Dict[str, Any]:
        """Get SMS balance from provider"""
        if provider == "africas_talking" and self.at_sms:
            try:
                application = africastalking.Application
                balance = application.fetch_application_data()
                return {
                    "success": True,
                    "provider": "africas_talking",
                    "balance": balance.get("UserData", {}).get("balance")
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Provider {provider} not supported"}


# Singleton instance
sms_service = SMSService()
