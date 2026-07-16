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
async def test_gate_clock_runs_from_send_date_not_entry_date(
    db: AsyncSession, test_tenant: Tenant
):
    """S207 (review S205): de wettelijke 15-dagen-klok rekent vanaf het échte
    verzendmoment (email_sent_at), niet vanaf stap-binnenkomst. Een zaak die 20
    dagen geleden op de 14-dagenbrief-stap kwam maar waarvan de brief pas 5 dagen
    geleden écht is verstuurd, moet nog geblokkeerd zijn."""
    case, dagenbrief, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=dagenbrief.id,
        entered_at=datetime.now(UTC) - timedelta(days=20), email_sent=True,
        email_sent_at=datetime.now(UTC) - timedelta(days=5),
        trigger_type="manual",
    ))
    await db.flush()
    reason = await check_dagenbrief_gate_for_case(db, test_tenant.id, case.id)
    assert reason is not None
    assert "14-dagentermijn" in reason


@pytest.mark.asyncio
async def test_gate_allows_15_days_after_send_date(
    db: AsyncSession, test_tenant: Tenant
):
    """Tegenhanger: 16 dagen ná de echte verzending is de termijn verstreken."""
    case, dagenbrief, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=dagenbrief.id,
        entered_at=datetime.now(UTC) - timedelta(days=30), email_sent=True,
        email_sent_at=datetime.now(UTC) - timedelta(days=16),
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
async def test_document_send_blocks_with_gate_code(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S207 — vierde verzenddeur (review S205): 'document per e-mail versturen'
    rendert élk eerder gegenereerd document opnieuw en mailt het. Op een
    consumentendossier op een sommatie-stap zonder verstreken 14-dagenbrief moet
    dezelfde gate vuren, mét de herkenbare code voor de voorkant."""
    from app.documents.models import GeneratedDocument

    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    doc = GeneratedDocument(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        generated_by_id=test_user.id, title="Eerste sommatie",
        document_type="sommatie_drukte", template_type="sommatie_drukte",
    )
    db.add(doc)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.post(
        f"/api/documents/{doc.id}/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_email": "debiteur@example.nl"},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "DAGENBRIEF_GATE"
    assert "14-dagenbrief" in detail["message"]


@pytest.mark.asyncio
async def test_document_send_override_sends_and_leaves_trail(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Met 'toch versturen' (compliance_override) gaat het document wél de deur
    uit én ligt er een onuitwisbaar spoor op het dossier."""
    from unittest.mock import AsyncMock, patch

    from app.documents.models import GeneratedDocument

    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    doc = GeneratedDocument(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        generated_by_id=test_user.id, title="Eerste sommatie",
        document_type="sommatie_drukte", template_type="sommatie_drukte",
    )
    db.add(doc)
    await db.commit()

    from types import SimpleNamespace

    email_log = SimpleNamespace(
        id=uuid.uuid4(), recipient="debiteur@example.nl",
        subject="Eerste sommatie", status="sent", error_message=None, template=None,
    )
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.documents.router.render_docx", new_callable=AsyncMock) as mock_render,
        patch("app.documents.router.docx_to_pdf", new_callable=AsyncMock) as mock_pdf,
        patch("app.email.send_service.send_with_attachment", new_callable=AsyncMock) as mock_send,
    ):
        mock_render.return_value = (b"docx", "sommatie.docx", "sommatie_drukte", None)
        mock_pdf.return_value = b"pdf"
        mock_send.return_value = email_log
        resp = await client.post(
            f"/api/documents/{doc.id}/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_email": "debiteur@example.nl", "compliance_override": True},
        )

    assert resp.status_code == 200, resp.text
    mock_send.assert_called_once()
    # S224 (huisregel M4): het onderwerp op de document-verzendroute komt uit de
    # gedeelde bouwer (huisformaat), niet uit "{titel} — {nr}" (dossiernr dubbel).
    assert (
        mock_send.call_args.kwargs["subject"] == "Cliënt — Eerste sommatie — 2026-96001"
    )

    activity = (await db.execute(
        select(CaseActivity).where(
            CaseActivity.case_id == case.id,
            CaseActivity.activity_type == "compliance_override",
        )
    )).scalar_one()
    assert "toch versturen" in activity.title.lower()


@pytest.mark.asyncio
async def test_compose_eml_blocks_with_gate_code(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S224 — vijfde verzenddeur (veegsessie): de .eml-route ('Open in Outlook')
    levert een kant-en-klare sommatie af die de gebruiker zelf verstuurt. Op een
    consumentendossier op een sommatie-stap zonder verstreken 14-dagenbrief moet
    dezelfde gate vuren, mét de herkenbare code voor de voorkant."""
    case, _d, _s = await _b2c_case_on_sommatie(db, test_tenant.id)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.post(
        f"/api/email/compose/cases/{case.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_email": "debiteur@example.nl",
            "subject": "Sommatie",
            "body": "Betaal nu.",
        },
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "DAGENBRIEF_GATE"
    assert "14-dagenbrief" in detail["message"]


@pytest.mark.asyncio
async def test_compose_eml_override_builds_and_leaves_trail(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Met 'toch openen' (compliance_override) komt de .eml wél terug én ligt er
    een onuitwisbaar spoor op het dossier."""
    case, _d, sommatie = await _b2c_case_on_sommatie(db, test_tenant.id)
    db.add(CaseStepHistory(
        tenant_id=test_tenant.id, case_id=case.id, step_id=sommatie.id,
        entered_at=datetime.now(UTC), trigger_type="manual",
    ))
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    resp = await client.post(
        f"/api/email/compose/cases/{case.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_email": "debiteur@example.nl",
            "subject": "Sommatie",
            "body": "Betaal nu.",
            "compliance_override": True,
        },
    )
    assert resp.status_code == 200, resp.text

    activity = (await db.execute(
        select(CaseActivity).where(
            CaseActivity.case_id == case.id,
            CaseActivity.activity_type == "compliance_override",
        )
    )).scalar_one()
    assert "toch versturen" in activity.title.lower()


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
