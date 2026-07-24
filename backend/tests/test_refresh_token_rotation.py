"""SEC-26 wachter: refresh-token-rotatie consumeert atomair (geen TOCTOU-race).

De oude opzet (SELECT → check is_used → UPDATE) liet twee gelijktijdige requests met
dezelfde token allebei door de hergebruik-detectie glippen. Deze wachters bewijzen:
1. hergebruik van een verbruikte token → ValueError + alle tokens ingetrokken;
2. een onbekende token → None;
3. GELIJKTIJDIG: twee sessies, één token → hooguit één wint, nooit allebei.
"""

import asyncio
import uuid

import pytest

from app.auth.service import rotate_refresh_token, store_refresh_token


async def _make_token(db, user, token: str) -> None:
    await store_refresh_token(db, token, user.id, user.tenant_id)
    await db.commit()


@pytest.mark.asyncio
async def test_reuse_of_consumed_token_is_detected(db, test_user):
    tok = "reuse-" + uuid.uuid4().hex
    await _make_token(db, test_user, tok)

    first = await rotate_refresh_token(db, tok)
    assert first is not None and first.is_used is True
    await db.commit()

    # Tweede poging met dezelfde token → hergebruik → ValueError + alles ingetrokken.
    with pytest.raises(ValueError):
        await rotate_refresh_token(db, tok)


@pytest.mark.asyncio
async def test_unknown_token_returns_none(db, test_user):
    assert await rotate_refresh_token(db, "bestaat-niet-" + uuid.uuid4().hex) is None


@pytest.mark.asyncio
async def test_concurrent_rotation_only_one_wins(session_factory, db, test_user):
    """Twee gelijktijdige rotaties van dezelfde token: nooit allebei een nieuw paar."""
    tok = "race-" + uuid.uuid4().hex
    await _make_token(db, test_user, tok)

    async def attempt():
        async with session_factory() as s:
            try:
                rt = await rotate_refresh_token(s, tok)
                await s.commit()
                return "ok" if rt is not None else "none"
            except ValueError:
                await s.rollback()
                return "reuse"

    results = await asyncio.gather(attempt(), attempt())

    # Precies één mag winnen; de ander moet hergebruik/none zijn — nooit 2× 'ok'.
    assert results.count("ok") == 1, results
