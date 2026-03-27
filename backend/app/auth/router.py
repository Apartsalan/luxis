"""Auth endpoints — login, registration, token refresh, and user management."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from jwt import PyJWTError as JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TenantDetailResponse,
    TenantUpdateRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.auth.service import (
    authenticate_user,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_id,
    hash_password,
    reset_password_with_token,
    rotate_refresh_token,
    store_refresh_token,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.email.service import is_configured as smtp_is_configured
from app.email.service import send_email
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password, receive JWT tokens."""
    user = await authenticate_user(db, login_data.email, login_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(str(user.id), str(user.tenant_id))
    refresh_token = create_refresh_token(str(user.id), str(user.tenant_id))

    # Store refresh token hash for rotation
    await store_refresh_token(db, refresh_token, user.id, user.tenant_id)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Register a new user in the admin's tenant. Admin only."""
    user = await create_user(
        db,
        tenant_id=admin.tenant_id,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=data.role,
    )
    await db.commit()
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for new access + refresh tokens (with rotation)."""
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Rotate: consume old token, detect reuse
    try:
        rt = await rotate_refresh_token(db, request.refresh_token)
    except ValueError:
        # Token reuse detected — all tokens revoked
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected — all sessions revoked",
        )

    if rt is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(str(user.id), str(user.tenant_id))
    new_refresh_token = create_refresh_token(str(user.id), str(user.tenant_id))

    # Store new refresh token hash
    await store_refresh_token(db, new_refresh_token, user.id, user.tenant_id)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


def _build_reset_email_html(reset_url: str) -> str:
    """Build a styled HTML email for password reset."""
    return f"""\
<!DOCTYPE html>
<html lang="nl">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f5f7;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0"
        style="background:#fff;border-radius:8px;overflow:hidden;">
        <tr><td style="background:#1e293b;padding:24px 32px;">
          <h1 style="margin:0;color:#fff;font-size:20px;">Luxis</h1>
        </td></tr>
        <tr><td style="padding:32px;">
          <h2 style="margin:0 0 16px;color:#1e293b;font-size:18px;">
            Wachtwoord herstellen</h2>
          <p style="color:#475569;font-size:14px;line-height:1.6;">
            Er is een verzoek ingediend om je wachtwoord te herstellen.
            Klik op onderstaande knop om een nieuw wachtwoord in te stellen.
          </p>
          <table cellpadding="0" cellspacing="0" style="margin:24px 0;">
            <tr><td style="background:#2563eb;border-radius:6px;">
              <a href="{reset_url}" style="display:inline-block;
                padding:12px 28px;color:#fff;text-decoration:none;
                font-size:14px;font-weight:600;">
                Wachtwoord herstellen
              </a>
            </td></tr>
          </table>
          <p style="color:#94a3b8;font-size:12px;line-height:1.5;">
            Deze link is 1 uur geldig. Als je geen wachtwoordherstel hebt aangevraagd,
            kun je deze e-mail veilig negeren.
          </p>
        </td></tr>
        <tr><td style="background:#f8fafc;padding:16px 32px;border-top:1px solid #e2e8f0;">
          <p style="margin:0;color:#94a3b8;font-size:11px;text-align:center;">
            &copy; Luxis &mdash; Juridisch dossierbeheer
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


async def _send_reset_email_safe(to: str, html_body: str) -> None:
    """Send reset email with error handling so background task never crashes."""
    try:
        await send_email(
            to=to,
            subject="Wachtwoord herstellen — Luxis",
            html_body=html_body,
        )
        logger.info("Password reset email sent to %s", to)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to)


@router.post("/forgot-password", status_code=200)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link. Always returns success to avoid leaking emails."""
    token = await create_password_reset_token(db, data.email)

    if token:
        frontend_url = settings.cors_origins.split(",")[0].strip()
        reset_url = f"{frontend_url}/reset-password?token={token}"

        if smtp_is_configured():
            html_body = _build_reset_email_html(reset_url)
            background_tasks.add_task(_send_reset_email_safe, data.email, html_body)
            logger.info("Password reset email queued for %s", data.email)
        else:
            logger.warning(
                "SMTP not configured — password reset requested for %s",
                data.email,
            )

    return {"detail": "Als het e-mailadres bekend is, ontvang je een herstellink."}


@router.post("/reset-password", status_code=200)
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    success = await reset_password_with_token(db, data.token, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ongeldige of verlopen herstellink. Vraag een nieuwe aan.",
        )
    return {"detail": "Wachtwoord succesvol gewijzigd."}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's info."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's profile (name, default hourly rate)."""
    allowed_fields = {"full_name", "default_hourly_rate"}
    for field, value in data.model_dump(exclude_unset=True).items():
        if field not in allowed_fields:
            continue
        setattr(current_user, field, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/me/password", status_code=204)
async def change_password_put(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password (PUT)."""
    await _change_password(data, db, current_user)


@router.post("/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    await _change_password(data, db, current_user)


async def _change_password(
    data: ChangePasswordRequest,
    db: AsyncSession,
    current_user: User,
) -> None:
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Huidig wachtwoord is onjuist",
        )
    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    await db.commit()


users_router = APIRouter(prefix="/api/users", tags=["users"])


@users_router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users in the current tenant."""
    result = await db.execute(select(User).where(User.tenant_id == current_user.tenant_id))
    return list(result.scalars().all())


@router.get("/tenant", response_model=TenantDetailResponse)
async def get_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's tenant (office) details."""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Kantoor niet gevonden")
    return tenant


@router.put("/tenant", response_model=TenantDetailResponse)
async def update_tenant(
    data: TenantUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Update the current user's tenant (office) details. Admin only."""
    allowed_fields = {
        "name",
        "kvk_number",
        "btw_number",
        "address",
        "postal_code",
        "city",
        "iban",
        "phone",
        "email",
        "modules_enabled",
    }
    result = await db.execute(select(Tenant).where(Tenant.id == admin.tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="Kantoor niet gevonden")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field not in allowed_fields:
            continue
        setattr(tenant, field, value)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant
