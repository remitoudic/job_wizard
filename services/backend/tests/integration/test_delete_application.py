"""Integration tests for delete-application endpoint."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
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


def test_delete_application_success(client: TestClient, auth_headers: dict, test_application: Application, test_session: Session):
    """Test successful application deletion."""
    app_id = test_application.id
    response = client.delete(
        f"/api/application/{app_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Application deleted successfully"
    
    # Verify DB
    # We need to use a fresh query to see that it's gone
    statement = select(Application).where(Application.id == app_id)
    result = test_session.exec(statement).first()
    assert result is None


def test_delete_application_not_found(client: TestClient, auth_headers: dict):
    """Test deleting a non-existent application."""
    response = client.delete(
        "/api/application/999999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "Application not found" in response.json()["detail"]


def test_delete_other_user_application(client: TestClient, auth_headers: dict, test_session: Session):
    """Test deleting an application belonging to another user."""
    # Create another user and their application
    from app.core.security import get_password_hash
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("pass"),
        username="other",
    )
    test_session.add(other_user)
    test_session.commit()
    
    other_app = Application(
        user_id=other_user.id,
        # Minimal fields
        job_description_id=1,
        generated_letter_id=1,
        status=ApplicationStatus.APPLIED
    )
    # We need to make sure job_desc and gen_letter exist for FKs if sqlite enforces them.
    # The fixture already created them with IDs.
    
    test_session.add(other_app)
    test_session.commit()
    test_session.refresh(other_app)
    
    # Try to delete with original auth_headers (which belong to 'testuser')
    response = client.delete(
        f"/api/application/{other_app.id}",
        headers=auth_headers
    )
    
    # Should be 404 because the query filters by user_id
    assert response.status_code == 404
