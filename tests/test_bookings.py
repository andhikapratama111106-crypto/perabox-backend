import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app.core.security import get_password_hash
from app.models.models import User, Service, ServiceCategory
import uuid

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_customer(test_db):
    db = TestingSessionLocal()
    user = User(
        id=uuid.uuid4(),
        email="testcustomer@example.com",
        password_hash=get_password_hash("Test123!"),
        full_name="Test Customer",
        phone="081234567890",
        role="customer",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_service(test_db):
    db = TestingSessionLocal()
    
    # Create category
    category = ServiceCategory(
        id=uuid.uuid4(),
        name="Test Category",
        slug="test-category",
        is_active=True,
    )
    db.add(category)
    db.commit()
    
    # Create service
    service = Service(
        id=uuid.uuid4(),
        category_id=category.id,
        name="Test Service",
        slug="test-service",
        description="Test service description",
        base_price=100000,
        duration_minutes=60,
        is_active=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    db.close()
    return service


@pytest.fixture
def auth_token(test_customer):
    """Get authentication token for test customer."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "testcustomer@example.com",
            "password": "Test123!"
        }
    )
    return response.json()["access_token"]


def test_create_booking_authenticated(test_customer, test_service, auth_token):
    """Test creating a booking with valid authentication."""
    booking_data = {
        "service_id": str(test_service.id),
        "scheduled_date": "2026-02-15",
        "scheduled_time": "10:00",
        "address": "Jl. Test No. 123, Jakarta",
        "notes": "Test booking"
    }
    
    response = client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == str(test_customer.id)
    assert data["service_id"] == str(test_service.id)
    assert data["status"] == "pending"
    assert data["total_price"] == "100000.00"


def test_create_booking_unauthenticated(test_service):
    """Test creating a booking without authentication."""
    booking_data = {
        "service_id": str(test_service.id),
        "scheduled_date": "2026-02-15",
        "scheduled_time": "10:00",
        "address": "Jl. Test No. 123, Jakarta",
    }
    
    response = client.post("/api/v1/bookings", json=booking_data)
    assert response.status_code == 403  # No auth header


def test_create_booking_invalid_service(auth_token):
    """Test creating a booking with invalid service ID."""
    booking_data = {
        "service_id": str(uuid.uuid4()),  # Non-existent service
        "scheduled_date": "2026-02-15",
        "scheduled_time": "10:00",
        "address": "Jl. Test No. 123, Jakarta",
    }
    
    response = client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_booking_past_date(test_service, auth_token):
    """Test creating a booking with past date."""
    booking_data = {
        "service_id": str(test_service.id),
        "scheduled_date": "2020-01-01",  # Past date
        "scheduled_time": "10:00",
        "address": "Jl. Test No. 123, Jakarta",
    }
    
    response = client.post(
        "/api/v1/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # Validation error
