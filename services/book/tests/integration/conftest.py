import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.session import Base, get_db
from app.main import app

# Real Postgres, reached via the host-mapped port from docker-compose.yml
# (book-db: "5434:5432"). Override with INTEGRATION_DATABASE_URL if your
# compose setup maps a different port.
#
# Why a real DB and not the in-memory SQLite used by the unit suite: SQLite
# has no real row-level locking, so it can't prove `with_for_update()` actually
# serializes concurrent stock updates — only Postgres can.
INTEGRATION_DATABASE_URL = os.environ.get(
    "INTEGRATION_DATABASE_URL",
    "postgresql+asyncpg://book_user:book_pass@localhost:5434/book_db",
)

# NullPool: a fresh asyncpg connection per checkout, discarded on return.
# Needed because pytest-asyncio gives each test function its own event loop —
# a pooled asyncpg connection bound to one loop breaks ("another operation
# in progress" / "attached to a different loop") when reused from another.
engine = create_async_engine(INTEGRATION_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _require_book_db():
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        pytest.skip(f"book-db not reachable at {INTEGRATION_DATABASE_URL} — run `docker compose up -d book-db`: {exc}")
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def reset_schema(_require_book_db):
    # Swap get_db to point at real Postgres for the duration of this test, then
    # put back whatever override was there before (the unit suite's SQLite one) —
    # popping it outright would leave later unit tests resolving the real
    # dependency, which points at the unreachable Docker-internal "db_book" host.
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    if previous_override is not None:
        app.dependency_overrides[get_db] = previous_override
    else:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    return {"X-User-ID": "11111111-1111-1111-1111-111111111111", "X-User-Role": "admin"}
