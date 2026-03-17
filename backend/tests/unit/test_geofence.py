"""
Unit tests for geofence distance calculations
"""

import pytest
from app.services.geofence_service import GeofenceService
import math

geofence_service = GeofenceService()


def test_haversine_distance_same_point():
    """Distance between same point should be 0"""
    lat, lon = -29.3167, 27.4833
    distance = geofence_service.haversine_distance(lat, lon, lat, lon)
    assert distance == 0


def test_haversine_distance_known_points():
    """Test distance between known points in Maseru"""
    # Ministry of Health HQ
    lat1, lon1 = -29.3167, 27.4833
    # Point ~100m away
    lat2, lon2 = -29.3177, 27.4843
    
    distance = geofence_service.haversine_distance(lat1, lon1, lat2, lon2)
    
    # Should be roughly 100-150 meters
    assert 50 < distance < 200


def test_haversine_distance_returns_positive():
    """Distance should always be positive"""
    distance = geofence_service.haversine_distance(
        -29.3167, 27.4833,
        -29.4167, 27.5833
    )
    assert distance > 0
