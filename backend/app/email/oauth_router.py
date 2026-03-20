"""Email OAuth router — endpoints for connecting/managing email providers.

Endpoints:
- GET  /api/email/oauth/authorize          — Get OAuth authorize URL (Gmail or Outlook)
- GET  /api/email/oauth/callback           — OAuth callback (Gmail redirects here)
- GET  /api/email/oauth/callback/outlook   — OAuth callback (Microsoft redirects here)
- GET  /api/email/oauth/status             — Check if current user has a connected email account
- POST /api/email/oauth/disconnect         — Remove email account connection
"""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.email.oauth_service import (
    decode_oauth_state,
    disconnect_email_account,
    encode_oauth_state,
    get_email_account,
    get_provider,
    store_email_account,
)
from app.shared.exceptions import BadRequestError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email/oauth", tags=["email-oauth"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class AuthorizeResponse(BaseModel):
    authorize_url: str


class EmailAccountStatus(BaseModel):
    connected: bool
    provider: str | None = None
    email_address: str | None = None
    connected_at: str | None = None


class DisconnectResponse(BaseModel):
    success: bool
    message: str


class ImapConnectRequest(BaseModel):
    email_address: str
    host: str
    port: int = 993
    password: str


class ImapConnectResponse(BaseModel):
    success: bool
    message: str
    email_address: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/authorize", response_model=AuthorizeResponse)
async def get_authorize_url(
    provider: str = Query(default="gmail", description="Email provider: gmail of outlook"),
    user: User = Depends(get_current_user),
):
    """Generate an OAuth authorization URL.

    The frontend opens this URL in a new window. After the user approves,
    the provider redirects to the appropriate callback with an auth code.
    """
    if provider == "gmail" and not settings.google_client_id:
        raise BadRequestError(
            "Google OAuth is niet geconfigureerd. "
            "Stel GOOGLE_CLIENT_ID en GOOGLE_CLIENT_SECRET in."
        )
    if provider == "outlook" and not settings.microsoft_client_id:
        raise BadRequestError(
            "Microsoft OAuth is niet geconfigureerd. "
            "Stel MICROSOFT_CLIENT_ID, MICROSOFT_TENANT_ID en MICROSOFT_CLIENT_SECRET in."
        )

    email_provider = get_provider(provider)
    state = encode_oauth_state(str(user.id), str(user.tenant_id), provider)
    url = email_provider.get_authorize_url(state)

    return AuthorizeResponse(authorize_url=url)


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from provider"),
    state: str = Query(..., description="State parameter for CSRF verification"),
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback endpoint — Google redirects here after user approves."""
    return await _handle_oauth_callback(code=code, state=state, db=db)


@router.get("/callback/outlook", response_class=HTMLResponse)
async def oauth_callback_outlook(
    request: Request,
    code: str = Query(..., description="Authorization code from Microsoft"),
    state: str = Query(..., description="State parameter for CSRF verification"),
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback endpoint for Microsoft/Outlook.

    Separate route because Azure App Registration has a distinct redirect URI:
    https://luxis.kestinglegal.nl/api/email/oauth/callback/outlook
    """
    return await _handle_oauth_callback(code=code, state=state, db=db)


