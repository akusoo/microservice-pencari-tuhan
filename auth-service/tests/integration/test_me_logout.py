"""
Integration tests — GET /auth/me and POST /auth/logout
"""
from tests.conftest import VALID_USER, register_and_login


class TestGetMe:
    def test_returns_user_info(self, client):
        token, _ = register_and_login(client)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == VALID_USER["username"]
        assert data["email"] == VALID_USER["email"]

    def test_no_token_returns_403(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_returns_200_with_message(self, client):
        token, _ = register_and_login(client)
        resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_refresh_after_logout_returns_401(self, client):
        token, _ = register_and_login(client)
        client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        resp = client.post("/auth/refresh")  # refresh token was revoked
        assert resp.status_code == 401

    def test_logout_without_token_returns_401(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code in (401, 403)
