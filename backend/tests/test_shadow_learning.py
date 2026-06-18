"""Shadow-learning (S168/S169) — leren van de eigen verzonden verweer-antwoorden.

Dekt: body opschonen (kop/aanhef/handtekening/quote), ophalen + formatteren
(+ use_count), backfill (bron = verzonden AI-verweerconcepten, categorie via de
classificatie, met dedup), en de edit-rate voor het kwaliteits-dashboard.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.ai_agent.learned_answers import (
    backfill_learned_answers,
    build_learned_examples_text,
    clean_answer_body,
    get_learning_stats,
)
from app.ai_agent.models import AIDraft, EmailClassification, LearnedAnswer
from app.email.oauth_models import EmailAccount
from app.email.synced_email_models import SyncedEmail
from tests.helpers.incasso_fixtures import create_incasso_case

# ── Helpers ──────────────────────────────────────────────────────────────


async def _account(db, tenant_id, user_id) -> EmailAccount:
    acc = EmailAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        provider="gmail",
        email_address="kantoor@test.nl",
        access_token_enc=b"x",
        refresh_token_enc=b"y",
    )
    db.add(acc)
    await db.flush()
    return acc


async def _email(
    db, tenant_id, account_id, *, case_id, direction, body, when, subject="Re: vordering"
) -> SyncedEmail:
    e = SyncedEmail(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_account_id=account_id,
        case_id=case_id,
        provider_message_id=f"m_{uuid.uuid4().hex[:10]}",
        subject=subject,
        from_email="x@test.nl",
        from_name="X",
        to_emails=json.dumps(["y@test.nl"]),
        cc_emails=json.dumps([]),
        snippet=body[:80],
        body_text=body,
        body_html=f"<p>{body}</p>",
        direction=direction,
        email_date=when,
    )
    db.add(e)
    await db.flush()
    return e


async def _classify(db, tenant_id, synced_email_id, case_id, category) -> EmailClassification:
    c = EmailClassification(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        synced_email_id=synced_email_id,
        case_id=case_id,
        category=category,
        confidence=0.9,
        reasoning="",
        suggested_action="escalate",
    )
    db.add(c)
    await db.flush()
    return c


# ── clean_answer_body ────────────────────────────────────────────────────


def test_clean_answer_body_strips_quote_and_signature():
    raw = (
        "U stelt dat sprake is van no cure no pay. Dat is onjuist: de "
        "opdrachtbevestiging vermeldt expliciet het tegendeel.\n\n"
        "Met vriendelijke groet,\nLisanne Kesting\n\n"
        "Op 1 januari 2026 schreef debiteur@x.nl:\n> ik betwist de factuur"
    )
    out = clean_answer_body(raw)
    assert "no cure no pay" in out
    assert "Met vriendelijke groet" not in out
    assert "schreef" not in out
    assert "ik betwist" not in out


def test_clean_answer_body_removes_leading_greeting():
    out = clean_answer_body(
        "Geachte heer Jansen,\n\nDe verplichting tot betaling staat vast."
    )
    assert out.startswith("De verplichting")


# ── retrieval + formatteren + use_count ──────────────────────────────────


@pytest.mark.asyncio
async def test_build_learned_examples_text_formats_and_bumps_use_count(db, test_tenant):
    for i in range(2):
        db.add(
            LearnedAnswer(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                category="betwisting",
                body=f"Argumentatie voorbeeld {i} met voldoende lengte voor een echte test.",
            )
        )
    await db.flush()

    text = await build_learned_examples_text(db, test_tenant.id, "betwisting")
    assert "eigen eerdere antwoorden" in text.lower()
    assert "Voorbeeld 1" in text
    assert "GEEN" in text  # PII-instructie aanwezig

    rows = (
        await db.execute(
            select(LearnedAnswer).where(LearnedAnswer.tenant_id == test_tenant.id)
        )
    ).scalars().all()
    assert all(r.use_count == 1 for r in rows)


@pytest.mark.asyncio
async def test_no_examples_returns_empty(db, test_tenant):
    assert await build_learned_examples_text(db, test_tenant.id, "juridisch_verweer") == ""
    assert await build_learned_examples_text(db, test_tenant.id, None) == ""


# ── backfill ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_backfill_learns_from_outbound_correction_and_dedups(
    db, test_tenant, test_user, test_company, test_person
):
    """Leert van de tekst die Lisanne ECHT verstuurt (haar correctie), niet het AI-voorstel."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Ik betwist de factuur, no cure no pay.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "betwisting")
    # Haar werkelijk verzonden antwoord — geen sommatie-onderwerp.
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht",
        body=(
            "Geachte heer,\n\nUw verweer faalt: de opdrachtbevestiging vermeldt het "
            "tegendeel. De verplichting tot betaling staat vast.\n\n"
            "Met vriendelijke groet,\nLisanne"
        ),
        when=t0 + timedelta(hours=1),
    )

    added = await backfill_learned_answers(db, test_tenant.id)
    assert added == 1
    rows = (
        await db.execute(
            select(LearnedAnswer).where(LearnedAnswer.tenant_id == test_tenant.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].category == "betwisting"
    assert "opdrachtbevestiging" in rows[0].body
    assert "Met vriendelijke groet" not in rows[0].body  # handtekening gestript
    assert "Geachte" not in rows[0].body  # aanhef gestript

    # Idempotent: tweede run voegt niets toe.
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_excludes_template_letters(
    db, test_tenant, test_user, test_company, test_person
):
    """Een sjabloon-sommatie is geen vrije verweer-reactie en moet worden uitgesloten."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Ik betwist de factuur.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "betwisting")
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="WEDEROM SOMMATIE TOT BETALING / 2026-00049",
        body=(
            "Eerder heb ik u aangeschreven betreffende de openstaande vordering. "
            "Ik verzoek u nogmaals het volledige bedrag te voldoen."
        ),
        when=t0 + timedelta(hours=1),
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_skips_non_learnable_category(
    db, test_tenant, test_user, test_company, test_person
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Dank voor uw bericht.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "ontvangstbevestiging")
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht",
        body="Wij hebben uw bericht in goede orde ontvangen en komen erop terug.",
        when=t0 + timedelta(hours=1),
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


# ── dashboard edit-rate ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_learning_stats_edit_rate_unchanged(
    db, test_tenant, test_user, test_company, test_person
):
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    body = "De verplichting tot betaling van de gefactureerde bedragen staat hiermee vast."
    gen = datetime.now(UTC)
    db.add(
        AIDraft(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            case_id=case.id,
            subject="Re",
            body=body,
            status="sent",
            generated_at=gen,
            sent_at=gen,
        )
    )
    # Uitgaande mail met (vrijwel) dezelfde tekst → bucket "ongewijzigd".
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        body=body, when=gen + timedelta(minutes=5),
    )
    await db.flush()

    stats = await get_learning_stats(db, test_tenant.id)
    assert stats["edit_rate"]["matched"] == 1
    assert stats["edit_rate"]["ongewijzigd"] == 1
