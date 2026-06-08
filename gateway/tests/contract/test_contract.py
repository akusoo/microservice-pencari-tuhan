"""
Contract tests — verify every gateway response shape is stable.

Upstream responses are mocked; we validate only what the gateway itself produces.
"""
import pytest
from jsonschema import validate, ValidationError as JsonSchemaError

from tests.conftest import mock_upstream


# ── Contract schemas ──────────────────────────────────────────────────────────

HEALTH_CONTRACT = {
    "type": "object",
    "required": ["status", "service"],
    "properties": {
        "status":  {"type": "string"},
        "service": {"type": "string"},
    },
    "additionalProperties": False,
}

ERROR_CONTRACT = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {},
    },
}

CIRCUIT_BREAKER_ENTRY_CONTRACT = {
    "type": "object",
    "required": ["name", "state", "failures", "fail_max", "reset_timeout_seconds"],
    "properties": {
        "name":                  {"type": "string"},
        "state":                 {"type": "string", "enum": ["closed", "open", "half_open"]},
        "failures":              {"type": "integer"},
        "fail_max":              {"type": "integer"},
        "reset_timeout_seconds": {"type": "number"},
    },
    "additionalProperties": False,
}


def assert_contract(data: dict, schema: dict):
    try:
        validate(instance=data, schema=schema)
    except JsonSchemaError as exc:
        pytest.fail(f"Response does not match contract:\n{exc.message}")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHealthContract:
    async def test_health_matches_contract(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert_contract(resp.json(), HEALTH_CONTRACT)

    async def test_health_service_is_gateway(self, client):
        resp = await client.get("/health")
        assert resp.json()["service"] == "gateway"


class TestErrorContract:
    async def test_401_missing_token_matches_error_contract(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401
        assert_contract(resp.json(), ERROR_CONTRACT)

    async def test_401_invalid_token_matches_error_contract(self, client):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer bad"})
        assert resp.status_code == 401
        assert_contract(resp.json(), ERROR_CONTRACT)

    async def test_404_unknown_route_matches_error_contract(self, client, member_token):
        resp = await client.get(
            "/no-such-route",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 404
        assert_contract(resp.json(), ERROR_CONTRACT)

    async def test_503_upstream_unreachable_matches_error_contract(self, client, member_token):
        from unittest.mock import AsyncMock, patch
        import httpx

        with patch("app.routers.proxy.httpx.AsyncClient") as MockClass:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {member_token}"},
            )
        assert resp.status_code == 503
        assert_contract(resp.json(), ERROR_CONTRACT)


class TestCircuitBreakerContract:
    async def test_circuit_breaker_status_matches_contract(self, client):
        resp = await client.get("/admin/circuit-breakers")
        assert resp.status_code == 200
        data = resp.json()
        for service_data in data.values():
            assert_contract(service_data, CIRCUIT_BREAKER_ENTRY_CONTRACT)
