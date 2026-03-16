"""
Unit tests for photo service
"""

import pytest
from app.services.photo_service import PhotoService

photo_service = PhotoService()


def test_photo_service_initialization():
    """Test photo service initializes"""
    assert photo_service is not None
    assert hasattr(photo_service, 'store_photo')
