"""Verweer-antwoord-bibliotheek (S167) — kandidaten vangen → goedkeuren → voeden.

Dekt: kern-weerlegging uit een sommatie-verpakt antwoord knippen, anonimiseer-voorstel,
kandidaat-vangst (echte weerlegging wél, kale sommatie/XXX/dubbel-met-library niet),
goedkeuren/afwijzen, en dat alleen GOEDGEKEURDE (geanonimiseerde) tekst de prompt voedt —
plus dat de voorbeelden alleen bij de verweer-stap in de prompt komen.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.ai_agent.defense_library import DEFENSE_EXAMPLES
from app.ai_agent.incasso_email_prompts import build_user_prompt
from app.ai_agent.learned_answers import (
    STATUS_APPROVED,
    STATUS_CANDIDATE,
    STATUS_REJECTED,
    approve_candidate,
    backfill_learned_answers,
    build_learned_examples_text,
    clean_answer_body,
    extract_rebuttal,
    get_learning_stats,
    list_candidates,
    reject_candidate,
    suggest_anonymization,
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
    db, tenant_id, account_id, *, case_id, direction, body, when,
    subject="Re: vordering", html_only=False,
) -> SyncedEmail:
    # html_only=True bootst een Outlook-mail na: body_text leeg, inhoud in body_html.
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
        body_text="" if html_only else body,
        body_html=f"<div><p>{body}</p></div>",
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


# Een sommatie-verpakt verweer-antwoord (Lisanne's echte huisstijl, zoals live op prod):
# sommatie-kop, preamble, de eigenlijke weerlegging, dan de "Vordering"-tabel + "Laatste
# sommatie / Hierbij sommeer ik u andermaal ..."-staart met factuurnummer/datums/IBAN.
def _wrapped_rebuttal(core: str) -> str:
    return (
        "Betreft: WEDEROM SOMMATIE TOT BETALING / 2026-00099\n\n"
        "Geachte heer,\n\n"
        "Eerder heb ik u aangeschreven betreffende de openstaande vordering van mijn "
        "cliënt. Deze vordering is ter incasso aan mijn kantoor overgedragen.\n\n"
        "Hierbij voorzie ik u van een inhoudelijke reactie, waarin ik uw stellingen weerleg.\n\n"
        f"{core}\n\n"
        "Indien ondanks deze correspondentie betaling uitblijft, ben ik genoodzaakt het "
        "incassotraject voort te zetten.\n\n"
        "Vordering Het openstaande saldo is als volgt gespecificeerd:\n"
        "Factuurnummer Datum Vervaldatum Bedrag 102894 2026-03-31 2026-04-14 € 1.210,00\n"
        "Laatste sommatie Hierbij sommeer ik u andermaal het bovengenoemd totaalbedrag van "
        "€ 1.210,00 uiterlijk binnen 3 dagen na heden te voldoen op IBAN: NL12RABO0123456789.\n\n"
        "Met vriendelijke groet,\nL. Kesting"
    )


# ── clean_answer_body (edit-rate helper) ─────────────────────────────────


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
    assert "ik betwist" not in out


# ── extract_rebuttal: kern uit sommatie-omlijsting ───────────────────────


def test_extract_rebuttal_drops_preamble_and_payment_tail():
    core = (
        "U heeft gesteld dat de geleverde machine ondeugdelijk was. Uit het door u "
        "ondertekende opleveringsrapport blijkt echter dat u de levering zonder enig "
        "voorbehoud heeft geaccepteerd. Van een gebrek is niet gebleken."
    )
    out = extract_rebuttal("REACTIE OP UW VERWEER", _wrapped_rebuttal(core))
    assert "opleveringsrapport" in out
    assert "Eerder heb ik u aangeschreven" not in out  # preamble weg
    assert "Vordering" not in out  # bedragen-tabel weg
    assert "Factuurnummer" not in out
    assert "102894" not in out  # factuurnummer uit de tabel weg
    assert "Hierbij sommeer" not in out  # sommatie-staart weg
    assert "Met vriendelijke groet" not in out  # handtekening weg


# ── suggest_anonymization ────────────────────────────────────────────────


def test_suggest_anonymization_masks_pii():
    src = "De heer Jansen dient € 1.234,56 te betalen vóór 13 mei 2026, kenmerk 2026-00099."
    out = suggest_anonymization(src)
    assert "Jansen" not in out
    assert "1.234,56" not in out
    assert "13 mei 2026" not in out
    assert "2026-00099" not in out
    assert "[bedrag]" in out
    assert "[datum]" in out
    assert "[naam]" in out
    assert "[kenmerk]" in out


def test_suggest_anonymization_masks_iso_date_and_invoice_number():
    """Echte prod-lek: ISO-datum (2026-03-31) en kaal factuurnummer (102894)."""
    src = "Factuur 102894 met vervaldatum 2026-04-14 is op 2026-03-31 verzonden."
    out = suggest_anonymization(src)
    assert "102894" not in out
    assert "2026-03-31" not in out
    assert "2026-04-14" not in out
    assert "[nummer]" in out
    assert "[datum]" in out


# ── retrieval: alleen GOEDGEKEURD, geanonimiseerde tekst ─────────────────


@pytest.mark.asyncio
async def test_build_learned_examples_uses_approved_anonymized_only(db, test_tenant):
    # Goedgekeurd voorbeeld → moet meegaan, met de geanonimiseerde tekst.
    db.add(
        LearnedAnswer(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            category="betwisting",
            body="Ruwe tekst met de naam Jansen erin die nooit verstuurd mag worden.",
            anonymized_body="Schone weerlegging met plaatshouder [naam] en genoeg lengte hiervoor.",
            status=STATUS_APPROVED,
            is_active=True,
        )
    )
    # Kandidaat (nog niet goedgekeurd) → mag NIET meegaan.
    db.add(
        LearnedAnswer(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            category="betwisting",
            body="Kandidaat die nog niet is beoordeeld en dus niet gebruikt mag worden.",
            anonymized_body="Kandidaat-voorstel dat nog wacht op goedkeuring van de advocaat.",
            status=STATUS_CANDIDATE,
            is_active=False,
        )
    )
    await db.flush()

    text = await build_learned_examples_text(db, test_tenant.id, "betwisting")
    assert "goedgekeurd" in text.lower()
    assert "GEEN" in text  # PII-instructie aanwezig
    assert "Schone weerlegging" in text
    assert "Jansen" not in text  # ruwe body wordt nooit meegestuurd
    assert "Kandidaat" not in text  # kandidaten voeden de prompt niet

    # use_count alleen op het goedgekeurde voorbeeld.
    approved = (
        await db.execute(
            select(LearnedAnswer).where(
                LearnedAnswer.tenant_id == test_tenant.id,
                LearnedAnswer.status == STATUS_APPROVED,
            )
        )
    ).scalar_one()
    assert approved.use_count == 1


@pytest.mark.asyncio
async def test_no_examples_returns_empty(db, test_tenant):
    assert await build_learned_examples_text(db, test_tenant.id, "juridisch_verweer") == ""
    assert await build_learned_examples_text(db, test_tenant.id, None) == ""


# ── injectie alleen bij de verweer-stap (bevinding 4) ────────────────────


def _minimal_prompt(step_name: str, learned: str) -> str:
    return build_user_prompt(
        step_name=step_name,
        template_subject="Betreft",
        template_body="Body",
        case_data={},
        debtor_data={},
        client_data={},
        invoices=[],
        amounts={},
        learned_examples_text=learned,
    )


def test_learned_examples_only_injected_at_verweer_step():
    marker = "UNIEKE-GELEERDE-VOORBEELDTEKST"
    assert marker in _minimal_prompt("Verweer beantwoorden", marker)
    assert marker not in _minimal_prompt("Tweede sommatie", marker)
    assert marker not in _minimal_prompt("Eerste sommatie", marker)


# ── kandidaat-vangst (backfill) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_backfill_captures_wrapped_rebuttal_as_candidate(
    db, test_tenant, test_user, test_company, test_person
):
    """Bevinding 1: een echte weerlegging IN een sommatie-sjabloon wordt nu gevangen
    (werd voorheen weggegooid omdat 'sommatie' in het onderwerp stond)."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Ik betwist: de machine was ondeugdelijk.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "betwisting")
    core = (
        "U heeft gesteld dat de geleverde machine ondeugdelijk was. Uit het door u "
        "ondertekende opleveringsrapport blijkt echter dat u de levering zonder enig "
        "voorbehoud heeft geaccepteerd. Van een gebrek is niet gebleken."
    )
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="REACTIE OP UW VERWEER / WEDEROM SOMMATIE",
        body=_wrapped_rebuttal(core), when=t0 + timedelta(hours=1), html_only=True,
    )

    added = await backfill_learned_answers(db, test_tenant.id)
    assert added == 1
    row = (
        await db.execute(
            select(LearnedAnswer).where(LearnedAnswer.tenant_id == test_tenant.id)
        )
    ).scalar_one()
    assert row.status == STATUS_CANDIDATE  # kandidaat, voedt de AI nog niet
    assert row.is_active is False
    assert "opleveringsrapport" in row.body
    assert "Eerder heb ik u aangeschreven" not in row.body  # sommatie-omlijsting weg
    assert "Factuurnummer" not in row.body  # bedragen-tabel weg
    assert "Hierbij sommeer" not in row.body  # sommatie-staart weg
    assert row.anonymized_body  # er is een anonimiseer-voorstel

    # Idempotent.
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_skips_duplicate_of_library(
    db, test_tenant, test_user, test_company, test_person
):
    """Bevinding 2: een weerlegging die vrijwel gelijk is aan een bestaande standaardtekst
    wordt NIET als kandidaat opgeslagen — die kennen we al."""
    library_body = next(e.body for e in DEFENSE_EXAMPLES if e.key == "verlengd_abonnement")
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Ik betwist: het abonnement is opgezegd.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "betwisting")
    # Opener + vrijwel de exacte library-tekst.
    body = "U heeft gesteld dat het abonnement is opgezegd.\n\n" + library_body
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht", body=body, when=t0 + timedelta(hours=1), html_only=True,
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_excludes_plain_sommatie(
    db, test_tenant, test_user, test_company, test_person
):
    """Een kale sommatie (geen weerlegging) is geen kandidaat."""
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
            "Ik verzoek u het volledige bedrag binnen vijf dagen te voldoen."
        ),
        when=t0 + timedelta(hours=1),
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_excludes_unfilled_xxx_template(
    db, test_tenant, test_user, test_company, test_person
):
    """Een verweer-sjabloon waar het argument nog 'XXX' is, mag niet gevangen worden."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    inbound = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Ik betwist de factuur.", when=t0,
    )
    await _classify(db, test_tenant.id, inbound.id, case.id, "juridisch_verweer")
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: reactie",
        body="U heeft gesteld dat u niets verschuldigd bent. XXX Met vriendelijke groet.",
        when=t0 + timedelta(hours=1), html_only=True,
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
        body="U heeft gesteld dat u het bericht ontving; wij komen erop terug.",
        when=t0 + timedelta(hours=1),
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


# ── goedkeuren / afwijzen ────────────────────────────────────────────────


async def _make_candidate(db, tenant_id) -> LearnedAnswer:
    row = LearnedAnswer(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        category="betwisting",
        body="Ruwe weerlegging met naam Jansen en bedrag € 500,00 erin voor de test.",
        anonymized_body="Weerlegging met [naam] en [bedrag] — voorstel dat lang genoeg is.",
        defense_type="overig",
        status=STATUS_CANDIDATE,
        is_active=False,
    )
    db.add(row)
    await db.flush()
    return row


@pytest.mark.asyncio
async def test_approve_candidate_activates_and_feeds_prompt(db, test_tenant):
    cand = await _make_candidate(db, test_tenant.id)
    assert await list_candidates(db, test_tenant.id)  # staat in de wachtrij

    approved = await approve_candidate(
        db, test_tenant.id, cand.id,
        anonymized_body="Definitieve geanonimiseerde weerlegging met genoeg lengte hiervoor.",
        defense_type="annuleringskosten_9_3",
    )
    assert approved is not None
    assert approved.status == STATUS_APPROVED
    assert approved.is_active is True
    assert approved.reviewed_at is not None
    assert approved.defense_type == "annuleringskosten_9_3"

    # Niet meer in de wachtrij, wél in de prompt.
    assert await list_candidates(db, test_tenant.id) == []
    text = await build_learned_examples_text(db, test_tenant.id, "betwisting")
    assert "Definitieve geanonimiseerde weerlegging" in text


@pytest.mark.asyncio
async def test_reject_candidate_never_feeds_prompt(db, test_tenant):
    cand = await _make_candidate(db, test_tenant.id)
    assert await reject_candidate(db, test_tenant.id, cand.id) is True

    refreshed = (
        await db.execute(
            select(LearnedAnswer).where(LearnedAnswer.id == cand.id)
        )
    ).scalar_one()
    assert refreshed.status == STATUS_REJECTED
    assert refreshed.is_active is False
    assert await list_candidates(db, test_tenant.id) == []
    assert await build_learned_examples_text(db, test_tenant.id, "betwisting") == ""


@pytest.mark.asyncio
async def test_approve_unknown_candidate_returns_none(db, test_tenant):
    assert await approve_candidate(
        db, test_tenant.id, uuid.uuid4(), anonymized_body="x" * 40
    ) is None
    assert await reject_candidate(db, test_tenant.id, uuid.uuid4()) is False


# ── dashboard-stats ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_learning_stats_counts_and_edit_rate(
    db, test_tenant, test_user, test_company, test_person
):
    # Eén kandidaat + één goedgekeurd voorbeeld.
    await _make_candidate(db, test_tenant.id)
    db.add(
        LearnedAnswer(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            category="betwisting",
            body="raw",
            anonymized_body="Goedgekeurd voorbeeld met voldoende lengte voor de weergave.",
            status=STATUS_APPROVED,
            is_active=True,
        )
    )

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
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        body=body, when=gen + timedelta(minutes=5),
    )
    await db.flush()

    stats = await get_learning_stats(db, test_tenant.id)
    assert stats["candidates"] == 1
    assert stats["total_examples"] == 1  # alleen goedgekeurd telt mee
    assert stats["edit_rate"]["matched"] == 1
    assert stats["edit_rate"]["ongewijzigd"] == 1
