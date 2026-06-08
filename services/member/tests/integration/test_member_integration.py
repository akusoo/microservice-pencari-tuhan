import uuid

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


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


async def test_unique_user_id_and_email_enforced_at_db_level(client, admin_headers, user_id):
    # The unit suite proves the service layer returns 409 on duplicates;
    # this proves the underlying unique indexes (ix_members_user_id,
    # ix_members_email — see alembic/versions/0001_create_members_table.py)
    # actually exist in Postgres, closing the race a service-layer-only check leaves open.
    await create_member(client, admin_headers, user_id, email="budi@example.com")

    dup_user = await client.post(
        "/members",
        json=member_payload(user_id, email="other@example.com"),
        headers=admin_headers,
    )
    assert dup_user.status_code == 409

    dup_email = await client.post(
        "/members",
        json=member_payload(str(uuid.uuid4()), email="budi@example.com"),
        headers=admin_headers,
    )
    assert dup_email.status_code == 409


async def test_memberstatus_enum_rejects_invalid_value_at_db_level(client, admin_headers, user_id, db_session):
    # Pydantic's MemberStatus enum already blocks bad values at the API layer
    # (see schemas/member.py MemberStatusUpdate); this proves Postgres' native
    # `memberstatus` ENUM type (alembic 0001) is the real backstop — a raw
    # write that bypasses the API (e.g. a future bulk-import script) still can't
    # persist a status outside active/inactive/blocked.
    created = await create_member(client, admin_headers, user_id)

    with pytest.raises(Exception, match="(?i)invalid input value for enum|memberstatus"):
        await db_session.execute(
            text("UPDATE members SET status = 'banned' WHERE id = :id"),
            {"id": created["id"]},
        )
        await db_session.commit()
