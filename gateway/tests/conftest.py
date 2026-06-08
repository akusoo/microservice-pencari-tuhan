import os

# Must be set before app import — settings is a module-level singleton
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-gateway-tests-32c!")

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import httpx
from httpx import AsyncClient, ASGITransport
from jose import jwt

from app.main import app
from app.circuit_breaker import _breakers, CircuitState

TEST_SECRET = os.environ["SECRET_KEY"]
TEST_ALGORITHM = "HS256"

USER_ID_MEMBER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
USER_ID_ADMIN  = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


# ── Token helpers ─────────────────────────────────────────────────────────────

def make_token(
    user_id: str = USER_ID_MEMBER,
    role: str = "member",
    token_type: str = "access",
    expires_in: timedelta = timedelta(minutes=15),
) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm=TEST_ALGORITHM)


# ── Upstream mock helper ──────────────────────────────────────────────────────

@asynccontextmanager
async def mock_upstream(status_code: int = 200, body: bytes = b'{"ok":true}', headers: dict = None):
    """Patch httpx.AsyncClient in the proxy router to return a canned response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.content = body
    mock_resp.headers = httpx.Headers(headers or {})

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_resp)

    with patch("app.routers.proxy.httpx.AsyncClient") as MockClass:
        MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClass.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_client


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Ensure circuit breakers start clean for every test."""
    for cb in _breakers.values():
        cb._failures = 0
        cb._state = CircuitState.CLOSED
    yield
    for cb in _breakers.values():
        cb._failures = 0
        cb._state = CircuitState.CLOSED


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def member_token():
    return make_token(user_id=USER_ID_MEMBER, role="member")


@pytest.fixture
def admin_token():
    return make_token(user_id=USER_ID_ADMIN, role="admin")


@pytest.fixture
def expired_token():
    return make_token(expires_in=timedelta(seconds=-1))


@pytest.fixture
def refresh_type_token():
    return make_token(token_type="refresh")
