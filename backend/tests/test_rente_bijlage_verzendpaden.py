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
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Tenant, User
from app.auth.service import create_access_token
from app.cases.models import Case, CaseFile
from app.collections.models import Claim
from app.documents.models import GeneratedDocument
from app.email.oauth_models import EmailAccount
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


@pytest.mark.asyncio
async def test_document_send_attaches_rente_for_plain_sommatie(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S220 punt 3: een handmatig via Documenten opgestelde eerste sommatie heeft
    brieftype 'sommatie' (niet 'sommatie_drukte'). Ook dan gaat het renteoverzicht
    mee op de documentenroute — voorheen viel het daar weg."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    doc = GeneratedDocument(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        generated_by_id=test_user.id, title="Sommatie",
        document_type="sommatie", template_type="sommatie",
    )
    db.add(doc)
    await db.commit()

    email_log = SimpleNamespace(
        id=uuid.uuid4(), recipient="debiteur@example.nl", subject="Sommatie",
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
        mock_main.return_value = (b"docx", "sommatie.docx", "sommatie", None)
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
    attachments = mock_send.call_args.kwargs["attachments"]
    filenames = [a[0] for a in attachments]
    assert any(f.startswith("renteoverzicht_") for f in filenames)


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


# ── Primaire verzendknop (compose/send, S212-review) ───────────────────────────


def _provider_mock(sent: dict):
    """Mock-provider die de send-kwargs vangt (voor een geslaagde /compose/send)."""
    async def fake_send_message(_token, **kwargs):
        sent.update(kwargs)
        return "msg-1"

    return SimpleNamespace(send_message=fake_send_message)


async def _make_email_account(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> EmailAccount:
    """Een écht verbonden account in de test-DB — nodig sinds /compose/send de
    verstuurde mail vastlegt (SyncedEmail.email_account_id is een harde koppeling)."""
    acc = EmailAccount(
        id=uuid.uuid4(), tenant_id=tenant_id, user_id=user_id,
        provider="outlook", email_address="incasso@example.nl",
        access_token_enc=b"x", refresh_token_enc=b"x",
    )
    db.add(acc)
    await db.flush()
    return acc


@pytest.mark.asyncio
async def test_compose_send_attaches_rente_bijlage_private(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """S212-review: de PRIMAIRE knop ('Versturen' → /compose/send) draagt het
    renteoverzicht bij een eerste-sommatie-sjabloon voor een privé aansprakelijke
    wederpartij — voorheen ging dit pad zonder sjabloontype en dus zonder bijlage."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    account = await _make_email_account(db, test_tenant.id, test_user.id)
    await db.commit()

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.get_email_account", new_callable=AsyncMock, return_value=account),
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
    ):
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente"
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "case_id": str(case.id),
                "template_type": "sommatie_drukte",
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    attachments = sent["attachments"]
    assert attachments is not None and len(attachments) == 1
    assert attachments[0].filename.startswith("renteoverzicht_")
    assert attachments[0].content_type == "application/pdf"


@pytest.mark.asyncio
async def test_compose_send_no_rente_bijlage_for_bv(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Keerzijde op de primaire knop: BV → geen bijlage (attachments blijft None)."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form="Besloten Vennootschap")
    account = await _make_email_account(db, test_tenant.id, test_user.id)
    await db.commit()

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.get_email_account", new_callable=AsyncMock, return_value=account),
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
    ):
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "case_id": str(case.id),
                "template_type": "sommatie_drukte",
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    assert sent["attachments"] is None
    mock_rente.assert_not_called()


@pytest.mark.asyncio
async def test_compose_send_auto_attaches_invoice_pdfs(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User, tmp_path
):
    """DF122-07 op de primaire knop: bij een sommatie-sjabloon gaan de factuur-PDF's
    van de actieve vorderingen automatisch mee — plus het renteoverzicht (eenmanszaak).
    Voorheen deed alleen het .eml-pad dit."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    # Factuur-PDF als dossierbestand op schijf + vordering die ernaar wijst.
    cf = CaseFile(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        original_filename="factuur-2026-001.pdf", stored_filename="f1.pdf",
        file_size=9, content_type="application/pdf", uploaded_by=test_user.id,
    )
    db.add(cf)
    db.add(Claim(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        description="Factuur 2026-001", principal_amount=Decimal("5000.00"),
        default_date=date(2026, 1, 1), invoice_file_id=cf.id,
    ))
    account = await _make_email_account(db, test_tenant.id, test_user.id)
    await db.commit()
    file_dir = tmp_path / str(test_tenant.id) / str(case.id)
    file_dir.mkdir(parents=True)
    (file_dir / "f1.pdf").write_bytes(b"%PDF-fact")

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.UPLOADS_BASE", tmp_path),
        patch("app.email.compose_router.get_email_account", new_callable=AsyncMock, return_value=account),
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
    ):
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente"
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "case_id": str(case.id),
                "template_type": "sommatie_drukte",
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    attachments = sent["attachments"]
    filenames = sorted(a.filename for a in attachments)
    assert filenames == ["factuur-2026-001.pdf", "renteoverzicht_2026-96500.pdf"]


# ── S220 hoofdvondst N1: afzender-vangrail + logging + BCC op /compose/send ─────


@pytest.mark.asyncio
async def test_compose_send_logs_prefers_tenant_account_and_passes_bcc(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """De primaire verstuurknop legt de mail nu vast (EmailLog + SyncedEmail +
    dossier-activiteit), verstuurt via het KANTOOR-account (incasso@) ook al klikt
    iemand met een eigen mailbox, en geeft BCC door aan de provider."""
    from sqlalchemy import select

    from app.cases.models import CaseActivity
    from app.email.models import EmailLog
    from app.email.synced_email_models import SyncedEmail

    # Kantoor-mailadres instellen + twee verbonden accounts: kantoor (incasso@) en
    # persoonlijk (seidony@). De vangrail moet het kantoor-account kiezen.
    test_tenant.email = "incasso@kestinglegal.nl"
    office = EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id,
        provider="outlook", email_address="incasso@kestinglegal.nl",
        access_token_enc=b"x", refresh_token_enc=b"x",
    )
    personal = EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id,
        provider="outlook", email_address="seidony@kestinglegal.nl",
        access_token_enc=b"x", refresh_token_enc=b"x",
    )
    db.add_all([office, personal])
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    await db.commit()

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
    ):
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "bcc": ["kopie@kantoor.nl"],
                "subject": "Eerste sommatie",
                "body_html": "<p>Betaal nu.</p>",
                "case_id": str(case.id),
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    # BCC doorgegeven aan de provider
    assert sent["bcc"] == ["kopie@kantoor.nl"]

    # Afzender-vangrail: verstuurd via het kantoor-account (niet het persoonlijke)
    synced = (
        await db.execute(select(SyncedEmail).where(SyncedEmail.case_id == case.id))
    ).scalars().all()
    assert len(synced) == 1
    assert synced[0].from_email == "incasso@kestinglegal.nl"
    assert synced[0].direction == "outbound"

    # Logging: EmailLog + dossier-activiteit
    logs = (
        await db.execute(select(EmailLog).where(EmailLog.case_id == case.id))
    ).scalars().all()
    assert len(logs) == 1 and logs[0].status == "sent"
    acts = (
        await db.execute(
            select(CaseActivity).where(
                CaseActivity.case_id == case.id, CaseActivity.activity_type == "email"
            )
        )
    ).scalars().all()
    assert any("verzonden" in a.title.lower() for a in acts)


