"""S212 — renteoverzicht-PDF als bijlage op de twee resterende verzendpaden.

De bijlage zat al op het batch- en follow-up-pad (S211). Dezelfde 14-dagenbrief/
eerste sommatie gaat óók via:
- het compose/AI-concept-pad (`compose/cases/{id}` → .eml voor Outlook; Lisanne's
  meest gebruikte route);
- het document-verzendpad (`documents/{id}/send`).

Getest volgens hetzelfde patroon als `test_followup.py`: bijlage WÉL bij een privé
aansprakelijke wederpartij (rechtsvorm leeg/eenmanszaak → besluit B), NIET bij een
BV/NV/stichting. Rendering wordt gemockt (mailslot dicht) — we toetsen de beslissing
en de bedrading, niet de PDF-inhoud.
"""

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case
from app.documents.models import GeneratedDocument
from app.incasso.models import IncassoPipelineStep
from app.relations.models import Contact


async def _case_with_opposing(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    legal_form: str | None,
    debtor_type: str = "b2b",
) -> Case:
    """Zakelijke zaak (b2b, geen 14-dagenbrief-gate) op de eerste-sommatie-stap met
    een wederpartij met de opgegeven rechtsvorm."""
    client = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="person", name="Cliënt",
    )
    opp = Contact(
        id=uuid.uuid4(), tenant_id=tenant_id, contact_type="company",
        name="Wederpartij", email="debiteur@example.nl", legal_form=legal_form,
    )
    db.add_all([client, opp])
    await db.flush()
    sommatie = IncassoPipelineStep(
        id=uuid.uuid4(), tenant_id=tenant_id, name="Eerste sommatie",
        sort_order=1, min_wait_days=0, max_wait_days=4, debtor_type="both",
        step_category="minnelijk", template_type="sommatie_drukte",
    )
    db.add(sommatie)
    await db.flush()
    case = Case(
        id=uuid.uuid4(), tenant_id=tenant_id, case_number="2026-96500",
        case_type="incasso", status="nieuw", debtor_type=debtor_type,
        client_id=client.id, opposing_party_id=opp.id,
        date_opened=date.today(), incasso_step_id=sommatie.id,
    )
    db.add(case)
    await db.flush()
    return case


# ── Document-verzendpad (documents/{id}/send) ──────────────────────────────────


@pytest.mark.asyncio
async def test_document_send_attaches_rente_bijlage_private(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Privé aansprakelijke wederpartij (rechtsvorm leeg → besluit B): het
    document-verzendpad stuurt de brief-PDF ÉN het renteoverzicht mee."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    doc = GeneratedDocument(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        generated_by_id=test_user.id, title="Eerste sommatie",
        document_type="sommatie_drukte", template_type="sommatie_drukte",
    )
    db.add(doc)
    await db.commit()

    email_log = SimpleNamespace(
        id=uuid.uuid4(), recipient="debiteur@example.nl", subject="Eerste sommatie",
        status="sent", error_message=None, template=None,
    )
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.documents.router.render_docx", new_callable=AsyncMock) as mock_main,
        patch("app.documents.router.docx_to_pdf", new_callable=AsyncMock) as mock_main_pdf,
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
        patch("app.email.send_service.send_with_attachment", new_callable=AsyncMock) as mock_send,
    ):
        mock_main.return_value = (b"docx", "sommatie.docx", "sommatie_drukte", None)
        mock_main_pdf.return_value = b"%PDF-main"
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente"
        mock_send.return_value = email_log
        resp = await client.post(
            f"/api/documents/{doc.id}/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_email": "debiteur@example.nl"},
        )

    assert resp.status_code == 200, resp.text
    mock_send.assert_called_once()
    attachments = mock_send.call_args.kwargs["attachments"]
    assert len(attachments) == 2
    filenames = [a[0] for a in attachments]
    assert any(f.startswith("renteoverzicht_") for f in filenames)


@pytest.mark.asyncio
async def test_document_send_no_rente_bijlage_for_bv(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Keerzijde: een BV (beperkte aansprakelijkheid) krijgt op het
    document-verzendpad GÉÉN renteoverzicht — alleen de brief-PDF."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form="Besloten Vennootschap")
    doc = GeneratedDocument(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        generated_by_id=test_user.id, title="Eerste sommatie",
        document_type="sommatie_drukte", template_type="sommatie_drukte",
    )
    db.add(doc)
    await db.commit()

    email_log = SimpleNamespace(
        id=uuid.uuid4(), recipient="debiteur@example.nl", subject="Eerste sommatie",
        status="sent", error_message=None, template=None,
    )
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.documents.router.render_docx", new_callable=AsyncMock) as mock_main,
        patch("app.documents.router.docx_to_pdf", new_callable=AsyncMock) as mock_main_pdf,
        patch("app.email.send_service.send_with_attachment", new_callable=AsyncMock) as mock_send,
    ):
        mock_main.return_value = (b"docx", "sommatie.docx", "sommatie_drukte", None)
        mock_main_pdf.return_value = b"%PDF-main"
        mock_send.return_value = email_log
        resp = await client.post(
            f"/api/documents/{doc.id}/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"recipient_email": "debiteur@example.nl"},
        )

    assert resp.status_code == 200, resp.text
    mock_send.assert_called_once()
    attachments = mock_send.call_args.kwargs["attachments"]
    assert len(attachments) == 1


# ── Compose/AI-concept-pad (compose/cases/{id} → .eml) ─────────────────────────


@pytest.mark.asyncio
async def test_compose_eml_attaches_rente_bijlage_private(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De .eml voor Outlook draagt het renteoverzicht als bijlage bij een privé
    aansprakelijke wederpartij op een eerste-sommatie-stap."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
    ):
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente-overzicht"
        resp = await client.post(
            f"/api/email/compose/cases/{case.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_email": "debiteur@example.nl",
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "template_type": "sommatie_drukte",
            },
        )

    assert resp.status_code == 200, resp.text
    assert b"renteoverzicht_2026-96500.pdf" in resp.content


@pytest.mark.asyncio
async def test_compose_eml_no_rente_bijlage_for_bv(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Keerzijde: de .eml voor een BV bevat geen renteoverzicht."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form="Besloten Vennootschap")
    await db.commit()

    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
    ):
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente-overzicht"
        resp = await client.post(
            f"/api/email/compose/cases/{case.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_email": "debiteur@example.nl",
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "template_type": "sommatie_drukte",
            },
        )

    assert resp.status_code == 200, resp.text
    assert b"renteoverzicht" not in resp.content
    mock_rente.assert_not_called()
