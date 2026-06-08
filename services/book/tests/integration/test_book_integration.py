import asyncio

import pytest

pytestmark = pytest.mark.integration


def book_payload(**overrides):
    payload = {
        "title": "Sapiens",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "publisher": "Harper",
        "category": "history",
        "description": "A brief history of humankind",
        "year": 2015,
        "total_copies": 1,
    }
    payload.update(overrides)
    return payload


async def create_book(client, admin_headers, **overrides):
    resp = await client.post("/books", json=book_payload(**overrides), headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()


async def test_unique_isbn_enforced_at_db_level(client, admin_headers):
    # The unit suite proves the service layer returns 409 on duplicate ISBN;
    # this proves the underlying unique index actually exists in Postgres —
    # the service-layer check alone wouldn't survive a concurrent insert race.
    await create_book(client, admin_headers, isbn="9780062316097")

    dup = await client.post(
        "/books",
        json=book_payload(isbn="9780062316097", title="Different Title"),
        headers=admin_headers,
    )
    assert dup.status_code == 409


async def test_concurrent_stock_updates_are_serialized_by_row_lock(client, admin_headers):
    # `with_for_update()` (book_service.update_stock) should serialize concurrent
    # PATCH /stock calls so a book with 1 copy can never go to -1 available —
    # this is the exact race a real Loan Service will create when two members
    # try to borrow the last copy at once. SQLite can't model this; Postgres can.
    created = await create_book(client, admin_headers, total_copies=1)
    book_id = created["id"]

    results = await asyncio.gather(
        client.patch(f"/books/{book_id}/stock", json={"delta": -1}),
        client.patch(f"/books/{book_id}/stock", json={"delta": -1}),
    )
    statuses = sorted(r.status_code for r in results)

    # Exactly one borrow succeeds (200 -> available_copies = 0); the other is
    # rejected as out-of-range (422) because the lock made it see the post-update state.
    assert statuses == [200, 422]

    final = await client.get(f"/books/{book_id}")
    assert final.json()["available_copies"] == 0
