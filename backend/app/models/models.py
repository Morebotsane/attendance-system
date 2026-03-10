"""
Database models for the attendance system
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import BaseModel, Base


class ShiftType(str, enum.Enum):
    """Shift types"""
    DAY = "day"
    NIGHT = "night"
    EVENING = "evening"


class AttendanceStatus(str, enum.Enum):
    """Attendance record status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FLAGGED = "flagged"


class FlagType(str, enum.Enum):
    """Types of attendance flags"""
    GEOFENCE_VIOLATION = "geofence_violation"
    PHOTO_MISMATCH = "photo_mismatch"
    DUPLICATE_CHECKIN = "duplicate_checkin"
    SUSPICIOUS_TIMING = "suspicious_timing"
    DEVICE_MISMATCH = "device_mismatch"


class Department(BaseModel):
    """Department model"""
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    location = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    geofence_radius = Column(Integer, default=100)  # meters
    
    # Relationships
    employees = relationship("Employee", back_populates="department")
    shifts = relationship("Shift", back_populates="department")


class Employee(BaseModel):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(20))
    position = Column(String(100))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    
    # Authentication
    hashed_password = Column(String(255))
    
    # QR Code
    qr_code_data = Column(String(255), unique=True, nullable=False, index=True)
    qr_code_image_url = Column(String(500))
    
    # Photo for face matching (optional)
    reference_photo_url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    audit_logs = relationship("AttendanceAuditLog", back_populates="employee")


class AttendanceRecord(BaseModel):
    """Attendance record model"""
    __tablename__ = "attendance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    
    # Check-in data
    check_in_time = Column(DateTime(timezone=True), index=True)
    check_in_latitude = Column(Float)
    check_in_longitude = Column(Float)
    check_in_photo_url = Column(String(500))
    check_in_device_id = Column(String(255))
    
    # Check-out data
    check_out_time = Column(DateTime(timezone=True))
    check_out_latitude = Column(Float)
    check_out_longitude = Column(Float)
    check_out_photo_url = Column(String(500))
    check_out_device_id = Column(String(255))
    
    # Metadata
    shift_type = Column(Enum(ShiftType))
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ACTIVE)
    notes = Column(Text)
    
    # Validation results (stored as JSON)
    validation_metadata = Column(JSON)
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")
    flags = relationship("AttendanceFlag", back_populates="attendance_record")
    audit_logs = relationship("AttendanceAuditLog", back_populates="attendance_record")


class AttendanceAuditLog(BaseModel):
    """Audit log for all attendance actions"""
    __tablename__ = "attendance_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_record_id = Column(UUID(as_uuid=True), ForeignKey("attendance_records.id"), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # check_in, check_out, manual_edit
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Media
    photo_url = Column(String(500))
    
    # Validation
    validation_status = Column(JSON)
    
    # For manual edits
    performed_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    notes = Column(Text)
    
    # Relationships
    attendance_record = relationship("AttendanceRecord", back_populates="audit_logs")
    employee = relationship("Employee", back_populates="audit_logs", foreign_keys=[employee_id])


class AttendanceFlag(BaseModel):
    """Flags for suspicious or problematic attendance records"""
    __tablename__ = "attendance_flags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_record_id = Column(UUID(as_uuid=True), ForeignKey("attendance_records.id"), nullable=False, index=True)
    
    flag_type = Column(Enum(FlagType), nullable=False)
    severity = Column(String(20))  # low, medium, high
    description = Column(Text)
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Relationships
    attendance_record = relationship("AttendanceRecord", back_populates="flags")


class Shift(BaseModel):
    """Shift definitions"""
    __tablename__ = "shifts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)  # Time only
    end_time = Column(DateTime, nullable=False)
    grace_period_minutes = Column(Integer, default=15)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    
    # Relationships
    department = relationship("Department", back_populates="shifts")
