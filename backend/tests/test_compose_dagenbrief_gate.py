"""S205 — 14-dagenbrief-gate op het AI-concept/losse verzendpad (compose/send).

De derde verzenddeur (naast batch en follow-up). Een verse case-mail op een
BIK-claimende sommatie-stap bij een consument zónder aantoonbaar verstuurde
14-dagenbrief wordt geblokkeerd (art. 6:96 lid 6 BW), tenzij de gebruiker bewust
'toch versturen' kiest — dan wordt een onuitwisbaar spoor gelegd. Antwoorden/
doorsturen en B2B raakt de gate niet.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case, CaseActivity
from app.collections.compliance import (
    check_dagenbrief_gate_for_case,
    record_dagenbrief_override,
)
from app.incasso.models import CaseStepHistory, IncassoPipelineStep
from app.relations.models import Contact


async def _b2c_case_on_sommatie(db, tenant_id, *, debtor_type="b2c", step_category="minnelijk"):
    client = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person", name="Cliënt",
    )
    db.add(client)
    await db.flush()
    dagenbrief = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="14-dagenbrief",
        sort_order=0, min_wait_days=0, max_wait_days=15, debtor_type="b2c",
        step_category="minnelijk",
    )
    sommatie = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4, debtor_type="both",
        step_category=step_category, template_type="sommatie_drukte",
    )
    db.add_all([dagenbrief, sommatie])
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number="2026-96001",
        case_type="incasso", status="nieuw", debtor_type=debtor_type,
        client_id=client.id, date_opened=date.today(), incasso_step_id=sommatie.id,
    )
    db.add(case)
    await db.flush()
    return case, dagenbrief, sommatie


# ── Service-laag: de gate-voor-losse-mail ──────────────────────────────────────


@pytest.mark.asyncio
async def test_gate_for_case_blocks_b2c_sommatie(db: AsyncSession, test_tenant: Tenant):
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    reason = await check_dagenbrief_gate_for_case(db, test_tenant.id, case.id)
    assert reason is not None
    assert "14-dagenbrief" in reason


@pytest.mark.asyncio
async def test_gate_for_case_ignores_b2b(db: AsyncSession, test_tenant: Tenant):
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id, debtor_type="b2b")
    assert await check_dagenbrief_gate_for_case(db, test_tenant.id, case.id) is None


@pytest.mark.asyncio
async def test_gate_for_case_ignores_non_sommatie_step(db: AsyncSession, test_tenant: Tenant):
    """Consument op een administratieve/regeling-stap → geen BIK-sommatie, geen blok."""
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id, step_category="regeling")
    assert await check_dagenbrief_gate_for_case(db, test_tenant.id, case.id) is None


@pytest.mark.asyncio
async def test_gate_for_case_allows_after_dagenbrief_sent(db: AsyncSession, test_tenant: Tenant):
    case, dagenbrief, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=dagenbrief.id,
        entered_at=datetime.now(UTC) - timedelta(days=20), email_sent=True,
        trigger_type="manual",
    ))
    await db.flush()
    assert await check_dagenbrief_gate_for_case(db, test_tenant.id, case.id) is None


@pytest.mark.asyncio
async def test_record_override_leaves_indelible_trail(
    db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, _d, sommatie = await _b2c_case_on_sommatie(db, test_tenant.id)
    # Open staphistorie-rij op de huidige stap zodat de notitie ergens landt.
    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=sommatie.id,
        entered_at=datetime.now(UTC), trigger_type="manual",
    ))
    await db.flush()

    await record_dagenbrief_override(
        db, test_tenant.id, case.id, test_user.id, "reden-tekst"
    )

    activity = (await db.execute(
        select(CaseActivity).where(
            CaseActivity.case_id == case.id,
            CaseActivity.activity_type == "compliance_override",
        )
    )).scalar_one()
    assert "toch versturen" in activity.title.lower()

    history = (await db.execute(
        select(CaseStepHistory).where(
            CaseStepHistory.case_id == case.id, CaseStepHistory.step_id == sommatie.id
        )
    )).scalar_one()
    assert history.notes and "overschreven" in history.notes.lower()


# ── HTTP-laag: de blokkade + herkenbare code voor de voorkant ──────────────────


@pytest.mark.asyncio
async def test_compose_send_blocks_with_gate_code(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.post(
        "/api/email/compose/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "to": ["debiteur@example.nl"],
            "subject": "Sommatie",
            "body_html": "<p>Betaal nu.</p>",
            "case_id": str(case.id),
            "already_branded": True,
        },
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "DAGENBRIEF_GATE"
    assert "14-dagenbrief" in detail["message"]


@pytest.mark.asyncio
async def test_compose_send_reply_bypasses_gate(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Een ANTWOORD op correspondentie is geen verse sommatie → de gate mag niet
    vuren. (Zonder e-mailaccount valt hij daarna op een andere fout, niet op de gate.)"""
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.post(
        "/api/email/compose/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "to": ["debiteur@example.nl"],
            "subject": "Re: uw bericht",
            "body_html": "<p>Dank voor uw reactie.</p>",
            "case_id": str(case.id),
            "reply_to_message_id": "abc-123",
        },
    )
    # Niet de gate: geen 422-DAGENBRIEF_GATE. (Wel een andere fout: geen mailaccount.)
    if resp.status_code == 422:
        assert resp.json()["detail"].get("code") != "DAGENBRIEF_GATE"
