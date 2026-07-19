import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from app.main import app
from app.api.deps import get_session
from app.core.security import get_password_hash, create_access_token
from database_pkg.models.user import User


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    admin = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpass123"),
        first_name="Admin",
        surname="User",
        is_superuser=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    token = create_access_token(subject=admin.email)
    return token, admin


@pytest.fixture(name="regular_user")
def regular_user_fixture(session: Session):
    user = User(
        email="user@example.com",
        username="user",
        hashed_password=get_password_hash("userpass123"),
        first_name="Regular",
        surname="User",
        is_superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(subject=user.email)
    return token, user


def test_list_users_restrictions(client: TestClient, admin_user, regular_user):
    admin_token, _ = admin_user
    user_token, _ = regular_user

    # Regular user should receive 403 Forbidden
    response = client.get(
        "/api/users/", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

    # Admin user should receive 200 OK
    response = client.get(
        "/api/users/", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2  # Admin + Regular user


def test_create_user_admin_only(
    client: TestClient, admin_user, regular_user, session: Session
):
    admin_token, _ = admin_user
    user_token, _ = regular_user

    new_user_payload = {
        "email": "new_created@example.com",
        "username": "newcreated",
        "first_name": "New",
        "surname": "Created",
        "password": "securepassword123",
        "is_superuser": False,
    }

    # Regular user tries to create a user -> should fail with 403
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {user_token}"},
        json=new_user_payload,
    )
    assert response.status_code == 403

    # Admin tries to create a user -> should succeed with 201 Created
    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_user_payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_created@example.com"
    assert data["username"] == "newcreated"
    assert data["is_superuser"] is False

    # Verify it's in the database
    db_user = session.exec(
        select(User).where(User.email == "new_created@example.com")
    ).first()
    assert db_user is not None
    assert db_user.first_name == "New"


def test_create_user_conflict(client: TestClient, admin_user):
    admin_token, _ = admin_user

    new_user_payload = {
        "email": "admin@example.com",  # Email conflict
        "username": "uniqueusername",
        "first_name": "Conflict",
        "surname": "User",
        "password": "securepassword123",
    }

    response = client.post(
        "/api/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_user_payload,
    )
    assert response.status_code == 400
    assert "email already exists" in response.json()["detail"]


@patch("app.api.routes.debug.get_temporal_client", new_callable=AsyncMock)
@patch("app.api.routes.debug.ollama.AsyncClient")
@patch("httpx.AsyncClient.post")
def test_debug_health_security(
    mock_httpx_post,
    mock_ollama_client_class,
    mock_get_temporal,
    client: TestClient,
    admin_user,
    regular_user,
):
    admin_token, _ = admin_user
    user_token, _ = regular_user

    # Mock temporal client to prevent actual gRPC calls
    mock_client = AsyncMock()
    mock_get_temporal.return_value = mock_client
    mock_client.service_client.check_health = AsyncMock()

    # Mock Ollama client
    mock_ollama_client = AsyncMock()
    mock_ollama_client_class.return_value = mock_ollama_client

    # Mock list() to return models
    mock_models_list = MagicMock()
    mock_model_obj = MagicMock()
    mock_model_obj.model = "gemma4:e2b"
    mock_models_list.models = [mock_model_obj]
    mock_ollama_client.list = AsyncMock(return_value=mock_models_list)
    mock_ollama_client.generate = AsyncMock()

    # Mock httpx post completions for Groq/OpenRouter
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_post.return_value = mock_response

    with patch("app.api.routes.debug.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "test-groq-key"
        mock_settings.GROQ_MODEL_1 = "test-groq-model"
        mock_settings.OPENROUTER_API_KEY = "test-or-key"
        mock_settings.OPENROUTER_MODEL = "test-or-model"
        mock_settings.OLLAMA_MODEL = "gemma4:e2b"
        mock_settings.OLLAMA_HOST = "http://ollama:11434"
        mock_settings.TEMPORAL_HOST = "temporal:7233"
        mock_settings.TEMPORAL_NAMESPACE = "jobwizard"
        mock_settings.CLOUDINARY_URL = None
        mock_settings.LLAMA_CLOUD_API_KEY = None

        # Regular user should be forbidden (403)
        response = client.get(
            "/api/debug/health", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

        # Admin user should succeed (200)
        response = client.get(
            "/api/debug/health", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "temporal" in data
        assert data["temporal"]["status"] == "ok"
        assert "ollama" in data
        assert data["ollama"]["inference_status"] == "ok"
        assert data["providers"]["groq"]["inference_status"] == "ok"
        assert data["providers"]["openrouter"]["inference_status"] == "ok"
