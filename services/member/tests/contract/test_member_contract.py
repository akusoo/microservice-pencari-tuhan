# Contract tests: pin the response shape of endpoints other services call directly
# over httpx (no gateway headers — see docs/erd.md "Cross-Service Reference Rules").
#
# Consumers:
#   - Loan Service reads GET /members/{member_id} to check `status` before
#     approving a loan (blocked/inactive members can't borrow).
#   - Fine Service reads the same endpoint via loan.member_id to resolve a member
#     for an overdue fine.
#
# If one of these assertions breaks, a Member change is about to break Loan/Fine
# integration — fix the contract or coordinate the change with those teams
# before merging.


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


async def test_get_member_contract_shape(client, admin_headers, user_id):
    created = await create_member(client, admin_headers, user_id)

    # Inter-service call: no X-User-ID/X-User-Role — Loan/Fine call this directly.
    resp = await client.get(f"/members/{created['id']}")
    assert resp.status_code == 200

    body = resp.json()
    for field in ("id", "user_id", "status", "full_name"):
        assert field in body, f"contract field '{field}' missing from GET /members/{{id}} response"

    assert isinstance(body["status"], str)
    assert body["status"] in ("active", "inactive", "blocked"), (
        "Loan Service branches on these three literal values to decide loan eligibility"
    )
    assert isinstance(body["id"], str)
    assert isinstance(body["user_id"], str)


async def test_get_member_contract_unknown_id_returns_404(client):
    # Loan Service must be able to tell "member not found" (404) apart from
    # "member exists but ineligible" (200 + status != active).
    resp = await client.get("/members/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_get_member_status_reflects_blocked_state(client, admin_headers, user_id):
    created = await create_member(client, admin_headers, user_id)

    await client.patch(
        f"/members/{created['id']}/status",
        json={"status": "blocked"},
        headers=admin_headers,
    )

    # Loan Service's eligibility check reads this exact field+value combo.
    resp = await client.get(f"/members/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "blocked"
