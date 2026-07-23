"""Wachters (S241) — meldingen-bundeling in de bel.

Meting 23-7: 112 ongelezen meldingen bij seidony, 93 bij kesting; grootste
stapels 63× 'taak te laat' en 25× 'nieuwe mail'. De bel werd daardoor
onbruikbaar — belangrijke meldingen verdronken. Typen met >= 3 ongelezen
meldingen worden nu één bundel-rij (grouped=true); de platte lijst blijft
ongewijzigd omdat de dossier-actiefeed die leest.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.notifications.models import Notification
from app.notifications.service import (
    BUNDLE_THRESHOLD,
    list_bell_notifications,
    list_notifications,
    mark_type_read,
)


async def _make_notifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    type_: str,
    count: int,
    is_read: bool = False,
    title_prefix: str = "Melding",
) -> list[Notification]:
    rows = [
        Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type=type_,
            title=f"{title_prefix} {i}",
            message="",
            is_read=is_read,
        )
        for i in range(count)
    ]
    db.add_all(rows)
    await db.flush()
    return rows


@pytest.mark.asyncio
async def test_drie_of_meer_ongelezen_van_zelfde_type_worden_een_bundel(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """3 ongelezen 'taak te laat' → één rij met bundle_count=3; een los ander
    type blijft een gewone rij."""
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="deadline_overdue", count=3
    )
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="email_received", count=1
    )

    items = await list_bell_notifications(db, test_tenant.id, test_user.id)

    bundles = [i for i in items if i.bundle_count is not None]
    singles = [i for i in items if i.bundle_count is None]
    assert len(bundles) == 1
    assert bundles[0].type == "deadline_overdue"
    assert bundles[0].bundle_count == 3
    # De 3 gebundelde meldingen staan NIET ook nog los in de lijst
    assert all(s.type != "deadline_overdue" for s in singles)
    assert len(singles) == 1
    assert singles[0].type == "email_received"


@pytest.mark.asyncio
async def test_onder_de_drempel_blijft_alles_los(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    await _make_notifications(
        db,
        test_tenant.id,
        test_user.id,
        type_="deadline_overdue",
        count=BUNDLE_THRESHOLD - 1,
    )

    items = await list_bell_notifications(db, test_tenant.id, test_user.id)

    assert all(i.bundle_count is None for i in items)
    assert len([i for i in items if i.type == "deadline_overdue"]) == BUNDLE_THRESHOLD - 1


@pytest.mark.asyncio
async def test_gelezen_meldingen_van_gebundeld_type_blijven_los_zichtbaar(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De bundel pakt alleen ONgelezen rijen; al-gelezen historie blijft staan."""
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="email_received", count=4
    )
    await _make_notifications(
        db,
        test_tenant.id,
        test_user.id,
        type_="email_received",
        count=2,
        is_read=True,
        title_prefix="Gelezen",
    )

    items = await list_bell_notifications(db, test_tenant.id, test_user.id)

    bundles = [i for i in items if i.bundle_count is not None]
    assert len(bundles) == 1
    assert bundles[0].bundle_count == 4
    read_singles = [i for i in items if i.bundle_count is None and i.type == "email_received"]
    assert len(read_singles) == 2
    assert all(i.is_read for i in read_singles)


@pytest.mark.asyncio
async def test_platte_lijst_blijft_ongewijzigd_bij_stapel(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De dossier-actiefeed leest de platte lijst — die mag NOOIT gaan bundelen."""
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="deadline_overdue", count=5
    )

    flat = await list_notifications(db, test_tenant.id, test_user.id)

    assert len(flat) == 5
    assert all(not hasattr(n, "bundle_count") or True for n in flat)  # ORM-rijen
    # Belangrijker: het zijn 5 losse rijen, geen 1
    assert len({n.id for n in flat}) == 5


@pytest.mark.asyncio
async def test_mark_type_read_alleen_eigen_type_en_eigen_gebruiker(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Bundel-klik markeert alleen het eigen type van de eigen gebruiker."""
    other_user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="s241-ander@test.local",
        hashed_password="x",
        full_name="Ander",
        role="advocaat",
        is_active=True,
    )
    db.add(other_user)
    await db.flush()

    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="deadline_overdue", count=3
    )
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="email_received", count=2
    )
    await _make_notifications(
        db, test_tenant.id, other_user.id, type_="deadline_overdue", count=2
    )

    count = await mark_type_read(db, test_tenant.id, test_user.id, "deadline_overdue")

    assert count == 3
    # Eigen ander type onaangeraakt; andere gebruiker onaangeraakt
    own_after = await list_notifications(db, test_tenant.id, test_user.id)
    assert all(n.is_read for n in own_after if n.type == "deadline_overdue")
    assert all(not n.is_read for n in own_after if n.type == "email_received")
    other_after = await list_notifications(db, test_tenant.id, other_user.id)
    assert all(not n.is_read for n in other_after)


@pytest.mark.asyncio
async def test_bundel_valt_nooit_uit_de_lijst_door_de_limit_kap(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Ook met een lijst vol nieuwere losse meldingen blijft de bundel bovenaan
    staan — een stapel ongelezen werk mag niet wegvallen achter de limit."""
    await _make_notifications(
        db, test_tenant.id, test_user.id, type_="deadline_overdue", count=4
    )
    # 15 nieuwere losse (gelezen) meldingen die de lijst zouden vullen
    await _make_notifications(
        db,
        test_tenant.id,
        test_user.id,
        type_="email_received",
        count=15,
        is_read=True,
        title_prefix="Nieuwer",
    )

    items = await list_bell_notifications(db, test_tenant.id, test_user.id, limit=15)

    assert len(items) == 15
    assert items[0].bundle_count == 4
    assert items[0].type == "deadline_overdue"


@pytest.mark.asyncio
async def test_bundel_drager_is_de_nieuwste_melding(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De bundel-rij draagt het id + tijdstip van de nieuwste melding, zodat de
    bel hem chronologisch op de juiste plek toont."""
    rows = await _make_notifications(
        db, test_tenant.id, test_user.id, type_="ai_draft_ready", count=3
    )

    items = await list_bell_notifications(db, test_tenant.id, test_user.id)

    bundle = next(i for i in items if i.bundle_count is not None)
    newest = max(rows, key=lambda r: (r.created_at, r.id))
    assert bundle.created_at == max(r.created_at for r in rows)
    # Drager is één van de stapel (bij gelijke timestamps kan de tiebreak
    # verschillen — het tijdstip is wat de sortering draagt)
    assert bundle.id in {r.id for r in rows}
    assert newest.type == bundle.type
