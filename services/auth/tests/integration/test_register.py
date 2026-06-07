"""
Integration tests — POST /auth/register

Tests hit the full FastAPI stack with a real SQLite-backed DB.
"""


class TestRegisterSuccess:
    def test_returns_201_with_user_fields(self, client):
        resp = client.post("/auth/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["role"] == "member"
        assert data["is_active"] is True
        assert "id" in data
        assert "password_hash" not in data  # must never be exposed


class TestRegisterValidation:
    def test_duplicate_username_returns_400(self, client):
        payload = {"username": "alice", "email": "a@example.com", "password": "password123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json={**payload, "email": "b@example.com"})
        assert resp.status_code == 400
        assert "Username" in resp.json()["detail"]

    def test_duplicate_email_returns_400(self, client):
        payload = {"username": "alice", "email": "same@example.com", "password": "password123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json={**payload, "username": "bob"})
        assert resp.status_code == 400
        assert "Email" in resp.json()["detail"]

    def test_password_too_short_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "short",
        })
        assert resp.status_code == 422

    def test_missing_fields_returns_422(self, client):
        resp = client.post("/auth/register", json={"username": "alice"})
        assert resp.status_code == 422

    def test_invalid_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "username": "alice",
            "email": "not-an-email",
            "password": "password123",
        })
        assert resp.status_code == 422
