"""
Unit tests — Pydantic validation in app/schemas/auth.py
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister, UserLogin


class TestUserRegister:
    def test_valid_data_passes(self):
        data = UserRegister(username="alice", email="alice@example.com", password="strongpass")
        assert data.username == "alice"

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(username="alice", email="alice@example.com", password="short")
        assert "8 characters" in str(exc_info.value)

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserRegister(username="alice", email="not-an-email", password="strongpass")

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            UserRegister(username="alice", email="alice@example.com")  # no password


class TestUserLogin:
    def test_valid_login_data(self):
        data = UserLogin(username="alice", password="mypassword")
        assert data.username == "alice"
        assert data.password == "mypassword"

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            UserLogin(password="mypassword")
