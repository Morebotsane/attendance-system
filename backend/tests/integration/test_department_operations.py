"""
Integration tests for department update, delete, and stats operations
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, admin_token: str, test_department):
    """Test updating department details"""
    response = await client.put(
        f"/api/v1/departments/{test_department.id}",
        json={
            "name": "Updated Department",
            "location": "Block C, Floor 2",
            "latitude": -29.3200,
            "longitude": 27.4900,
            "geofence_radius": 150
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Department"
    assert data["location"] == "Block C, Floor 2"
    assert data["geofence_radius"] == 150


@pytest.mark.asyncio
async def test_update_department_geofence_only(client: AsyncClient, admin_token: str, test_department):
    """Test updating just the geofence radius"""
    response = await client.put(
        f"/api/v1/departments/{test_department.id}",
        json={
            "geofence_radius": 200
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["geofence_radius"] == 200


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, admin_token: str):
    """Test deleting a department"""
    # Create a temporary department to delete
    create_response = await client.post(
        "/api/v1/departments/",
        json={
            "name": "Temporary Department",
            "code": "TEMP",
            "location": "Temp Location",
            "latitude": -29.3000,
            "longitude": 27.5000,
            "geofence_radius": 100
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if create_response.status_code == 201:
        department_id = create_response.json()["id"]
        
        # Delete it
        response = await client.delete(
            f"/api/v1/departments/{department_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert "message" in response.json()


@pytest.mark.asyncio
async def test_get_department_employees(client: AsyncClient, admin_token: str, test_department, test_employee):
    """Test getting all employees in a department"""
    response = await client.get(
        f"/api/v1/departments/{test_department.id}/employees",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_department_stats(client: AsyncClient, admin_token: str, test_department):
    """Test getting department statistics"""
    response = await client.get(
        f"/api/v1/departments/{test_department.id}/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "total_employees" in data
    assert "department_name" in data


@pytest.mark.asyncio
async def test_update_department_location(client: AsyncClient, admin_token: str, test_department):
    """Test updating department location coordinates"""
    response = await client.put(
        f"/api/v1/departments/{test_department.id}",
        json={
            "latitude": -29.3500,
            "longitude": 27.5000
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == -29.3500
    assert data["longitude"] == 27.5000


@pytest.mark.asyncio
async def test_update_nonexistent_department(client: AsyncClient, admin_token: str):
    """Test updating department that doesn't exist"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = await client.put(
        f"/api/v1/departments/{fake_uuid}",
        json={
            "name": "New Name"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_department(client: AsyncClient, admin_token: str):
    """Test deleting department that doesn't exist"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = await client.delete(
        f"/api/v1/departments/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_employees_nonexistent_department(client: AsyncClient, admin_token: str):
    """Test getting employees for non-existent department"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = await client.get(
        f"/api/v1/departments/{fake_uuid}/employees",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_department_operations_require_admin(client: AsyncClient):
    """Test that department update/delete require admin authentication"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    # Test update without auth
    response = await client.put(
        f"/api/v1/departments/{fake_uuid}",
        json={"name": "Test"}
    )
    assert response.status_code == 403
    
    # Test delete without auth
    response = await client.delete(f"/api/v1/departments/{fake_uuid}")
    assert response.status_code == 403
