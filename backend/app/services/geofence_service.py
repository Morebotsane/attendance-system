"""
Geofencing service for location validation
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Department
from app.core.config import settings


class GeofenceService:
    """Service for geofence validation"""
    
    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        This formula accounts for Earth's spherical shape and provides
        accurate distances for points on the globe.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in meters
        """
        # Earth's radius in meters
        R = 6371000
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = R * c
        
        return distance
    
    async def validate_location(
        self,
        db: AsyncSession,
        department_id: str,
        user_lat: float,
        user_lon: float,
        gps_accuracy: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Validate if user is within department's geofence
        
        Args:
            db: Database session
            department_id: Department UUID
            user_lat: User's latitude
            user_lon: User's longitude
            gps_accuracy: GPS accuracy in meters (optional)
            
        Returns:
            Dict with validation results
        """
        # Get department
        result = await db.execute(
            select(Department).where(Department.id == department_id)
        )
        department = result.scalar_one_or_none()
        
        if not department:
            return {
                "valid": False,
                "error": "Department not found"
            }
        
        # Check if geofence is configured
        if not department.latitude or not department.longitude:
            # No geofence configured - allow by default
            return {
                "valid": True,
                "reason": "No geofence configured for this department",
                "department": department.name
            }
        
        # Calculate distance
        distance = self.haversine_distance(
            department.latitude,
            department.longitude,
            user_lat,
            user_lon
        )
        
        # Get allowed radius
        allowed_radius = department.geofence_radius or settings.DEFAULT_GEOFENCE_RADIUS_METERS
        
        # Check GPS accuracy (if provided)
        if gps_accuracy and gps_accuracy > settings.GEOFENCE_ACCURACY_REQUIRED_METERS:
            return {
                "valid": False,
                "reason": f"GPS accuracy too low ({gps_accuracy:.0f}m). Please try again in a location with better signal.",
                "distance_meters": round(distance, 2),
                "allowed_radius": allowed_radius,
                "gps_accuracy": gps_accuracy
            }
        
        # Validate distance
        is_valid = distance <= allowed_radius
        
        return {
            "valid": is_valid,
            "distance_meters": round(distance, 2),
            "allowed_radius": allowed_radius,
            "department": department.name,
            "department_location": {
                "lat": department.latitude,
                "lon": department.longitude
            },
            "user_location": {
                "lat": user_lat,
                "lon": user_lon
            },
            "gps_accuracy": gps_accuracy,
            "reason": None if is_valid else f"You are {distance - allowed_radius:.0f}m outside the allowed area"
        }
    
    @staticmethod
    def calculate_center_point(coordinates: list) -> tuple:
        """
        Calculate the center point of multiple coordinates
        Useful for determining department center from multiple locations
        
        Args:
            coordinates: List of (lat, lon) tuples
            
        Returns:
            (center_lat, center_lon) tuple
        """
        if not coordinates:
            return None
        
        x = y = z = 0
        
        for lat, lon in coordinates:
            lat_rad = radians(lat)
            lon_rad = radians(lon)
            
            x += cos(lat_rad) * cos(lon_rad)
            y += cos(lat_rad) * sin(lon_rad)
            z += sin(lat_rad)
        
        total = len(coordinates)
        x /= total
        y /= total
        z /= total
        
        center_lon = atan2(y, x)
        hyp = sqrt(x * x + y * y)
        center_lat = atan2(z, hyp)
        
        return (radians(center_lat), radians(center_lon))
    
    @staticmethod
    def is_within_time_window(
        current_time: any,
        window_start: any,
        window_end: any
    ) -> bool:
        """
        Check if current time is within allowed check-in window
        
        Args:
            current_time: datetime object
            window_start: datetime or time object
            window_end: datetime or time object
            
        Returns:
            True if within window
        """
        # Extract time components if datetime objects
        if hasattr(current_time, 'time'):
            current_time = current_time.time()
        if hasattr(window_start, 'time'):
            window_start = window_start.time()
        if hasattr(window_end, 'time'):
            window_end = window_end.time()
        
        return window_start <= current_time <= window_end


# Create singleton instance
geofence_service = GeofenceService()
