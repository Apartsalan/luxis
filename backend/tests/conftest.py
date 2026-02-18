"""Test configuration — sets up a test database and provides fixtures."""

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.relations.models import Contact

# Use a separate test database URL (only replace the database name at the end)
_base_url = settings.database_url
TEST_DATABASE_URL = _base_url.rsplit("/", 1)[0] + "/luxis_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db():
    """Provide a test database session."""
    async with TestSession() as session:
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
    ) as ac:
        yield ac

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


@pytest_asyncio.fixture
async def auth_headers(test_user: User, test_tenant: Tenant) -> dict[str, str]:
    """Provide Authorization headers with a valid access token."""
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_company(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Create a test company contact."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Acme B.V.",
        email="info@acme.nl",
        kvk_number="12345678",
        btw_number="NL123456789B01",
        visit_address="Herengracht 100",
        visit_postcode="1015 BS",
        visit_city="Amsterdam",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@pytest_asyncio.fixture
async def test_person(db: AsyncSession, test_tenant: Tenant) -> Contact:
    """Create a test person contact."""
    contact = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="person",
        name="Jan de Vries",
        first_name="Jan",
        last_name="de Vries",
        email="jan@devries.nl",
        phone="+31612345678",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact
