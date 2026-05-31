"""Integration tests for save-application endpoint."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from datetime import datetime
from unittest.mock import patch
from pathlib import Path

# Mock the upload directory creation before importing main
with patch.object(Path, "mkdir"):
    from app.main import app

from app.core.security import create_access_token
from database_pkg.models import User, JobDescription, GeneratedLetter, Application
from app.core.db import get_session


# Test database setup
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


def test_save_application_success(
    client: TestClient, test_session: Session, auth_headers: dict, test_user: User
):
    """Test successful application save."""
    request_data = {
        "job_url": "https://www.linkedin.com/jobs/view/123456789",
        "job_title": "Senior Backend Engineer",
        "job_company": "TechCorp",
        "job_description": "We are looking for a talented backend engineer...",
        "job_requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "job_source": "LinkedIn",
        "generated_letters": [
            {
                "model": "gpt-4",
                "letter": "Dear Hiring Manager, I am excited to apply...",
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "model": "claude-3",
                "letter": "To whom it may concern, I am writing to express...",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
        "selected_letter_index": 0,
        "header": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "address": "123 Main St, City, Country",
        },
        "cover_letter_body": "Dear Hiring Manager, I am excited to apply... [Final edited version]",
    }

    response = client.post(
        "/api/save-application", json=request_data, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "application_id" in data
    assert "job_description_id" in data
    assert "generated_letter_id" in data
    assert data["message"] == "Application saved successfully"

    # Verify database records
    job_desc = test_session.get(JobDescription, data["job_description_id"])
    assert job_desc is not None
    assert job_desc.url == request_data["job_url"]
    assert job_desc.job_title == request_data["job_title"]

    gen_letter = test_session.get(GeneratedLetter, data["generated_letter_id"])
    assert gen_letter is not None
    assert gen_letter.user_id == test_user.id
    assert len(gen_letter.generated_letters) == 2

    application = test_session.get(Application, data["application_id"])
    assert application is not None
    assert application.user_id == test_user.id
    assert application.job_description_id == data["job_description_id"]
    assert application.generated_letter_id == data["generated_letter_id"]
    assert application.header["name"] == "Test User"


def test_save_application_job_description_deduplication(
    client: TestClient, test_session: Session, auth_headers: dict, test_user: User
):
    """Test that same job URL reuses existing JobDescription and updates the existing Application."""
    job_url = "https://www.linkedin.com/jobs/view/987654321"

    # Create first application
    request_data = {
        "job_url": job_url,
        "job_title": "Frontend Developer",
        "job_company": "WebCo",
        "job_description": "React developer needed...",
        "job_requirements": ["React", "TypeScript"],
        "job_source": "LinkedIn",
        "generated_letters": [
            {
                "model": "gpt-4",
                "letter": "First application letter...",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
        "selected_letter_index": 0,
        "header": {"name": "Test User"},
        "cover_letter_body": "First application letter...",
    }

    response1 = client.post(
        "/api/save-application", json=request_data, headers=auth_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    job_desc_id_1 = data1["job_description_id"]
    app_id_1 = data1["application_id"]

    # Create second application with same URL
    request_data["cover_letter_body"] = "Second application letter..."
    request_data["generated_letters"][0]["letter"] = "Second application letter..."

    response2 = client.post(
        "/api/save-application", json=request_data, headers=auth_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    job_desc_id_2 = data2["job_description_id"]
    app_id_2 = data2["application_id"]

    # Verify same JobDescription was reused
    assert job_desc_id_1 == job_desc_id_2

    # Verify that the existing application was updated and reused (deduplicated)
    assert app_id_1 == app_id_2

    # Verify database was updated with new cover letter
    updated_app = test_session.get(Application, app_id_1)
    assert updated_app is not None
    assert updated_app.cover_letter_final["body"] == "Second application letter..."


def test_save_application_unauthorized(client: TestClient):
    """Test that endpoint requires authentication."""
    request_data = {
        "job_url": "https://example.com/job",
        "job_title": "Test Job",
        "job_company": "Test Company",
        "job_description": "Test description",
        "job_requirements": [],
        "job_source": "Test",
        "generated_letters": [],
        "selected_letter_index": 0,
        "header": {},
        "cover_letter_body": "Test",
    }

    # Request without auth headers
    response = client.post("/api/save-application", json=request_data)
    assert response.status_code == 401


def test_save_application_with_empty_generated_letters(
    client: TestClient, test_session: Session, auth_headers: dict, test_user: User
):
    """Test handling of empty generated letters list."""
    request_data = {
        "job_url": "https://www.linkedin.com/jobs/view/111111",
        "job_title": "Data Scientist",
        "job_company": "DataCo",
        "job_description": "Data science position...",
        "job_requirements": ["Python", "ML"],
        "job_source": "LinkedIn",
        "generated_letters": [],  # Empty list
        "selected_letter_index": 0,
        "header": {"name": "Test User"},
        "cover_letter_body": "Manually written cover letter",
    }

    # This should fail because we can't select index 0 from empty list
    response = client.post(
        "/api/save-application", json=request_data, headers=auth_headers
    )
    assert response.status_code == 500  # Internal server error due to IndexError
