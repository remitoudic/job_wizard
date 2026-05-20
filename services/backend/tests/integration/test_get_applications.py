"""Integration tests for get-applications and get-application-details endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from pathlib import Path

# Mock the upload directory creation before importing main
with patch.object(Path, "mkdir"):
    from app.main import app

from app.core.security import create_access_token
from database_pkg.models import (
    User,
    JobDescription,
    GeneratedLetter,
    Application,
    ApplicationStatus,
)
from app.core.db import get_session


# Test database setup fixtures
@pytest.fixture(name="test_db")
def test_db_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="test_session")
def test_session_fixture(test_db):
    with Session(test_db) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(test_session: Session):
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
    access_token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="client")
def client_fixture(test_session: Session):
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_applications")
def test_applications_fixture(test_session: Session, test_user: User):
    apps = []
    for i in range(5):
        job_desc = JobDescription(
            url=f"https://example.com/job{i}",
            full_description=f"Test Description {i}",
            requirements=["Python"],
            job_title=f"Test Job {i}",
            company=f"Test Company {i}",
            source="Manual",
        )
        test_session.add(job_desc)

        gen_letter = GeneratedLetter(
            user_id=test_user.id,
            generated_letters=[{"model": "test", "letter": "text", "timestamp": "now"}],
        )
        test_session.add(gen_letter)
        test_session.commit()

        application = Application(
            user_id=test_user.id,
            job_description_id=job_desc.id,
            generated_letter_id=gen_letter.id,
            header={"name": f"Test {i}"},
            cover_letter_final={"body": f"Final {i}"},
            status=ApplicationStatus.APPLIED,
        )
        test_session.add(application)
        test_session.commit()
        test_session.refresh(application)
        apps.append(application)
    return apps


def test_get_applications_pagination(
    client: TestClient, auth_headers: dict, test_applications: list[Application]
):
    response = client.get("/api/applications?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "applications" in data
    assert "total" in data
    assert data["total"] == 5
    assert len(data["applications"]) == 2


def test_get_applications_without_details(
    client: TestClient, auth_headers: dict, test_applications: list[Application]
):
    response = client.get(
        "/api/applications?include_details=false", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    app_data = data["applications"][0]
    assert "id" in app_data
    assert "job_title" in app_data
    assert "cover_letter_final" not in app_data
    assert "job_description" not in app_data


def test_get_applications_with_details(
    client: TestClient, auth_headers: dict, test_applications: list[Application]
):
    response = client.get(
        "/api/applications?include_details=true", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    app_data = data["applications"][0]
    assert "cover_letter_final" in app_data
    assert "job_description" in app_data


def test_get_application_details_success(
    client: TestClient, auth_headers: dict, test_applications: list[Application]
):
    target_app = test_applications[0]
    response = client.get(
        f"/api/application/{target_app.id}/details", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "cover_letter_final" in data
    assert "job_description" in data
    assert "header" in data
    assert "requirements" in data
    assert data["cover_letter_final"]["body"] == target_app.cover_letter_final["body"]


def test_get_application_details_not_found(client: TestClient, auth_headers: dict):
    response = client.get("/api/application/9999/details", headers=auth_headers)
    assert response.status_code == 404
    assert "Application not found" in response.json()["detail"]
