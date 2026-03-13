"""
Employee management endpoints - CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.models import Employee
from app.schemas.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse
)
from app.api.endpoints.auth import (
    get_current_employee, get_current_admin, hash_password
)
from app.services.qr_service import qr_service

router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Create new employee (Admin only)
    Generates QR code automatically
    """
    # Check if employee number already exists
    result = await db.execute(
        select(Employee).where(Employee.employee_number == employee_data.employee_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee number already exists"
        )
    
    # Check if email already exists
    if employee_data.email:
        result = await db.execute(
            select(Employee).where(Employee.email == employee_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create employee
    new_employee = Employee(
        employee_number=employee_data.employee_number,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        email=employee_data.email,
        phone=employee_data.phone,
        position=employee_data.position,
        department_id=employee_data.department_id,
        hashed_password=hash_password(employee_data.password),
        qr_code_data="",  # Will be set below
        is_active=True
    )
    
    db.add(new_employee)
    await db.flush()  # Get the ID
    
    # Generate QR code
    qr_data = qr_service.generate_employee_qr_data(str(new_employee.id))
    qr_image_url = qr_service.save_qr_image(qr_data, str(new_employee.id))
    
    new_employee.qr_code_data = qr_data
    new_employee.qr_code_image_url = qr_image_url
    
    await db.commit()
    await db.refresh(new_employee)
    
    return EmployeeResponse.model_validate(new_employee)


@router.get("/", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    department_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """
    List all employees with filtering and pagination
    """
    query = select(Employee)
    
    # Apply filters
    if search:
        search_filter = or_(
            Employee.first_name.ilike(f"%{search}%"),
            Employee.last_name.ilike(f"%{search}%"),
            Employee.employee_number.ilike(f"%{search}%"),
            Employee.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    if department_id:
        query = query.where(Employee.department_id == department_id)
    
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    return [EmployeeResponse.model_validate(emp) for emp in employees]


@router.get("/count")
async def count_employees(
    department_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get total count of employees"""
    query = select(func.count(Employee.id))
    
    if department_id:
        query = query.where(Employee.department_id == department_id)
    
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"total": count}


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get employee by ID"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return EmployeeResponse.model_validate(employee)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Update employee (Admin only)"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Update fields
    update_data = employee_data.model_dump(exclude_unset=True)
    
    # Check email uniqueness if being updated
    if "email" in update_data and update_data["email"]:
        result = await db.execute(
            select(Employee).where(
                Employee.email == update_data["email"],
                Employee.id != employee_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    await db.commit()
    await db.refresh(employee)
    
    return EmployeeResponse.model_validate(employee)


@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Soft delete employee (sets is_active to False)
    Admin only
    """
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prevent deleting yourself
    if employee.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete
    employee.is_active = False
    await db.commit()
    
    return {"message": f"Employee {employee.employee_number} deactivated successfully"}


@router.post("/{employee_id}/activate")
async def activate_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Reactivate a deactivated employee (Admin only)"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    employee.is_active = True
    await db.commit()
    
    return {"message": f"Employee {employee.employee_number} activated successfully"}


@router.post("/{employee_id}/regenerate-qr", response_model=EmployeeResponse)
async def regenerate_qr_code(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """
    Regenerate QR code for an employee (Admin only)
    Useful if QR code is compromised
    """
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Generate new QR code
    qr_data = qr_service.generate_employee_qr_data(str(employee.id))
    qr_image_url = qr_service.save_qr_image(qr_data, str(employee.id))
    
    employee.qr_code_data = qr_data
    employee.qr_code_image_url = qr_image_url
    
    await db.commit()
    await db.refresh(employee)
    
    return EmployeeResponse.model_validate(employee)


@router.get("/by-number/{employee_number}", response_model=EmployeeResponse)
async def get_employee_by_number(
    employee_number: str,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get employee by employee number"""
    result = await db.execute(
        select(Employee).where(Employee.employee_number == employee_number)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return EmployeeResponse.model_validate(employee)