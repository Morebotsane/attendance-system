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
async def test_daily_report(client: AsyncClient, admin_token: str, test_employee, test_department):
    """Test generating daily attendance report"""
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
    
    # Now get the daily report
    today = datetime.now().strftime("%Y-%m-%d")
    response = await client.get(
        f"/api/v1/reports/daily?date={today}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Daily report status: {response.status_code}")
    if response.status_code != 200:
        print(f"🔍 Error: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "present" in data
    assert "records" in data


@pytest.mark.asyncio
async def test_monthly_report(client: AsyncClient, admin_token: str):
    """Test generating monthly attendance report"""
    # Get current month report
    year = datetime.now().year
    month = datetime.now().month
    
    response = await client.get(
        f"/api/v1/reports/monthly?year={year}&month={month}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Monthly report status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert "year" in data
    assert "month" in data
    assert "statistics" in data


@pytest.mark.asyncio
async def test_employee_report(client: AsyncClient, admin_token: str, test_employee):
    """Test generating report for specific employee"""
    # Get last 30 days
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    response = await client.get(
        f"/api/v1/reports/employee/{test_employee.id}?start_date={start_date}&end_date={end_date}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Employee report status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert "employee" in data
    assert "attendance_records" in data
    assert "statistics" in data


@pytest.mark.asyncio
async def test_summary_report(client: AsyncClient, admin_token: str):
    """Test generating summary report"""
    response = await client.get(
        "/api/v1/reports/summary",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Summary report status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_employees" in data
    assert "total_departments" in data


@pytest.mark.asyncio
async def test_department_report(client: AsyncClient, admin_token: str, test_department):
    """Test generating department attendance report"""
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    response = await client.get(
        f"/api/v1/reports/department/{test_department.id}?start_date={start_date}&end_date={end_date}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Department report status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert "department" in data
    assert "statistics" in data


@pytest.mark.asyncio
async def test_reports_require_auth(client: AsyncClient):
    """Test that reports require authentication"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    response = await client.get(f"/api/v1/reports/daily?date={today}")
    assert response.status_code == 403  # Forbidden
