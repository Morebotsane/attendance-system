"""
Integration tests for department endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, admin_token: str):
    """Test creating a new department"""
    response = await client.post(
        "/api/v1/departments/",
        json={
            "name": "Emergency",
            "code": "ER",
            "location": "Block B, Floor 1",
            "latitude": -29.3180,
            "longitude": 27.4840,
            "geofence_radius": 75
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Emergency"
    assert data["code"] == "ER"


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, admin_token: str, test_department):
    """Test listing all departments"""
    response = await client.get(
        "/api/v1/departments/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the test department


@pytest.mark.asyncio
async def test_get_department(client: AsyncClient, admin_token: str, test_department):
    """Test getting specific department"""
    response = await client.get(
        f"/api/v1/departments/{test_department.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Department"
