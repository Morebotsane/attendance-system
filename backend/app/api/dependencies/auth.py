"""
Authentication dependencies
Export commonly used auth functions for easy importing
"""

from app.api.endpoints.auth import (
    get_current_employee,
    get_current_admin,
    hash_password,
    verify_password
)

__all__ = [
    "get_current_employee",
    "get_current_admin",
    "hash_password",
    "verify_password"
]