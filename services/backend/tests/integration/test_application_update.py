from fastapi.testclient import TestClient
import pytest
from app.main import app
from sqlmodel import Session, select
from database_pkg.models import Application, JobDescription

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_update_application_success(
    client: TestClient, session: Session, current_user_token_headers: dict
):
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
    resp = client.patch(
        "/api/application/99999",
        json={"notes": "test"},
        headers=current_user_token_headers,
    )
    assert resp.status_code == 404


def test_update_application_invalid_status(
    client: TestClient, session: Session, current_user_token_headers: dict
):
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
