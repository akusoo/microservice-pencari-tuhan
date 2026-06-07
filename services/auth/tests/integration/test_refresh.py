"""
Integration tests — POST /auth/refresh
"""
from tests.conftest import VALID_USER, register_and_login


class TestRefreshSuccess:
    def test_returns_new_access_token(self, client):
        old_token, _ = register_and_login(client)
        resp = client.post("/auth/refresh")  # cookie is sent automatically by TestClient
        assert resp.status_code == 200
        new_token = resp.json()["access_token"]
        assert new_token != old_token

    def test_sets_new_refresh_cookie(self, client):
        old_cookie = client.cookies.get("refresh_token")
        register_and_login(client)
        old_cookie = client.cookies.get("refresh_token")
        client.post("/auth/refresh")
        new_cookie = client.cookies.get("refresh_token")
        assert old_cookie != new_cookie  # rotation happened


class TestRefreshFailure:
    def test_missing_cookie_returns_401(self, client):
        # Never logged in — no cookie
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401

    def test_revoked_token_returns_401(self, client):
        register_and_login(client)
        # First refresh rotates the token
        client.post("/auth/refresh")
        # Manually restore the old cookie to simulate replay attack
        # (TestClient already replaced it, so sending again with fresh cookie is valid,
        #  but using the *old* cookie value is not — simulate by clearing and setting old value)
        old_cookie = client.cookies.get("refresh_token")
        client.post("/auth/refresh")  # this rotates away from old_cookie
        # Now set old_cookie back and try again
        client.cookies.set("refresh_token", old_cookie)
        resp = client.post("/auth/refresh")
        assert resp.status_code == 401
