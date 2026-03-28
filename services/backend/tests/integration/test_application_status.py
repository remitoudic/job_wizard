"""Integration tests for update-application-status endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from pathlib import Path

# Mock the upload directory creation before importing main
with patch.object(Path, 'mkdir'):
    from app.main import app

from app.core.security import create_access_token
from database_pkg.models import User, JobDescription, GeneratedLetter, Application, ApplicationStatus
from app.core.db import get_session

# Test database setup fixtures
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


@pytest.fixture(name="test_user")
def test_user_fixture(test_session: Session):
    """Create a test user."""
    from app.core.security import get_password_hash
    
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        surname="User",
        username="testuser",
        is_superuser=False,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    """Create authentication headers with valid JWT token."""
    access_token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="client")
def client_fixture(test_session: Session):
    """Create test client with database session override."""
    def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_application")
def test_application_fixture(test_session: Session, test_user: User):
    """Create a test application."""
    # Create Job Description
    job_desc = JobDescription(
        url="https://example.com/job",
        full_description="Test Description",
        requirements=["Python"],
        job_title="Test Job",
        company="Test Company",
        source="Manual"
    )
    test_session.add(job_desc)
    
    # Create Generated Letter
    gen_letter = GeneratedLetter(
        user_id=test_user.id,
        generated_letters=[{"model": "test", "letter": "text", "timestamp": "now"}]
    )
    test_session.add(gen_letter)
    test_session.commit()
    
    # Create Application
    application = Application(
        user_id=test_user.id,
        job_description_id=job_desc.id,
        generated_letter_id=gen_letter.id,
        header={"name": "Test"},
        cover_letter_final={"body": "Final"},
        status=ApplicationStatus.APPLIED
    )
    test_session.add(application)
    test_session.commit()
    test_session.refresh(application)
    return application


def test_update_status_success(client: TestClient, auth_headers: dict, test_application: Application, test_session: Session):
    """Test successful status update."""
    new_status = "interview"
    response = client.patch(
        f"/api/application/{test_application.id}/status",
        json={"status": new_status},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == new_status
    
    # Verify DB
    test_session.refresh(test_application)
    assert test_application.status == ApplicationStatus.INTERVIEW


def test_update_status_invalid_enum(client: TestClient, auth_headers: dict, test_application: Application):
    """Test updating with an invalid status string."""
    response = client.patch(
        f"/api/application/{test_application.id}/status",
        json={"status": "invalid_status_value"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]


def test_update_status_not_found(client: TestClient, auth_headers: dict):
    """Test updating a non-existent application."""
    response = client.patch(
        "/api/application/999999/status",
        json={"status": "interview"},
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "Application not found" in response.json()["detail"]
