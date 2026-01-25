from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
import pytest
from app.main import app
from app.api.deps import get_session
from app.core.security import get_password_hash
from src.models.user import User

# Setup in-memory database for testing
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

def test_user_authentication_unit(session: Session):
    from app.services.user import user_service
    
    email = "test@example.com"
    password = "password123"
    
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name="Test",
        surname="User"
    )
    session.add(user)
    session.commit()
    
    # Test valid credentials
    authenticated_user = user_service.authenticate(session, email, password)
    assert authenticated_user is not None
    assert authenticated_user.email == email
    
    # Test invalid password
    failed_auth = user_service.authenticate(session, email, "wrongpassword")
    assert failed_auth is None
    
    # Test non-existent user
    unknown_user = user_service.authenticate(session, "unknown@example.com", password)
    assert unknown_user is None

def test_login_integration(client: TestClient, session: Session):
    email = "integration@example.com"
    password = "integrationpass"
    
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name="Integration",
        surname="User"
    )
    session.add(user)
    session.commit()
    
    # Test successful login
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test invalid login
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": "wrongpassword"},
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
