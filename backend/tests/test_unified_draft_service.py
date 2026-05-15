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
    assert "E: incasso@kestinglegal.nl" in draft.body_html
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
    assert "E: incasso@kestinglegal.nl" not in draft.body_html
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
