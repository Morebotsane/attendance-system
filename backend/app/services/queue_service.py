"""
Kiosk Queue Management Service
Handles session creation, queue positioning, and status updates
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional

from app.models.kiosk_session import KioskSession, SessionStatus, SessionType
from app.models.models import Employee, Department
from app.services.qr_service import qr_service


class QueueService:
    """Manages kiosk check-in/out queue"""
    
    async def join_queue(
        self,
        db: AsyncSession,
        employee_id: str,
        session_type: SessionType,
        department_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> dict:
        """
        Employee joins queue for check-in/out
        
        Args:
            employee_id: UUID of employee
            session_type: "checkin" or "checkout"
            department_id: Optional department filter
            latitude: Employee's GPS latitude
            longitude: Employee's GPS longitude
            
        Returns:
            {
                "session_id": "uuid",
                "queue_position": 1,
                "status": "ACTIVE" or "WAITING",
                "expires_at": "timestamp",
                "estimated_wait_seconds": 120
            }
        """
        # Clean up expired sessions first
        await self._cleanup_expired_sessions(db, department_id)
        
        # Check if employee already has an active session
        existing = await db.execute(
            select(KioskSession).where(
                and_(
                    KioskSession.employee_id == uuid.UUID(employee_id),
                    KioskSession.session_type == session_type,
                    KioskSession.status.in_([SessionStatus.WAITING, SessionStatus.ACTIVE]),
                    KioskSession.expires_at > datetime.now(timezone.utc)
                )
            )
        )
        existing_session = existing.scalar_one_or_none()
        
        if existing_session:
            # Return existing session info
            return await self._get_session_info(db, existing_session)
        
        # Get current queue size for this department/type
        queue_query = select(func.count(KioskSession.id)).where(
            and_(
                KioskSession.session_type == session_type,
                KioskSession.status.in_([SessionStatus.WAITING, SessionStatus.ACTIVE]),
                KioskSession.expires_at > datetime.now(timezone.utc)
            )
        )
        
        if department_id:
            queue_query = queue_query.where(KioskSession.department_id == uuid.UUID(department_id))
        
        result = await db.execute(queue_query)
        current_queue_size = result.scalar() or 0
        
        # Create new session
        new_position = current_queue_size + 1
        session = KioskSession(
            employee_id=uuid.UUID(employee_id),
            department_id=uuid.UUID(department_id) if department_id else None,
            session_type=session_type,
            status=SessionStatus.ACTIVE if new_position == 1 else SessionStatus.WAITING,
            queue_position=new_position,
            created_latitude=latitude,
            created_longitude=longitude
        )
        
        # If position 1, generate session QR immediately
        if new_position == 1:
            session.qr_data = self._generate_session_qr(str(session.id), session_type)
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        return await self._get_session_info(db, session)
    
    async def get_session_status(
        self,
        db: AsyncSession,
        session_id: str
    ) -> dict:
        """
        Get current status of a session (for polling)
        
        Returns:
            {
                "session_id": "uuid",
                "status": "ACTIVE",
                "queue_position": 1,
                "your_turn": true,
                "qr_data": "encrypted_session_qr",
                "expires_at": "timestamp"
            }
        """
        result = await db.execute(
            select(KioskSession).where(KioskSession.id == uuid.UUID(session_id))
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return {"error": "Session not found"}
        
        # Check if expired
        if session.expires_at < datetime.now(timezone.utc):
            session.status = SessionStatus.EXPIRED
            await db.commit()
            return {"error": "Session expired", "status": "EXPIRED"}
        
        return await self._get_session_info(db, session)
    
    async def get_current_session(
        self,
        db: AsyncSession,
        department_id: Optional[str] = None,
        session_type: SessionType = SessionType.CHECKIN
    ) -> Optional[dict]:
        """
        Get the current ACTIVE session (for kiosk to display)
        
        Returns:
            {
                "session_id": "uuid",
                "qr_data": "encrypted_session_qr",
                "employee_name": "John Doe",
                "session_type": "checkin",
                "expires_at": "timestamp"
            }
        """
        # Clean up expired first
        await self._cleanup_expired_sessions(db, department_id)
        
        # Get session at position 1 (ACTIVE)
        query = select(KioskSession).where(
            and_(
                KioskSession.status == SessionStatus.ACTIVE,
                KioskSession.session_type == session_type,
                KioskSession.queue_position == 1,
                KioskSession.expires_at > datetime.now(timezone.utc)
            )
        )
        
        if department_id:
            query = query.where(KioskSession.department_id == uuid.UUID(department_id))
        
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Get employee name
        emp_result = await db.execute(
            select(Employee).where(Employee.id == session.employee_id)
        )
        employee = emp_result.scalar_one_or_none()
        
        return {
            "session_id": str(session.id),
            "qr_data": session.qr_data,
            "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            "session_type": session.session_type.value,
            "expires_at": session.expires_at.isoformat(),
            "queue_position": session.queue_position
        }
    
    async def complete_session(
        self,
        db: AsyncSession,
        session_id: str,
        employee_id: str
    ) -> bool:
        """
        Mark session as completed and advance queue
        
        Returns:
            True if successful, False if validation failed
        """
        result = await db.execute(
            select(KioskSession).where(KioskSession.id == uuid.UUID(session_id))
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        # Validate session belongs to this employee
        if str(session.employee_id) != employee_id:
            return False
        
        # Validate session is ACTIVE
        if session.status != SessionStatus.ACTIVE:
            return False
        
        # Mark completed
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        # Advance queue - move next session to position 1
        await self._advance_queue(db, session.department_id, session.session_type)
        
        return True
    
    async def cancel_session(
        self,
        db: AsyncSession,
        session_id: str,
        employee_id: str
    ) -> bool:
        """Employee cancels their queue session"""
        result = await db.execute(
            select(KioskSession).where(
                and_(
                    KioskSession.id == uuid.UUID(session_id),
                    KioskSession.employee_id == uuid.UUID(employee_id)
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return False
        
        old_position = session.queue_position
        session.status = SessionStatus.CANCELLED
        await db.commit()
        
        # If they were in queue, shift everyone up
        if old_position > 0:
            await self._advance_queue(db, session.department_id, session.session_type)
        
        return True
    
    # Helper methods
    
    async def _cleanup_expired_sessions(
        self,
        db: AsyncSession,
        department_id: Optional[str] = None
    ):
        """Mark expired sessions and advance queue"""
        query = update(KioskSession).where(
            and_(
                KioskSession.status.in_([SessionStatus.WAITING, SessionStatus.ACTIVE]),
                KioskSession.expires_at < datetime.now(timezone.utc)
            )
        ).values(status=SessionStatus.EXPIRED)
        
        await db.execute(query)
        await db.commit()
        
        # Advance queue if needed
        await self._advance_queue(db, department_id, SessionType.CHECKIN)
        await self._advance_queue(db, department_id, SessionType.CHECKOUT)
    
    async def _advance_queue(
        self,
        db: AsyncSession,
        department_id: Optional[uuid.UUID],
        session_type: SessionType
    ):
        """Move next session in queue to position 1"""
        # Get all waiting sessions, ordered by creation time
        query = select(KioskSession).where(
            and_(
                KioskSession.status == SessionStatus.WAITING,
                KioskSession.session_type == session_type,
                KioskSession.expires_at > datetime.now(timezone.utc)
            )
        ).order_by(KioskSession.created_at)
        
        if department_id:
            query = query.where(KioskSession.department_id == department_id)
        
        result = await db.execute(query)
        waiting_sessions = result.scalars().all()
        
        # Update positions
        for idx, session in enumerate(waiting_sessions, start=1):
            session.queue_position = idx
            
            # First in line becomes ACTIVE
            if idx == 1:
                session.status = SessionStatus.ACTIVE
                session.qr_data = self._generate_session_qr(str(session.id), session_type)
        
        await db.commit()
    
    def _generate_session_qr(self, session_id: str, session_type: SessionType) -> str:
        """Generate encrypted QR for session"""
        import json
        import base64
        import hashlib
        from cryptography.fernet import Fernet
        from app.core.config import settings
        
        data = {
            "session_id": session_id,
            "type": session_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        json_data = json.dumps(data)
        
        # Generate Fernet key from SECRET_KEY
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        fernet = Fernet(fernet_key)
        
        encrypted = fernet.encrypt(json_data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    async def _get_session_info(self, db: AsyncSession, session: KioskSession) -> dict:
        """Format session info for API response"""
        # Estimate wait time (60 seconds per person ahead)
        estimated_wait = max(0, (session.queue_position - 1) * 60)
        
        return {
            "session_id": str(session.id),
            "queue_position": session.queue_position,
            "status": session.status.value,
            "your_turn": session.status == SessionStatus.ACTIVE,
            "qr_data": session.qr_data,
            "expires_at": session.expires_at.isoformat(),
            "estimated_wait_seconds": estimated_wait,
            "session_type": session.session_type.value
        }


# Create singleton
queue_service = QueueService()
