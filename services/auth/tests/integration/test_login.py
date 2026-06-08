"""
Integration tests — POST /auth/login
"""
import asyncio

from sqlalchemy import update
from tests.conftest import VALID_USER, TestSessionFactory


class TestLoginSuccess:
    def test_returns_access_token(self, client):
        client.post("/auth/register", json=VALID_USER)
        resp = client.post("/auth/login", json={
            "username": VALID_USER["username"],
            "password": VALID_USER["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_sets_httponly_refresh_cookie(self, client):
        client.post("/auth/register", json=VALID_USER)
        resp = client.post("/auth/login", json={
            "username": VALID_USER["username"],
            "password": VALID_USER["password"],
        })
        assert "refresh_token" in resp.cookies


class TestLoginFailure:
    def test_wrong_password_returns_401(self, client):
        client.post("/auth/register", json=VALID_USER)
        resp = client.post("/auth/login", json={
            "username": VALID_USER["username"],
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "username": "nobody",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_inactive_user_returns_403(self, client):
        from app.models.user import User

        client.post("/auth/register", json=VALID_USER)

        async def _deactivate():
            async with TestSessionFactory() as session:
                await session.execute(
                    update(User).where(User.username == VALID_USER["username"]).values(is_active=False)
                )
                await session.commit()

        asyncio.run(_deactivate())

        resp = client.post("/auth/login", json={
            "username": VALID_USER["username"],
            "password": VALID_USER["password"],
        })
        assert resp.status_code == 403
