"""Refresh-token revocation on password change / reset (SEC-1, S161).

A password change or reset must invalidate existing sessions: an attacker
holding a stolen 7-day refresh token should not keep access after the legitimate
user changes (or resets) their password.
"""

from sqlalchemy import select

from app.auth.models import RefreshToken, User
from app.auth.service import (
    create_password_reset_token,
    reset_password_with_token,
    store_refresh_token,
)


async def test_change_password_revokes_refresh_tokens(client, test_user: User):
    """After changing the password, an old refresh token can no longer be used."""
    login = await client.post(
        "/api/auth/login",
        json={"email": test_user.email, "password": "testpassword123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    access_token = tokens["access_token"]
    old_refresh = tokens["refresh_token"]

    change = await client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current_password": "testpassword123", "new_password": "BrandNewPass456"},
    )
    assert change.status_code == 204

    # The old refresh token must now be rejected.
    refresh = await client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert refresh.status_code == 401


async def test_reset_password_revokes_refresh_tokens(db, test_user: User):
    """Resetting the password marks all of the user's refresh tokens as used."""
    await store_refresh_token(db, "dummy-jwt-token", test_user.id, test_user.tenant_id)

    token = await create_password_reset_token(db, test_user.email)
    assert token is not None

    ok = await reset_password_with_token(db, token, "freshpassword789")
    assert ok is True

    rows = (
        await db.execute(select(RefreshToken).where(RefreshToken.user_id == test_user.id))
    ).scalars().all()
    assert rows, "expected at least one stored refresh token"
    assert all(rt.is_used for rt in rows), "reset must revoke all refresh tokens"