@router.get("/status", response_model=EmailAccountStatus)
async def get_oauth_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if the current user has a connected email account."""
    account = await get_email_account(db, user.id, user.tenant_id)
    if not account:
        return EmailAccountStatus(connected=False)

    return EmailAccountStatus(
        connected=True,
        provider=account.provider,
        email_address=account.email_address,
        connected_at=account.connected_at.isoformat() if account.connected_at else None,
    )


@router.post("/imap/connect", response_model=ImapConnectResponse)
async def connect_imap_account(
    body: ImapConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect an IMAP email account (e.g. BaseNet).

    Tests the connection first, then stores encrypted credentials.
    """
    import imaplib

    # Test the IMAP connection
    try:
        imap = imaplib.IMAP4_SSL(body.host, body.port)
        imap.login(body.email_address, body.password)
        imap.select("INBOX", readonly=True)
        imap.close()
        imap.logout()
    except Exception as e:
        logger.error(f"IMAP connection test failed: {e}")
        return ImapConnectResponse(
            success=False,
            message=f"IMAP verbinding mislukt: {e}",
        )

    # Store as EmailAccount with provider="imap"
    # Password in access_token_enc, host:port in scopes
    await store_email_account(
        db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        provider="imap",
        email_address=body.email_address,
        access_token=body.password,
        refresh_token="imap-no-refresh-token",
        expires_in=999999999,  # Never expires (password-based)
        scopes=f"{body.host}:{body.port}",
    )

    logger.info(f"IMAP account verbonden: {body.email_address} ({body.host}:{body.port})")
    return ImapConnectResponse(
        success=True,
        message=f"IMAP account verbonden: {body.email_address}",
        email_address=body.email_address,
    )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_email(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the current user's email account."""
    removed = await disconnect_email_account(db, user.id, user.tenant_id)
    if not removed:
        return DisconnectResponse(success=False, message="Geen e-mailaccount verbonden")
    return DisconnectResponse(success=True, message="E-mailaccount ontkoppeld")


# ── Shared callback logic ─────────────────────────────────────────────────────


async def _handle_oauth_callback(
    *, code: str, state: str, db: AsyncSession
) -> HTMLResponse:
    """Shared OAuth callback logic for both Gmail and Outlook.

    1. Decodes the state to get user_id + tenant_id + provider
    2. Exchanges the code for tokens
    3. Stores encrypted tokens in the database
    4. Returns an HTML page that sends a message to the opener window and closes itself
    """
    try:
        state_data = decode_oauth_state(state)
    except Exception:
        logger.error("Ongeldig OAuth state parameter")
        return HTMLResponse(_error_html("Ongeldige state parameter. Probeer opnieuw."))

    user_id = state_data["user_id"]
    tenant_id = state_data["tenant_id"]
    provider = state_data["provider"]

    try:
        email_provider = get_provider(provider)
        tokens = await email_provider.exchange_code(code)
    except Exception as e:
        logger.error(f"OAuth token exchange mislukt ({provider}): {e}")
        return HTMLResponse(_error_html(f"Token exchange mislukt: {e}"))

    if not tokens.refresh_token:
        logger.error(f"Geen refresh token ontvangen van {provider}")
        if provider == "gmail":
            hint = (
                "Ga naar myaccount.google.com → Beveiliging → Apps van derden "
                "en verwijder Luxis, probeer dan opnieuw."
            )
        else:
            hint = "Probeer de verbinding opnieuw. Neem contact op als het blijft falen."
        return HTMLResponse(
            _error_html(f"Geen refresh token ontvangen. {hint}")
        )

    try:
        from app.middleware.tenant import set_tenant_context

        await set_tenant_context(db, tenant_id)

        await store_email_account(
            db,
            user_id=user_id,
            tenant_id=tenant_id,
            provider=provider,
            email_address=tokens.email,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            scopes=tokens.scope,
        )
    except Exception as e:
        logger.error(f"Email account opslaan mislukt: {e}")
        return HTMLResponse(_error_html(f"Opslaan mislukt: {e}"))

    return HTMLResponse(_success_html(tokens.email, provider))


# ── HTML templates for OAuth callback popup ──────────────────────────────────


def _success_html(email: str, provider: str) -> str:
    """HTML page shown after successful OAuth — notifies opener and closes."""
    import html as _html
    import json as _json
    safe_email = _html.escape(email)
    safe_provider = _html.escape(provider)
    # JSON-encode for safe JavaScript string embedding
    js_email = _json.dumps(email)
    js_provider = _json.dumps(provider)
    origin = settings.cors_origins.split(",")[0].strip()
    js_origin = _json.dumps(origin)
    return f"""<!DOCTYPE html>
<html>
<head><title>Luxis — E-mail verbonden</title></head>
<body style="font-family: system-ui, sans-serif; display: flex; justify-content: center;
             align-items: center; height: 100vh; margin: 0; background: #f9fafb;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">&#10003;</div>
    <h2 style="color: #1a1a2e;">E-mail verbonden!</h2>
    <p style="color: #666;">{safe_email} ({safe_provider})</p>
    <p style="color: #999; font-size: 0.875rem;">Dit venster sluit automatisch...</p>
  </div>
  <script>
    // Notify the opener window that OAuth succeeded
    if (window.opener) {{
      window.opener.postMessage({{
        type: 'LUXIS_EMAIL_OAUTH_SUCCESS',
        email: {js_email},
        provider: {js_provider}
      }}, {js_origin});
    }}
    // Close this popup after a brief delay
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>"""


def _error_html(message: str) -> str:
    """HTML page shown after failed OAuth."""
    import json as _json
    # Escape for safe HTML insertion
    safe_msg = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
      var origin = {_json.dumps(settings.cors_origins.split(",")[0].strip())};
      window.opener.postMessage({{
        type: 'LUXIS_EMAIL_OAUTH_ERROR',
        error: {_json.dumps(message)}
      }}, origin);
    }}
  </script>
</body>
</html>"""
