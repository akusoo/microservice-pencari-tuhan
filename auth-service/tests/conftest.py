"""
Shared fixtures for all test types.

Uses SQLite in-memory so tests run without a real PostgreSQL instance.
StaticPool ensures every request in a test shares the same in-memory DB connection.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base

SQLITE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db(reset_db):
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers used across multiple test modules ──────────────────────────────────

VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
}


def register_and_login(client: TestClient, user: dict = VALID_USER) -> tuple[str, TestClient]:
    """Register a user and return (access_token, client)."""
    client.post("/auth/register", json=user)
    resp = client.post("/auth/login", json={"username": user["username"], "password": user["password"]})
    return resp.json()["access_token"], client
