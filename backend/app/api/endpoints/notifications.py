"""
Notification endpoints for testing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.models.models import Employee
from app.api.endpoints.auth import get_current_admin
from app.tasks.notifications import send_sms_task, send_email_task
from app.templates.notifications import templates, format_phone_number
from app.middleware.rate_limiter import limiter, check_sms_budget, check_employee_sms_limit
from slowapi import Limiter
from fastapi import Request

router = APIRouter()


class SendSMSRequest(BaseModel):
    phone_number: str
    message: str
    provider: str = "auto"


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    html_body: str = None


@router.post("/test-sms")
@limiter.limit("5/minute")  # Rate limit: 5 SMS tests per minute
async def test_sms(
    request: Request,
    sms_request: SendSMSRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Test SMS sending (Admin only)"""
    
    # Check SMS budget
    if not await check_sms_budget():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily SMS budget exceeded"
        )
    
    # Format phone number
    phone = format_phone_number(sms_request.phone_number)
    
    # Send SMS via Celery task
    task = send_sms_task.delay(phone, sms_request.message, sms_request.provider)
    
    return {
        "message": "SMS queued for sending",
        "task_id": task.id,
        "phone": phone,
        "provider": sms_request.provider
    }


@router.post("/test-email")
@limiter.limit("10/minute")  # Rate limit: 10 email tests per minute
async def test_email(
    request: Request,
    email_request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Test email sending (Admin only)"""
    
    # Send email via Celery task
    task = send_email_task.delay(
        email_request.to_email,
        email_request.subject,
        email_request.body,
        email_request.html_body
    )
    
    return {
        "message": "Email queued for sending",
        "task_id": task.id,
        "to": email_request.to_email
    }


@router.get("/task-status/{task_id}")
async def get_task_status(
    task_id: str,
    current_admin: Employee = Depends(get_current_admin)
):
    """Get status of a background task"""
    from app.core.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
