"""Tests for the Exact Online integration module."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.token_encryption import encrypt_token
from app.exact_online.models import ExactOnlineConnection, ExactSyncLog
from app.exact_online.provider import ExactOnlineProvider, ExactTokens
from app.exact_online.sync_service import get_connection, get_valid_token, sync_contact
from app.invoices.models import Invoice, InvoiceLine
from app.relations.models import Contact


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def exact_connection(db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Create a test Exact Online connection."""
    conn = ExactOnlineConnection(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        division_id=123456,
        division_name="Kesting Legal B.V.",
        access_token_enc=encrypt_token("test-access-token"),
        refresh_token_enc=encrypt_token("test-refresh-token"),
        token_expiry=datetime.now(UTC) + timedelta(minutes=5),
        connected_email="lisanne@kestinglegal.nl",
        connected_by=test_user.id,
        sales_journal_code="70",
        bank_journal_code="10",
        default_revenue_gl="8000",
        default_expense_gl="4000",
        is_active=True,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn


# ── Model Tests ──────────────────────────────────────────────────────────────


class TestExactOnlineModels:
    """Test model creation and queries."""

    @pytest.mark.asyncio
    async def test_create_connection(self, db: AsyncSession, test_tenant: Tenant, test_user: User):
        conn = ExactOnlineConnection(
            tenant_id=test_tenant.id,
            division_id=999,
            division_name="Test Divisie",
            access_token_enc=encrypt_token("token"),
            refresh_token_enc=encrypt_token("refresh"),
            connected_email="test@test.nl",
            connected_by=test_user.id,
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)

        assert conn.id is not None
        assert conn.division_id == 999
        assert conn.is_active is True

    @pytest.mark.asyncio
    async def test_create_sync_log(self, db: AsyncSession, test_tenant: Tenant):
        log = ExactSyncLog(
            tenant_id=test_tenant.id,
            entity_type="invoice",
            entity_id=uuid.uuid4(),
            exact_id="abc-123",
            exact_number="INV-001",
            sync_status="synced",
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        assert log.id is not None
        assert log.sync_status == "synced"
        assert log.exact_id == "abc-123"


# ── Provider Tests ───────────────────────────────────────────────────────────


class TestExactOnlineProvider:
    """Test the provider (OAuth + API client) with mocked HTTP calls."""

    def test_authorize_url(self):
        with patch("app.exact_online.provider.settings") as mock_settings:
            mock_settings.exact_online_client_id = "test-client-id"
            mock_settings.exact_online_client_secret = "test-secret"
            mock_settings.exact_online_redirect_uri = "https://test.nl/callback"

            provider = ExactOnlineProvider()
            url = provider.get_authorize_url("test-state-123")

            assert "start.exactonline.nl" in url
            assert "client_id=test-client-id" in url
            assert "response_type=code" in url
            assert "state=test-state-123" in url
            assert "redirect_uri=https%3A%2F%2Ftest.nl%2Fcallback" in url

    @pytest.mark.asyncio
    async def test_exchange_code(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.exact_online.provider.settings") as mock_settings:
            mock_settings.exact_online_client_id = "test-id"
            mock_settings.exact_online_client_secret = "test-secret"
            mock_settings.exact_online_redirect_uri = "https://test.nl/callback"

            provider = ExactOnlineProvider()

            with patch("httpx.AsyncClient.post", return_value=mock_response):
                tokens = await provider.exchange_code("auth-code-123")

            assert tokens.access_token == "new-access"
            assert tokens.refresh_token == "new-refresh"
            assert tokens.expires_in == 600

    @pytest.mark.asyncio
    async def test_refresh_token(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "refreshed-access",
            "refresh_token": "rotated-refresh",
            "expires_in": 600,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.exact_online.provider.settings") as mock_settings:
            mock_settings.exact_online_client_id = "test-id"
            mock_settings.exact_online_client_secret = "test-secret"
            mock_settings.exact_online_redirect_uri = "https://test.nl/callback"

            provider = ExactOnlineProvider()

            with patch("httpx.AsyncClient.post", return_value=mock_response):
                tokens = await provider.refresh_access_token("old-refresh")

            assert tokens.access_token == "refreshed-access"
            assert tokens.refresh_token == "rotated-refresh"


# ── Service Tests ────────────────────────────────────────────────────────────


class TestExactOnlineService:
    """Test sync service logic."""

    @pytest.mark.asyncio
    async def test_get_connection(self, db: AsyncSession, exact_connection: ExactOnlineConnection, test_tenant: Tenant):
        conn = await get_connection(db, test_tenant.id)
        assert conn is not None
        assert conn.division_id == 123456

    @pytest.mark.asyncio
    async def test_get_connection_returns_none(self, db: AsyncSession, test_tenant: Tenant):
        conn = await get_connection(db, test_tenant.id)
        assert conn is None

    @pytest.mark.asyncio
    async def test_get_valid_token_not_expired(
        self, db: AsyncSession, exact_connection: ExactOnlineConnection
    ):
        token = await get_valid_token(db, exact_connection)
        assert token == "test-access-token"

    @pytest.mark.asyncio
    async def test_get_valid_token_expired_refreshes(
        self, db: AsyncSession, exact_connection: ExactOnlineConnection
    ):
        # Expire the token
        exact_connection.token_expiry = datetime.now(UTC) - timedelta(minutes=5)
        await db.commit()

        mock_tokens = ExactTokens(
            access_token="fresh-token",
            refresh_token="fresh-refresh",
            expires_in=600,
        )

        with patch.object(
            ExactOnlineProvider, "refresh_access_token", return_value=mock_tokens
        ):
            token = await get_valid_token(db, exact_connection)

        assert token == "fresh-token"


# ── Router Tests ─────────────────────────────────────────────────────────────


class TestExactOnlineRouter:
    """Test API endpoints."""

    @pytest.mark.asyncio
    async def test_status_not_connected(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/exact-online/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False

    @pytest.mark.asyncio
    async def test_status_connected(
        self, client: AsyncClient, auth_headers: dict, exact_connection: ExactOnlineConnection
    ):
        resp = await client.get("/api/exact-online/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["division_name"] == "Kesting Legal B.V."
        assert data["connected_email"] == "lisanne@kestinglegal.nl"

    @pytest.mark.asyncio
    async def test_authorize_requires_admin(self, client: AsyncClient, db: AsyncSession, test_tenant: Tenant):
        """Non-admin users should not be able to authorize."""
        from app.auth.service import create_access_token, hash_password

        non_admin = User(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            email="medewerker@kestinglegal.nl",
            hashed_password=hash_password("test123"),
            full_name="Medewerker",
            role="medewerker",
        )
        db.add(non_admin)
        await db.commit()

        token = create_access_token(str(non_admin.id), str(test_tenant.id))
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/exact-online/authorize", headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_disconnect(
        self, client: AsyncClient, auth_headers: dict, exact_connection: ExactOnlineConnection
    ):
        resp = await client.post("/api/exact-online/disconnect", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/exact-online/disconnect", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_settings_update(
        self, client: AsyncClient, auth_headers: dict, exact_connection: ExactOnlineConnection
    ):
        resp = await client.put(
            "/api/exact-online/settings",
            headers=auth_headers,
            json={
                "sales_journal_code": "71",
                "bank_journal_code": "11",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_sync_log_not_found(self, client: AsyncClient, auth_headers: dict):
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/exact-online/sync-log/invoice/{fake_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["synced"] is False

    @pytest.mark.asyncio
    async def test_sync_requires_connection(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/exact-online/sync", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "koppeling" in data["message"].lower()
