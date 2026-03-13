"""
Department management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.models import Department, Employee
from app.schemas.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse
)
from app.api.endpoints.auth import get_current_employee, get_current_admin

router = APIRouter()


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Create new department (Admin only)"""
    # Check if code already exists
    result = await db.execute(
        select(Department).where(Department.code == department_data.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    
    # Create department
    new_department = Department(**department_data.model_dump())
    db.add(new_department)
    await db.commit()
    await db.refresh(new_department)
    
    return DepartmentResponse.model_validate(new_department)


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """List all departments with pagination"""
    query = select(Department).offset(skip).limit(limit)
    result = await db.execute(query)
    departments = result.scalars().all()
    
    return [DepartmentResponse.model_validate(dept) for dept in departments]


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get department by ID"""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return DepartmentResponse.model_validate(department)


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    department_data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Update department (Admin only)"""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Update fields
    update_data = department_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)
    
    await db.commit()
    await db.refresh(department)
    
    return DepartmentResponse.model_validate(department)


@router.delete("/{department_id}")
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Delete department (Admin only)"""
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has employees
    result = await db.execute(
        select(func.count(Employee.id)).where(Employee.department_id == department_id)
    )
    employee_count = result.scalar()
    
    if employee_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department with {employee_count} employees. Reassign them first."
        )
    
    await db.delete(department)
    await db.commit()
    
    return {"message": f"Department {department.code} deleted successfully"}


@router.get("/{department_id}/employees", response_model=List)
async def get_department_employees(
    department_id: UUID,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get all employees in a department"""
    # Verify department exists
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Get employees
    query = select(Employee).where(Employee.department_id == department_id)
    
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    return [
        {
            "id": emp.id,
            "employee_number": emp.employee_number,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "position": emp.position,
            "is_active": emp.is_active
        }
        for emp in employees
    ]


@router.get("/{department_id}/stats")
async def get_department_stats(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get department statistics"""
    # Verify department exists
    result = await db.execute(
        select(Department).where(Department.id == department_id)
    )
    department = result.scalar_one_or_none()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Total employees
    result = await db.execute(
        select(func.count(Employee.id)).where(Employee.department_id == department_id)
    )
    total_employees = result.scalar()
    
    # Active employees
    result = await db.execute(
        select(func.count(Employee.id)).where(
            Employee.department_id == department_id,
            Employee.is_active == True
        )
    )
    active_employees = result.scalar()
    
    return {
        "department_id": department_id,
        "department_name": department.name,
        "department_code": department.code,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": total_employees - active_employees,
        "geofence_configured": bool(department.latitude and department.longitude),
        "geofence_radius": department.geofence_radius
    }