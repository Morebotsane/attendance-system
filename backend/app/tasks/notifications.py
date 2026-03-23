"""
Background tasks for sending notifications
"""
from celery import Task
from app.core.celery_app import celery_app
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotificationTask(Task):
    """Base task with retry logic"""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


@celery_app.task(base=NotificationTask, name="send_sms_task")
def send_sms_task(phone_number: str, message: str, provider: str = "auto") -> Dict[str, Any]:
    """
    Send SMS notification with automatic fallback
    
    Args:
        phone_number: Recipient phone number (E.164 format)
        message: SMS message content
        provider: "africas_talking", "twilio", or "auto" for automatic fallback
    
    Returns:
        Dict with status and details
    """
    from app.services.sms_service import sms_service
    
    try:
        logger.info(f"Sending SMS to {phone_number} via {provider}")
        result = sms_service.send_sms(phone_number, message, provider)
        logger.info(f"SMS sent successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise


@celery_app.task(base=NotificationTask, name="send_email_task")
def send_email_task(
    to_email: str,
    subject: str,
    body: str,
    html_body: str = None
) -> Dict[str, Any]:
    """
    Send email notification
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
    
    Returns:
        Dict with status and details
    """
    from app.services.email_service import email_service
    
    try:
        logger.info(f"Sending email to {to_email}")
        result = email_service.send_email(to_email, subject, body, html_body)
        logger.info(f"Email sent successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


@celery_app.task(name="send_bulk_sms_task")
def send_bulk_sms_task(recipients: list, message: str) -> Dict[str, Any]:
    """
    Send SMS to multiple recipients (with rate limiting)
    
    Args:
        recipients: List of phone numbers
        message: SMS message content
    
    Returns:
        Dict with success/failure counts
    """
    from app.services.sms_service import sms_service
    import time
    
    results = {"success": 0, "failed": 0, "details": []}
    
    for phone in recipients:
        try:
            result = sms_service.send_sms(phone, message)
            results["success"] += 1
            results["details"].append({"phone": phone, "status": "sent"})
            time.sleep(0.1)  # Rate limiting: 10 SMS/second max
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"phone": phone, "status": "failed", "error": str(e)})
            logger.error(f"Failed to send SMS to {phone}: {str(e)}")
    
    return results
