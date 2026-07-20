"""S231 — WACHTER: kantoormail gaat altijd vanaf incasso@, via het beste vervoer.

Aanleiding (Arsalan, 20-7, tijdens demo): mail naar hotmail/outlook kaatste terug.
Oorzaak gemeten in de bounce zelf: BaseNets uitgaande relay 194.180.216.120 staat
op Microsofts blokkadelijst (550 5.7.1, code S3150). Lisannes eigen BaseNet-webmail
kwam wél aan — die verlaat het netwerk via een andere uitgang.

De oplossing scheidt VERVOER van AFZENDER: versturen mag via het Graph-account van
een medewerker, mits er incasso@ boven staat ("Verzenden als" in Microsoft 365).
Dat is precies waar het mis kan gaan — huisregel M1 (afzender = kantooradres) mag
niet sneuvelen omdat we het vervoer verleggen.

Deze wachter toetst de SOORT: welk kanaal er ook gekozen wordt, de afzender die
op de mail komt is het kantooradres. Faalt zodra een toekomstige provider of route
dat laat lopen.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.email.oauth_models import EmailAccount
from app.email.oauth_service import resolve_office_channel

OFFICE = "incasso@kestinglegal.nl"


async def _account(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    address: str,
    provider: str,
    days_ago: int = 0,
) -> EmailAccount:
    from datetime import timedelta

    acc = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider=provider,
        email_address=address,
        access_token_enc=b"x",
        refresh_token_enc=b"x",
        connected_at=datetime.now(UTC) - timedelta(days=days_ago),
    )
    db.add(acc)
    await db.flush()
    return acc


@pytest.fixture
async def office_tenant(db: AsyncSession, test_tenant: Tenant) -> Tenant:
    test_tenant.email = OFFICE
    await db.flush()
    return test_tenant


@pytest.mark.asyncio
async def test_graph_op_kantooradres_is_eerste_keuze(
    db: AsyncSession, office_tenant: Tenant, test_user: User
):
    """Ideaal: het kantooradres zelf via Graph — geen 'verzenden als' nodig."""
    acc = await _account(
        db, office_tenant.id, test_user.id, address=OFFICE, provider="outlook"
    )
    await _account(
        db, office_tenant.id, test_user.id, address=OFFICE, provider="imap"
    )

    channel = await resolve_office_channel(db, office_tenant.id)

    assert channel.account is not None and channel.account.id == acc.id
    assert channel.from_address is None  # accountadres ís al het kantooradres


@pytest.mark.asyncio
async def test_ander_graph_account_verstuurt_namens_kantoor(
    db: AsyncSession, office_tenant: Tenant, test_user: User
):
    """De route die de Microsoft-blokkade omzeilt: vervoer via het persoonlijke
    Graph-account, afzender incasso@. Zonder from_address zou het persoonlijke
    adres op de sommatie belanden — precies wat huisregel M1 verbiedt."""
    await _account(
        db, office_tenant.id, test_user.id, address=OFFICE, provider="imap"
    )
    graph = await _account(
        db, office_tenant.id, test_user.id,
        address="seidony@kestinglegal.nl", provider="outlook",
    )

    channel = await resolve_office_channel(db, office_tenant.id)

    assert channel.account is not None and channel.account.id == graph.id
    assert channel.from_address == OFFICE


@pytest.mark.asyncio
async def test_zonder_graph_valt_terug_op_basenet(
    db: AsyncSession, office_tenant: Tenant, test_user: User
):
    """Geen Graph-account: het oude gedrag blijft werken (geen regressie)."""
    imap = await _account(
        db, office_tenant.id, test_user.id, address=OFFICE, provider="imap"
    )

    channel = await resolve_office_channel(db, office_tenant.id)

    assert channel.account is not None and channel.account.id == imap.id
    assert channel.from_address is None


@pytest.mark.asyncio
async def test_geen_kantooradres_ingesteld_geeft_geen_kanaal(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Zonder kantooradres kiest de resolver niets — beller valt terug op het
    gebruikersaccount. Nooit stilletjes namens een willekeurig adres versturen."""
    test_tenant.email = None
    await _account(
        db, test_tenant.id, test_user.id,
        address="seidony@kestinglegal.nl", provider="outlook",
    )
    await db.flush()

    channel = await resolve_office_channel(db, test_tenant.id)

    assert channel.account is None
    assert channel.from_address is None


@pytest.mark.asyncio
async def test_elke_provider_kent_de_afzender_afspraak():
    """Wachter op de SOORT: een provider die `from_address` niet accepteert, laat
    de afzender stil terugvallen op het accountadres. Elke provider moet hem
    kennen — ook een die er later bij komt."""
    import inspect

    from app.email.providers.base import EmailProvider
    from app.email.providers.imap_provider import ImapProvider
    from app.email.providers.outlook import OutlookProvider

    for provider_cls in (EmailProvider, ImapProvider, OutlookProvider):
        params = inspect.signature(provider_cls.send_message).parameters
        assert "from_address" in params, (
            f"{provider_cls.__name__}.send_message kent 'from_address' niet — "
            "die route kan de afzender niet garanderen"
        )


@pytest.mark.asyncio
async def test_graph_zet_afzender_in_het_bericht():
    """De Graph-aanroep moet het from-veld écht meesturen; anders belooft de
    resolver iets dat de provider niet waarmaakt."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.email.providers.outlook import OutlookProvider

    captured: dict = {}

    class _Resp:
        def raise_for_status(self):
            return None

    async def _post(url, headers=None, json=None):
        captured["json"] = json
        return _Resp()

    fake_client = MagicMock()
    fake_client.post = AsyncMock(side_effect=_post)
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.email.providers.outlook.httpx.AsyncClient", return_value=fake_client),
        patch("app.email.service.check_outbound_lock", return_value=None),
    ):
        await OutlookProvider().send_message(
            "token",
            to=["debiteur@example.nl"],
            subject="Eerste sommatie",
            body_html="<p>x</p>",
            from_address=OFFICE,
        )

    sender = captured["json"]["message"]["from"]["emailAddress"]["address"]
    assert sender == OFFICE
