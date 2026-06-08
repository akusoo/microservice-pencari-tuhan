# Unit tests: Pydantic schema validation in isolation — no app, no DB, no HTTP.
# Pins the request-shape rules the API relies on before anything reaches the DB.

import uuid

import pytest
from pydantic import ValidationError

from app.models.member import MemberStatus
from app.schemas.member import MemberCreate, MemberStatusUpdate, MemberUpdate


def base_payload(**overrides):
    payload = {
        "user_id": str(uuid.uuid4()),
        "full_name": "Budi Santoso",
        "email": "budi@example.com",
    }
    payload.update(overrides)
    return payload


def test_member_create_accepts_valid_payload():
    member = MemberCreate(**base_payload())
    assert member.email == "budi@example.com"
    assert member.phone is None  # optional field defaults to None


def test_member_create_rejects_malformed_email():
    with pytest.raises(ValidationError, match="email"):
        MemberCreate(**base_payload(email="not-an-email"))


def test_member_create_requires_user_id():
    with pytest.raises(ValidationError, match="user_id"):
        MemberCreate(**{k: v for k, v in base_payload().items() if k != "user_id"})


def test_member_update_allows_all_fields_omitted():
    # PUT supports partial updates — an empty body must be valid.
    update = MemberUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_member_status_update_only_accepts_known_statuses():
    assert MemberStatusUpdate(status="blocked").status == MemberStatus.blocked

    with pytest.raises(ValidationError, match="status"):
        MemberStatusUpdate(status="banned")