# ── S220 punt 1/25: brieftype afleiden uit de stap op de AI-concept-route ───────


@pytest.mark.asyncio
async def test_compose_send_derives_template_from_step_no_invoice_attach(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User, tmp_path
):
    """Een verse dossier-mail aan de debiteur ZONDER sjabloontype (AI-concept-route)
    leidt het brieftype af uit de huidige stap → het renteoverzicht gaat alsnog mee.
    Op deze afgeleide route gaan factuur-PDF's bewust NIET automatisch mee."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    account = await _make_email_account(db, test_tenant.id, test_user.id)
    cf = CaseFile(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        original_filename="factuur-2026-001.pdf", stored_filename="f1.pdf",
        file_size=9, content_type="application/pdf", uploaded_by=test_user.id,
    )
    db.add(cf)
    db.add(Claim(
        id=uuid.uuid4(), tenant_id=test_tenant.id, case_id=case.id,
        description="Factuur 2026-001", principal_amount=Decimal("5000.00"),
        default_date=date(2026, 1, 1), invoice_file_id=cf.id,
    ))
    await db.commit()
    file_dir = tmp_path / str(test_tenant.id) / str(case.id)
    file_dir.mkdir(parents=True)
    (file_dir / "f1.pdf").write_bytes(b"%PDF-fact")

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.UPLOADS_BASE", tmp_path),
        patch("app.email.compose_router.get_email_account", new_callable=AsyncMock, return_value=account),
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
        patch("app.documents.rente_bijlage.docx_to_pdf", new_callable=AsyncMock) as mock_rente_pdf,
    ):
        mock_rente.return_value = (b"docx", "renteoverzicht_2026-96500.docx", "renteoverzicht", None)
        mock_rente_pdf.return_value = b"%PDF-rente"
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["debiteur@example.nl"],
                "subject": "Betaalherinnering",
                "body_html": "<p>Betaal nu.</p>",
                "case_id": str(case.id),
                "already_branded": True,
                # GEEN template_type — moet worden afgeleid uit de sommatie-stap
            },
        )

    assert resp.status_code == 200, resp.text
    attachments = sent["attachments"]
    filenames = sorted(a.filename for a in (attachments or []))
    assert filenames == ["renteoverzicht_2026-96500.pdf"]


@pytest.mark.asyncio
async def test_compose_send_no_derivation_when_recipient_not_debtor(
    client, db: AsyncSession, test_tenant: Tenant, test_user: User
):
    """Geen afleiding als de mail niet aan de debiteur gaat (bijv. aan de cliënt):
    zonder sjabloontype geen renteoverzicht."""
    case = await _case_with_opposing(db, test_tenant.id, legal_form=None)
    account = await _make_email_account(db, test_tenant.id, test_user.id)
    await db.commit()

    sent: dict = {}
    provider = _provider_mock(sent)
    token = create_access_token(str(test_user.id), str(test_tenant.id))
    with (
        patch("app.email.compose_router.get_email_account", new_callable=AsyncMock, return_value=account),
        patch("app.email.compose_router.get_provider", return_value=provider),
        patch("app.email.compose_router.get_valid_access_token", new_callable=AsyncMock, return_value="tok"),
        patch("app.email.compose_router.imap_smtp_kwargs", return_value={}),
        patch("app.documents.rente_bijlage.render_docx", new_callable=AsyncMock) as mock_rente,
    ):
        resp = await client.post(
            "/api/email/compose/send",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "to": ["client@elders.nl"],
                "subject": "Statusupdate",
                "body_html": "<p>Ter info.</p>",
                "case_id": str(case.id),
                "already_branded": True,
            },
        )

    assert resp.status_code == 200, resp.text
    assert sent["attachments"] is None
    mock_rente.assert_not_called()
