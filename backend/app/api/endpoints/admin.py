"""
Admin endpoints - QR generation, flags management, audit logs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models.models import (
    Employee, AttendanceFlag, AttendanceAuditLog
)
from app.schemas.schemas import QRCodeResponse
from app.api.endpoints.auth import get_current_admin
from app.services.qr_service import qr_service

router = APIRouter()


@router.post("/generate-qr/{employee_id}", response_model=QRCodeResponse)
async def generate_employee_qr(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Generate/Regenerate QR code for an employee
    Returns QR code data, base64 image, and URL
    """
    # Get employee
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Generate QR code
    qr_data = qr_service.generate_employee_qr_data(str(employee.id))
    qr_base64 = qr_service.generate_qr_base64(qr_data)
    qr_url = qr_service.save_qr_image(qr_data, str(employee.id))
    
    # Update employee record
    employee.qr_code_data = qr_data
    employee.qr_code_image_url = qr_url
    await db.commit()
    
    return QRCodeResponse(
        employee_id=employee.id,
        qr_code_data=qr_data,
        qr_code_image_base64=qr_base64,
        qr_code_image_url=qr_url
    )


@router.get("/qr/{employee_id}/download")
async def download_qr_code(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Download QR code as PNG image
    """
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee or not employee.qr_code_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    # Generate image
    qr_image = qr_service.generate_qr_image(employee.qr_code_data)
    
    # Return as downloadable file
    return Response(
        content=qr_image,
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=qr_{employee.employee_number}.png"
        }
    )


@router.get("/flags")
async def list_flags(
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    List all attendance flags with filtering
    """
    query = select(AttendanceFlag)
    
    if is_resolved is not None:
        query = query.where(AttendanceFlag.is_resolved == is_resolved)
    
    if severity:
        query = query.where(AttendanceFlag.severity == severity)
    
    query = query.offset(skip).limit(limit).order_by(AttendanceFlag.created_at.desc())
    
    result = await db.execute(query)
    flags = result.scalars().all()
    
    return [
        {
            "id": flag.id,
            "attendance_record_id": flag.attendance_record_id,
            "flag_type": flag.flag_type.value,
            "severity": flag.severity,
            "description": flag.description,
            "is_resolved": flag.is_resolved,
            "resolved_by": flag.resolved_by,
            "resolved_at": flag.resolved_at,
            "created_at": flag.created_at
        }
        for flag in flags
    ]


@router.post("/flags/{flag_id}/resolve")
async def resolve_flag(
    flag_id: UUID,
    resolution_notes: str,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Mark a flag as resolved
    """
    result = await db.execute(
        select(AttendanceFlag).where(AttendanceFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flag not found"
        )
    
    if flag.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flag is already resolved"
        )
    
    # Mark as resolved
    flag.is_resolved = True
    flag.resolved_by = current_admin.id
    flag.resolved_at = datetime.utcnow()
    flag.resolution_notes = resolution_notes
    
    await db.commit()
    
    return {
        "message": "Flag resolved successfully",
        "flag_id": flag_id,
        "resolved_by": f"{current_admin.first_name} {current_admin.last_name}"
    }


@router.get("/audit-log")
async def get_audit_log(
    employee_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Get attendance audit log with filtering
    """
    query = select(AttendanceAuditLog)
    
    if employee_id:
        query = query.where(AttendanceAuditLog.employee_id == employee_id)
    
    if action:
        query = query.where(AttendanceAuditLog.action == action)
    
    if start_date:
        query = query.where(AttendanceAuditLog.timestamp >= start_date)
    
    if end_date:
        query = query.where(AttendanceAuditLog.timestamp <= end_date)
    
    query = query.offset(skip).limit(limit).order_by(AttendanceAuditLog.timestamp.desc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "employee_id": log.employee_id,
            "attendance_record_id": log.attendance_record_id,
            "action": log.action,
            "timestamp": log.timestamp,
            "latitude": log.latitude,
            "longitude": log.longitude,
            "ip_address": log.ip_address,
            "photo_url": log.photo_url,
            "validation_status": log.validation_status
        }
        for log in logs
    ]


@router.get("/stats")
async def system_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Get overall system statistics
    """
    # Total employees
    result = await db.execute(select(func.count(Employee.id)))
    total_employees = result.scalar()
    
    # Active employees
    result = await db.execute(
        select(func.count(Employee.id)).where(Employee.is_active == True)
    )
    active_employees = result.scalar()
    
    # Total flags
    result = await db.execute(select(func.count(AttendanceFlag.id)))
    total_flags = result.scalar()
    
    # Unresolved flags
    result = await db.execute(
        select(func.count(AttendanceFlag.id)).where(
            AttendanceFlag.is_resolved == False
        )
    )
    unresolved_flags = result.scalar()
    
    # Today's check-ins
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(AttendanceAuditLog.id)).where(
            AttendanceAuditLog.action == "check_in",
            AttendanceAuditLog.timestamp >= today_start
        )
    )
    today_checkins = result.scalar()
    
    return {
        "employees": {
            "total": total_employees,
            "active": active_employees,
            "inactive": total_employees - active_employees
        },
        "flags": {
            "total": total_flags,
            "unresolved": unresolved_flags,
            "resolved": total_flags - unresolved_flags
        },
        "today": {
            "check_ins": today_checkins,
            "attendance_rate": round(
                (today_checkins / active_employees * 100) if active_employees > 0 else 0,
                2
            )
        }
    }


@router.post("/bulk-qr-generate")
async def bulk_generate_qr(
    department_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Bulk generate QR codes for all employees (or department)
    Useful for initial setup
    """
    query = select(Employee).where(Employee.is_active == True)
    
    if department_id:
        query = query.where(Employee.department_id == department_id)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    generated = 0
    for employee in employees:
        qr_data = qr_service.generate_employee_qr_data(str(employee.id))
        qr_url = qr_service.save_qr_image(qr_data, str(employee.id))
        
        employee.qr_code_data = qr_data
        employee.qr_code_image_url = qr_url
        generated += 1
    
    await db.commit()
    
    return {
        "message": f"Generated QR codes for {generated} employees",
        "count": generated
    }