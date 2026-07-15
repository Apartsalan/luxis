"""Tests for UnifiedDraftService (S145).

Validates that all 3 intents (next_step / reply_to_email / free_compose):
- Persist an AIDraft with both body (plain) and body_html (wrapped)
- Use the branded render path (data-URL logo, case_type-dependent email)
- Strip HTML safely if AI accidentally returns it
- Fall back gracefully when build_base_context() throws
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytest_asyncio

from app.ai_agent.models import AIDraft, DraftStatus
from app.ai_agent.unified_draft_service import (
    DraftIntent,
    _betreft_line,
    _plain_to_html,
    generate_unified_draft,
)
from app.cases.models import Case
from app.email.synced_email_models import SyncedEmail
from app.relations.models import Contact

# ── Helpers (no DB) ───────────────────────────────────────────────────────


def test_plain_to_html_paragraphs():
    out = _plain_to_html("Eerste alinea.\n\nTweede alinea.")
    assert "<p" in out
    assert "Eerste alinea." in out
    assert "Tweede alinea." in out
    assert out.count("<p") == 2


def test_plain_to_html_single_newlines_become_br():
    out = _plain_to_html("Regel 1\nRegel 2")
    assert "<br>" in out
    assert "Regel 1" in out and "Regel 2" in out


def test_plain_to_html_strips_html_input():
    """If AI returns HTML by accident, strip it before wrapping."""
    out = _plain_to_html("<p>Met <strong>opmaak</strong>.</p>")
    assert "<strong>" not in out
    assert "opmaak" in out


def test_plain_to_html_empty():
    assert _plain_to_html("") == ""
    assert _plain_to_html(None) == ""  # type: ignore[arg-type]


def test_betreft_line_uses_subject():
    out = _betreft_line("2026-00001", "Aanmaning factuur 12345")
    assert "Aanmaning factuur 12345" in out
    assert "Betreft" in out


def test_betreft_line_falls_back_to_case_number():
    out = _betreft_line("2026-00001", "")
    assert "2026-00001" in out


# ── Integration: generate_unified_draft ─────────────────────────────────


@pytest_asyncio.fixture
async def incasso_case(db, test_tenant, test_company, test_user) -> Case:
    """Minimal incasso case with client + opposing party."""
    opposing = Contact(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        contact_type="company",
        name="Debiteur BV",
        email="debiteur@example.com",
        is_btw_plichtig=True,
    )
    db.add(opposing)
    await db.flush()

    # client must be BTW-plichtig so build_base_context doesn't try to add BTW row
    test_company.is_btw_plichtig = True
    await db.flush()

    case = Case(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        case_number="2026-00100",
        description="Test dossier S145",
        case_type="incasso",
        debtor_type="b2b",
        status="nieuw",
        is_active=True,
        client_id=test_company.id,
        opposing_party_id=opposing.id,
        assigned_to_id=test_user.id,
        date_opened=date.today() - timedelta(days=5),
        total_principal=Decimal("1000.00"),
        total_paid=Decimal("0.00"),
        interest_type="statutory",
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@pytest.fixture
def fake_base_context() -> dict:
    """Minimal context that _render_branded + _signature + _schuldhulp_disclaimer accept."""
    return {
        "kantoor": {
            "naam": "Kesting Legal",
            "adres": "IJsbaanpad 9",
            "postcode_stad": "1076 CV Amsterdam",
            "telefoon": "06-22184090",
            "email": "kesting@kestinglegal.nl",
            "kvk": "12345678",
            "iban": "NL20 RABO 0388 5065 20",
        },
        "wederpartij": {
            "naam": "Debiteur BV",
            "adres": "Teststraat 1",
            "postcode_stad": "1000 AA Amsterdam",
        },
        "zaak": {
            "zaaknummer": "2026-00100",
            "type": "incasso",
            "referentie_regel": "",
        },
        "vandaag": "15 mei 2026",
    }


def _patch_ai(monkeypatch, *, subject: str, body: str, tone: str = "formeel"):
    """Patch the AI call inside unified_draft_service."""

    async def fake_call(_system, _user):
        return ({"subject": subject, "body": body, "tone": tone}, "fake-model")

    monkeypatch.setattr(
        "app.ai_agent.unified_draft_service.call_intake_ai", fake_call
    )


def _patch_context(monkeypatch, ctx: dict):
    async def fake_build(_db, _tenant, _case):
        return ctx

    monkeypatch.setattr(
        "app.ai_agent.unified_draft_service.build_base_context", fake_build
    )


@pytest.mark.asyncio
async def test_next_step_intent_persists_draft_with_branded_html(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    _patch_ai(monkeypatch, subject="Aanmaning factuur 1", body="Eerste alinea.\n\nTweede alinea.")
    _patch_context(monkeypatch, fake_base_context)

    draft = await generate_unified_draft(
        db,
        test_tenant.id,
        test_user.id,
        case_id=incasso_case.id,
        intent=DraftIntent.NEXT_STEP,
    )

    assert isinstance(draft, AIDraft)
    assert draft.status == DraftStatus.GENERATED
    assert draft.subject == "Aanmaning factuur 1"
    # Plain body persisted
    assert draft.body == "Eerste alinea.\n\nTweede alinea."
    # Branded HTML wrap
    assert draft.body_html is not None
    assert "data:image/png;base64," in draft.body_html, "logo data-URL ontbreekt"
    assert "Eerste alinea." in draft.body_html
    assert "Tweede alinea." in draft.body_html
    # case_type=incasso → handtekening toont incasso@kestinglegal.nl
    # (note: kantoor-footer mag wél kantoor-email tonen; check signature line specifiek)
    assert "E: Incasso@kestinglegal.nl" in draft.body_html
    assert "E: kesting@kestinglegal.nl" not in draft.body_html
    # Schuldhulp disclaimer present (incasso case)
    assert "schuldenaar" in draft.body_html.lower()


@pytest.mark.asyncio
async def test_free_compose_for_advies_uses_kantoor_email(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    # Switch the case to a non-incasso type
    incasso_case.case_type = "advies"
    await db.flush()
    fake_base_context["zaak"]["type"] = "advies"

    _patch_ai(monkeypatch, subject="Advies", body="Korte inhoud.")
    _patch_context(monkeypatch, fake_base_context)

    draft = await generate_unified_draft(
        db,
        test_tenant.id,
        test_user.id,
        case_id=incasso_case.id,
        intent=DraftIntent.FREE_COMPOSE,
    )

    assert draft.body_html is not None
    # Handtekening switcht: non-incasso case → kesting@kestinglegal.nl in signature line
    assert "E: kesting@kestinglegal.nl" in draft.body_html
    assert "E: Incasso@kestinglegal.nl" not in draft.body_html
    # Non-incasso case → geen schuldhulp disclaimer
    assert "schuldenaar" not in draft.body_html.lower()


@pytest.mark.asyncio
async def test_reply_to_email_requires_source_email_id(
    db, test_tenant, test_user, incasso_case, monkeypatch
):
    _patch_ai(monkeypatch, subject="Re:", body="ok")
    with pytest.raises(ValueError, match="source_email_id"):
        await generate_unified_draft(
            db,
            test_tenant.id,
            test_user.id,
            case_id=incasso_case.id,
            intent=DraftIntent.REPLY_TO_EMAIL,
        )


@pytest.mark.asyncio
async def test_reply_to_email_uses_source_email(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    # Synced email needs an account; create a stub one via raw insert isn't
    # needed — instead we skip the FK by not assigning to an account.
    # Actually email_account_id is NOT NULL → create a minimal email account.
    from app.email.oauth_models import EmailAccount

    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="outlook",
        email_address="lisanne@kestinglegal.nl",
        access_token_enc=b"stub",
        refresh_token_enc=b"stub",
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(account)
    await db.flush()

    src = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email_account_id=account.id,
        case_id=incasso_case.id,
        provider_message_id="test@example.com",
        from_email="debiteur@example.com",
        from_name="Debiteur",
        subject="Ik betwist deze factuur",
        body_text="Ik vind dat ik niets verschuldigd ben.",
        body_html="",
        direction="inbound",
        email_date=datetime.now(UTC),
    )
    db.add(src)
    await db.commit()

    _patch_ai(monkeypatch, subject="Re: Ik betwist deze factuur", body="Reactie.", tone="zakelijk")
    _patch_context(monkeypatch, fake_base_context)

    draft = await generate_unified_draft(
        db,
        test_tenant.id,
        test_user.id,
        case_id=incasso_case.id,
        intent=DraftIntent.REPLY_TO_EMAIL,
        tone="zakelijk",
        source_email_id=src.id,
    )

    assert draft.subject.startswith("Re:")
    assert draft.body == "Reactie."
    assert draft.tone == "zakelijk"
    assert draft.body_html is not None
    assert "data:image/png;base64," in draft.body_html


@pytest.mark.asyncio
async def test_graceful_fallback_when_context_build_fails(
    db, test_tenant, test_user, incasso_case, monkeypatch
):
    """build_base_context raises → body_html=None, body still persisted."""

    async def boom(_db, _tenant, _case):
        raise RuntimeError("simulated context failure")

    monkeypatch.setattr(
        "app.ai_agent.unified_draft_service.build_base_context", boom
    )
    _patch_ai(monkeypatch, subject="X", body="Plain body content.")

    draft = await generate_unified_draft(
        db,
        test_tenant.id,
        test_user.id,
        case_id=incasso_case.id,
        intent=DraftIntent.FREE_COMPOSE,
    )

    assert draft.body == "Plain body content."
    assert draft.body_html is None  # graceful fallback


@pytest.mark.asyncio
async def test_unknown_case_raises_value_error(
    db, test_tenant, test_user, monkeypatch
):
    _patch_ai(monkeypatch, subject="x", body="y")
    with pytest.raises(ValueError, match="Dossier niet gevonden"):
        await generate_unified_draft(
            db,
            test_tenant.id,
            test_user.id,
            case_id=uuid.uuid4(),
            intent=DraftIntent.FREE_COMPOSE,
        )


@pytest.mark.asyncio
async def test_ai_returning_html_in_body_is_stripped(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    """If AI ignores the 'no HTML' rule, _plain_to_html should sanitize."""
    _patch_ai(
        monkeypatch,
        subject="Test",
        body="<p>Met <strong>opmaak</strong>.</p>",
    )
    _patch_context(monkeypatch, fake_base_context)

    draft = await generate_unified_draft(
        db,
        test_tenant.id,
        test_user.id,
        case_id=incasso_case.id,
        intent=DraftIntent.FREE_COMPOSE,
    )

    # body_html is the wrapped output. Within the BODY content area there
    # should be no <strong> from the AI input — strip_html removed it.
    assert draft.body_html is not None
    assert "<strong>opmaak</strong>" not in draft.body_html
    assert "opmaak" in draft.body_html


# ── S173: kennis-injectie (AV + bibliotheek) bij verweer ──────────────────


def _patch_ai_capture(monkeypatch, holder, *, subject="X", body="Y", tone="formeel"):
    """Als _patch_ai, maar bewaart de user-prompt zodat we kunnen bewijzen dat de
    kennis (AV/bibliotheek) er wél/niet in zit."""

    async def fake_call(_system, _user):
        holder["user"] = _user
        return ({"subject": subject, "body": body, "tone": tone}, "fake-model")

    monkeypatch.setattr(
        "app.ai_agent.unified_draft_service.call_intake_ai", fake_call
    )


@pytest.mark.asyncio
async def test_reply_verweer_injects_av_and_library(
    db, test_tenant, test_user, test_company, incasso_case, fake_base_context, monkeypatch
):
    """Bij een verweer-classificatie krijgt de compose-dialog nu de AV én de verweer-
    bibliotheek mee — voorheen zag dit pad niets (kernbevinding S172)."""
    from app.ai_agent.models import EmailClassification
    from app.email.oauth_models import EmailAccount
    from app.relations.models import ContactTerms

    db.add(
        ContactTerms(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            contact_id=test_company.id,
            file_path="/tmp/av.pdf",
            file_name="av.pdf",
            label="v1",
            valid_from=date(2026, 1, 1),
        )
    )
    account = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="outlook",
        email_address="lisanne@kestinglegal.nl",
        access_token_enc=b"stub",
        refresh_token_enc=b"stub",
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(account)
    await db.flush()
    src = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email_account_id=account.id,
        case_id=incasso_case.id,
        provider_message_id="verweer@example.com",
        from_email="debiteur@example.com",
        from_name="Debiteur",
        subject="Ik betwist de factuur",
        body_text="Er gold no cure no pay.",
        body_html="",
        direction="inbound",
        email_date=datetime.now(UTC),
    )
    db.add(src)
    await db.flush()
    db.add(
        EmailClassification(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            synced_email_id=src.id,
            case_id=incasso_case.id,
            category="juridisch_verweer",
            confidence=0.9,
            suggested_action="reply",
        )
    )
    await db.commit()

    holder: dict = {}
    _patch_ai_capture(monkeypatch, holder, subject="Re:", body="Reactie.")
    _patch_context(monkeypatch, fake_base_context)

    with patch(
        "app.ai_agent.knowledge_context._extract_pdf_text",
        return_value="Artikel 9.3 — commissie bij intrekking.",
    ):
        await generate_unified_draft(
            db,
            test_tenant.id,
            test_user.id,
            case_id=incasso_case.id,
            intent=DraftIntent.REPLY_TO_EMAIL,
            tone="zakelijk",
            source_email_id=src.id,
        )

    user_msg = holder["user"]
    assert "Artikel 9.3" in user_msg          # AV meegestuurd
    assert "Verweer-bibliotheek" in user_msg  # statische bibliotheek meegestuurd


@pytest.mark.asyncio
async def test_free_compose_without_verweer_omits_av(
    db, test_tenant, test_user, test_company, incasso_case, fake_base_context, monkeypatch
):
    """Zonder verweer-classificatie stuurt de compose-dialog géén AV/bibliotheek mee,
    ook al is er AV beschikbaar (S164-les: minder losse tekst = minder afdwalen)."""
    from app.relations.models import ContactTerms

    db.add(
        ContactTerms(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            contact_id=test_company.id,
            file_path="/tmp/av.pdf",
            file_name="av.pdf",
            label="v1",
            valid_from=date(2026, 1, 1),
        )
    )
    await db.commit()

    holder: dict = {}
    _patch_ai_capture(monkeypatch, holder, subject="X", body="Y")
    _patch_context(monkeypatch, fake_base_context)

    with patch(
        "app.ai_agent.knowledge_context._extract_pdf_text",
        return_value="Artikel 9.3 — commissie bij intrekking.",
    ):
        await generate_unified_draft(
            db,
            test_tenant.id,
            test_user.id,
            case_id=incasso_case.id,
            intent=DraftIntent.FREE_COMPOSE,
        )

    user_msg = holder["user"]
    assert "Artikel 9.3" not in user_msg
    assert "Verweer-bibliotheek" not in user_msg


@pytest.mark.asyncio
async def test_free_compose_fallback_uses_last_case_classification(
    db, test_tenant, test_user, test_company, incasso_case, fake_base_context, monkeypatch
):
    """Fable-review S173: free_compose heeft geen bron-email, maar valt terug op de laatste
    INKOMENDE dossier-classificatie. Staat die op verweer, dan injecteert de compose-dialog
    tóch AV + bibliotheek. Dekt het anders ongeteste fallback-pad (`_last_case_classification_
    category`) — als dat pad stuk is bleef de S172-kernbevinding stil bestaan."""
    from app.ai_agent.models import EmailClassification
    from app.email.oauth_models import EmailAccount
    from app.relations.models import ContactTerms

    db.add(
        ContactTerms(
            id=uuid.uuid4(), tenant_id=test_tenant.id, contact_id=test_company.id,
            file_path="/tmp/av.pdf", file_name="av.pdf", label="v1", valid_from=date(2026, 1, 1),
        )
    )
    account = EmailAccount(
        id=uuid.uuid4(), tenant_id=test_tenant.id, user_id=test_user.id, provider="outlook",
        email_address="lisanne@kestinglegal.nl", access_token_enc=b"stub",
        refresh_token_enc=b"stub", token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(account)
    await db.flush()
    inbound = SyncedEmail(
        id=uuid.uuid4(), tenant_id=test_tenant.id, email_account_id=account.id,
        case_id=incasso_case.id, provider_message_id="in@example.com",
        from_email="debiteur@example.com", from_name="Debiteur", subject="Ik betwist",
        body_text="Betwisting.", body_html="", direction="inbound", email_date=datetime.now(UTC),
    )
    db.add(inbound)
    await db.flush()
    db.add(
        EmailClassification(
            id=uuid.uuid4(), tenant_id=test_tenant.id, synced_email_id=inbound.id,
            case_id=incasso_case.id, category="juridisch_verweer", confidence=0.9,
            suggested_action="reply",
        )
    )
    await db.commit()

    holder: dict = {}
    _patch_ai_capture(monkeypatch, holder, subject="X", body="Y")
    _patch_context(monkeypatch, fake_base_context)

    with patch(
        "app.ai_agent.knowledge_context._extract_pdf_text",
        return_value="Artikel 9.3 — commissie bij intrekking.",
    ):
        await generate_unified_draft(
            db, test_tenant.id, test_user.id, case_id=incasso_case.id,
            intent=DraftIntent.FREE_COMPOSE,
        )

    user_msg = holder["user"]
    assert "Artikel 9.3" in user_msg           # AV via fallback-classificatie
    assert "Verweer-bibliotheek" in user_msg


# ── S221 3.2: ontdubbelen ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_next_step_dedup_returns_existing_draft(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    """Tweede 'volgende stap'-generatie voor dezelfde zaak+stap geeft het
    bestaande concept terug i.p.v. een tweede te maken (dubbelklik-bescherming)."""
    _patch_ai(monkeypatch, subject="Eerste sommatie", body="Alinea.")
    _patch_context(monkeypatch, fake_base_context)

    first = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.NEXT_STEP,
    )
    second = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.NEXT_STEP,
    )
    assert second.id == first.id
    assert first.intent == "next_step"

    # Slechts één rij in de DB voor deze zaak.
    from sqlalchemy import func, select
    count = await db.scalar(
        select(func.count()).select_from(AIDraft).where(AIDraft.case_id == incasso_case.id)
    )
    assert count == 1


@pytest.mark.asyncio
async def test_free_compose_never_dedups(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    """Vrij opstellen maakt bewust elke keer een nieuw concept."""
    _patch_ai(monkeypatch, subject="Vrij", body="Tekst.")
    _patch_context(monkeypatch, fake_base_context)

    a = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.FREE_COMPOSE,
    )
    b = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.FREE_COMPOSE,
    )
    assert a.id != b.id


@pytest.mark.asyncio
async def test_dedup_ignores_discarded_draft(
    db, test_tenant, test_user, incasso_case, fake_base_context, monkeypatch
):
    """Een weggegooid concept blokkeert een nieuwe generatie niet."""
    _patch_ai(monkeypatch, subject="Eerste sommatie", body="Alinea.")
    _patch_context(monkeypatch, fake_base_context)

    first = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.NEXT_STEP,
    )
    first.status = DraftStatus.DISCARDED
    await db.flush()

    second = await generate_unified_draft(
        db, test_tenant.id, test_user.id,
        case_id=incasso_case.id, intent=DraftIntent.NEXT_STEP,
    )
    assert second.id != first.id
