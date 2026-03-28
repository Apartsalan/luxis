"""Exact Online router — OAuth, settings, and sync endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.email.oauth_service import decode_oauth_state, encode_oauth_state
from app.email.token_encryption import encrypt_token
from app.exact_online.models import ExactOnlineConnection, ExactSyncLog
from app.exact_online.provider import ExactOnlineProvider
from app.exact_online.schemas import (
    ExactAuthorizeResponse,
    ExactConnectionStatus,
    ExactDisconnectResponse,
    ExactGLAccount,
    ExactJournal,
    ExactSettingsResponse,
    ExactSettingsUpdate,
    ExactSetupData,
    ExactVATCode,
    InvoiceSyncResult,
    SyncResult,
)
from app.exact_online.sync_service import (
    get_connection,
    get_valid_token,
    sync_all,
    sync_invoice,
    sync_payment,
)
from app.invoices.models import Invoice
from app.shared.exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exact-online", tags=["exact-online"])


# ── OAuth ────────────────────────────────────────────────────────────────────


@router.get("/authorize", response_model=ExactAuthorizeResponse)
async def get_authorize_url(
    user: User = Depends(require_role("admin")),
):
    """Generate Exact Online OAuth authorization URL. Admin only."""
    if not settings.exact_online_client_id:
        raise BadRequestError(
            "Exact Online is niet geconfigureerd. "
            "Stel EXACT_ONLINE_CLIENT_ID en EXACT_ONLINE_CLIENT_SECRET in."
        )

    provider = ExactOnlineProvider()
    state = await encode_oauth_state(str(user.id), str(user.tenant_id), "exact_online")
    url = provider.get_authorize_url(state)

    return ExactAuthorizeResponse(authorize_url=url)


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback — Exact Online redirects here after user approves."""
    try:
        state_data = await decode_oauth_state(state)
    except Exception:
        logger.error("Ongeldig Exact Online OAuth state parameter")
        return HTMLResponse(_error_html("Ongeldige state parameter. Probeer opnieuw."))

    user_id = state_data["user_id"]
    tenant_id = state_data["tenant_id"]

    provider = ExactOnlineProvider()

    try:
        tokens = await provider.exchange_code(code)
    except Exception as e:
        logger.error(f"Exact Online token exchange mislukt: {e}")
        return HTMLResponse(_error_html("Token exchange mislukt. Probeer opnieuw."))

    if not tokens.refresh_token:
        return HTMLResponse(_error_html("Geen refresh token ontvangen."))

    try:
        # Get division info
        me = await provider.get_current_me(tokens.access_token)
        division_id = me["CurrentDivision"]
        division_name = me.get("DivisionCustomerName", "")
        email = me.get("Email", "")

        # Set tenant context
        from app.middleware.tenant import set_tenant_context
        await set_tenant_context(db, tenant_id)

        # Store or update connection
        from datetime import UTC, datetime, timedelta

        existing = await get_connection(db, uuid.UUID(tenant_id))
        if existing:
            existing.division_id = division_id
            existing.division_name = division_name
            existing.access_token_enc = encrypt_token(tokens.access_token)
            existing.refresh_token_enc = encrypt_token(tokens.refresh_token)
            existing.token_expiry = datetime.now(UTC) + timedelta(seconds=tokens.expires_in)
            existing.connected_email = email
            existing.connected_by = uuid.UUID(user_id)
            existing.is_active = True
            await db.flush()
        else:
            conn = ExactOnlineConnection(
                tenant_id=uuid.UUID(tenant_id),
                division_id=division_id,
                division_name=division_name,
                access_token_enc=encrypt_token(tokens.access_token),
                refresh_token_enc=encrypt_token(tokens.refresh_token),
                token_expiry=datetime.now(UTC) + timedelta(seconds=tokens.expires_in),
                connected_email=email,
                connected_by=uuid.UUID(user_id),
            )
            db.add(conn)
            await db.flush()

    except Exception as e:
        logger.error(f"Exact Online connectie opslaan mislukt: {e}")
        return HTMLResponse(_error_html("Opslaan mislukt. Probeer opnieuw."))

    return HTMLResponse(_success_html(email, division_name))


@router.get("/status", response_model=ExactConnectionStatus)
async def get_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if the tenant has a connected Exact Online account."""
    conn = await get_connection(db, user.tenant_id)
    if not conn:
        return ExactConnectionStatus(connected=False)

    return ExactConnectionStatus(
        connected=True,
        division_name=conn.division_name,
        connected_email=conn.connected_email,
        connected_at=conn.created_at.isoformat() if conn.created_at else None,
        last_sync_at=conn.last_sync_at.isoformat() if conn.last_sync_at else None,
        sales_journal_code=conn.sales_journal_code,
        bank_journal_code=conn.bank_journal_code,
        default_revenue_gl=conn.default_revenue_gl,
        default_expense_gl=conn.default_expense_gl,
    )


@router.post("/disconnect", response_model=ExactDisconnectResponse)
async def disconnect(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Exact Online. Admin only."""
    conn = await get_connection(db, user.tenant_id)
    if not conn:
        return ExactDisconnectResponse(success=False, message="Geen Exact Online koppeling gevonden")

    conn.is_active = False
    await db.flush()
    return ExactDisconnectResponse(success=True, message="Exact Online ontkoppeld")


# ── Settings ─────────────────────────────────────────────────────────────────


