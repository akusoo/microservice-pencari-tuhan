"""
Contract tests — verify every response shape matches the published API contract.

Approach: define the expected JSON Schema for each response, then validate
actual responses against it. This ensures the service never silently breaks
its contract with consumers (e.g. API Gateway, other services, frontend).
"""
import pytest
from jsonschema import validate, ValidationError

# ── Contract definitions (the "published API") ────────────────────────────────

USER_CONTRACT = {
    "type": "object",
    "required": ["id", "username", "email", "role", "is_active", "created_at"],
    "properties": {
        "id":         {"type": "string"},
        "username":   {"type": "string"},
        "email":      {"type": "string"},
        "role":       {"type": "string", "enum": ["member", "librarian", "admin"]},
        "is_active":  {"type": "boolean"},
        "created_at": {"type": "string"},
    },
    "additionalProperties": False,
}

TOKEN_CONTRACT = {
    "type": "object",
    "required": ["access_token", "token_type"],
    "properties": {
        "access_token": {"type": "string", "minLength": 10},
        "token_type":   {"type": "string", "enum": ["bearer"]},
    },
    "additionalProperties": False,
}

MESSAGE_CONTRACT = {
    "type": "object",
    "required": ["message"],
    "properties": {
        "message": {"type": "string"},
    },
    "additionalProperties": False,
}

ERROR_CONTRACT = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {},  # string or list — FastAPI can return both
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def assert_contract(data: dict, schema: dict):
    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        pytest.fail(f"Response does not match contract:\n{exc.message}")


_USER_PAYLOAD = {
    "username": "contractuser",
    "email": "contract@example.com",
    "password": "contractpass",
}


@pytest.fixture
def registered_client(client):
    client.post("/auth/register", json=_USER_PAYLOAD)
    return client


@pytest.fixture
def logged_in(registered_client):
    resp = registered_client.post("/auth/login", json={
        "username": _USER_PAYLOAD["username"],
        "password": _USER_PAYLOAD["password"],
    })
    token = resp.json()["access_token"]
    return registered_client, token


# ── Contract tests ────────────────────────────────────────────────────────────

class TestRegisterContract:
    def test_register_response_matches_user_contract(self, client):
        resp = client.post("/auth/register", json=_USER_PAYLOAD)
        assert resp.status_code == 201
        assert_contract(resp.json(), USER_CONTRACT)

    def test_register_does_not_expose_password_hash(self, client):
        resp = client.post("/auth/register", json=_USER_PAYLOAD)
        assert "password_hash" not in resp.json()
        assert "password" not in resp.json()


class TestLoginContract:
    def test_login_response_matches_token_contract(self, registered_client):
        resp = registered_client.post("/auth/login", json={
            "username": _USER_PAYLOAD["username"],
            "password": _USER_PAYLOAD["password"],
        })
        assert resp.status_code == 200
        assert_contract(resp.json(), TOKEN_CONTRACT)

    def test_login_error_matches_error_contract(self, client):
        resp = client.post("/auth/login", json={"username": "nobody", "password": "wrong"})
        assert resp.status_code == 401
        assert_contract(resp.json(), ERROR_CONTRACT)


class TestRefreshContract:
    def test_refresh_response_matches_token_contract(self, logged_in):
        client, _ = logged_in
        resp = client.post("/auth/refresh")
        assert resp.status_code == 200
        assert_contract(resp.json(), TOKEN_CONTRACT)


class TestMeContract:
    def test_me_response_matches_user_contract(self, logged_in):
        client, token = logged_in
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert_contract(resp.json(), USER_CONTRACT)


class TestLogoutContract:
    def test_logout_response_matches_message_contract(self, logged_in):
        client, token = logged_in
        resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert_contract(resp.json(), MESSAGE_CONTRACT)
