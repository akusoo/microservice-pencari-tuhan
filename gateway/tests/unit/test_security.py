"""
Unit tests — gateway/app/core/security.py (decode_token)

No HTTP, no upstream. Pure function calls.
"""
import pytest
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.core.security import decode_token
from tests.conftest import TEST_SECRET, TEST_ALGORITHM, make_token


def test_valid_token_returns_payload():
    token = make_token(user_id="user-123", role="member")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "member"
    assert payload["type"] == "access"


def test_valid_admin_token_returns_correct_role():
    token = make_token(user_id="admin-xyz", role="admin")
    payload = decode_token(token)
    assert payload["role"] == "admin"


def test_tampered_token_raises_401():
    token = make_token()
    tampered = token[:-4] + "xxxx"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401


def test_expired_token_raises_401():
    token = make_token(expires_in=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_wrong_token_type_raises_401():
    """Refresh token must not be accepted as access token."""
    token = make_token(token_type="refresh")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_wrong_secret_raises_401():
    payload = {
        "sub": "user-123",
        "role": "member",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    token = jwt.encode(payload, "wrong-secret", algorithm=TEST_ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_garbage_string_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("this.is.garbage")
    assert exc_info.value.status_code == 401
