"""
Unit tests for authentication
"""

import pytest
from app.api.endpoints.auth import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    """Test password hashing and verification"""
    password = "secure_password_123"
    hashed = hash_password(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test JWT token creation"""
    employee_id = "test-employee-id-123"
    token = create_access_token(employee_id)
    
    # Token should be a string
    assert isinstance(token, str)
    
    # Should be able to decode
    payload = decode_token(token)
    assert payload["sub"] == employee_id
    assert payload["type"] == "access"


def test_token_validation():
    """Test token validation"""
    # Valid token
    employee_id = "test-id"
    token = create_access_token(employee_id)
    payload = decode_token(token)
    
    assert payload["sub"] == employee_id
    
    # Invalid token should raise exception
    with pytest.raises(Exception):
        decode_token("invalid.token.here")