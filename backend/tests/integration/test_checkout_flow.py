"""
Integration tests for check-out flow
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from PIL import Image
import io


def create_test_image() -> io.BytesIO:
    """Create a minimal valid PNG image for testing"""
    img = Image.new('RGB', (100, 100), color='yellow')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.mark.asyncio
async def test_successful_checkout(client: AsyncClient, test_employee, test_department):
    """Test successful check-out after check-in"""
    # First check in
    checkin_image = create_test_image()
    checkin_response = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-checkout-device"
        },
        files={"photo": ("checkin.png", checkin_image, "image/png")}
    )
    
    assert checkin_response.status_code == 201
    
    # Now check out
    checkout_image = create_test_image()
    checkout_response = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-checkout-device"
        },
        files={"photo": ("checkout.png", checkout_image, "image/png")}
    )
    
    print(f"\n🔍 Check-out status: {checkout_response.status_code}")
    if checkout_response.status_code == 200:
        print(f"🔍 Check-out data: {checkout_response.json()}")
    
    assert checkout_response.status_code == 200
    data = checkout_response.json()
    assert data["status"] == "completed"
    assert data["check_out_time"] is not None
    assert data["check_out_latitude"] == test_department.latitude


@pytest.mark.asyncio
async def test_checkout_without_checkin(client: AsyncClient, test_employee, test_department):
    """Test check-out fails when no active check-in exists"""
    checkout_image = create_test_image()
    
    response = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-no-checkin-device"
        },
        files={"photo": ("checkout.png", checkout_image, "image/png")}
    )
    
    print(f"\n🔍 Check-out without check-in status: {response.status_code}")
    if response.status_code != 200:
        print(f"🔍 Error: {response.json()}")
    
    assert response.status_code == 404
    assert "No active" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_with_invalid_qr(client: AsyncClient, test_department):
    """Test check-out with invalid QR code"""
    checkout_image = create_test_image()
    
    response = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": "invalid-qr-code-data",
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-invalid-qr"
        },
        files={"photo": ("checkout.png", checkout_image, "image/png")}
    )
    
    print(f"\n🔍 Invalid QR check-out status: {response.status_code}")
    
    assert response.status_code == 400
    assert "Invalid QR code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_checkout(client: AsyncClient, test_employee, test_department):
    """Test that duplicate check-outs are prevented"""
    # Check in
    checkin_image = create_test_image()
    await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-duplicate-device"
        },
        files={"photo": ("checkin.png", checkin_image, "image/png")}
    )
    
    # First check-out
    checkout_image1 = create_test_image()
    first_checkout = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-duplicate-device"
        },
        files={"photo": ("checkout1.png", checkout_image1, "image/png")}
    )
    
    assert first_checkout.status_code == 200
    
    # Try to check out again
    checkout_image2 = create_test_image()
    second_checkout = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-duplicate-device"
        },
        files={"photo": ("checkout2.png", checkout_image2, "image/png")}
    )
    
    print(f"\n🔍 Duplicate check-out status: {second_checkout.status_code}")
    
    assert second_checkout.status_code == 404
    assert "No active" in second_checkout.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_photo_validation(client: AsyncClient, test_employee, test_department):
    """Test that check-out requires valid photo"""
    # Check in first
    checkin_image = create_test_image()
    await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-photo-device"
        },
        files={"photo": ("checkin.png", checkin_image, "image/png")}
    )
    
    # Try to check out with invalid photo
    fake_image = io.BytesIO(b"not a valid image")
    
    response = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-photo-device"
        },
        files={"photo": ("invalid.png", fake_image, "image/png")}
    )
    
    print(f"\n🔍 Invalid photo check-out status: {response.status_code}")
    
    assert response.status_code == 500
    assert "Failed to store photo" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_updates_status(client: AsyncClient, test_employee, test_department):
    """Test that check-out updates attendance status to completed"""
    # Check in
    checkin_image = create_test_image()
    checkin_resp = await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-status-device"
        },
        files={"photo": ("checkin.png", checkin_image, "image/png")}
    )
    
    checkin_data = checkin_resp.json()
    assert checkin_data["status"] == "active"
    
    # Check out
    checkout_image = create_test_image()
    checkout_resp = await client.post(
        "/api/v1/attendance/check-out",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-status-device"
        },
        files={"photo": ("checkout.png", checkout_image, "image/png")}
    )
    
    checkout_data = checkout_resp.json()
    print(f"\n🔍 Status after check-out: {checkout_data['status']}")
    
    assert checkout_data["status"] == "completed"
    assert checkout_data["id"] == checkin_data["id"]  # Same record
