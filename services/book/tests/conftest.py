import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app

# In-memory SQLite shared via StaticPool so every session sees the same DB.
# Generic SQLAlchemy types only (Uuid/String/Text/Integer/DateTime, ilike(),
# with_for_update()) — all translate cleanly to SQLite for test purposes.
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def reset_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    return {"X-User-ID": "11111111-1111-1111-1111-111111111111", "X-User-Role": "admin"}


@pytest.fixture
def librarian_headers():
    return {"X-User-ID": "22222222-2222-2222-2222-222222222222", "X-User-Role": "librarian"}


@pytest.fixture
def member_headers():
    return {"X-User-ID": "33333333-3333-3333-3333-333333333333", "X-User-Role": "member"}
