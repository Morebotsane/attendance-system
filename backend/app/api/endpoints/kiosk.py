"""
Kiosk-specific endpoints for generating location-based QR codes
"""
from typing import Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Department
from app.services.qr_service import qr_service

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


@router.get("/qr")
async def get_kiosk_qr(
    department_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate encrypted daily kiosk tokens - NOT URLs!
    
    Returns TWO encrypted tokens:
    - checkin_qr: Encrypted token for check-in (valid today only)
    - checkout_qr: Encrypted token for check-out (valid today only)
    
    Tokens rotate daily and contain:
    - type: "checkin" or "checkout"
    - date: today's date
    - nonce: random value to prevent pre-generation
    
    Args:
        department_id: Optional UUID of department where kiosk is located
        
    Returns:
        checkin_qr: Encrypted daily token for check-in
        checkout_qr: Encrypted daily token for check-out
        expires_at: Midnight tonight (tokens expire)
        date: Today's date
        department: Department info if department_id provided
        location_name: Human-readable location name
    """
    
    department = None
    location_name = "General"
    
    if department_id:
        # Fetch department details
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = result.scalar_one_or_none()
        
        if not department:
            raise HTTPException(
                status_code=404,
                detail=f"Department with id {department_id} not found"
            )
        
        location_name = department.name
    
    # Generate encrypted tokens for today
    today_str = date.today().isoformat()
    checkin_token = qr_service.generate_kiosk_token("checkin", today_str)
    checkout_token = qr_service.generate_kiosk_token("checkout", today_str)
    
    # Calculate expiration (midnight tonight)
    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    return {
        "checkin_qr": checkin_token,
        "checkout_qr": checkout_token,
        "expires_at": tomorrow.isoformat(),
        "date": today_str,
        "department_id": department_id,
        "location_name": location_name,
        "department": {
            "id": str(department.id),
            "name": department.name,
            "code": department.code,
            "location": department.location,
            "latitude": float(department.latitude),
            "longitude": float(department.longitude),
            "geofence_radius": department.geofence_radius
        } if department else None
    }


@router.get("/locations")
async def get_kiosk_locations(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all departments/locations for kiosk setup
    """
    result = await db.execute(
        select(Department)
        .order_by(Department.name)
    )
    departments = result.scalars().all()
    
    return {
        "locations": [
            {
                "id": str(dept.id),
                "name": dept.name,
                "code": dept.code,
                "location": dept.location,
                "latitude": float(dept.latitude),
                "longitude": float(dept.longitude),
                "geofence_radius": dept.geofence_radius
            }
            for dept in departments
        ],
        "total": len(departments)
    }
