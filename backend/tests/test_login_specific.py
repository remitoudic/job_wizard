"""Test login with specific user credentials."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from pathlib import Path

# Mock the upload directory creation before importing main
with patch.object(Path, 'mkdir'):
    from app.main import app

from app.core.security import get_password_hash
from src.models import User
from app.core.db import get_session

@pytest.fixture(name="test_db")
def test_db_fixture():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="test_session")
def test_session_fixture(test_db):
    """Create a test session."""
    with Session(test_db) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(test_session: Session):
    """Create test client with database session override."""
    def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_login_specific_user(client: TestClient, test_session: Session):
    """Test login with specific credentials requested by user."""
    email = "remitoudic@gmail" # Using exact string from request (assuming permissive validation or valid format)
    password = "remitoudic"
    
    # Create the user first
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name="Remi",
        surname="Toudic",
        username="remitoudic",
        is_superuser=False,
    )
    test_session.add(user)
    test_session.commit()
    
    # Attempt login
    # OAuth2PasswordRequestForm expects 'username' and 'password' in form-data
    login_data = {
        "username": email,
        "password": password
    }
    
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
