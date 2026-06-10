"""Account-lockout persistence tests (SEC-161).

Regression for a silently-broken security control: ``authenticate_user`` used
``db.flush()`` for the failed-attempt counter, but a failed login ends with the
endpoint raising ``HTTPException`` — and ``get_db`` rolls the transaction back on
any exception. So the increment was discarded on every failed login and the
account lockout (SEC-20) never triggered in production.

These tests reproduce the production request lifecycle faithfully: the standard
``client`` fixture cannot, because its ``override_get_db`` does not replicate
``get_db``'s commit/rollback. So we drive sessions directly and roll back after
each failed attempt — exactly what the 401 does in production — then assert the
counter survived via a fresh session.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.models import User
from app.auth.service import authenticate_user
from app.config import settings

_TEST_URL = settings.database_url.rsplit("/", 1)[0] + "/luxis_test"


async def _failed_login_then_rollback(maker, email: str) -> None:
    """One failed-login request, faithful to prod: authenticate (wrong password),
    then roll the transaction back the way get_db does on the 401 HTTPException."""
    async with maker() as session:
        result = await authenticate_user(session, email, "wrong-password")
        assert result is None
        await session.rollback()


async def test_failed_login_increment_survives_request_rollback(test_user):
    """The failed-attempt counter must persist across the request rollback.

    flush() → rolled back → count stays 0 (the bug). commit() → count == 1.
    """
    engine = create_async_engine(_TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        await _failed_login_then_rollback(maker, test_user.email)

        async with maker() as session:
            user = await session.get(User, test_user.id)
            assert user.failed_login_count == 1, (
                "failed_login_count was rolled back with the request — "
                "lockout never triggers"
            )
    finally:
        await engine.dispose()


async def test_account_locks_after_five_failures(test_user):
    """After 5 failed logins the account is locked, and a 6th attempt with the
    CORRECT password is rejected while the lock is active."""
    engine = create_async_engine(_TEST_URL, poolclass=NullPool)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        for _ in range(5):
            await _failed_login_then_rollback(maker, test_user.email)

        async with maker() as session:
            user = await session.get(User, test_user.id)
            assert user.failed_login_count >= 5
            assert user.locked_until is not None, "account should be locked after 5 failures"

        # Correct password while locked → still rejected.
        async with maker() as session:
            result = await authenticate_user(session, test_user.email, "testpassword123")
            assert result is None, "locked account must reject even a correct password"
    finally:
        await engine.dispose()
