"""
Integration tests for the application update endpoint.

This module ensures that the full application update endpoint works correctly.
This allows users to modify the core attributes of an application (e.g., job title,
company, cover letter body, and status) through a single PATCH request.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from sqlmodel import Session, select, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from database_pkg.models import Application, JobDescription, User
from app.core.db import get_session
from app.core.security import create_access_token


@pytest.fixture(name="test_db")
def test_db_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(test_db):
    with Session(test_db) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    from app.core.security import get_password_hash

    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        surname="User",
        username="testuser",
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="current_user_token_headers")
def auth_headers_fixture(test_user: User):
    access_token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_update_application_success(
    client: TestClient, session: Session, current_user_token_headers: dict
):
    """
    Test a successful full update of an existing application.

    This test verifies that:
    1. A newly created application can be updated via PATCH.
    2. Multiple fields (title, company, status, notes, cover letter) can be updated simultaneously.
    3. The changes are properly persisted across both the `Application` and `JobDescription` tables.
    """
    # 1. Create an application first
    app_data = {
        "job_url": "https://test.com/job/1",
        "job_title": "Original Title",
        "job_company": "Original Company",
        "job_description": "Original Description",
        "job_requirements": ["Requirement 1"],
        "job_source": "Test",
        "generated_letters": [
            {"model": "test-model", "letter": "Original Letter", "timestamp": "now"}
        ],
        "selected_letter_index": 0,
        "header": {"name": "Test User"},
        "cover_letter_body": "Original Letter Body",
    }

    resp = client.post(
        "/api/save-application", json=app_data, headers=current_user_token_headers
    )
    assert resp.status_code == 200
    app_id = resp.json()["application_id"]

    # 2. Update it
    update_data = {
        "job_title": "New Title",
        "company": "New Company",
        "status": "interview",
        "notes": "Met with hiring manager.",
        "cover_letter_body": "Updated Letter Body",
    }

    resp = client.patch(
        f"/api/application/{app_id}",
        json=update_data,
        headers=current_user_token_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 3. Verify changes
    resp = client.get(
        f"/api/application/{app_id}/details", headers=current_user_token_headers
    )
    assert resp.status_code == 200
    details = resp.json()
    assert details["notes"] == "Met with hiring manager."
    assert details["cover_letter_final"]["body"] == "Updated Letter Body"

    # Check job description update
    stmt = (
        select(Application, JobDescription)
        .join(JobDescription)
        .where(Application.id == app_id)
    )
    result = session.exec(stmt).first()
    app, job = result
    assert job.job_title == "New Title"
    assert job.company == "New Company"
    assert app.status.value == "interview"


def test_update_application_not_found(
    client: TestClient, current_user_token_headers: dict
):
    """
    Test updating an application that does not exist.

    Verifies that passing an invalid or non-existent application ID
    correctly yields a 404 Not Found response.
    """
    resp = client.patch(
        "/api/application/99999",
        json={"notes": "test"},
        headers=current_user_token_headers,
    )
    assert resp.status_code == 404


def test_update_application_invalid_status(
    client: TestClient, session: Session, current_user_token_headers: dict
):
    """
    Test that updating an application with an invalid status is rejected.

    Ensures data integrity by preventing arbitrary strings from being
    saved to the application's status field.
    """
    # Create app
    app_data = {
        "job_url": "https://test.com/job/2",
        "job_title": "Title",
        "job_company": "Company",
        "job_description": "Desc",
        "job_requirements": [],
        "job_source": "Test",
        "generated_letters": [{"model": "m", "letter": "l", "timestamp": "t"}],
        "header": {},
        "cover_letter_body": "body",
    }
    resp = client.post(
        "/api/save-application", json=app_data, headers=current_user_token_headers
    )
    app_id = resp.json()["application_id"]

    # Invalid status
    resp = client.patch(
        f"/api/application/{app_id}",
        json={"status": "invalid_status"},
        headers=current_user_token_headers,
    )
    assert resp.status_code == 400
    assert "Invalid status" in resp.json()["detail"]
