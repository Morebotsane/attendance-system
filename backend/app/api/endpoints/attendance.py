"""
Attendance endpoints for check-in/check-out operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
import uuid
import json

from app.db.session import get_db
from app.models.models import (
    Employee, AttendanceRecord, AttendanceAuditLog, 
    AttendanceStatus, FlagType, AttendanceFlag
)
from app.models.kiosk_session import KioskSession, SessionStatus
from app.schemas.schemas import (
    AttendanceRecordResponse,
    CheckInRequest, CheckOutRequest
)
from app.services.qr_service import qr_service
from app.services.geofence_service import geofence_service
from app.services.photo_service import photo_service
from app.services.queue_service import queue_service
from app.tasks.notifications import send_sms_task, send_email_task
from app.templates.notifications import templates, format_phone_number
from app.api.endpoints.auth import decode_token

router = APIRouter()
security = HTTPBearer(auto_error=False)


def serialize_for_json(obj):
    """Convert datetime objects to ISO format strings for JSON storage"""
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


async def create_flag(
    db: AsyncSession,
    attendance_id: uuid.UUID | None,
    flag_type: FlagType,
    description: str,
    severity: str = "medium"
):
    """Helper to create attendance flags"""
    flag = AttendanceFlag(
        attendance_record_id=attendance_id,
        flag_type=flag_type,
        description=description,
        severity=severity,
        is_resolved=False
    )
    db.add(flag)
    await db.commit()
    return flag


def _decrypt_session_qr(qr_data: str) -> dict:
    """Decrypt session QR to get session_id"""
    import base64
    import hashlib
    from cryptography.fernet import Fernet
    from app.core.config import settings
    
    try:
        encrypted = base64.urlsafe_b64decode(qr_data.encode())
        
        # Generate Fernet key from SECRET_KEY (same as queue_service)
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        fernet = Fernet(fernet_key)
        
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())
    except Exception as e:
        return {"error": str(e)}


@router.post("/check-in", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    qr_code_data: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    device_id: str = Form(...),
    photo: UploadFile = File(...),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Process employee check-in
    
    NOW SUPPORTS 3 QR FLOWS:
    1. SESSION QR (new) - scanned from kiosk after joining queue (requires JWT)
    2. KIOSK TOKEN (old) - daily rotating token (requires JWT)
    3. EMPLOYEE BADGE QR (legacy) - employee's personal badge (no JWT required)
    
    Steps:
    1. Validate QR code and get employee
    2. Verify geofence (employee is at authorized location)
    3. Check for duplicate check-in
    4. Process and store photo
    5. Create attendance record
    6. Log action in audit trail
    7. Send SMS + Email notifications
    8. Complete session (if session-based)
    """
    
    employee_id = None
    qr_validation_type = None
    session_id = None
    
    # PRIORITY 1: Try session QR validation (NEW FLOW)
    session_data = _decrypt_session_qr(qr_code_data)
    if "session_id" in session_data and not session_data.get("error"):
        # This is a session QR!
        session_id = session_data["session_id"]
        
        # MUST have JWT for session-based check-in
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session-based check-in requires authentication. Please log in."
            )
        
        # Decode JWT to get employee_id
        try:
            token = credentials.credentials
            payload = decode_token(token)
            employee_id = payload.get("sub")
            if not employee_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )
        
        # Validate session exists and belongs to this employee
        session_result = await db.execute(
            select(KioskSession).where(KioskSession.id == uuid.UUID(session_id))
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Validate session belongs to this employee
        if str(session.employee_id) != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to you"
            )
        
        # Validate session is ACTIVE (their turn)
        if session.status != SessionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is {session.status.value}. Wait for your turn."
            )
        
        # Validate session not expired
        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session expired. Please join queue again."
            )
        
        qr_validation_type = "session_qr"
        
    else:
        # PRIORITY 2: Try kiosk token validation (OLD FLOW)
        kiosk_validation = qr_service.validate_kiosk_token(qr_code_data, "checkin")
        
        if kiosk_validation["valid"]:
            # Valid kiosk token - requires JWT
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Kiosk check-in requires authentication. Please log in to the app."
                )
            
            # Decode JWT to get employee_id
            try:
                token = credentials.credentials
                payload = decode_token(token)
                employee_id = payload.get("sub")
                if not employee_id:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {str(e)}"
                )
            
            qr_validation_type = "kiosk_token"
            
        else:
            # PRIORITY 3: Try employee badge QR (LEGACY FLOW - backward compatible)
            badge_qr = qr_service.decode_qr_data(qr_code_data)
            
            if not badge_qr.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid QR code. Please scan a valid session QR, kiosk QR, or employee badge."
                )
            
            employee_id = badge_qr["employee_id"]
            qr_validation_type = "employee_badge"
    
    # Get employee
    result = await db.execute(
        select(Employee).where(
            and_(
                Employee.id == uuid.UUID(employee_id),
                Employee.is_active == True
            )
        )
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found or inactive"
        )
    
    # 2. Validate geofence
    if employee.department_id:
        geo_validation = await geofence_service.validate_location(
            db=db,
            department_id=str(employee.department_id),
            user_lat=latitude,
            user_lon=longitude
        )
        
        if not geo_validation["valid"]:
            await create_flag(
                db=db,
                attendance_id=None,
                flag_type=FlagType.GEOFENCE_VIOLATION,
                description=f"Check-in attempted from {geo_validation['distance_meters']}m away. {geo_validation.get('reason', '')}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=geo_validation.get('reason', 'You are not within the authorized check-in area')
            )
    else:
        geo_validation = {"valid": True, "reason": "No department assigned"}
    
    # 3. Check for duplicate check-in
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.check_in_time >= today_start,
                AttendanceRecord.check_in_time < today_end,
                AttendanceRecord.status.in_([AttendanceStatus.ACTIVE, AttendanceStatus.COMPLETED])
            )
        )
    )
    existing_record = result.scalar_one_or_none()
    
    if existing_record and existing_record.check_in_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already checked in today at {existing_record.check_in_time.strftime('%H:%M:%S')}"
        )
    
    # 4. Store photo
    try:
        photo_url = await photo_service.store_photo(
            photo=photo,
            employee_id=str(employee.id),
            photo_type="check_in"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store photo: {str(e)}"
        )
    
    # 5. Create attendance record
    validation_metadata = serialize_for_json({
        "geofence": geo_validation,
        "qr_validation": {
            "type": qr_validation_type,
            "session_id": session_id
        }
    })
    
    attendance_record = AttendanceRecord(
        employee_id=employee.id,
        check_in_time=datetime.utcnow(),
        check_in_latitude=latitude,
        check_in_longitude=longitude,
        check_in_photo_url=photo_url,
        check_in_device_id=device_id,
        status=AttendanceStatus.ACTIVE,
        validation_metadata=validation_metadata
    )
    
    db.add(attendance_record)
    await db.flush()
    
    # 6. Create audit log
    audit_log = AttendanceAuditLog(
        attendance_record_id=attendance_record.id,
        employee_id=employee.id,
        action="check_in",
        timestamp=datetime.utcnow(),
        latitude=latitude,
        longitude=longitude,
        photo_url=photo_url,
        validation_status=serialize_for_json(geo_validation)
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(attendance_record)
    
    # 7. Complete session if session-based
    if session_id:
        await queue_service.complete_session(db, session_id, employee_id)
    
    # 8. Send SMS notification (async, non-blocking)
    if employee.phone:
        try:
            phone = format_phone_number(employee.phone)
            notification = templates.check_in_success(
                employee_name=f"{employee.first_name} {employee.last_name}",
                time=attendance_record.check_in_time.strftime("%H:%M")
            )
            send_sms_task.delay(phone, notification["sms"])
        except Exception as e:
            print(f"Failed to send check-in SMS: {e}")
    
    # 9. Send email notification (async, non-blocking)
    if employee.email:
        try:
            notification = templates.check_in_success(
                employee_name=f"{employee.first_name} {employee.last_name}",
                time=attendance_record.check_in_time.strftime("%H:%M")
            )
            send_email_task.delay(
                to_email=employee.email,
                subject=notification["subject"],
                body=notification["email"],
                html_body=notification["html"]
            )
        except Exception as e:
            print(f"Failed to send check-in email: {e}")
    
    return attendance_record


@router.post("/check-out", response_model=AttendanceRecordResponse)
async def check_out(
    qr_code_data: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    device_id: str = Form(...),
    photo: UploadFile = File(...),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Process employee check-out
    
    SUPPORTS 3 QR FLOWS (same as check-in):
    1. SESSION QR - scanned from kiosk after joining queue
    2. KIOSK TOKEN - daily rotating token
    3. EMPLOYEE BADGE QR - employee's personal badge
    """
    
    employee_id = None
    qr_validation_type = None
    session_id = None
    
    # PRIORITY 1: Try session QR validation
    session_data = _decrypt_session_qr(qr_code_data)
    if "session_id" in session_data and not session_data.get("error"):
        session_id = session_data["session_id"]
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session-based check-out requires authentication."
            )
        
        try:
            token = credentials.credentials
            payload = decode_token(token)
            employee_id = payload.get("sub")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        
        # Validate session
        session_result = await db.execute(
            select(KioskSession).where(KioskSession.id == uuid.UUID(session_id))
        )
        session = session_result.scalar_one_or_none()
        
        if not session or str(session.employee_id) != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session")
        
        if session.status != SessionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wait for your turn")
        
        qr_validation_type = "session_qr"
        
    else:
        # PRIORITY 2: Try kiosk token
        kiosk_validation = qr_service.validate_kiosk_token(qr_code_data, "checkout")
        
        if kiosk_validation["valid"]:
            if not credentials:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
            
            try:
                token = credentials.credentials
                payload = decode_token(token)
                employee_id = payload.get("sub")
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
            
            qr_validation_type = "kiosk_token"
            
        else:
            # PRIORITY 3: Try employee badge QR
            badge_qr = qr_service.decode_qr_data(qr_code_data)
            
            if not badge_qr.get("valid"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR code")
            
            employee_id = badge_qr["employee_id"]
            qr_validation_type = "employee_badge"
    
    # Find active attendance record
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == uuid.UUID(employee_id),
                AttendanceRecord.check_in_time >= today_start,
                AttendanceRecord.status == AttendanceStatus.ACTIVE
            )
        )
    )
    attendance_record = result.scalar_one_or_none()
    
    if not attendance_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active check-in found for today"
        )
    
    # Store photo
    try:
        photo_url = await photo_service.store_photo(
            photo=photo,
            employee_id=str(employee_id),
            photo_type="check_out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store photo: {str(e)}"
        )
    
    # Update record
    attendance_record.check_out_time = datetime.utcnow()
    attendance_record.check_out_latitude = latitude
    attendance_record.check_out_longitude = longitude
    attendance_record.check_out_photo_url = photo_url
    attendance_record.check_out_device_id = device_id
    attendance_record.status = AttendanceStatus.COMPLETED
    
    # Create audit log
    audit_log = AttendanceAuditLog(
        attendance_record_id=attendance_record.id,
        employee_id=uuid.UUID(employee_id),
        action="check_out",
        timestamp=datetime.utcnow(),
        latitude=latitude,
        longitude=longitude,
        photo_url=photo_url
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(attendance_record)
    
    # Complete session if session-based
    if session_id:
        await queue_service.complete_session(db, session_id, employee_id)
    
    # Get employee for notification
    emp_result = await db.execute(
        select(Employee).where(Employee.id == uuid.UUID(employee_id))
    )
    employee = emp_result.scalar_one_or_none()
    
    # Calculate hours worked
    if attendance_record.check_in_time and attendance_record.check_out_time:
        time_diff = attendance_record.check_out_time - attendance_record.check_in_time
        hours_worked = time_diff.total_seconds() / 3600
    else:
        hours_worked = 0
    
    # Send notifications
    if employee and employee.phone:
        try:
            phone = format_phone_number(employee.phone)
            notification = templates.check_out_success(
                employee_name=f"{employee.first_name} {employee.last_name}",
                time=attendance_record.check_out_time.strftime("%H:%M"),
                hours_worked=hours_worked
            )
            send_sms_task.delay(phone, notification["sms"])
        except Exception as e:
            print(f"Failed to send check-out SMS: {e}")
    
    if employee and employee.email:
        try:
            notification = templates.check_out_success(
                employee_name=f"{employee.first_name} {employee.last_name}",
                time=attendance_record.check_out_time.strftime("%H:%M"),
                hours_worked=hours_worked
            )
            send_email_task.delay(
                to_email=employee.email,
                subject=notification["subject"],
                body=notification["email"],
                html_body=notification["html"]
            )
        except Exception as e:
            print(f"Failed to send check-out email: {e}")
    
    return attendance_record


@router.get("/today", response_model=list[AttendanceRecordResponse])
async def get_today_attendance(
    db: AsyncSession = Depends(get_db)
):
    """Get all attendance records for today"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.check_in_time >= today_start,
                AttendanceRecord.check_in_time < today_end
            )
        ).order_by(AttendanceRecord.check_in_time.desc())
    )
    
    records = result.scalars().all()
    return records
