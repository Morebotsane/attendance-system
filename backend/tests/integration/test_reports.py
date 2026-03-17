"""
Integration tests for reports endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from PIL import Image
import io


def create_test_image() -> io.BytesIO:
    """Create a minimal valid PNG image for testing"""
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.mark.asyncio
async def test_daily_report_post(client: AsyncClient, admin_token: str, test_employee, test_department):
    """Test generating daily attendance report via POST"""
    # First, create an attendance record
    fake_image = create_test_image()
    await client.post(
        "/api/v1/attendance/check-in",
        data={
            "qr_code_data": test_employee.qr_code_data,
            "latitude": test_department.latitude,
            "longitude": test_department.longitude,
            "device_id": "test-device-daily"
        },
        files={"photo": ("test.png", fake_image, "image/png")}
    )
    
    # Now get the daily report via POST
    today = datetime.now().isoformat()
    response = await client.post(
        "/api/v1/reports/daily",
        json={"date": today},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Daily report status: {response.status_code}")
    if response.status_code != 200:
        print(f"🔍 Error: {response.json()}")
    else:
        print(f"🔍 Data: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "present" in data
    assert "absent" in data


@pytest.mark.asyncio
async def test_monthly_report_get(client: AsyncClient, admin_token: str):
    """Test generating monthly attendance report via GET"""
    year = datetime.now().year
    month = datetime.now().month
    
    response = await client.get(
        f"/api/v1/reports/monthly?year={year}&month={month}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Monthly report status: {response.status_code}")
    print(f"🔍 Monthly data: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert "month" in data
    assert "daily_breakdown" in data
    assert data["year"] == year
    assert data["month"] == month


@pytest.mark.asyncio
async def test_employee_report_get(client: AsyncClient, admin_token: str, test_employee):
    """Test generating report for specific employee via GET"""
    # Use ISO format datetime strings
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = datetime.now().isoformat()
    
    response = await client.get(
        f"/api/v1/reports/employee/{test_employee.id}?start_date={start_date}&end_date={end_date}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Employee report status: {response.status_code}")
    if response.status_code != 200:
        print(f"🔍 Error: {response.json()}")
    else:
        print(f"🔍 Data keys: {list(response.json().keys())}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_summary_report_get(client: AsyncClient, admin_token: str):
    """Test generating summary report via GET"""
    response = await client.get(
        "/api/v1/reports/summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Summary report status: {response.status_code}")
    print(f"🔍 Summary data: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    # Match actual response structure
    assert "today" in data
    assert "this_week" in data
    assert "this_month" in data
    assert "total_employees" in data["today"]


@pytest.mark.asyncio
async def test_flags_report_get(client: AsyncClient, admin_token: str):
    """Test getting attendance flags report"""
    response = await client.get(
        "/api/v1/reports/flags",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Flags report status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_reports_require_auth(client: AsyncClient):
    """Test that reports require authentication"""
    # Test summary endpoint without auth
    response = await client.get("/api/v1/reports/summary")
    assert response.status_code == 403
    
    # Test flags without auth
    response = await client.get("/api/v1/reports/flags")
    assert response.status_code == 403
    
    # Test monthly without auth
    response = await client.get("/api/v1/reports/monthly?year=2026&month=3")
    assert response.status_code == 403
