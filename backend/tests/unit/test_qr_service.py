"""
Unit tests for QR service
"""

import pytest
from app.services.qr_service import qr_service


def test_generate_qr_data():
    """Test QR code generation"""
    employee_id = "test-123"
    qr_data = qr_service.generate_employee_qr_data(employee_id)
    
    assert qr_data is not None
    assert isinstance(qr_data, str)
    assert len(qr_data) > 0


def test_decode_qr_data():
    """Test QR code decoding"""
    employee_id = "test-123"
    qr_data = qr_service.generate_employee_qr_data(employee_id)
    
    result = qr_service.decode_qr_data(qr_data)
    
    assert result["valid"] is True
    assert result["employee_id"] == employee_id
