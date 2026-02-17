"""Test configuration — sets up a test database and provides fixtures."""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import Tenant, User
from app.auth.service import hash_password
from app.config import settings
from app.database import Base, get_db
from app.main import app

# Use a separate test database URL (append _test to the database name)
TEST_DATABASE_URL = settings.database_url.replace("/luxis", "/luxis_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a test database session."""
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Provide a test HTTP client with the test database injected."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(db: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Kesting Legal",
        slug="kesting-legal",
        kvk_number="88601536",
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user belonging to the test tenant."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="lisanne@kestinglegal.nl",
        hashed_password=hash_password("testpassword123"),
        full_name="Lisanne Kesting",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
