"""
Integration tests for admin endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from PIL import Image
import io


def create_test_image() -> io.BytesIO:
    """Create a minimal valid PNG image for testing"""
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.mark.asyncio
async def test_generate_qr_for_employee(client: AsyncClient, admin_token: str, test_employee):
    """Test admin generating QR code for employee"""
    response = await client.post(
        f"/api/v1/admin/generate-qr/{test_employee.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "qr_code_data" in data
    assert "qr_code_image_base64" in data
    assert "qr_code_image_url" in data


@pytest.mark.asyncio
async def test_download_qr_code(client: AsyncClient, admin_token: str, test_employee):
    """Test downloading QR code as PNG image"""
    # First generate QR
    await client.post(
        f"/api/v1/admin/generate-qr/{test_employee.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Now download it
    response = await client.get(
        f"/api/v1/admin/qr/{test_employee.id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_view_all_flags(client: AsyncClient, admin_token: str, test_employee, test_department):
    """Test viewing all attendance flags"""
    # Create a flag by checking in outside geofence
    fake_image = create_test_image()
    await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": -29.9999,
            "longitude": 27.9999,
            "device_id": "test-flag-device"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    # Now view flags
    response = await client.get(
        "/api/v1/admin/flags",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least the flag we just created


@pytest.mark.asyncio
async def test_resolve_flag(client: AsyncClient, admin_token: str, test_employee, test_department):
    """Test resolving an attendance flag"""
    # Create a flag
    fake_image = create_test_image()
    await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": -29.9999,
            "longitude": 27.9999,
            "device_id": "test-resolve-device"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    # Get the flag ID
    flags_response = await client.get(
        "/api/v1/admin/flags",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    flags = flags_response.json()
    
    if len(flags) > 0:
        flag_id = flags[0]["id"]
        
        # Resolve the flag - FIXED: Use query parameter!
        response = await client.post(
            f"/api/v1/admin/flags/{flag_id}/resolve?resolution_notes=Approved by supervisor",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"\n🔍 Resolve flag status: {response.status_code}")
        if response.status_code == 200:
            print(f"🔍 Resolved: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Flag resolved successfully"


@pytest.mark.asyncio
async def test_view_audit_log(client: AsyncClient, admin_token: str):
    """Test viewing audit log"""
    response = await client.get(
        "/api/v1/admin/audit-log",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_system_stats(client: AsyncClient, admin_token: str):
    """Test getting system statistics"""
    response = await client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 System stats: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    # Match actual nested structure
    assert "employees" in data
    assert "total" in data["employees"]
    assert "flags" in data
    assert "today" in data


@pytest.mark.asyncio
async def test_bulk_qr_generate(client: AsyncClient, admin_token: str, test_department):
    """Test bulk QR code generation"""
    response = await client.post(
        "/api/v1/admin/bulk-qr-generate",
        json={"department_id": str(test_department.id)},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Bulk QR: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 0


@pytest.mark.asyncio
async def test_admin_endpoints_require_admin_auth(client: AsyncClient):
    """Test that admin endpoints require admin authentication"""
    response = await client.get("/api/v1/admin/flags")
    assert response.status_code == 403
    
    response = await client.get("/api/v1/admin/stats")
    assert response.status_code == 403
    
    response = await client.get("/api/v1/admin/audit-log")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_qr_invalid_employee(client: AsyncClient, admin_token: str):
    """Test generating QR for non-existent employee"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = await client.post(
        f"/api/v1/admin/generate-qr/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404
