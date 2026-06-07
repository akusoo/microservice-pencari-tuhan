"""
Component tests — auth-service as a black box.

Tests a complete realistic user journey end-to-end through the service,
verifying all pieces work together correctly.
"""


class TestFullAuthFlow:
    """Happy path: register → login → use token → refresh → logout."""

    def test_complete_flow(self, client):
        # 1. Register
        reg = client.post("/auth/register", json={
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "flowpass123",
        })
        assert reg.status_code == 201
        user_id = reg.json()["id"]

        # 2. Login — get access token + refresh cookie
        login = client.post("/auth/login", json={
            "username": "flowuser",
            "password": "flowpass123",
        })
        assert login.status_code == 200
        access_token = login.json()["access_token"]
        assert "refresh_token" in login.cookies

        # 3. Use access token — get own profile
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me.status_code == 200
        assert me.json()["id"] == user_id

        # 4. Refresh — rotate token, get new access token
        refresh = client.post("/auth/refresh")
        assert refresh.status_code == 200
        new_access_token = refresh.json()["access_token"]
        assert new_access_token != access_token

        # 5. Old access token still works (it hasn't expired yet)
        me_old = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_old.status_code == 200

        # 6. New access token works
        me_new = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
        assert me_new.status_code == 200

        # 7. Logout — revoke refresh token
        logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {new_access_token}"})
        assert logout.status_code == 200

        # 8. Refresh after logout must fail
        post_logout_refresh = client.post("/auth/refresh")
        assert post_logout_refresh.status_code == 401


class TestRefreshTokenRotation:
    """Security: old refresh token must be rejected after rotation."""

    def test_old_refresh_token_rejected_after_rotation(self, client):
        client.post("/auth/register", json={
            "username": "rotuser",
            "email": "rot@example.com",
            "password": "rotpass123",
        })
        client.post("/auth/login", json={"username": "rotuser", "password": "rotpass123"})
        old_cookie = client.cookies.get("refresh_token")

        # Rotate
        client.post("/auth/refresh")

        # Replay old token — must be rejected
        client.cookies.set("refresh_token", old_cookie)
        replay = client.post("/auth/refresh")
        assert replay.status_code == 401


class TestMultipleUsers:
    """Tokens are user-scoped — one user cannot use another user's token."""

    def test_tokens_are_isolated_between_users(self, client):
        for user in [
            {"username": "user1", "email": "u1@example.com", "password": "pass1234"},
            {"username": "user2", "email": "u2@example.com", "password": "pass5678"},
        ]:
            client.post("/auth/register", json=user)

        login1 = client.post("/auth/login", json={"username": "user1", "password": "pass1234"})
        token1 = login1.json()["access_token"]

        me1 = client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"})
        assert me1.json()["username"] == "user1"

        login2 = client.post("/auth/login", json={"username": "user2", "password": "pass5678"})
        token2 = login2.json()["access_token"]

        me2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"})
        assert me2.json()["username"] == "user2"

        # Cross-token: token1 should never return user2's data
        assert me1.json()["id"] != me2.json()["id"]
