"""
Unit tests — app/utils/jwt.py

No DB, no HTTP. Pure function calls.
"""
import time
import pytest
from jose import JWTError

from app.utils.jwt import create_access_token, verify_access_token


def test_create_access_token_returns_string():
    token = create_access_token("user-123", "member")
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_token_returns_payload():
    token = create_access_token("user-abc", "admin")
    payload = verify_access_token(token)

    assert payload["sub"] == "user-abc"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_verify_token_contains_exp():
    token = create_access_token("user-xyz", "member")
    payload = verify_access_token(token)
    assert "exp" in payload
    # expiry must be in the future
    assert payload["exp"] > time.time()


def test_verify_tampered_token_raises():
    token = create_access_token("user-123", "member")
    bad_token = token[:-4] + "xxxx"
    with pytest.raises(JWTError):
        verify_access_token(bad_token)


def test_verify_wrong_type_raises():
    """A token manually crafted without type='access' must be rejected."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    payload = {
        "sub": "user-123",
        "role": "member",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "refresh",  # wrong type
    }
    bad_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    with pytest.raises(JWTError):
        verify_access_token(bad_token)


def test_different_users_produce_different_tokens():
    t1 = create_access_token("user-1", "member")
    t2 = create_access_token("user-2", "member")
    assert t1 != t2
