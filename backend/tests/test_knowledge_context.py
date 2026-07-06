"""Tests voor de gedeelde AV-resolver (S173) — `resolve_case_terms`.

Kernbevinding uit de S172-audit: er waren drie AI-conceptpaden met drie verschillende
"geheugens" — alleen het incasso-pad zag de geversioneerde Algemene Voorwaarden (AV).
Deze tests bewijzen dat de gedeelde resolver de juiste AV oplevert, plus één regressie-
vangnet dat het al-correcte incasso-verweerpad ongewijzigd blijft.
"""

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agent.knowledge_context import resolve_case_terms
from app.auth.models import Tenant
from app.cases.models import Case
from app.collections.models import Claim
from app.relations.models import Contact, ContactTerms


@pytest_asyncio.fixture
async def client_contact(db: AsyncSession, test_tenant: Tenant) -> Contact:
    c = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Cliënt BV",
        email="client@example.nl",
    )
    db.add(c)
    await db.flush()
    return c


async def _make_case(
    db: AsyncSession,
    tenant: Tenant,
    client: Contact,
    *,
    contact_terms_id: uuid.UUID | None = None,
) -> Case:
    debtor = Contact(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        contact_type="company",
        name="Debiteur BV",
        email="debtor@example.nl",
    )
    db.add(debtor)
    await db.flush()
    case = Case(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        case_number=f"{date.today().year}-98001",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        interest_type="statutory",
        contractual_compound=True,
        client_id=client.id,
        opposing_party_id=debtor.id,
        contact_terms_id=contact_terms_id,
        date_opened=date.today(),
    )
    db.add(case)
    await db.flush()
    return case


@pytest.mark.asyncio
async def test_resolve_uses_versioned_contact_terms(
    db: AsyncSession, test_tenant: Tenant, client_contact: Contact
):
    """Smart-default: de AV-versie die geldig is op de factuurdatum wordt gekozen."""
    terms = ContactTerms(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_id=client_contact.id,
        file_path="/tmp/av_2026.pdf",
        file_name="av_2026.pdf",
        label="Versie 2026",
        valid_from=date(2026, 1, 1),
    )
    db.add(terms)
    await db.flush()
    case = await _make_case(db, test_tenant, client_contact)
    db.add(
        Claim(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            description="Factuur F1",
            principal_amount=Decimal("100.00"),
            invoice_number="F1",
            invoice_date=date(2026, 3, 1),
            default_date=date(2026, 3, 15),
        )
    )
    await db.flush()

    fake_av = "Artikel 9.3 — bij intrekking is 15% commissie verschuldigd."
    with patch(
        "app.ai_agent.knowledge_context._extract_pdf_text", return_value=fake_av
    ):
        av_text, pdf_path = await resolve_case_terms(db, test_tenant.id, case)

    assert pdf_path == "/tmp/av_2026.pdf"
    assert av_text is not None
    assert "Artikel 9.3" in av_text


@pytest.mark.asyncio
async def test_resolve_falls_back_to_legacy_terms_file_path(
    db: AsyncSession, test_tenant: Tenant, client_contact: Contact
):
    """Zonder ContactTerms-versie valt de resolver terug op de legacy single-file kolom."""
    client_contact.terms_file_path = "/tmp/legacy_av.pdf"
    await db.flush()
    case = await _make_case(db, test_tenant, client_contact)

    with patch(
        "app.ai_agent.knowledge_context._extract_pdf_text",
        return_value="Legacy AV tekst.",
    ):
        av_text, pdf_path = await resolve_case_terms(db, test_tenant.id, case)

    assert pdf_path == "/tmp/legacy_av.pdf"
    assert av_text == "Legacy AV tekst."


@pytest.mark.asyncio
async def test_resolve_returns_none_without_terms(
    db: AsyncSession, test_tenant: Tenant, client_contact: Contact
):
    """Cliënt zonder enige AV → (None, None), geen PDF-poging."""
    case = await _make_case(db, test_tenant, client_contact)
    av_text, pdf_path = await resolve_case_terms(db, test_tenant.id, case)
    assert av_text is None
    assert pdf_path is None


