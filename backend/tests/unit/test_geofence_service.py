"""
Unit tests for geofence service
"""

import pytest
from app.services.geofence_service import GeofenceService

geofence_service = GeofenceService()


def test_geofence_service_initialization():
    """Test geofence service initializes"""
    assert geofence_service is not None
