"""
Component tests — gateway as a black box.

Verifies the full request lifecycle: auth enforcement → token decode
→ header injection → proxy to upstream → response passthrough.
"""
import pytest
from tests.conftest import mock_upstream, make_token, USER_ID_MEMBER


class TestAuthenticatedFlow:
    """Happy path: valid token → headers injected → upstream response returned."""

    async def test_valid_member_request_proxied_with_injected_headers(self, client):
        token = make_token(user_id=USER_ID_MEMBER, role="member")
        upstream_body = b'{"username":"testuser","role":"member"}'

        async with mock_upstream(200, upstream_body) as mock_client:
            resp = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        headers_sent = mock_client.request.call_args.kwargs["headers"]
        assert headers_sent["X-User-ID"] == USER_ID_MEMBER
        assert headers_sent["X-User-Role"] == "member"

    async def test_upstream_response_body_returned_as_is(self, client):
        token = make_token()
        expected = b'{"id":"abc","title":"Clean Code"}'

        async with mock_upstream(200, expected):
            resp = await client.get(
                "/books/some-id",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.content == expected

    async def test_upstream_status_code_preserved(self, client):
        token = make_token()
        async with mock_upstream(404, b'{"detail":"Not found"}'):
            resp = await client.get(
                "/books/nonexistent",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 404

    async def test_upstream_error_status_preserved(self, client):
        token = make_token()
        async with mock_upstream(500, b'{"detail":"Internal error"}'):
            resp = await client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 500


class TestUnauthenticatedFlow:
    """Requests without valid token must be stopped at the gateway."""

    async def test_no_token_blocked(self, client):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_invalid_token_blocked(self, client):
        resp = await client.get(
            "/books",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401

    async def test_public_route_not_blocked(self, client):
        async with mock_upstream(200, b'{"access_token":"tok","token_type":"bearer"}'):
            resp = await client.post(
                "/auth/login",
                json={"username": "alice", "password": "pass1234"},
            )
        assert resp.status_code == 200


class TestRoleInjection:
    """Different roles must be correctly propagated in X-User-Role header."""

    async def test_librarian_role_injected(self, client):
        token = make_token(role="librarian")
        async with mock_upstream(200, b'[]') as mock_client:
            await client.get("/books", headers={"Authorization": f"Bearer {token}"})

        headers_sent = mock_client.request.call_args.kwargs["headers"]
        assert headers_sent["X-User-Role"] == "librarian"

    async def test_admin_role_injected(self, client, admin_token):
        async with mock_upstream(201, b'{"id":"1"}') as mock_client:
            await client.post(
                "/books",
                json={"title": "x"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        headers_sent = mock_client.request.call_args.kwargs["headers"]
        assert headers_sent["X-User-Role"] == "admin"
