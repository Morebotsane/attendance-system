"""
Queue Management Endpoints for Kiosk Check-in/out
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.queue_service import queue_service
from app.models.kiosk_session import SessionType
from app.api.endpoints.auth import decode_token

router = APIRouter(prefix="/queue", tags=["Queue"])
security = HTTPBearer()


# Request/Response models
class JoinQueueRequest(BaseModel):
    """Request to join check-in/out queue"""
    session_type: str  # "checkin" or "checkout"
    department_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class QueueStatusResponse(BaseModel):
    """Queue status response"""
    session_id: str
    queue_position: int
    status: str
    your_turn: bool
    qr_data: Optional[str]
    expires_at: str
    estimated_wait_seconds: int
    session_type: str


@router.post("/join", response_model=QueueStatusResponse)
async def join_queue(
    request: JoinQueueRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Employee joins check-in/out queue
    
    Flow:
    1. Employee taps "Check In" on their phone
    2. Phone calls this endpoint with JWT
    3. Backend creates session and assigns queue position
    4. Returns position and status
    5. Phone polls /queue/status/{session_id} for updates
    
    Returns:
        - session_id: UUID to track this session
        - queue_position: 1 = your turn, 2+ = waiting
        - status: ACTIVE (your turn) or WAITING
        - your_turn: boolean flag
        - qr_data: Session QR to scan (only if your_turn=true)
        - estimated_wait_seconds: How long to wait
    """
    # Decode JWT to get employee_id
    try:
        token = credentials.credentials
        payload = decode_token(token)
        employee_id = payload.get("sub")
        if not employee_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    # Validate session type
    try:
        session_type_enum = SessionType(request.session_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_type. Must be 'checkin' or 'checkout'"
        )
    
    # Join queue
    result = await queue_service.join_queue(
        db=db,
        employee_id=employee_id,
        session_type=session_type_enum,
        department_id=request.department_id,
        latitude=request.latitude,
        longitude=request.longitude
    )
    
    return result


@router.get("/status/{session_id}", response_model=QueueStatusResponse)
async def get_queue_status(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current queue status for a session
    
    Phone polls this endpoint every 2-3 seconds to:
    - Check if it's their turn (queue_position = 1)
    - Get session QR when your_turn = true
    - Monitor estimated wait time
    
    Returns same format as /join endpoint
    """
    # Verify JWT (ensures only session owner can check status)
    try:
        token = credentials.credentials
        payload = decode_token(token)
        employee_id = payload.get("sub")
        if not employee_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    # Get session status
    result = await queue_service.get_session_status(db, session_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.get("/current")
async def get_current_session(
    department_id: Optional[str] = None,
    session_type: str = "checkin",
    db: AsyncSession = Depends(get_db)
):
    """
    Get current active session (for kiosk display)
    
    Kiosk polls this endpoint every 2 seconds to:
    - Check if there's an active session (someone at position 1)
    - Get session QR to display
    - Show employee name (optional, for confirmation)
    
    Returns:
        {
            "session_id": "uuid",
            "qr_data": "encrypted_session_qr",
            "employee_name": "John Doe",
            "session_type": "checkin",
            "expires_at": "timestamp"
        }
        
        OR null if no active session
    """
    # Validate session type
    try:
        session_type_enum = SessionType(session_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session_type. Must be 'checkin' or 'checkout'"
        )
    
    result = await queue_service.get_current_session(
        db=db,
        department_id=department_id,
        session_type=session_type_enum
    )
    
    return result


@router.post("/cancel/{session_id}")
async def cancel_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a queue session
    
    Employee can cancel if they:
    - Change their mind
    - Walk away
    - Switch to different kiosk
    
    Advances queue automatically
    """
    # Verify JWT
    try:
        token = credentials.credentials
        payload = decode_token(token)
        employee_id = payload.get("sub")
        if not employee_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    # Cancel session
    success = await queue_service.cancel_session(db, session_id, employee_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already completed"
        )
    
    return {
        "message": "Session cancelled successfully",
        "session_id": session_id
    }


@router.get("/debug/all")
async def debug_all_sessions(
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint - view all active sessions
    WARNING: Remove this in production!
    """
    from sqlalchemy import select
    from app.models.kiosk_session import KioskSession
    
    result = await db.execute(
        select(KioskSession).order_by(KioskSession.created_at.desc()).limit(20)
    )
    sessions = result.scalars().all()
    
    return [
        {
            "session_id": str(s.id),
            "employee_id": str(s.employee_id),
            "status": s.status.value,
            "position": s.queue_position,
            "type": s.session_type.value,
            "created": s.created_at.isoformat(),
            "expires": s.expires_at.isoformat()
        }
        for s in sessions
    ]
