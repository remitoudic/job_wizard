"""Integration tests for the check-duplicate-application endpoint."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

with patch.object(Path, "mkdir"):
    from app.main import app

from app.core.db import get_session
from app.core.security import create_access_token
from database_pkg.models import Application, ApplicationStatus, JobDescription, User


@pytest.fixture(name="test_db")
def test_db_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="test_session")
def test_session_fixture(test_db):
    with Session(test_db) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(test_session: Session):
    from app.core.security import get_password_hash
    user = User(email="testuser@example.com", hashed_password=get_password_hash("testpass123"), first_name="Test", surname="User", username="testuser", is_superuser=False)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="other_user")
def other_user_fixture(test_session: Session):
    from app.core.security import get_password_hash
    user = User(email="other@example.com", hashed_password=get_password_hash("otherpass"), first_name="Other", surname="User", username="otheruser", is_superuser=False)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    return {"Authorization": f"Bearer {create_access_token(subject=test_user.email)}"}


@pytest.fixture(name="client")
def client_fixture(test_session: Session):
    def override_get_session():
        yield test_session
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def create_app_for_user(session: Session, user: User, job_url: str, job_title: str = "Test Job", company: str = "TestCo") -> Application:
    job_desc = JobDescription(url=job_url, full_description="Test desc", requirements=["Python"], job_title=job_title, company=company, source="Manual")
    session.add(job_desc)
    session.commit()
    session.refresh(job_desc)
    app = Application(user_id=user.id, job_description_id=job_desc.id, status=ApplicationStatus.APPLIED, cover_letter_final={"model": "test", "timestamp": "2025-01-01", "body": "Dear..."})
    session.add(app)
    session.commit()
    session.refresh(app)
    return app


class TestCheckDuplicateNoMatch:
    def test_no_applications_at_all(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/application/check-duplicate?job_url=https://example.com/job/123", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {"is_duplicate": False, "existing_application": None}

    def test_different_url_no_match(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, "https://example.com/job/other")
        resp = client.get("/api/application/check-duplicate?job_url=https://example.com/job/123", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {"is_duplicate": False, "existing_application": None}


class TestCheckDuplicateExactMatch:
    def test_exact_url_match(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        url = "https://example.com/job/123"
        app = create_app_for_user(test_session, test_user, url)
        resp = client.get(f"/api/application/check-duplicate?job_url={url}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_duplicate"] is True
        assert data["existing_application"]["id"] == app.id
        assert data["existing_application"]["cover_letter_body"] == "Dear..."


class TestCheckDuplicateUrlNormalization:
    def test_www_vs_non_www(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, "https://example.com/job/123")
        resp = client.get("/api/application/check-duplicate?job_url=https://www.example.com/job/123", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True

    def test_trailing_slash(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, "https://example.com/job/123/")
        resp = client.get("/api/application/check-duplicate?job_url=https://example.com/job/123", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True


class TestCheckDuplicateLinkedIn:
    VIEW_URL = "https://www.linkedin.com/jobs/view/4386770393/"
    COLLECTIONS_URL = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4386770393"

    def test_stored_view_searched_collections(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, self.VIEW_URL)
        resp = client.get(f"/api/application/check-duplicate?job_url={self.COLLECTIONS_URL}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True

    def test_stored_collections_searched_view(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, self.COLLECTIONS_URL)
        resp = client.get(f"/api/application/check-duplicate?job_url={self.VIEW_URL}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True

    def test_view_url_without_www(self, client: TestClient, auth_headers: dict, test_session: Session, test_user: User):
        create_app_for_user(test_session, test_user, "https://www.linkedin.com/jobs/view/4386770393/")
        resp = client.get("/api/application/check-duplicate?job_url=https://linkedin.com/jobs/view/4386770393/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True


class TestCheckDuplicateOtherUser:
    def test_other_user_app_not_matched(self, client: TestClient, auth_headers: dict, test_session: Session, other_user: User):
        create_app_for_user(test_session, other_user, "https://example.com/job/123")
        resp = client.get("/api/application/check-duplicate?job_url=https://example.com/job/123", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is False


class TestCheckDuplicateUnauthorized:
    def test_no_auth_header(self, client: TestClient):
        resp = client.get("/api/application/check-duplicate?job_url=https://example.com/job/123")
        assert resp.status_code == 401
