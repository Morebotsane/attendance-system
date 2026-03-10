"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class ShiftType(str, Enum):
    DAY = "day"
    NIGHT = "night"
    EVENING = "evening"


class AttendanceStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FLAGGED = "flagged"


# ============================================
# Employee Schemas
# ============================================

class EmployeeBase(BaseModel):
    employee_number: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[UUID] = None


class EmployeeCreate(EmployeeBase):
    password: str = Field(..., min_length=8)


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    id: UUID
    qr_code_data: str
    qr_code_image_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Department Schemas
# ============================================

class DepartmentBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geofence_radius: int = 100


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geofence_radius: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Attendance Schemas
# ============================================

class CheckInRequest(BaseModel):
    qr_code_data: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    device_id: str
    
    @field_validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if v == 0.0:
            raise ValueError('Invalid coordinates')
        return v


class CheckOutRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    device_id: str


class AttendanceRecordBase(BaseModel):
    employee_id: UUID
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    shift_type: Optional[ShiftType] = None
    status: AttendanceStatus = AttendanceStatus.ACTIVE


class AttendanceRecordResponse(AttendanceRecordBase):
    id: UUID
    check_in_latitude: Optional[float] = None
    check_in_longitude: Optional[float] = None
    check_out_latitude: Optional[float] = None
    check_out_longitude: Optional[float] = None
    check_in_photo_url: Optional[str] = None
    check_out_photo_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    success: bool
    message: str
    attendance_id: UUID
    employee_name: str
    check_in_time: datetime
    validation_results: dict


class CheckOutResponse(BaseModel):
    success: bool
    message: str
    attendance_id: UUID
    check_out_time: datetime
    total_hours: float
    validation_results: dict


# ============================================
# Geolocation Schemas
# ============================================

class GeolocationValidation(BaseModel):
    valid: bool
    distance_meters: Optional[float] = None
    allowed_radius: Optional[int] = None
    reason: Optional[str] = None


# ============================================
# Report Schemas
# ============================================

class DailyReportRequest(BaseModel):
    date: datetime
    department_id: Optional[UUID] = None


class DailyReportResponse(BaseModel):
    date: datetime
    department_name: Optional[str] = None
    total_employees: int
    present: int
    absent: int
    late: int
    on_time: int
    not_checked_out: int
    attendance_rate: float


class EmployeeAttendanceReport(BaseModel):
    employee_id: UUID
    employee_name: str
    department: str
    total_days: int
    days_present: int
    days_absent: int
    days_late: int
    attendance_rate: float
    average_check_in_time: Optional[str] = None


# ============================================
# Authentication Schemas
# ============================================

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # employee_id
    exp: datetime


class LoginRequest(BaseModel):
    employee_number: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    employee: EmployeeResponse


# ============================================
# QR Code Schemas
# ============================================

class QRCodeGenerateRequest(BaseModel):
    employee_id: UUID


class QRCodeResponse(BaseModel):
    employee_id: UUID
    qr_code_data: str
    qr_code_image_base64: str
    qr_code_image_url: str
