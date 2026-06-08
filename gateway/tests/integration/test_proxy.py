"""
Integration tests — gateway proxy routing, JWT enforcement, header injection.

Upstream services are mocked so tests run without real service containers.
"""
import pytest
import httpx

from tests.conftest import mock_upstream, make_token, USER_ID_MEMBER, USER_ID_ADMIN
from app.circuit_breaker import _breakers


class TestHealthAndAdmin:
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "gateway"}

    async def test_circuit_breaker_status_returns_all_services(self, client):
        resp = await client.get("/admin/circuit-breakers")
        assert resp.status_code == 200
        data = resp.json()
        for svc in ("auth", "books", "members", "loans", "fines"):
            assert svc in data
            assert data[svc]["state"] == "closed"


class TestAuthEnforcement:
    async def test_protected_route_without_token_returns_401(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401
        assert "Missing Authorization header" in resp.json()["detail"]

    async def test_protected_route_with_invalid_token_returns_401(self, client):
        resp = await client.get("/auth/me", headers={"Authorization": "Bearer garbage.token"})
        assert resp.status_code == 401

    async def test_protected_route_with_expired_token_returns_401(self, client, expired_token):
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

    async def test_protected_route_with_refresh_token_type_returns_401(self, client, refresh_type_token):
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_type_token}"})
        assert resp.status_code == 401

    async def test_missing_bearer_prefix_returns_401(self, client, member_token):
        resp = await client.get("/auth/me", headers={"Authorization": member_token})
        assert resp.status_code == 401


class TestPublicRoutes:
    async def test_register_passes_without_auth(self, client):
        body = b'{"id":"123","username":"x","email":"x@x.com","role":"member","is_active":true,"created_at":"2024-01-01T00:00:00Z"}'
        async with mock_upstream(201, body):
            resp = await client.post("/auth/register", json={
                "username": "x", "email": "x@x.com", "password": "pass1234"
            })
        assert resp.status_code == 201

    async def test_login_passes_without_auth(self, client):
        body = b'{"access_token":"tok","token_type":"bearer"}'
        async with mock_upstream(200, body):
            resp = await client.post("/auth/login", json={"username": "x", "password": "pass1234"})
        assert resp.status_code == 200

    async def test_refresh_passes_without_auth(self, client):
        body = b'{"access_token":"newtok","token_type":"bearer"}'
        async with mock_upstream(200, body):
            resp = await client.post("/auth/refresh")
        assert resp.status_code == 200


class TestHeaderInjection:
    async def test_user_id_header_injected(self, client, member_token):
        async with mock_upstream(200, b'{}') as mock_client:
            await client.get("/auth/me", headers={"Authorization": f"Bearer {member_token}"})

        call_headers = mock_client.request.call_args.kwargs["headers"]
        assert call_headers.get("X-User-ID") == USER_ID_MEMBER

    async def test_user_role_header_injected(self, client, member_token):
        async with mock_upstream(200, b'{}') as mock_client:
            await client.get("/auth/me", headers={"Authorization": f"Bearer {member_token}"})

        call_headers = mock_client.request.call_args.kwargs["headers"]
        assert call_headers.get("X-User-Role") == "member"

    async def test_admin_role_header_injected(self, client, admin_token):
        async with mock_upstream(200, b'{}') as mock_client:
            await client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})

        call_headers = mock_client.request.call_args.kwargs["headers"]
        assert call_headers.get("X-User-ID") == USER_ID_ADMIN
        assert call_headers.get("X-User-Role") == "admin"

    async def test_original_auth_header_still_forwarded(self, client, member_token):
        async with mock_upstream(200, b'{}') as mock_client:
            await client.get("/auth/me", headers={"Authorization": f"Bearer {member_token}"})

        call_headers = mock_client.request.call_args.kwargs["headers"]
        assert "authorization" in {k.lower() for k in call_headers}


class TestRouting:
    async def test_unknown_prefix_returns_404(self, client, member_token):
        resp = await client.get(
            "/unknown/endpoint",
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 404

    async def test_books_route_proxied(self, client, member_token):
        body = b'[]'
        async with mock_upstream(200, body):
            resp = await client.get("/books", headers={"Authorization": f"Bearer {member_token}"})
        assert resp.status_code == 200

    async def test_members_route_proxied(self, client, member_token):
        body = b'{"id":"1","full_name":"Budi"}'
        async with mock_upstream(200, body):
            resp = await client.get("/members/me", headers={"Authorization": f"Bearer {member_token}"})
        assert resp.status_code == 200


class TestUpstreamErrors:
    async def test_upstream_connect_error_returns_503(self, client, member_token):
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

    async def test_upstream_timeout_returns_504(self, client, member_token):
        from unittest.mock import AsyncMock, patch
        import httpx

        with patch("app.routers.proxy.httpx.AsyncClient") as MockClass:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {member_token}"},
            )
        assert resp.status_code == 504

    async def test_connect_errors_increment_circuit_breaker(self, client, member_token):
        from unittest.mock import AsyncMock, patch

        with patch("app.routers.proxy.httpx.AsyncClient") as MockClass:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
            MockClass.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClass.return_value.__aexit__ = AsyncMock(return_value=False)

            await client.get("/auth/me", headers={"Authorization": f"Bearer {member_token}"})

        assert _breakers["auth"]._failures == 1
