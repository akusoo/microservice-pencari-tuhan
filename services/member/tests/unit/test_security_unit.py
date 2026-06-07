# Unit tests: pure functions/classes in isolation — no FastAPI app, no DB,
# no HTTP transport. These call the dependency callables directly the way
# FastAPI's DI would resolve them, to pin behavior at the smallest testable grain.

import uuid

import pytest
from fastapi import HTTPException

from app.core.security import get_current_user_id, get_current_user_role, require_roles


def test_get_current_user_id_parses_valid_uuid():
    # Member parses X-User-ID into a uuid.UUID — it needs the typed value to
    # look up "my profile" by user_id (unlike Book, which passes it through raw).
    parsed = get_current_user_id("11111111-1111-1111-1111-111111111111")
    assert parsed == uuid.UUID("11111111-1111-1111-1111-111111111111")
    assert isinstance(parsed, uuid.UUID)


def test_get_current_user_id_rejects_malformed_value_with_401():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_id("not-a-uuid")

    assert exc_info.value.status_code == 401


def test_get_current_user_role_passes_header_value_through():
    assert get_current_user_role("admin") == "admin"


def test_require_roles_allows_listed_role():
    checker = require_roles("admin", "librarian")
    assert checker(role="admin") == "admin"
    assert checker(role="librarian") == "librarian"


def test_require_roles_rejects_unlisted_role_with_403():
    checker = require_roles("admin")

    with pytest.raises(HTTPException) as exc_info:
        checker(role="member")

    assert exc_info.value.status_code == 403
