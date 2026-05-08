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
from database_pkg.models import User, JobDescription, GeneratedLetter, Application, ApplicationStatus, ApplicationStatusHistory
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

@pytest.fixture(name="session")
def session_fixture(test_db):
    """Create a test session."""
    with Session(test_db) as session:
        yield session

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create a test user."""
    from app.core.security import get_password_hash
    
    user = User(
        email="historyuser@example.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="History",
        surname="User",
        username="historyuser",
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    """Create authentication headers with valid JWT token."""
    access_token = create_access_token(subject=test_user.email)
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(autouse=True)
async def manage_pubsub():
    """No-op override: tests don't need the PubSub manager."""
    yield

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with database session override."""
    def override_get_session():
        yield session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_application_history_tracking(client: TestClient, session: Session, auth_headers: dict):
    # 1. Create an application
    # We need to simulate the multi-step process or just call the save-application endpoint
    app_data = {
        "job_url": "https://test.com/history-job",
        "job_title": "History Tester",
        "job_company": "History Corp",
        "job_description": "Description",
        "job_requirements": [],
        "job_source": "Test",
        "generated_letters": [
            {"model": "test-model", "letter": "Original Letter", "timestamp": "now"}
        ],
        "selected_letter_index": 0,
        "header": {"name": "Test User"},
        "cover_letter_body": "Original Letter Body"
    }
    
    # Note: save-application might have dependencies like generated_letter and job_description in DB
    # For simplicity, we'll test the history recording via PATCH and assume creation logic is correct
    # Actually, let's try to call save-application first
    resp = client.post("/api/save-application", json=app_data, headers=auth_headers)
    assert resp.status_code == 200
    app_id = resp.json()["application_id"]
    
    # 2. Check initial history (should have 'applied' entry)
    resp = client.get(f"/api/application/{app_id}/history", headers=auth_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 1
    assert history[0]["new_status"] == "applied"
    assert history[0]["old_status"] is None
    
    # 3. Update status to 'interview'
    update_data = {
        "status": "interview",
        "notes": "First interview scheduled"
    }
    resp = client.patch(f"/api/application/{app_id}", json=update_data, headers=auth_headers)
    assert resp.status_code == 200
    
    # 4. Verify history again
    resp = client.get(f"/api/application/{app_id}/history", headers=auth_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    # Newest should be first (ordered by created_at desc)
    assert history[0]["new_status"] == "interview"
    assert history[0]["old_status"] == "applied"
    assert history[0]["notes"] == "First interview scheduled"
    
    # 5. Update status to 'finish'
    resp = client.patch(f"/api/application/{app_id}", json={"status": "finish"}, headers=auth_headers)
    assert resp.status_code == 200
    
    # 6. Final verification
    resp = client.get(f"/api/application/{app_id}/history", headers=auth_headers)
    history = resp.json()
    assert len(history) == 3
    assert history[0]["new_status"] == "finish"
    assert history[0]["old_status"] == "interview"
    assert history[0]["notes"] == "Status manual update" # Default note
