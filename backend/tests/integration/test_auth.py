# Fix test_auth.py (integration)
"""
Integration tests for authentication
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_admin):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "employee_number": "ADMIN001",
            "password": "admin123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "employee_number": "ADMIN001",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
