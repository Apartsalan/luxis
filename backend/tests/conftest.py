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
from app.workflow.models import WorkflowStatus, WorkflowTransition

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


@pytest_asyncio.fixture
async def second_tenant(db: AsyncSession) -> Tenant:
    """Create a second tenant for isolation tests."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Van den Berg Advocaten",
        slug="vandenberg",
        kvk_number="99001122",
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def second_user(db: AsyncSession, second_tenant: Tenant) -> User:
    """Create a user belonging to the second tenant."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=second_tenant.id,
        email="pieter@vandenberg.nl",
        hashed_password=hash_password("testpassword456"),
        full_name="Pieter van den Berg",
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_auth_headers(second_user: User, second_tenant: Tenant) -> dict[str, str]:
    """Provide Authorization headers for the second tenant."""
    token = create_access_token(str(second_user.id), str(second_tenant.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def workflow_data(db: AsyncSession, test_tenant: Tenant) -> dict[str, uuid.UUID]:
    """Seed workflow statuses and transitions for the test tenant.

    Mirrors the essential data from migration 009_workflow_tables.
    Returns a dict mapping status slugs to their UUIDs.
    """
    tenant_id = test_tenant.id

    # Create workflow statuses
    statuses_config = [
        ("nieuw", "Nieuw", "intake", 10, "#3b82f6", False, True),
        ("herinnering", "Herinnering", "pre_legal", 20, "#f59e0b", False, False),
        ("aanmaning", "Aanmaning", "pre_legal", 30, "#f97316", False, False),
        ("14_dagenbrief", "14-Dagenbrief", "pre_legal", 40, "#ef4444", False, False),
        ("sommatie", "Sommatie", "legal", 50, "#dc2626", False, False),
        ("tweede_sommatie", "Tweede Sommatie", "legal", 55, "#b91c1c", False, False),
        ("dagvaarding", "Dagvaarding", "legal", 60, "#7c3aed", False, False),
        ("vonnis", "Vonnis", "execution", 70, "#6d28d9", False, False),
        ("executie", "Executie", "execution", 80, "#4c1d95", False, False),
        ("betalingsregeling", "Betalingsregeling", "legal", 45, "#0ea5e9", False, False),
        ("conservatoir_beslag", "Conservatoir Beslag", "legal", 58, "#be185d", False, False),
        ("faillissementsaanvraag", "Faillissementsaanvraag", "execution", 85, "#991b1b", False, False),
        ("betaald", "Betaald", "closed", 90, "#10b981", True, False),
        ("schikking", "Schikking", "closed", 91, "#14b8a6", True, False),
        ("oninbaar", "Oninbaar", "closed", 95, "#6b7280", True, False),
    ]

    slug_to_id: dict[str, uuid.UUID] = {}
    for slug, label, phase, sort_order, color, is_terminal, is_initial in statuses_config:
        status_id = uuid.uuid4()
        slug_to_id[slug] = status_id
        db.add(WorkflowStatus(
            id=status_id,
            tenant_id=tenant_id,
            slug=slug,
            label=label,
            phase=phase,
            sort_order=sort_order,
            color=color,
            is_terminal=is_terminal,
            is_initial=is_initial,
        ))

    # Create transitions (from_slug, to_slug, debtor_type)
    transitions = [
        ("nieuw", "herinnering", "both"),
        ("nieuw", "aanmaning", "both"),
        ("nieuw", "14_dagenbrief", "b2c"),
        ("nieuw", "sommatie", "b2b"),
        ("nieuw", "betaald", "both"),
        ("nieuw", "oninbaar", "both"),
        ("herinnering", "aanmaning", "both"),
        ("herinnering", "14_dagenbrief", "b2c"),
        ("herinnering", "sommatie", "b2b"),
        ("herinnering", "betaald", "both"),
        ("herinnering", "oninbaar", "both"),
        ("aanmaning", "14_dagenbrief", "b2c"),
        ("aanmaning", "sommatie", "b2b"),
        ("aanmaning", "betaald", "both"),
        ("aanmaning", "oninbaar", "both"),
        ("14_dagenbrief", "sommatie", "both"),
        ("14_dagenbrief", "betaald", "both"),
        ("14_dagenbrief", "oninbaar", "both"),
        ("sommatie", "tweede_sommatie", "both"),
        ("sommatie", "dagvaarding", "both"),
        ("sommatie", "betaald", "both"),
        ("sommatie", "oninbaar", "both"),
        ("dagvaarding", "vonnis", "both"),
        ("dagvaarding", "betaald", "both"),
        ("dagvaarding", "schikking", "both"),
        ("vonnis", "executie", "both"),
        ("vonnis", "betaald", "both"),
        ("vonnis", "schikking", "both"),
        ("executie", "betaald", "both"),
        ("executie", "oninbaar", "both"),
    ]

    for from_slug, to_slug, debtor_type in transitions:
        db.add(WorkflowTransition(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            from_status_id=slug_to_id[from_slug],
            to_status_id=slug_to_id[to_slug],
            debtor_type=debtor_type,
        ))

    await db.commit()
    return slug_to_id
