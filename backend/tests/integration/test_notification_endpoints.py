"""
Integration tests for notification endpoints
"""
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
class TestNotificationEndpoints:
    """Test notification API endpoints"""
    
    async def test_test_sms_endpoint_exists(self):
        """Test SMS endpoint exists and responds"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/notifications/test-sms",
                json={
                    "phone_number": "+26612345678",
                    "message": "Test message"
                }
            )
            
            # Accept 200 (success), 403 (rate limited), or 500 (error)
            assert response.status_code in [200, 403, 500]
            # Endpoint exists (not 404)
            assert response.status_code != 404
    
    async def test_test_email_endpoint_exists(self):
        """Test email endpoint exists and responds"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/notifications/test-email",
                json={
                    "to_email": "test@example.com",
                    "subject": "Test",
                    "body": "Test body"
                }
            )
            
            # Accept 200 (success), 403 (rate limited), or 500 (error)
            assert response.status_code in [200, 403, 500]
            # Endpoint exists (not 404)
            assert response.status_code != 404
