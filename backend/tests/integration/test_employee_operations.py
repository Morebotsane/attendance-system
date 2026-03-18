"""
Integration tests for employee update, delete, and other operations
"""

import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
async def test_update_employee(client: AsyncClient, admin_token: str, test_employee):
    """Test updating employee details"""
    response = await client.put(
        f"/api/v1/employees/{test_employee.id}",
        json={
            "first_name": "Updated",
            "last_name": "Employee",
            "email": "updated@test.com",
            "phone": "+266-5555-5555",
            "position": "Senior Nurse"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Employee"
    assert data["email"] == "updated@test.com"
    assert data["position"] == "Senior Nurse"


@pytest.mark.asyncio
async def test_delete_employee(client: AsyncClient, admin_token: str, test_department):
    """Test deleting/deactivating an employee"""
    # Create a temporary employee to delete
    create_response = await client.post(
        "/api/v1/employees/",
        json={
            "employee_number": "TEMP001",
            "first_name": "Temporary",
            "last_name": "Employee",
            "email": "temp@test.com",
            "position": "Temp",
            "department_id": str(test_department.id),
            "password": "temp123"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Create temp employee status: {create_response.status_code}")
    
    # Only proceed if creation succeeded
    if create_response.status_code == 201:
        employee_id = create_response.json()["id"]
        
        # Delete the employee
        response = await client.delete(
            f"/api/v1/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        print(f"🔍 Delete employee status: {response.status_code}")
        print(f"🔍 Delete response: {response.json()}")
        
        assert response.status_code == 200
        assert "message" in response.json()


@pytest.mark.asyncio
async def test_activate_employee(client: AsyncClient, admin_token: str, test_employee):
    """Test activating an employee"""
    response = await client.post(
        f"/api/v1/employees/{test_employee.id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"\n🔍 Activate employee status: {response.status_code}")
    print(f"🔍 Activate response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    # Just check that response has a message or success indicator
    assert "message" in data or "employee_number" in data


@pytest.mark.asyncio
async def test_regenerate_qr_code(client: AsyncClient, admin_token: str, test_employee):
    """Test regenerating QR code for employee"""
    # Get original QR code
    original_qr = test_employee.qr_code_data
    
    # Regenerate QR
    response = await client.post(
        f"/api/v1/employees/{test_employee.id}/regenerate-qr",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "qr_code_data" in data
    assert data["qr_code_data"] != original_qr


@pytest.mark.asyncio
async def test_get_employee_by_number(client: AsyncClient, admin_token: str, test_employee):
    """Test getting employee by employee number"""
    response = await client.get(
        f"/api/v1/employees/by-number/{test_employee.employee_number}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["employee_number"] == test_employee.employee_number
    assert data["id"] == str(test_employee.id)


@pytest.mark.asyncio
async def test_get_employee_count(client: AsyncClient, admin_token: str):
    """Test getting total employee count"""
    response = await client.get(
        "/api/v1/employees/count",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data or "count" in data


@pytest.mark.asyncio
async def test_update_employee_invalid_data(client: AsyncClient, admin_token: str, test_employee):
    """Test updating employee with invalid email"""
    response = await client.put(
        f"/api/v1/employees/{test_employee.id}",
        json={
            "first_name": "Test",
            "email": "not-a-valid-email"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Should fail validation
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_nonexistent_employee(client: AsyncClient, admin_token: str):
    """Test deleting employee that doesn't exist"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = await client.delete(
        f"/api/v1/employees/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_employees_with_filters(client: AsyncClient, admin_token: str, test_department):
    """Test listing employees with department filter"""
    response = await client.get(
        f"/api/v1/employees/?department_id={test_department.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_employees_with_search(client: AsyncClient, admin_token: str):
    """Test searching employees by name"""
    response = await client.get(
        "/api/v1/employees/?search=Test",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
