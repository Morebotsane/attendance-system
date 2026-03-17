"""
Integration tests for attendance check-in/check-out flow
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
import io
from PIL import Image


def create_test_image() -> io.BytesIO:
    """Create a minimal valid PNG image for testing"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.mark.asyncio
async def test_check_in_success(client: AsyncClient, test_employee, test_department):
    """Test successful check-in within geofence"""
    fake_image = create_test_image()
    
    response = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-device-001"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    print(f"\n🔍 Check-in response: {response.status_code}")
    if response.status_code != 201:
        print(f"🔍 Error details: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_check_in_outside_geofence(client: AsyncClient, test_employee):
    """Test check-in rejection when outside geofence"""
    fake_image = create_test_image()
    
    response = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": -29.4000,
            "longitude": 27.5000,
            "device_id": "test-device-001"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    print(f"\n🔍 Geofence test response: {response.status_code}")
    print(f"🔍 Message: {response.json()['detail']}")
    
    assert response.status_code == 403
    assert "outside the allowed area" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_checkin_prevented(client: AsyncClient, test_employee, test_department):
    """Test that duplicate check-ins are prevented"""
    fake_image = create_test_image()
    
    response1 = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-device-001"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    print(f"\n🔍 First check-in: {response1.status_code}")
    if response1.status_code != 201:
        print(f"🔍 First check-in error: {response1.json()}")
    
    fake_image2 = create_test_image()
    response = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-device-001"
        },
        files={"photo": ("test.png", fake_image2, "image/png")}
    )
    
    print(f"\n🔍 Duplicate check-in: {response.status_code}")
    if response.status_code != 400:
        print(f"🔍 Error: {response.json()}")
    
    assert response.status_code == 400
    assert "already checked in" in response.json()["detail"].lower()
