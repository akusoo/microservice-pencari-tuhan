# Contract tests: pin the response shape of endpoints other services call directly
# over httpx (no gateway headers — see docs/erd.md "Cross-Service Reference Rules").
#
# Consumers:
#   - Loan Service reads GET /books/{book_id} to display/validate a book on a loan,
#     and calls PATCH /books/{book_id}/stock to reserve/release a copy.
#
# If one of these assertions breaks, a Book change is about to break Loan
# integration — fix the contract or coordinate the change with the Loan team
# before merging.


def book_payload(**overrides):
    payload = {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "publisher": "Harper",
        "category": "history",
        "description": "A brief history of humankind",
        "year": 2015,
        "total_copies": 3,
    }
    payload.update(overrides)
    return payload


async def create_book(client, admin_headers, **overrides):
    resp = await client.post("/books", json=book_payload(**overrides), headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()


async def test_get_book_contract_shape(client, admin_headers):
    created = await create_book(client, admin_headers)

    resp = await client.get(f"/books/{created['id']}")
    assert resp.status_code == 200

    body = resp.json()
    # Fields Loan Service is expected to read off this response.
    for field in ("id", "title", "author", "isbn", "category", "available_copies", "total_copies"):
        assert field in body, f"contract field '{field}' missing from GET /books/{{id}} response"

    assert isinstance(body["available_copies"], int)
    assert isinstance(body["total_copies"], int)
    assert isinstance(body["title"], str)
    assert isinstance(body["isbn"], str)


async def test_stock_endpoint_is_open_and_returns_updated_count(client, admin_headers):
    created = await create_book(client, admin_headers, total_copies=2)
    book_id = created["id"]

    # Inter-service call: Loan Service hits this with no X-User-ID/X-User-Role —
    # gateway does not sit between services, only between browser and gateway-facing routes.
    resp = await client.patch(f"/books/{book_id}/stock", json={"delta": -1})
    assert resp.status_code == 200

    body = resp.json()
    assert "available_copies" in body
    assert body["available_copies"] == 1
    assert isinstance(body["available_copies"], int)


async def test_stock_endpoint_rejects_unknown_book_with_404(client):
    # Loan Service must be able to distinguish "book vanished" (404) from
    # "out of range" (422) to decide whether to retry or surface a user error.
    resp = await client.patch(
        "/books/00000000-0000-0000-0000-000000000000/stock",
        json={"delta": -1},
    )
    assert resp.status_code == 404


async def test_stock_endpoint_request_shape(client, admin_headers):
    created = await create_book(client, admin_headers, total_copies=1)

    # Contract: the request body is {"delta": <int>} — nothing else required,
    # no auth headers. Loan Service should be able to build this payload from
    # just "borrow" (-1) / "return" (+1) without knowing Book's internals.
    resp = await client.patch(f"/books/{created['id']}/stock", json={"delta": 1})
    assert resp.status_code == 422  # already at total_copies, can't exceed it — proves range is enforced server-side
