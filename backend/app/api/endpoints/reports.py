"""
Reports and analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, timedelta, time
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.models import (
    Employee, Department, AttendanceRecord,
    AttendanceStatus, AttendanceFlag
)
from app.schemas.schemas import (
    DailyReportRequest, DailyReportResponse,
    EmployeeAttendanceReport
)
from app.api.endpoints.auth import get_current_employee

router = APIRouter()


@router.post("/daily", response_model=DailyReportResponse)
async def daily_report(
    report_request: DailyReportRequest,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    Generate daily attendance report
    Shows present, absent, late, on-time for a specific date
    """
    target_date = report_request.date.date()
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    # Get department if specified
    department_name = None
    if report_request.department_id:
        result = await db.execute(
            select(Department).where(Department.id == report_request.department_id)
        )
        department = result.scalar_one_or_none()
        if department:
            department_name = department.name
    
    # Total employees (in department if specified)
    query = select(func.count(Employee.id)).where(Employee.is_active == True)
    if report_request.department_id:
        query = query.where(Employee.department_id == report_request.department_id)
    
    result = await db.execute(query)
    total_employees = result.scalar()
    
    # Employees who checked in
    query = select(func.count(AttendanceRecord.id.distinct())).where(
        and_(
            AttendanceRecord.check_in_time >= start_of_day,
            AttendanceRecord.check_in_time <= end_of_day
        )
    )
    if report_request.department_id:
        query = query.join(Employee).where(Employee.department_id == report_request.department_id)
    
    result = await db.execute(query)
    present = result.scalar()
    
    # Absent = total - present
    absent = total_employees - present
    
    # Late arrivals (after 8:15 AM - configurable)
    late_threshold = datetime.combine(target_date, time(8, 15))
    query = select(func.count(AttendanceRecord.id)).where(
        and_(
            AttendanceRecord.check_in_time >= start_of_day,
            AttendanceRecord.check_in_time > late_threshold
        )
    )
    if report_request.department_id:
        query = query.join(Employee).where(Employee.department_id == report_request.department_id)
    
    result = await db.execute(query)
    late = result.scalar()
    
    # On time
    on_time = present - late
    
    # Not checked out yet
    query = select(func.count(AttendanceRecord.id)).where(
        and_(
            AttendanceRecord.check_in_time >= start_of_day,
            AttendanceRecord.check_in_time <= end_of_day,
            AttendanceRecord.check_out_time == None
        )
    )
    if report_request.department_id:
        query = query.join(Employee).where(Employee.department_id == report_request.department_id)
    
    result = await db.execute(query)
    not_checked_out = result.scalar()
    
    # Calculate attendance rate
    attendance_rate = (present / total_employees * 100) if total_employees > 0 else 0
    
    return DailyReportResponse(
        date=report_request.date,
        department_name=department_name,
        total_employees=total_employees,
        present=present,
        absent=absent,
        late=late,
        on_time=on_time,
        not_checked_out=not_checked_out,
        attendance_rate=round(attendance_rate, 2)
    )


@router.get("/employee/{employee_id}")
async def employee_attendance_report(
    employee_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    Get attendance report for a specific employee
    """
    # Verify employee exists
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get all attendance records in date range
    query = select(AttendanceRecord).where(
        and_(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.check_in_time >= start_date,
            AttendanceRecord.check_in_time <= end_date
        )
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Calculate statistics
    total_days = (end_date - start_date).days + 1
    days_present = len(records)
    days_absent = total_days - days_present
    
    # Count late arrivals
    late_threshold_time = time(8, 15)
    days_late = sum(
        1 for record in records 
        if record.check_in_time.time() > late_threshold_time
    )
    
    # Calculate average check-in time
    if records:
        total_minutes = sum(
            record.check_in_time.hour * 60 + record.check_in_time.minute 
            for record in records
        )
        avg_minutes = total_minutes // len(records)
        avg_check_in_time = f"{avg_minutes // 60:02d}:{avg_minutes % 60:02d}"
    else:
        avg_check_in_time = None
    
    attendance_rate = (days_present / total_days * 100) if total_days > 0 else 0
    
    return {
        "employee_id": employee_id,
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "employee_number": employee.employee_number,
        "department": employee.department.name if employee.department else None,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "days_present": days_present,
        "days_absent": days_absent,
        "days_late": days_late,
        "attendance_rate": round(attendance_rate, 2),
        "average_check_in_time": avg_check_in_time,
        "records": [
            {
                "date": record.check_in_time.date(),
                "check_in": record.check_in_time.time(),
                "check_out": record.check_out_time.time() if record.check_out_time else None,
                "hours_worked": (
                    (record.check_out_time - record.check_in_time).total_seconds() / 3600
                    if record.check_out_time else None
                ),
                "status": record.status.value
            }
            for record in records
        ]
    }


@router.get("/monthly")
async def monthly_report(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    department_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    Generate monthly attendance summary
    """
    # Get all attendance for the month
    query = select(AttendanceRecord).where(
        and_(
            extract('year', AttendanceRecord.check_in_time) == year,
            extract('month', AttendanceRecord.check_in_time) == month
        )
    )
    
    if department_id:
        query = query.join(Employee).where(Employee.department_id == department_id)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Group by day
    daily_stats = {}
    for record in records:
        day = record.check_in_time.day
        if day not in daily_stats:
            daily_stats[day] = {
                "date": record.check_in_time.date(),
                "present": 0,
                "late": 0
            }
        
        daily_stats[day]["present"] += 1
        
        if record.check_in_time.time() > time(8, 15):
            daily_stats[day]["late"] += 1
    
    return {
        "year": year,
        "month": month,
        "total_records": len(records),
        "daily_breakdown": list(daily_stats.values())
    }


@router.get("/flags")
async def get_attendance_flags(
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    Get attendance flags (anomalies, violations)
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
            "created_at": flag.created_at
        }
        for flag in flags
    ]


@router.get("/summary")
async def attendance_summary(
    department_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    Get overall attendance summary (today + this week + this month)
    """
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), time.min)
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    
    async def get_count(start_date):
        query = select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.check_in_time >= start_date
        )
        if department_id:
            query = query.join(Employee).where(Employee.department_id == department_id)
        result = await db.execute(query)
        return result.scalar()
    
    today_count = await get_count(today_start)
    week_count = await get_count(week_start)
    month_count = await get_count(month_start)
    
    # Total active employees
    query = select(func.count(Employee.id)).where(Employee.is_active == True)
    if department_id:
        query = query.where(Employee.department_id == department_id)
    result = await db.execute(query)
    total_employees = result.scalar()
    
    return {
        "today": {
            "present": today_count,
            "total_employees": total_employees,
            "rate": round((today_count / total_employees * 100) if total_employees > 0 else 0, 2)
        },
        "this_week": {
            "check_ins": week_count
        },
        "this_month": {
            "check_ins": month_count
        }
    }