"""
Test configuration and fixtures
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import Base
from app.db.session import get_db
from app.models.models import Employee, Department
from app.api.endpoints.auth import hash_password, create_access_token
from app.services.qr_service import qr_service
from main import app


# Test database URL - Use PostgreSQL just like production!
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/attendance_test_db"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_department(db_session: AsyncSession) -> Department:
    """Create a test department"""
    department = Department(
        name="Test Department",
        code="TEST",
        location="Test Location",
        latitude=-29.3167,
        longitude=27.4833,
        geofence_radius=100
    )
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)
    return department


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession, test_department: Department) -> Employee:
    """Create a test admin user"""
    admin = Employee(
        employee_number="ADMIN001",
        first_name="Test",
        last_name="Admin",
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        department_id=test_department.id,
        qr_code_data="test_qr_code_admin",
        is_active=True,
        is_admin=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Generate proper QR code
    qr_data = qr_service.generate_employee_qr_data(str(admin.id))
    admin.qr_code_data = qr_data
    await db_session.commit()
    
    return admin


@pytest_asyncio.fixture
async def admin_token(test_admin: Employee) -> str:
    """Create an access token for the admin user"""
    # FIXED: Use correct function signature
    return create_access_token(employee_id=str(test_admin.id))


@pytest_asyncio.fixture
async def test_employee(db_session: AsyncSession, test_department: Department) -> Employee:
    """Create a test regular employee"""
    employee = Employee(
        employee_number="EMP001",
        first_name="Test",
        last_name="Employee",
        email="employee@test.com",
        hashed_password=hash_password("employee123"),
        department_id=test_department.id,
        qr_code_data="test_qr_code_emp",
        is_active=True,
        is_admin=False
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    
    # Generate proper QR code
    qr_data = qr_service.generate_employee_qr_data(str(employee.id))
    employee.qr_code_data = qr_data
    await db_session.commit()
    
    return employee
