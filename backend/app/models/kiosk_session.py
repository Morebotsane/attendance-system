"""
Kiosk Session Model for Queue Management
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime, timedelta, timezone

from app.db.base import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration"""
    WAITING = "WAITING"      # In queue, not their turn yet
    ACTIVE = "ACTIVE"        # Their turn - can scan kiosk QR
    COMPLETED = "COMPLETED"  # Successfully checked in/out
    EXPIRED = "EXPIRED"      # Timeout - didn't complete in time
    CANCELLED = "CANCELLED"  # Employee manually cancelled


class SessionType(str, enum.Enum):
    """Session type enumeration"""
    CHECKIN = "checkin"
    CHECKOUT = "checkout"


class KioskSession(Base):
    """
    Kiosk Session - tracks employee's position in check-in/out queue
    
    Flow:
    1. Employee taps "Check In" → creates session (WAITING)
    2. System assigns queue_position based on existing queue
    3. When position = 1 → status changes to ACTIVE
    4. Kiosk displays session QR
    5. Employee scans → submits → session becomes COMPLETED
    6. Next session moves to position 1
    """
    __tablename__ = "kiosk_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Employee reference
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    
    # Department reference (optional - for department-specific kiosks)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    # Session details
    session_type = Column(SQLEnum(SessionType), nullable=False)  # checkin or checkout
    status = Column(SQLEnum(SessionStatus), nullable=False, default=SessionStatus.WAITING)
    queue_position = Column(Integer, nullable=False)  # 1 = their turn, 2+ = waiting
    
    # Session QR data (kiosk displays this when it's their turn)
    qr_data = Column(String(500), nullable=True)  # Generated when status = ACTIVE
    
    # GPS location when session created (validates employee is on-site)
    created_latitude = Column(Float, nullable=True)
    created_longitude = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Auto-set to +5 minutes
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="kiosk_sessions")
    department = relationship("Department")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-set expiration to 5 minutes from now (timezone-aware UTC)
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
