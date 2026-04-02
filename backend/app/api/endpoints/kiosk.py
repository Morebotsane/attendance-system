"""
Kiosk-specific endpoints for generating location-based QR codes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Department

router = APIRouter(prefix="/kiosk", tags=["kiosk"])


@router.get("/qr")
async def get_kiosk_qr(
    department_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate QR code data for kiosk display
    
    The QR contains a URL that employees scan with their phones
    URL includes location/department information for pre-validation
    
    Args:
        department_id: Optional UUID of department where kiosk is located
        
    Returns:
        qr_data: URL to encode in QR (frontend generates QR image from this)
        url: Same as qr_data (for clarity)
        department: Department info if department_id provided
        location_name: Human-readable location name
    """
    
    # Base check-in URL (frontend URL)
    base_url = "https://5173-firebase-attendance-system-1773135120418.cluster-vpxjqdstfzgs6qeiaf7rdlsqrc.cloudworkstations.dev/check-in"
    
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
        
        # Build URL with department parameter
        url = f"{base_url}?dept={department_id}"
    else:
        # General kiosk (no specific department)
        url = base_url
    
    return {
        "qr_data": url,
        "url": url,
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
    
    Use this to:
    - Configure which kiosk is at which location
    - Admin panel for kiosk management
    - Dropdown in kiosk settings
    
    Returns:
        List of departments with location info
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
