"""
Integration tests for employee endpoints
"""

import pytest
from httpx import AsyncClient

from app.models.models import Employee


@pytest.mark.asyncio
async def test_create_employee(client: AsyncClient, admin_token: str, test_department):
    """Test creating a new employee"""
    response = await client.post(
        "/api/v1/employees/",
        json={
            "employee_number": "NEWEMPLOYEE001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@test.com",
            "position": "Nurse",
            "department_id": str(test_department.id),
            "password": "secure123"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["employee_number"] == "NEWEMPLOYEE001"
    assert data["first_name"] == "John"
    assert "qr_code_data" in data


@pytest.mark.asyncio
async def test_list_employees(client: AsyncClient, admin_token: str, test_admin):
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
async def test_get_employee(client: AsyncClient, admin_token: str, test_admin):
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
    assert response.status_code == 403  # Forbidden (no auth header)