@router.get("/setup-data", response_model=ExactSetupData)
async def get_setup_data(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Fetch journals, GL accounts, and VAT codes from Exact Online.

    Used to populate the settings dropdowns after connecting.
    """
    conn = await get_connection(db, user.tenant_id)
    if not conn:
        raise BadRequestError("Geen Exact Online koppeling gevonden")

    provider = ExactOnlineProvider()
    token = await get_valid_token(db, conn)

    journals_raw = await provider.get_journals(token, conn.division_id)
    gl_raw = await provider.get_gl_accounts(token, conn.division_id)
    vat_raw = await provider.get_vat_codes(token, conn.division_id)

    journals = [
        ExactJournal(code=j["Code"], description=j.get("Description", ""))
        for j in journals_raw
    ]
    gl_accounts = [
        ExactGLAccount(id=g["ID"], code=g.get("Code", ""), description=g.get("Description", ""))
        for g in gl_raw
    ]
    vat_codes = [
        ExactVATCode(
            code=v["Code"],
            description=v.get("Description", ""),
            percentage=float(v.get("Percentage", 0)),
        )
        for v in vat_raw
    ]

    return ExactSetupData(
        journals=journals,
        gl_accounts=gl_accounts,
        vat_codes=vat_codes,
    )


@router.put("/settings", response_model=ExactSettingsResponse)
async def update_settings(
    body: ExactSettingsUpdate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update Exact Online journal and GL account mappings. Admin only."""
    conn = await get_connection(db, user.tenant_id)
    if not conn:
        raise BadRequestError("Geen Exact Online koppeling gevonden")

    if body.sales_journal_code is not None:
        conn.sales_journal_code = body.sales_journal_code
    if body.bank_journal_code is not None:
        conn.bank_journal_code = body.bank_journal_code
    if body.default_revenue_gl is not None:
        conn.default_revenue_gl = body.default_revenue_gl
    if body.default_expense_gl is not None:
        conn.default_expense_gl = body.default_expense_gl
    await db.flush()

    return ExactSettingsResponse(success=True, message="Instellingen opgeslagen")


# ── Sync ─────────────────────────────────────────────────────────────────────


@router.post("/sync", response_model=SyncResult)
async def trigger_sync(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full sync of all unsynchronized entities. Admin only."""
    result = await sync_all(db, user.tenant_id)
    return SyncResult(**result)


@router.post("/sync/invoice/{invoice_id}", response_model=InvoiceSyncResult)
async def sync_single_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync a single invoice to Exact Online."""
    conn = await get_connection(db, user.tenant_id)
    if not conn:
        raise BadRequestError("Geen Exact Online koppeling gevonden")

    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == user.tenant_id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Factuur niet gevonden")

    if invoice.status == "concept":
        raise BadRequestError("Concept-facturen kunnen niet gesynchroniseerd worden")

    exact_id = await sync_invoice(db, conn, invoice)
    if exact_id:
        return InvoiceSyncResult(
            success=True,
            message=f"Factuur {invoice.invoice_number} gesynchroniseerd",
            exact_id=exact_id,
        )
    return InvoiceSyncResult(success=False, message="Synchronisatie mislukt")


@router.get("/sync-log/{entity_type}/{entity_id}")
async def get_sync_status(
    entity_type: str,
    entity_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if a specific entity has been synced to Exact Online."""
    result = await db.execute(
        select(ExactSyncLog).where(
            ExactSyncLog.tenant_id == user.tenant_id,
            ExactSyncLog.entity_type == entity_type,
            ExactSyncLog.entity_id == entity_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        return {"synced": False}

    return {
        "synced": log.sync_status == "synced",
        "exact_id": log.exact_id,
        "exact_number": log.exact_number,
        "sync_status": log.sync_status,
        "error_message": log.error_message,
        "synced_at": log.created_at.isoformat() if log.created_at else None,
    }


# ── HTML templates ───────────────────────────────────────────────────────────


def _success_html(email: str, division_name: str) -> str:
    """HTML page shown after successful Exact Online OAuth."""
    import html as _html
    import json as _json

    safe_email = _html.escape(email)
    safe_division = _html.escape(division_name)
    origin = settings.cors_origins.split(",")[0].strip()
    js_origin = _json.dumps(origin)
    return f"""<!DOCTYPE html>
<html>
<head><title>Luxis — Exact Online verbonden</title></head>
<body style="font-family: system-ui, sans-serif; display: flex; justify-content: center;
             align-items: center; height: 100vh; margin: 0; background: #f9fafb;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">&#10003;</div>
    <h2 style="color: #1a1a2e;">Exact Online verbonden!</h2>
    <p style="color: #666;">{safe_email}</p>
    <p style="color: #999; font-size: 0.875rem;">Divisie: {safe_division}</p>
    <p style="color: #999; font-size: 0.875rem;">Dit venster sluit automatisch...</p>
  </div>
  <script>
    if (window.opener) {{
      window.opener.postMessage({{
        type: 'LUXIS_EXACT_OAUTH_SUCCESS',
        email: {_json.dumps(email)},
        division: {_json.dumps(division_name)}
      }}, {js_origin});
    }}
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>"""


def _error_html(message: str) -> str:
    """HTML page shown after failed Exact Online OAuth."""
    import json as _json

    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    origin = settings.cors_origins.split(",")[0].strip()
    return f"""<!DOCTYPE html>
<html>
<head><title>Luxis — Fout</title></head>
<body style="font-family: system-ui, sans-serif; display: flex; justify-content: center;
             align-items: center; height: 100vh; margin: 0; background: #fef2f2;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">&#10007;</div>
    <h2 style="color: #991b1b;">Verbinding mislukt</h2>
    <p style="color: #666;">{safe_msg}</p>
    <p style="color: #999; font-size: 0.875rem;">Sluit dit venster en probeer opnieuw.</p>
  </div>
  <script>
    if (window.opener) {{
      var origin = {_json.dumps(origin)};
      window.opener.postMessage({{
        type: 'LUXIS_EXACT_OAUTH_ERROR',
        error: {_json.dumps(message)}
      }}, origin);
    }}
  </script>
</body>
</html>"""
