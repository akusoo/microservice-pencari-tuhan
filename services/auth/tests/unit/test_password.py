"""
Unit tests — hash/verify functions in app/core/security.py
"""
from app.core.security import hash_password, verify_password, hash_token


def test_hash_password_returns_bcrypt_string():
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$")


def test_hash_password_is_not_plaintext():
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_same_password_produces_different_hashes():
    h1 = hash_password("same_password")
    h2 = hash_password("same_password")
    assert h1 != h2


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_hash_token_is_deterministic():
    t = "some-random-refresh-token"
    assert hash_token(t) == hash_token(t)


def test_hash_token_different_inputs():
    assert hash_token("token-a") != hash_token("token-b")


def test_hash_token_is_sha256_hex():
    result = hash_token("any-token")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)
