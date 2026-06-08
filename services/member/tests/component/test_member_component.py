# Component tests: exercise Member Service as a whole, black-box, through its
# real HTTP interface (FastAPI app + routers + RBAC + service + repository),
# with only the DB swapped for in-memory SQLite (see ../conftest.py). This is
# the layer that proves routing, validation, RBAC and business rules compose
# correctly end-to-end *within* the service boundary — as opposed to:
#   - tests/unit       : isolated functions/classes, no app, no DB
#   - tests/contract   : pinned response shapes for OTHER services to depend on
#   - tests/integration: real Postgres, proves DB-specific guarantees


def member_payload(user_id, **overrides):
    payload = {
        "user_id": user_id,
        "full_name": "Budi Santoso",
        "email": "budi@example.com",
        "phone": "081234567890",
        "address": "Jl. Merdeka No. 1",
    }
    payload.update(overrides)
    return payload


async def create_member(client, admin_headers, user_id, **overrides):
    resp = await client.post("/members", json=member_payload(user_id, **overrides), headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "member"}


async def test_create_member_as_admin(client, admin_headers, user_id):
    body = await create_member(client, admin_headers, user_id)
    assert body["full_name"] == "Budi Santoso"
    assert body["status"] == "active"  # default status on creation
    assert body["user_id"] == user_id


async def test_create_member_forbidden_for_member_role(client, member_headers, user_id):
    resp = await client.post("/members", json=member_payload(user_id), headers=member_headers)
    assert resp.status_code == 403


async def test_create_member_requires_gateway_headers(client, user_id):
    resp = await client.post("/members", json=member_payload(user_id))
    assert resp.status_code == 422  # missing X-User-ID / X-User-Role


async def test_create_member_duplicate_user_or_email_conflict(client, admin_headers, user_id):
    await create_member(client, admin_headers, user_id)

    same_user = await client.post(
        "/members",
        json=member_payload(user_id, email="other@example.com"),
        headers=admin_headers,
    )
    assert same_user.status_code == 409

    other_id = "55555555-5555-5555-5555-555555555555"
    same_email = await client.post(
        "/members",
        json=member_payload(other_id, email="budi@example.com"),
        headers=admin_headers,
    )
    assert same_email.status_code == 409


async def test_list_members_admin_or_librarian_only(client, admin_headers, librarian_headers, member_headers, user_id):
    await create_member(client, admin_headers, user_id)

    forbidden = await client.get("/members", headers=member_headers)
    assert forbidden.status_code == 403

    as_librarian = await client.get("/members", headers=librarian_headers)
    assert as_librarian.status_code == 200
    assert len(as_librarian.json()) == 1


async def test_get_member_by_id_open_for_inter_service_calls(client, admin_headers, user_id):
    created = await create_member(client, admin_headers, user_id)

    # Loan Service checks member status via direct httpx — no gateway headers.
    resp = await client.get(f"/members/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


async def test_get_member_not_found(client):
    resp = await client.get("/members/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_get_my_profile(client, admin_headers, member_headers, user_id):
    await create_member(client, admin_headers, user_id)

    resp = await client.get("/members/me", headers=member_headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id


async def test_get_my_profile_rejects_malformed_user_id(client):
    resp = await client.get("/members/me", headers={"X-User-ID": "not-a-uuid", "X-User-Role": "member"})
    assert resp.status_code == 401


async def test_get_my_profile_not_found_when_no_member_record(client):
    resp = await client.get(
        "/members/me",
        headers={"X-User-ID": "99999999-9999-9999-9999-999999999999", "X-User-Role": "member"},
    )
    assert resp.status_code == 404


async def test_update_member(client, admin_headers, librarian_headers, user_id):
    created = await create_member(client, admin_headers, user_id)
    resp = await client.put(
        f"/members/{created['id']}",
        json={"phone": "089999999999"},
        headers=librarian_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "089999999999"


async def test_update_member_email_conflict(client, admin_headers, user_id):
    await create_member(client, admin_headers, user_id, email="budi@example.com")
    other_id = "66666666-6666-6666-6666-666666666666"
    other = await create_member(client, admin_headers, other_id, email="other@example.com", full_name="Ani")

    resp = await client.put(f"/members/{other['id']}", json={"email": "budi@example.com"}, headers=admin_headers)
    assert resp.status_code == 409


async def test_update_status(client, admin_headers, user_id):
    created = await create_member(client, admin_headers, user_id)
    resp = await client.patch(
        f"/members/{created['id']}/status",
        json={"status": "blocked"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"


async def test_update_status_forbidden_for_member_role(client, admin_headers, member_headers, user_id):
    created = await create_member(client, admin_headers, user_id)
    resp = await client.patch(
        f"/members/{created['id']}/status",
        json={"status": "active"},
        headers=member_headers,
    )
    assert resp.status_code == 403


async def test_delete_member_admin_only(client, admin_headers, librarian_headers, user_id):
    created = await create_member(client, admin_headers, user_id)

    forbidden = await client.delete(f"/members/{created['id']}", headers=librarian_headers)
    assert forbidden.status_code == 403

    resp = await client.delete(f"/members/{created['id']}", headers=admin_headers)
    assert resp.status_code == 204

    missing = await client.get(f"/members/{created['id']}")
    assert missing.status_code == 404
