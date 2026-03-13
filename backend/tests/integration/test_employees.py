"""
Integration tests for employee endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Employee, Department
from app.api.endpoints.auth import hash_password, create_access_token


@pytest.fixture
async def test_department(db_session: AsyncSession):
    """Create test department"""
    department = Department(
        name="Test Department",
        code="TEST",
        latitude=-29.3167,
        longitude=27.4833,
        geofence_radius=100
    )
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)
    return department


@pytest.fixture
async def test_admin(db_session: AsyncSession, test_department):
    """Create test admin employee"""
    admin = Employee(
        employee_number="ADMIN001",
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        qr_code_data="test_qr_data",
        department_id=test_department.id,
        is_active=True,
        is_admin=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token(test_admin):
    """Create admin access token"""
    return create_access_token(str(test_admin.id))


@pytest.mark.asyncio
async def test_create_employee(client: AsyncClient, admin_token, test_department):
    """Test creating a new employee"""
    response = await client.post(
        "/api/v1/employees/",
        json={
            "employee_number": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "position": "Nurse",
            "department_id": str(test_department.id),
            "password": "secure123"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["employee_number"] == "EMP001"
    assert data["first_name"] == "John"
    assert "qr_code_data" in data


@pytest.mark.asyncio
async def test_list_employees(client: AsyncClient, admin_token, test_admin):
    """Test listing employees"""
    response = await client.get(
        "/api/v1/employees/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the admin


@pytest.mark.asyncio
async def test_get_employee(client: AsyncClient, admin_token, test_admin):
    """Test getting specific employee"""
    response = await client.get(
        f"/api/v1/employees/{test_admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["employee_number"] == "ADMIN001"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that endpoints require authentication"""
    response = await client.get("/api/v1/employees/")
    assert response.status_code == 403  # No auth header