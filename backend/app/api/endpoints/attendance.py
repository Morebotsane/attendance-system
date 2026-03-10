"""
Attendance endpoints for check-in, check-out, and attendance queries
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.schemas.schemas import (
    CheckInRequest, CheckInResponse,
    CheckOutRequest, CheckOutResponse,
    AttendanceRecordResponse
)
from app.models.models import (
    Employee, AttendanceRecord, AttendanceAuditLog,
    AttendanceFlag, AttendanceStatus, FlagType
)
from app.services.qr_service import qr_service
from app.services.geofence_service import geofence_service
from app.services.photo_service import photo_service


router = APIRouter()


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(
    request: CheckInRequest,
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
    qr_result = qr_service.decode_qr_data(request.qr_code_data)
    
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
            user_lat=request.latitude,
            user_lon=request.longitude
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
    now = datetime.utcnow()
    
    attendance = AttendanceRecord(
        employee_id=employee.id,
        check_in_time=now,
        check_in_latitude=request.latitude,
        check_in_longitude=request.longitude,
        check_in_photo_url=photo_url,
        check_in_device_id=request.device_id,
        status=AttendanceStatus.ACTIVE,
        validation_metadata={
            "geofence": geo_validation,
            "qr_generated_at": qr_result.get("generated_at").isoformat() if qr_result.get("generated_at") else None
        }
    )
    
    db.add(attendance)
    await db.commit()
    await db.refresh(attendance)
    
    # 6. Create audit log
    audit_log = AttendanceAuditLog(
        attendance_record_id=attendance.id,
        employee_id=employee.id,
        action="check_in",
        timestamp=now,
        latitude=request.latitude,
        longitude=request.longitude,
        photo_url=photo_url,
        validation_status={"geofence": geo_validation}
    )
    
    db.add(audit_log)
    await db.commit()
    
    return CheckInResponse(
        success=True,
        message=f"Welcome, {employee.first_name}! Check-in successful.",
        attendance_id=attendance.id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        check_in_time=attendance.check_in_time,
        validation_results=attendance.validation_metadata
    )


@router.post("/check-out", response_model=CheckOutResponse)
async def check_out(
    request: CheckOutRequest,
    photo: UploadFile = File(...),
    employee_id: uuid.UUID = None,  # Get from auth token in production
    db: AsyncSession = Depends(get_db)
):
    """
    Process employee check-out with geolocation and photo
    """
    
    # Get today's active attendance record
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    result = await db.execute(
        select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.check_in_time >= today_start,
                AttendanceRecord.check_in_time < today_end,
                AttendanceRecord.status == AttendanceStatus.ACTIVE,
                AttendanceRecord.check_out_time == None
            )
        )
    )
    attendance = result.scalar_one_or_none()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active check-in found for today"
        )
    
    # Get employee
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    # Validate geofence (optional for check-out)
    if employee.department_id:
        geo_validation = await geofence_service.validate_location(
            db=db,
            department_id=str(employee.department_id),
            user_lat=request.latitude,
            user_lon=request.longitude
        )
    else:
        geo_validation = {"valid": True}
    
    # Store photo
    photo_url = await photo_service.store_photo(
        photo=photo,
        employee_id=str(employee.id),
        photo_type="check_out"
    )
    
    # Update attendance record
    now = datetime.utcnow()
    attendance.check_out_time = now
    attendance.check_out_latitude = request.latitude
    attendance.check_out_longitude = request.longitude
    attendance.check_out_photo_url = photo_url
    attendance.check_out_device_id = request.device_id
    attendance.status = AttendanceStatus.COMPLETED
    
    # Calculate total hours
    total_hours = (now - attendance.check_in_time).total_seconds() / 3600
    
    await db.commit()
    await db.refresh(attendance)
    
    # Create audit log
    audit_log = AttendanceAuditLog(
        attendance_record_id=attendance.id,
        employee_id=employee.id,
        action="check_out",
        timestamp=now,
        latitude=request.latitude,
        longitude=request.longitude,
        photo_url=photo_url,
        validation_status={"geofence": geo_validation}
    )
    
    db.add(audit_log)
    await db.commit()
    
    return CheckOutResponse(
        success=True,
        message=f"Goodbye, {employee.first_name}! Check-out successful.",
        attendance_id=attendance.id,
        check_out_time=attendance.check_out_time,
        total_hours=round(total_hours, 2),
        validation_results={"geofence": geo_validation}
    )


@router.get("/today", response_model=List[AttendanceRecordResponse])
async def get_today_attendance(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all attendance records for today
    Optionally filter by department
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    query = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.check_in_time >= today_start,
            AttendanceRecord.check_in_time < today_end
        )
    )
    
    if department_id:
        # Join with Employee to filter by department
        query = query.join(Employee).where(Employee.department_id == department_id)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return records


async def create_flag(
    db: AsyncSession,
    attendance_id: Optional[uuid.UUID],
    flag_type: FlagType,
    description: str,
    severity: str = "medium"
):
    """
    Helper function to create attendance flag
    """
    flag = AttendanceFlag(
        attendance_record_id=attendance_id,
        flag_type=flag_type,
        severity=severity,
        description=description
    )
    
    db.add(flag)
    await db.commit()
    
    return flag
