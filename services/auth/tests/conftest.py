"""
Shared fixtures for all test types.

Uses SQLite in-memory (via aiosqlite) so tests run without a real PostgreSQL instance.
StaticPool ensures all async connections within a test share the same in-memory DB.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionFactory = async_sessionmaker(engine_test, expire_on_commit=False)


async def _create_tables() -> None:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables() -> None:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test, drop after."""
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


@pytest.fixture
def client(reset_db):
    async def _override_get_db():
        async with TestSessionFactory() as session:
            yield session

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
