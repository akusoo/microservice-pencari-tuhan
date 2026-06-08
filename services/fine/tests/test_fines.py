import uuid
from unittest.mock import patch

import pytest

MOCK_LOAN_ID = uuid.uuid4()
MOCK_MEMBER_ID = uuid.uuid4()


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "fine"}


async def test_create_fine(client):
    payload = {
        "loan_id": str(MOCK_LOAN_ID),
        "member_id": str(MOCK_MEMBER_ID),
        "amount": 5000.0,
    }
    resp = await client.post("/fines", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["loan_id"] == str(MOCK_LOAN_ID)
    assert body["member_id"] == str(MOCK_MEMBER_ID)
    assert body["amount"] == 5000.0
    assert body["is_paid"] is False
    assert body["paid_at"] is None


async def test_create_fine_duplicate_loan_id(client):
    payload = {
        "loan_id": str(MOCK_LOAN_ID),
        "member_id": str(MOCK_MEMBER_ID),
        "amount": 5000.0,
    }
    await client.post("/fines", json=payload)
    resp = await client.post("/fines", json=payload)
    assert resp.status_code == 409


async def test_list_fines_requires_admin_or_librarian(client):
    resp = await client.get("/fines")
    assert resp.status_code == 422

    resp = await client.get("/fines", headers={"X-User-Role": "member", "X-User-ID": str(uuid.uuid4())})
    assert resp.status_code == 403

    resp = await client.get("/fines", headers={"X-User-Role": "admin", "X-User-ID": str(uuid.uuid4())})
    assert resp.status_code == 200


async def test_get_fine(client):
    payload = {
        "loan_id": str(MOCK_LOAN_ID),
        "member_id": str(MOCK_MEMBER_ID),
        "amount": 5000.0,
    }
    created = (await client.post("/fines", json=payload)).json()

    resp = await client.get(f"/fines/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_fine_not_found(client):
    resp = await client.get(f"/fines/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_pay_fine(client):
    with patch("app.services.fine_service.member_client.update_member_status") as mock_update:
        payload = {
            "loan_id": str(MOCK_LOAN_ID),
            "member_id": str(MOCK_MEMBER_ID),
            "amount": 5000.0,
        }
        created = (await client.post("/fines", json=payload)).json()

        resp = await client.patch(f"/fines/{created['id']}/pay")
        assert resp.status_code == 200
        assert resp.json()["is_paid"] is True
        assert resp.json()["paid_at"] is not None
        mock_update.assert_called_once_with(MOCK_MEMBER_ID, "active")


async def test_pay_fine_already_paid(client):
    with patch("app.services.fine_service.member_client.update_member_status"):
        payload = {
            "loan_id": str(MOCK_LOAN_ID),
            "member_id": str(MOCK_MEMBER_ID),
            "amount": 5000.0,
        }
        created = (await client.post("/fines", json=payload)).json()
        await client.patch(f"/fines/{created['id']}/pay")

        resp = await client.patch(f"/fines/{created['id']}/pay")
        assert resp.status_code == 400


async def test_unpaid_fines(client):
    payload = {
        "loan_id": str(uuid.uuid4()),
        "member_id": str(MOCK_MEMBER_ID),
        "amount": 5000.0,
    }
    await client.post("/fines", json=payload)

    resp = await client.get("/fines/unpaid", headers={"X-User-Role": "admin", "X-User-ID": str(uuid.uuid4())})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
