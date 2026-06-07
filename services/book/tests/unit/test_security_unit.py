# Unit tests: pure functions/classes in isolation — no FastAPI app, no DB,
# no HTTP transport. These call the dependency callables directly the way
# FastAPI's DI would resolve them, to pin behavior at the smallest testable grain.

import pytest
from fastapi import HTTPException

from app.core.security import get_current_user_id, get_current_user_role, require_roles


def test_get_current_user_id_passes_header_value_through():
    # Book trusts the gateway-injected X-User-ID verbatim — it doesn't need to
    # parse it (only Member does, to look up its own profile by user_id).
    assert get_current_user_id("11111111-1111-1111-1111-111111111111") == "11111111-1111-1111-1111-111111111111"


def test_get_current_user_role_passes_header_value_through():
    assert get_current_user_role("librarian") == "librarian"


def test_require_roles_allows_listed_role():
    checker = require_roles("admin", "librarian")
    assert checker(role="admin") == "admin"
    assert checker(role="librarian") == "librarian"


def test_require_roles_rejects_unlisted_role_with_403():
    checker = require_roles("admin")

    with pytest.raises(HTTPException) as exc_info:
        checker(role="member")

    assert exc_info.value.status_code == 403
