import uuid
from unittest.mock import patch

import pytest

MOCK_MEMBER_ID = uuid.uuid4()
MOCK_BOOK_ID = uuid.uuid4()

MOCK_ACTIVE_MEMBER = {
    "id": str(MOCK_MEMBER_ID),
    "user_id": str(uuid.uuid4()),
    "full_name": "John Doe",
    "email": "john@test.com",
    "status": "active",
}


@pytest.fixture(autouse=True)
def mock_clients():
    with (
        patch("app.services.loan_service.book_client.get_book") as mock_get_book,
        patch("app.services.loan_service.book_client.update_stock") as mock_update_stock,
        patch("app.services.loan_service.member_client.get_member", return_value=MOCK_ACTIVE_MEMBER),
        patch("app.services.loan_service.fine_client.create_fine"),
    ):
        mock_get_book.return_value = {
            "id": str(MOCK_BOOK_ID),
            "title": "Test Book",
            "available_copies": 3,
        }
        yield


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "loan"}


async def test_create_loan(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    resp = await client.post("/loans", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["member_id"] == str(MOCK_MEMBER_ID)
    assert body["book_id"] == str(MOCK_BOOK_ID)
    assert body["status"] == "active"
    assert body["return_date"] is None
    assert "id" in body


async def test_create_loan_book_unavailable(client):
    with patch("app.services.loan_service.book_client.get_book") as mock:
        mock.return_value = {"id": str(MOCK_BOOK_ID), "available_copies": 0}
        payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
        resp = await client.post("/loans", json=payload)
        assert resp.status_code == 400
        assert "not available" in resp.json()["detail"].lower()


async def test_create_loan_member_not_active(client):
    with patch("app.services.loan_service.member_client.get_member") as mock:
        mock.return_value = {**MOCK_ACTIVE_MEMBER, "status": "blocked"}
        payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
        resp = await client.post("/loans", json=payload)
        assert resp.status_code == 400
        assert "not active" in resp.json()["detail"].lower()


async def test_list_loans_requires_admin_or_librarian(client):
    resp = await client.get("/loans")
    assert resp.status_code == 422

    resp = await client.get("/loans", headers={"X-User-Role": "member", "X-User-ID": str(uuid.uuid4())})
    assert resp.status_code == 403

    resp = await client.get("/loans", headers={"X-User-Role": "admin", "X-User-ID": str(uuid.uuid4())})
    assert resp.status_code == 200


async def test_get_loan(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    created = (await client.post("/loans", json=payload)).json()

    resp = await client.get(f"/loans/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


async def test_get_loan_not_found(client):
    resp = await client.get(f"/loans/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_return_loan(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    created = (await client.post("/loans", json=payload)).json()

    resp = await client.patch(f"/loans/{created['id']}/return")
    assert resp.status_code == 200
    assert resp.json()["status"] == "returned"
    assert resp.json()["return_date"] is not None


async def test_extend_loan(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    created = (await client.post("/loans", json=payload)).json()
    original_due = created["due_date"]

    resp = await client.patch(f"/loans/{created['id']}/extend", json={"extra_days": 7})
    assert resp.status_code == 200
    assert resp.json()["due_date"] > original_due


async def test_extend_loan_already_returned(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    created = (await client.post("/loans", json=payload)).json()
    await client.patch(f"/loans/{created['id']}/return")

    resp = await client.patch(f"/loans/{created['id']}/extend", json={"extra_days": 7})
    assert resp.status_code == 400


async def test_overdue_loans(client, mock_clients):
    payload = {"member_id": str(MOCK_MEMBER_ID), "book_id": str(MOCK_BOOK_ID)}
    await client.post("/loans", json=payload)

    resp = await client.get("/loans/overdue")
    assert resp.status_code == 200
