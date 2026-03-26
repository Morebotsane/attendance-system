"""
Attendance endpoints for check-in/check-out operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
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
from app.schemas.schemas import (
    AttendanceRecordResponse,
    CheckInRequest, CheckOutRequest
)
from app.services.qr_service import qr_service
from app.services.geofence_service import geofence_service
from app.services.photo_service import photo_service

router = APIRouter()


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


@router.post("/check-in", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    qr_code_data: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    device_id: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Process employee check-in with QR code, geolocation, and photo
    
    Steps:
    1. Validate QR code and get employee
    2. Verify geofence (employee is at authorized location)
    3. Check for duplicate check-in
    4. Process and store photo
    5. Create attendance record
    6. Log action in audit trail
    """
    
    # 1. Decode and validate QR code
    qr_result = qr_service.decode_qr_data(qr_code_data)
    
    if not qr_result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid QR code"
        )
    
    employee_id = qr_result["employee_id"]
    
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
            # Create flag for geofence violation
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
    # Serialize validation metadata to ensure JSON compatibility
    validation_metadata = serialize_for_json({
        "geofence": geo_validation,
        "qr_validation": qr_result
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
    
    return attendance_record


@router.post("/check-out", response_model=AttendanceRecordResponse)
async def check_out(
    qr_code_data: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    device_id: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Process employee check-out"""
    
    # Decode QR code
    qr_result = qr_service.decode_qr_data(qr_code_data)
    
    if not qr_result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid QR code"
        )
    
    employee_id = qr_result["employee_id"]
    
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