@pytest.mark.asyncio
async def test_resolve_returns_none_without_client(
    db: AsyncSession, test_tenant: Tenant
):
    """Dossier zonder cliënt → (None, None) zonder DB-werk."""
    case = SimpleNamespace(client_id=None, contact_terms_id=None, id=uuid.uuid4())
    av_text, pdf_path = await resolve_case_terms(db, test_tenant.id, case)
    assert av_text is None
    assert pdf_path is None


@pytest.mark.asyncio
async def test_resolve_explicit_contact_terms_id_wins_over_newer_version(
    db: AsyncSession, test_tenant: Tenant, client_contact: Contact
):
    """Expliciete `case.contact_terms_id` heeft voorrang, óók als er een nieuwere versie is."""
    old = ContactTerms(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_id=client_contact.id,
        file_path="/tmp/av_old.pdf", file_name="av_old.pdf", label="2024",
        valid_from=date(2024, 1, 1), valid_to=date(2025, 12, 31),
    )
    new = ContactTerms(
        id=uuid.uuid4(), tenant_id=test_tenant.id, contact_id=client_contact.id,
        file_path="/tmp/av_new.pdf", file_name="av_new.pdf", label="2026",
        valid_from=date(2026, 1, 1),
    )
    db.add_all([old, new])
    await db.flush()
    case = await _make_case(db, test_tenant, client_contact, contact_terms_id=old.id)

    with patch("app.ai_agent.knowledge_context._extract_pdf_text", return_value="oud"):
        _, pdf_path = await resolve_case_terms(db, test_tenant.id, case)
    assert pdf_path == "/tmp/av_old.pdf"  # expliciete keuze wint van nieuwere versie


@pytest.mark.asyncio
async def test_resolve_versioned_wins_over_legacy(
    db: AsyncSession, test_tenant: Tenant, client_contact: Contact
):
    """Een ContactTerms-versie wint van de legacy `terms_file_path`-kolom als beide bestaan."""
    client_contact.terms_file_path = "/tmp/legacy.pdf"
    db.add(
        ContactTerms(
            id=uuid.uuid4(), tenant_id=test_tenant.id, contact_id=client_contact.id,
            file_path="/tmp/versioned.pdf", file_name="versioned.pdf", label="v1",
            valid_from=date(2026, 1, 1),
        )
    )
    await db.flush()
    case = await _make_case(db, test_tenant, client_contact)  # geen expliciete terms_id

    with patch("app.ai_agent.knowledge_context._extract_pdf_text", return_value="v"):
        _, pdf_path = await resolve_case_terms(db, test_tenant.id, case)
    assert pdf_path == "/tmp/versioned.pdf"  # niet de legacy-kolom


def test_incasso_prompt_keeps_full_defense_library():
    """Regressie-vangnet (S173): het incasso-verweerpad injecteert bij inkomend verweer
    nog steeds ALLE 5 bibliotheek-voorbeelden — incl. het Engelse — en de volledige AV.
    De gedeelde AV-resolver mag dit pad niet stil hebben versmald (Fable-review S173)."""
    from app.ai_agent.incasso_email_prompts import build_user_prompt

    user = build_user_prompt(
        step_name="Verweer beantwoorden",
        template_subject="Betreft: dossier",
        template_body="Geachte heer/mevrouw,",
        case_data={"case_number": "2026-00001", "debtor_type": "b2b"},
        debtor_data={"name": "Debiteur BV", "contact_type": "company"},
        client_data={"name": "Cliënt BV"},
        invoices=[],
        amounts={},
        av_text="Artikel 9.3 — commissie bij intrekking van de opdracht.",
        incoming_defense="Ik betwist de factuur; er gold no cure no pay.",
    )

    # Volledige AV aanwezig
    assert "Artikel 9.3" in user
    # Alle 5 voorbeelden incl. het Engelse
    assert "Verweer-bibliotheek" in user
    assert "English: automatic renewal" in user
