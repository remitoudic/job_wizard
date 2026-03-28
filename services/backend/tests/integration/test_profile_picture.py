import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
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

@pytest.fixture(name="user_token")
def user_token_fixture(session: Session):
    user = User(
        email="test_pic@example.com",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        surname="Pic"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(subject=user.email)
    return token, user

@patch("app.api.routes.users.cloudinary_service.upload_image")
def test_upload_profile_picture(mock_upload, client: TestClient, user_token):
    token, user = user_token
    mock_upload.return_value = "https://example.com/uploaded.jpg"

    files = {'file': ('test.jpg', b"fake_image_content", 'image/jpeg')}
    response = client.post(
        "/api/users/me/picture",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data["profile_picture_url"] == "https://example.com/uploaded.jpg"
    mock_upload.assert_called_once()

@patch("app.api.routes.users.cloudinary_service.delete_image")
def test_delete_profile_picture(mock_delete, client: TestClient, user_token, session: Session):
    token, user = user_token
    
    # Set the profile picture initially
    user.profile_picture_url = "https://example.com/to_delete.jpg"
    session.add(user)
    session.commit()

    response = client.delete(
        "/api/users/me/picture",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["profile_picture_url"] is None
    mock_delete.assert_called_once_with("https://example.com/to_delete.jpg")
