"""
Pytest Configuration and Fixtures
==================================

Shared fixtures for all tests including:
- Database session management
- Test client setup
- Mock data factories
- Authentication helpers

Author: Prior Auth AI Team
Version: 1.0.0
"""

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.db.base import Base
from backend.main import app
from backend.models import User, Clinic, UserRole, UserStatus, ClinicStatus
from backend.core.security import get_password_hash


# Test database URL (using separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/priorauth", "/priorauth_test")

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine (session scope)."""
    return test_engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(engine):
    """
    Set up test database schema before all tests.
    Tear down after all tests complete.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Automatically rolls back after test completion.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with database session override.
    """
    from backend.api.dependencies import get_db
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_clinic(db: Session) -> Clinic:
    """Create a test clinic."""
    clinic = Clinic(
        name="Test Medical Clinic",
        npi="9876543210",
        tax_id="98-7654321",
        address={
            "street": "456 Test Ave",
            "city": "Test City",
            "state": "TS",
            "zip": "12345"
        },
        phone="+1-555-999-8888",
        email="test@testclinic.com",
        status=ClinicStatus.ACTIVE,
        is_active=True,
        subscription_tier="trial",
        features_enabled=["ai_extraction", "analytics"]
    )
    
    db.add(clinic)
    db.commit()
    db.refresh(clinic)
    
    return clinic


@pytest.fixture
def test_admin_user(db: Session, test_clinic: Clinic) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@test.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        clinic_id=test_clinic.id,
        is_active=True,
        email_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def test_clinician_user(db: Session, test_clinic: Clinic) -> User:
    """Create a test clinician user."""
    user = User(
        email="clinician@test.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="Clinician",
        role=UserRole.CLINICIAN,
        status=UserStatus.ACTIVE,
        clinic_id=test_clinic.id,
        is_active=True,
        email_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def test_staff_user(db: Session, test_clinic: Clinic) -> User:
    """Create a test staff user."""
    user = User(
        email="staff@test.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="Staff",
        role=UserRole.STAFF,
        status=UserStatus.ACTIVE,
        clinic_id=test_clinic.id,
        is_active=True,
        email_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def admin_token_headers(client: TestClient, test_admin_user: User) -> dict:
    """Get authentication headers for admin user."""
    from backend.core.security import create_access_token
    
    token = create_access_token(subject=str(test_admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def clinician_token_headers(client: TestClient, test_clinician_user: User) -> dict:
    """Get authentication headers for clinician user."""
    from backend.core.security import create_access_token
    
    token = create_access_token(subject=str(test_clinician_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_token_headers(client: TestClient, test_staff_user: User) -> dict:
    """Get authentication headers for staff user."""
    from backend.core.security import create_access_token
    
    token = create_access_token(subject=str(test_staff_user.id))
    return {"Authorization": f"Bearer {token}"}


# Mock data factories

@pytest.fixture
def user_factory(db: Session, test_clinic: Clinic):
    """Factory for creating test users."""
    
    def _create_user(
        email: str = None,
        role: UserRole = UserRole.STAFF,
        status: UserStatus = UserStatus.ACTIVE,
        **kwargs
    ) -> User:
        if email is None:
            import uuid
            email = f"user_{uuid.uuid4().hex[:8]}@test.com"
        
        user = User(
            email=email,
            password_hash=get_password_hash("testpassword123"),
            first_name=kwargs.get("first_name", "Test"),
            last_name=kwargs.get("last_name", "User"),
            role=role,
            status=status,
            clinic_id=test_clinic.id,
            is_active=kwargs.get("is_active", True),
            email_verified=kwargs.get("email_verified", True),
            **{k: v for k, v in kwargs.items() if k not in [
                "first_name", "last_name", "is_active", "email_verified"
            ]}
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    return _create_user


@pytest.fixture
def clinic_factory(db: Session):
    """Factory for creating test clinics."""
    
    def _create_clinic(name: str = None, npi: str = None, **kwargs) -> Clinic:
        import uuid
        
        if name is None:
            name = f"Test Clinic {uuid.uuid4().hex[:8]}"
        
        if npi is None:
            npi = str(uuid.uuid4().int)[:10]
        
        clinic = Clinic(
            name=name,
            npi=npi,
            status=kwargs.get("status", ClinicStatus.ACTIVE),
            is_active=kwargs.get("is_active", True),
            address=kwargs.get("address", {}),
            **{k: v for k, v in kwargs.items() if k not in [
                "status", "is_active", "address"
            ]}
        )
        
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        
        return clinic
    
    return _create_clinic


# Pytest configuration

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related"
    )