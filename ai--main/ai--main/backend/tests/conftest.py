import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import User
from app.models.upload import Upload

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign key support for SQLite
@event.listens_for(engine_test, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """Return a TestClient wired to the test database."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper: register + login, return (client, token, user_data)
# ---------------------------------------------------------------------------

def _register_and_login(client: TestClient, username: str, email: str, password: str):
    """Register a user and log in, returning the bearer token."""
    client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    token = resp.json()["access_token"]
    return token


@pytest.fixture()
def auth_header(client):
    """Create a regular test user and return the Authorization header dict."""
    token = _register_and_login(client, "testuser", "test@example.com", "password123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_auth_header(client):
    """Create a second regular test user and return the Authorization header dict."""
    token = _register_and_login(client, "testuser2", "test2@example.com", "password123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth_header(client):
    """Create an admin user directly in the DB, log in, and return the header."""
    db = TestingSessionLocal()
    admin = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    resp = client.post(
        "/api/auth/login",
        data={"username": "adminuser", "password": "adminpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Upload fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_upload(client, auth_header):
    """Insert a completed upload directly into the DB and return its id."""
    db = TestingSessionLocal()
    # Fetch the user id from the token
    resp = client.get("/api/auth/me", headers=auth_header)
    user_id = resp.json()["id"]

    upload = Upload(
        user_id=user_id,
        filename="test_notes.pdf",
        file_type="pdf",
        file_path="/tmp/fake_test_file.pdf",
        file_size=1024,
        status="Completed",
        transcript="This is a test transcript about machine learning.",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    upload_id = upload.id
    db.close()
    return upload_id
