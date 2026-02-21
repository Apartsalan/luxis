"""Email OAuth router — endpoints for connecting/managing email providers.

Endpoints:
- GET  /api/email/oauth/authorize   — Get OAuth authorize URL (redirects to Google/Microsoft)
- GET  /api/email/oauth/callback    — OAuth callback (Google redirects here with code)
- GET  /api/email/oauth/status      — Check if current user has a connected email account
- POST /api/email/oauth/disconnect  — Remove email account connection
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


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/authorize", response_model=AuthorizeResponse)
async def get_authorize_url(
    provider: str = Query(default="gmail", description="Email provider: gmail of outlook"),
    user: User = Depends(get_current_user),
):
    """Generate an OAuth authorization URL.

    The frontend opens this URL in a new window. After the user approves,
    Google redirects to /api/email/oauth/callback with an auth code.
    """
    if not settings.google_client_id:
        raise BadRequestError(
            "Google OAuth is niet geconfigureerd. "
            "Stel GOOGLE_CLIENT_ID en GOOGLE_CLIENT_SECRET in."
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
    """OAuth callback endpoint — Google redirects here after user approves.

    This endpoint:
    1. Decodes the state to get user_id + tenant_id
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
        logger.error(f"OAuth token exchange mislukt: {e}")
        return HTMLResponse(_error_html(f"Token exchange mislukt: {e}"))

    if not tokens.refresh_token:
        logger.error("Geen refresh token ontvangen van Google")
        return HTMLResponse(
            _error_html(
                "Geen refresh token ontvangen. "
                "Ga naar myaccount.google.com → Beveiliging → Apps van derden "
                "en verwijder Luxis, probeer dan opnieuw."
            )
        )

    try:
        # Set tenant context manually since this is an unauthenticated callback
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

    # Return HTML that notifies the opener window and closes itself
    return HTMLResponse(_success_html(tokens.email, provider))


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


# ── HTML templates for OAuth callback popup ──────────────────────────────────


def _success_html(email: str, provider: str) -> str:
    """HTML page shown after successful OAuth — notifies opener and closes."""
    return f"""<!DOCTYPE html>
<html>
<head><title>Luxis — E-mail verbonden</title></head>
<body style="font-family: system-ui, sans-serif; display: flex; justify-content: center;
             align-items: center; height: 100vh; margin: 0; background: #f9fafb;">
  <div style="text-align: center; padding: 2rem;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">&#10003;</div>
    <h2 style="color: #1a1a2e;">E-mail verbonden!</h2>
    <p style="color: #666;">{email} ({provider})</p>
    <p style="color: #999; font-size: 0.875rem;">Dit venster sluit automatisch...</p>
  </div>
  <script>
    // Notify the opener window that OAuth succeeded
    if (window.opener) {{
      window.opener.postMessage({{
        type: 'LUXIS_EMAIL_OAUTH_SUCCESS',
        email: '{email}',
        provider: '{provider}'
      }}, '*');
    }}
    // Close this popup after a brief delay
    setTimeout(() => window.close(), 2000);
  </script>
</body>
</html>"""


def _error_html(message: str) -> str:
    """HTML page shown after failed OAuth."""
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
      window.opener.postMessage({{
        type: 'LUXIS_EMAIL_OAUTH_ERROR',
        error: '{safe_msg}'
      }}, '*');
    }}
  </script>
</body>
</html>"""
