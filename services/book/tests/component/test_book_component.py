# Component tests: exercise Book Service as a whole, black-box, through its
# real HTTP interface (FastAPI app + routers + RBAC + service + repository),
# with only the DB swapped for in-memory SQLite (see ../conftest.py). This is
# the layer that proves routing, validation, RBAC and business rules compose
# correctly end-to-end *within* the service boundary — as opposed to:
#   - tests/unit       : isolated functions/classes, no app, no DB
#   - tests/contract   : pinned response shapes for OTHER services to depend on
#   - tests/integration: real Postgres, proves DB-specific guarantees


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


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "book"}


async def test_create_book_as_admin(client, admin_headers):
    body = await create_book(client, admin_headers)
    assert body["title"] == "Sapiens"
    assert body["available_copies"] == body["total_copies"] == 3
    assert "id" in body and "created_at" in body


async def test_create_book_as_librarian(client, librarian_headers):
    resp = await client.post("/books", json=book_payload(isbn="9780062316098"), headers=librarian_headers)
    assert resp.status_code == 201


async def test_create_book_forbidden_for_member(client, member_headers):
    resp = await client.post("/books", json=book_payload(), headers=member_headers)
    assert resp.status_code == 403


async def test_create_book_requires_gateway_headers(client):
    resp = await client.post("/books", json=book_payload())
    assert resp.status_code == 422  # missing X-User-ID / X-User-Role


async def test_create_book_duplicate_isbn_conflict(client, admin_headers):
    await create_book(client, admin_headers)
    resp = await client.post("/books", json=book_payload(title="Sapiens 2nd Ed"), headers=admin_headers)
    assert resp.status_code == 409


async def test_list_books(client, admin_headers):
    await create_book(client, admin_headers, isbn="9780062316097")
    await create_book(client, admin_headers, isbn="9780062316098", title="Homo Deus")
    resp = await client.get("/books")
    assert resp.status_code == 200
    titles = [b["title"] for b in resp.json()]
    assert titles == sorted(titles)  # ordered by title
    assert len(titles) == 2


async def test_get_book_by_id(client, admin_headers):
    created = await create_book(client, admin_headers)
    resp = await client.get(f"/books/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["isbn"] == created["isbn"]


async def test_get_book_not_found(client):
    resp = await client.get("/books/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_search_books_by_title_author_or_category(client, admin_headers):
    await create_book(client, admin_headers, isbn="9780062316097", title="Sapiens", author="Harari", category="history")
    await create_book(client, admin_headers, isbn="9780062316098", title="Clean Code", author="Martin", category="programming")

    by_title = await client.get("/books/search", params={"q": "sapiens"})
    assert {b["title"] for b in by_title.json()} == {"Sapiens"}

    by_category = await client.get("/books/search", params={"q": "programming"})
    assert {b["title"] for b in by_category.json()} == {"Clean Code"}


async def test_update_book(client, admin_headers, librarian_headers):
    created = await create_book(client, admin_headers)
    resp = await client.put(
        f"/books/{created['id']}",
        json={"description": "Updated blurb"},
        headers=librarian_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated blurb"


async def test_update_book_forbidden_for_member(client, admin_headers, member_headers):
    created = await create_book(client, admin_headers)
    resp = await client.put(f"/books/{created['id']}", json={"year": 2020}, headers=member_headers)
    assert resp.status_code == 403


async def test_delete_book_admin_only(client, admin_headers, librarian_headers):
    created = await create_book(client, admin_headers)

    forbidden = await client.delete(f"/books/{created['id']}", headers=librarian_headers)
    assert forbidden.status_code == 403

    resp = await client.delete(f"/books/{created['id']}", headers=admin_headers)
    assert resp.status_code == 204

    missing = await client.get(f"/books/{created['id']}")
    assert missing.status_code == 404


async def test_update_stock_open_for_inter_service_calls(client, admin_headers):
    created = await create_book(client, admin_headers, total_copies=2)
    book_id = created["id"]

    # Loan Service borrows a copy — no gateway headers on inter-service calls.
    borrow = await client.patch(f"/books/{book_id}/stock", json={"delta": -1})
    assert borrow.status_code == 200
    assert borrow.json()["available_copies"] == 1

    # Returning the copy
    ret = await client.patch(f"/books/{book_id}/stock", json={"delta": 1})
    assert ret.json()["available_copies"] == 2


async def test_update_stock_rejects_out_of_range(client, admin_headers):
    created = await create_book(client, admin_headers, total_copies=1)
    book_id = created["id"]

    over = await client.patch(f"/books/{book_id}/stock", json={"delta": 5})
    assert over.status_code == 422

    under = await client.patch(f"/books/{book_id}/stock", json={"delta": -5})
    assert under.status_code == 422
