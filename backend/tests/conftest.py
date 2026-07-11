"""Test configuration — sets up a test database and provides fixtures."""

import importlib
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import Tenant, User
from app.auth.service import create_access_token, hash_password
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.relations.models import Contact
from app.workflow.models import WorkflowStatus, WorkflowTransition

# Import ALL model modules so Base.metadata.create_all() creates every table.
# Uses importlib to avoid overwriting the `app` name (FastAPI instance) with
# the `app` package module that bare `import app.x.models` would cause.
for _mod in [
    "app.ai_agent.followup_models",
    "app.ai_agent.intake_models",
    "app.ai_agent.models",
    "app.ai_agent.payment_matching_models",
    "app.calendar.models",
    "app.cases.models",
    "app.collections.models",
    "app.documents.models",
    "app.email.attachment_models",
    "app.email.models",
    "app.email.oauth_models",
    "app.email.synced_email_models",
    "app.exact_online.models",
    "app.incasso.models",
    "app.invoices.models",
    "app.products.models",
    "app.notifications.models",
    "app.relations.kyc_models",
    "app.settings.models",
    "app.time_entries.models",
    "app.trust_funds.models",
]:
    importlib.import_module(_mod)

# Use a separate test database URL (only replace the database name at the end)
_base_url = settings.database_url
TEST_DATABASE_URL = _base_url.rsplit("/", 1)[0] + "/luxis_test"

# NullPool: no connection caching between tests. Each test gets a fresh
# connection on its own event loop, avoiding "attached to a different loop".
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# Schema is created ONCE per test-process (first test), then each test starts
# from a clean slate via TRUNCATE instead of DROP SCHEMA. Recreating the schema
# per test invalidated asyncpg's prepared-statement cache → intermittent
# `UndefinedTableError` on INSERT (KNOWN-002 / KNOWN-003). TRUNCATE issues no DDL,
# so cached plans stay valid. The flag resets per process, so the very first test
# always rebuilds the schema from scratch (clean slate across runs).
_schema_created = False


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Ensure the schema exists, then truncate all tables for a clean per-test slate.

    First test in the process drops + recreates the public schema and builds every
    table. Subsequent tests only TRUNCATE ... RESTART IDENTITY CASCADE — fast and,
    crucially, free of the schema-recreate that corrupted the statement cache.
    """
    global _schema_created
    async with test_engine.begin() as conn:
        if not _schema_created:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(Base.metadata.create_all)
            # If the luxis_app role exists in this cluster (dev/prod-like DBs
            # where RLS migrations ran), the tenant middleware will SET ROLE to
            # it on authenticated requests. The freshly recreated schema must
            # therefore grant luxis_app access, or every endpoint test fails with
            # "relation ... does not exist" (no schema USAGE). Roles are
            # cluster-global, so a sibling DB's migration can make this role
            # appear here. In CI the role is absent → this is skipped and tests
            # run as the superuser exactly as before. RLS *policies* are NOT
            # added here on purpose — tests/test_rls_isolation.py proves
            # enforcement; here we only keep the suite runnable under the role.
            role_exists = (
                await conn.execute(
                    text("SELECT 1 FROM pg_roles WHERE rolname = 'luxis_app'")
                )
            ).scalar()
            if role_exists:
                await conn.execute(text("GRANT USAGE ON SCHEMA public TO luxis_app"))
                await conn.execute(
                    text(
                        "GRANT SELECT, INSERT, UPDATE, DELETE "
                        "ON ALL TABLES IN SCHEMA public TO luxis_app"
                    )
                )
                await conn.execute(
                    text(
                        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO luxis_app"
                    )
                )
            _schema_created = True
        else:
            table_names = ", ".join(
                f'"{table.name}"' for table in Base.metadata.sorted_tables
            )
            if table_names:
                await conn.execute(
                    text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE")
                )
    yield


@pytest_asyncio.fixture
async def db(setup_database):
    """Provide a test database session.

    Depends on setup_database to guarantee tables exist before any session is opened.
    """
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
def session_factory():
    """Factory for *independent* sessions on the test engine.

    Concurrency tests need two simultaneous transactions on separate
    connections (NullPool gives each its own) to exercise row-locking — the
    single shared `db` session cannot contend with itself.
    """
    return TestSession


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Provide a test HTTP client with the test database injected."""

    async def override_get_db():
        # Mirror app.database.get_db so endpoint tests exercise the REAL
        # transaction semantics: commit on success, rollback on exception.
        # The old bare `yield db` skipped both — which is exactly how the
        # SEC-161 lockout bug hid (a handler flushed a counter then raised
        # HTTPException; in prod get_db rolled it back, but the test never did).
        # The shared session's lifecycle stays owned by the `db` fixture, so we
        # commit/rollback here but do NOT close it.
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise

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
        (
            "faillissementsaanvraag",
            "Faillissementsaanvraag",
            "execution",
            85,
            "#991b1b",
            False,
            False,
        ),
        ("betaald", "Betaald", "closed", 90, "#10b981", True, False),
        ("schikking", "Schikking", "closed", 91, "#14b8a6", True, False),
        ("oninbaar", "Oninbaar", "closed", 95, "#6b7280", True, False),
    ]

    slug_to_id: dict[str, uuid.UUID] = {}
    for slug, label, phase, sort_order, color, is_terminal, is_initial in statuses_config:
        status_id = uuid.uuid4()
        slug_to_id[slug] = status_id
        db.add(
            WorkflowStatus(
                id=status_id,
                tenant_id=tenant_id,
                slug=slug,
                label=label,
                phase=phase,
                sort_order=sort_order,
                color=color,
                is_terminal=is_terminal,
                is_initial=is_initial,
            )
        )

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
        db.add(
            WorkflowTransition(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                from_status_id=slug_to_id[from_slug],
                to_status_id=slug_to_id[to_slug],
                debtor_type=debtor_type,
            )
        )

    await db.commit()
    return slug_to_id
