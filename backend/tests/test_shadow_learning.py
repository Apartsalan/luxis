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
from app.ai_agent.knowledge_context import last_inbound_defense
from app.ai_agent.learned_answers import (
    STATUS_APPROVED,
    STATUS_CANDIDATE,
    STATUS_REJECTED,
    approve_candidate,
    backfill_learned_answers,
    build_learned_examples_text,
    clean_answer_body,
    extract_rebuttal,
    get_learned_examples,
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


def test_extract_rebuttal_strips_leading_intro_boilerplate():
    """F1 (S168): 'U heeft gereageerd. Hieronder treft u mijn antwoord aan.' is filler
    en hoort niet in het opgeslagen voorbeeld — alleen het argument blijft over."""
    body = (
        "Geachte heer,\n\n"
        "U heeft gereageerd. Hieronder treft u mijn antwoord aan.\n\n"
        "De door u gestelde ontbinding mist grond: er is nooit tijdig een gebrek "
        "gemeld, zodat het klachtrecht van artikel 7:23 BW is vervallen.\n\n"
        "Met vriendelijke groet,\nL. Kesting"
    )
    out = extract_rebuttal("Re: SOMMATIE", body)
    assert out.startswith("De door u gestelde ontbinding")
    assert "Hieronder treft u mijn antwoord aan" not in out
    assert "U heeft gereageerd" not in out
    assert "artikel 7:23 BW" in out  # het echte argument blijft
    assert "Met vriendelijke groet" not in out


def test_extract_rebuttal_preserves_substantive_opener():
    """Regressiewaarborg bij F1: een inhoudelijke opener ('U heeft gesteld ...') mag
    NIET als boilerplate worden gestript."""
    body = (
        "U heeft gesteld dat niet is geleverd. Uit de vrachtbrief blijkt het tegendeel."
    )
    out = extract_rebuttal("Re", body)
    assert out.startswith("U heeft gesteld dat niet is geleverd")


def test_extract_rebuttal_cuts_opgave_van_de_vordering():
    """F3 (S168): administratieve 'opgave van de vordering'-mail → tail wordt afgeknipt,
    zodat er te weinig substance overblijft en de backfill hem overslaat."""
    body = (
        "Naar aanleiding van uw bericht het volgende. "
        "Hierbij doe ik u een opgave van de vordering die cliënte ter incasso uit "
        "handen heeft gegeven. De vordering bedraagt thans € 1.000,00."
    )
    out = extract_rebuttal("Re", body)
    assert "opgave van de vordering" not in out
    assert "ter incasso" not in out
    assert "€ 1.000,00" not in out


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


def test_suggest_anonymization_masks_email():
    """Echte prod-lek (S169): e-mailadressen bleven staan in het anonimiseer-voorstel."""
    src = "Verzoek voortaan peter@langedijk.nl te gebruiken i.p.v. info@langedijk.nl."
    out = suggest_anonymization(src)
    assert "peter@langedijk.nl" not in out
    assert "info@langedijk.nl" not in out
    assert "@" not in out
    assert out.count("[e-mail]") == 2


def test_suggest_anonymization_masks_eur_word_and_dash_amounts():
    """F2 (S168): echte prod-lekken 'EUR 700,-' (woord i.p.v. €) en '€ –100,00'
    (en-dash vóór het cijfer) glipten langs het kale €-teken."""
    src = "Betaal EUR 700,- ; de creditering van € –100,00 en EUR 25,- zijn verwerkt."
    out = suggest_anonymization(src)
    assert "700" not in out
    assert "100,00" not in out
    assert "25" not in out
    assert out.count("[bedrag]") >= 3


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


@pytest.mark.asyncio
async def test_retrieval_prefers_newest_approved_over_high_use_count(db, test_tenant):
    """Fable-review F1: sorteren op use_count is zelfversterkend (wie één keer wint,
    wint eeuwig). Het nieuwst goedgekeurde antwoord van een type moet voorrang krijgen."""
    from datetime import timedelta

    now = datetime.now(UTC)
    # Drie oudere antwoorden van hetzelfde type met hoge tellers verdringen onder
    # use_count-sortering het nieuwste antwoord (teller 0) uit de top-3.
    for i, uses in enumerate((25, 20, 15)):
        db.add(
            LearnedAnswer(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                category="betwisting",
                body=f"raw oud {i}",
                anonymized_body=f"OUD antwoord {i} dat al vaak is meegestuurd, met lengte.",
                defense_type="verlengd_abonnement",
                status=STATUS_APPROVED,
                is_active=True,
                use_count=uses,
                reviewed_at=now - timedelta(days=30 + i),
            )
        )
    db.add(
        LearnedAnswer(
            id=uuid.uuid4(),
            tenant_id=test_tenant.id,
            category="betwisting",
            body="raw nieuw",
            anonymized_body="NIEUW verbeterd antwoord dat net is goedgekeurd met genoeg lengte.",
            defense_type="verlengd_abonnement",
            status=STATUS_APPROVED,
            is_active=True,
            use_count=0,
            reviewed_at=now,
        )
    )
    await db.flush()

    text = await build_learned_examples_text(db, test_tenant.id, "betwisting")
    assert "NIEUW verbeterd antwoord" in text  # nieuwste goedkeuring wint


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
async def test_backfill_dedups_near_identical_candidates(
    db, test_tenant, test_user, test_company, test_person
):
    """Fable-review F2: twee vrijwel identieke weerleggingen (live op prod: 3 varianten
    van hetzelfde abonnement-antwoord) moeten één kandidaat opleveren, niet twee. En na
    een afwijzing mag een vrijwel gelijke mail niet opnieuw kandidaat worden."""
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
    # Zelfde weerlegging, twee mails (minieme variatie in de tweede).
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht", body=_wrapped_rebuttal(core),
        when=t0 + timedelta(hours=1), html_only=True,
    )
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht (2)", body=_wrapped_rebuttal(core + " Aldus ongegrond."),
        when=t0 + timedelta(hours=2), html_only=True,
    )

    assert await backfill_learned_answers(db, test_tenant.id) == 1  # niet 2

    # Afwijzen → een derde vrijwel gelijke mail wordt géén nieuwe kandidaat.
    cand = (await list_candidates(db, test_tenant.id))[0]
    await reject_candidate(db, test_tenant.id, cand.id)
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="RE: uw bericht (3)", body=_wrapped_rebuttal(core),
        when=t0 + timedelta(hours=3), html_only=True,
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_skips_empty_boilerplate_reply(
    db, test_tenant, test_user, test_company, test_person
):
    """Een mail met alleen 'ik heb uw reactie besproken, hieronder mijn antwoord' + sommatie
    (geen echt argument) is geen bruikbaar voorbeeld."""
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
        subject="RE: uw bericht",
        body=_wrapped_rebuttal(
            "U heeft gereageerd waarna ik uw reactie met cliënte heb besproken. "
            "Hieronder treft u mijn antwoord aan."
        ),
        when=t0 + timedelta(hours=1), html_only=True,
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


@pytest.mark.asyncio
async def test_backfill_skips_forwarded_debtor_mail(
    db, test_tenant, test_user, test_company, test_person
):
    """S173-a: een doorgestuurde (Fwd:) mail is Lisanne's uitgaande mail, maar de inhoud is
    de geciteerde debiteur-tekst — nooit als voorbeeld leren (audit §5.b). Zelfde body die
    zónder Fwd: wél gevangen wordt, zodat alleen de subjectguard het verschil maakt."""
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
    core = (
        "U heeft gesteld dat de geleverde machine ondeugdelijk was. Uit het door u "
        "ondertekende opleveringsrapport blijkt echter dat u de levering zonder enig "
        "voorbehoud heeft geaccepteerd. Van een gebrek is niet gebleken."
    )
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="Fwd: reactie debiteur", body=_wrapped_rebuttal(core),
        when=t0 + timedelta(hours=1), html_only=True,
    )
    assert await backfill_learned_answers(db, test_tenant.id) == 0


@pytest.mark.asyncio
async def test_backfill_skips_debtor_voice_but_keeps_genuine_rebuttal(
    db, test_tenant, test_user, test_company, test_person
):
    """S173-b: bij een Re:-mail (waar de Fwd:-guard niet grijpt) waarvan de kern in
    debiteur-stem staat ('...wil ik een betalingsregeling aanvragen...') wordt de mail
    overgeslagen — terwijl een échte weerlegging in dezelfde run wél wordt gevangen. Bewijst
    dat de guard specifiek is en niet alles wegvangt (audit §5.b, Fable-review S173)."""
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

    # (1) Debiteur-stem in de kern — moet worden overgeslagen.
    debtor_core = (
        "Naar aanleiding van uw bericht wil ik een betalingsregeling aanvragen, omdat ik "
        "op dit moment niet in staat ben het volledige bedrag ineens te voldoen. Ik stel "
        "voor het bedrag in maandelijkse termijnen te betalen."
    )
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="Re: uw bericht", body=_wrapped_rebuttal(debtor_core),
        when=t0 + timedelta(hours=1), html_only=True,
    )
    # (2) Echte weerlegging van Lisanne — moet wél gevangen worden.
    genuine_core = (
        "U heeft gesteld dat de geleverde machine ondeugdelijk was. Uit het door u "
        "ondertekende opleveringsrapport blijkt echter dat u de levering zonder enig "
        "voorbehoud heeft geaccepteerd. Van een gebrek is niet gebleken."
    )
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        subject="Re: uw bericht (2)", body=_wrapped_rebuttal(genuine_core),
        when=t0 + timedelta(hours=2), html_only=True,
    )

    assert await backfill_learned_answers(db, test_tenant.id) == 1  # alleen de echte
    row = (
        await db.execute(
            select(LearnedAnswer).where(LearnedAnswer.tenant_id == test_tenant.id)
        )
    ).scalar_one()
    assert "opleveringsrapport" in row.body
    assert "betalingsregeling" not in row.body


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


@pytest.mark.asyncio
async def test_reject_candidate_leaves_approved_untouched(db, test_tenant):
    """Fable-review S170: enkelvoudig afwijzen mag een al GOEDGEKEURD voorbeeld
    niet terugzetten — zelfde guard als de bulk-variant (raakt AI-voeding)."""
    approved = LearnedAnswer(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        category="betwisting",
        body="raw",
        anonymized_body="Goedgekeurd voorbeeld dat afwijzen moet overleven, lang genoeg.",
        status=STATUS_APPROVED,
        is_active=True,
    )
    db.add(approved)
    await db.flush()

    assert await reject_candidate(db, test_tenant.id, approved.id) is False

    refreshed = (
        await db.execute(select(LearnedAnswer).where(LearnedAnswer.id == approved.id))
    ).scalar_one()
    assert refreshed.status == STATUS_APPROVED
    assert refreshed.is_active is True


@pytest.mark.asyncio
async def test_reject_candidates_bulk_only_touches_own_pending(db, test_tenant):
    """Bulk-afwijzen ruimt meerdere kandidaten in één keer op, maar laat een al
    goedgekeurd voorbeeld ongemoeid (raakt alleen status 'kandidaat')."""
    from app.ai_agent.learned_answers import reject_candidates_bulk

    c1 = await _make_candidate(db, test_tenant.id)
    c2 = await _make_candidate(db, test_tenant.id)
    approved = LearnedAnswer(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        category="betwisting",
        body="raw",
        anonymized_body="Goedgekeurd voorbeeld dat niet teruggezet mag worden, lang genoeg.",
        status=STATUS_APPROVED,
        is_active=True,
    )
    db.add(approved)
    await db.flush()

    rejected = await reject_candidates_bulk(
        db, test_tenant.id, [c1.id, c2.id, approved.id]
    )
    assert rejected == 2  # alleen de twee kandidaten, niet het goedgekeurde voorbeeld
    assert await list_candidates(db, test_tenant.id) == []

    still_approved = (
        await db.execute(select(LearnedAnswer).where(LearnedAnswer.id == approved.id))
    ).scalar_one()
    assert still_approved.status == STATUS_APPROVED
    assert still_approved.is_active is True

    # Lege lijst is een no-op.
    assert await reject_candidates_bulk(db, test_tenant.id, []) == 0


@pytest.mark.asyncio
async def test_approve_candidates_bulk_activates_pending_only(db, test_tenant):
    """Bulk-goedkeuren activeert meerdere kandidaten in één keer met hun eigen tekst +
    voor-gelabeld type; laat een al afgewezen rij ongemoeid en valt bij ontbrekende
    geanonimiseerde tekst terug op de ruwe body (nooit een leeg voorbeeld)."""
    from app.ai_agent.learned_answers import approve_candidates_bulk

    c1 = await _make_candidate(db, test_tenant.id)
    c2 = await _make_candidate(db, test_tenant.id)
    c2.anonymized_body = None  # geen geanonimiseerde tekst → moet terugvallen op body
    # Een al afgewezen rij mag bulk-goedkeuren NIET terugzetten.
    rejected_row = LearnedAnswer(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        category="betwisting",
        body="raw afgewezen",
        anonymized_body="Eerder afgewezen voorbeeld, moet afgewezen blijven, lang genoeg.",
        status=STATUS_REJECTED,
        is_active=False,
    )
    db.add(rejected_row)
    await db.flush()
    # Id's als losse waarden vastleggen vóór het verversen (anders triggert het lezen van
    # .id op een verlopen ORM-object async-IO op de verkeerde plek → MissingGreenlet).
    c1_id, c2_id, rej_id = c1.id, c2.id, rejected_row.id

    # Lege lijst is een no-op — vóór de bulk-update, zolang de sessie nog schoon is.
    assert await approve_candidates_bulk(db, test_tenant.id, []) == 0

    approved = await approve_candidates_bulk(db, test_tenant.id, [c1_id, c2_id, rej_id])
    assert approved == 2  # alleen de twee kandidaten
    assert await list_candidates(db, test_tenant.id) == []  # wachtrij leeg

    # Verifieer via kolom-queries (niet via de ORM-objecten): een bulk-UPDATE met
    # synchronize_session=False laat de identity-map staan, dus objecten teruglezen zou
    # verouderde waarden geven. Kolom-tuples hitten altijd de database.
    async def _cols(cid):
        return (
            await db.execute(
                select(
                    LearnedAnswer.status,
                    LearnedAnswer.is_active,
                    LearnedAnswer.defense_type,
                    LearnedAnswer.anonymized_body,
                    LearnedAnswer.body,
                ).where(LearnedAnswer.id == cid)
            )
        ).first()

    s1, active1, type1, _, _ = await _cols(c1_id)
    assert s1 == STATUS_APPROVED and active1 is True
    assert type1 == "overig"  # eigen voor-gelabelde type behouden
    # c2 had geen geanonimiseerde tekst → terugval op de ruwe body, niet leeg.
    s2, _, _, anon2, body2 = await _cols(c2_id)
    assert s2 == STATUS_APPROVED and anon2 == body2
    # De eerder afgewezen rij is niet aangeraakt.
    s_rej, _, _, _, _ = await _cols(rej_id)
    assert s_rej == STATUS_REJECTED


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


# ── last_inbound_defense_category: staleness-gate (S174) ─────────────────


@pytest.mark.asyncio
async def test_last_inbound_category_returns_newest_inbound_by_email_date(
    db, test_tenant, test_user, test_company, test_person
):
    """De helper kiest de LAATSTE inkomende mail op e-maildatum (niet op
    classificatie.created_at). Nieuwste inbound is verweer → die categorie wint."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    old = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Oud bericht.", when=t0 - timedelta(days=5),
    )
    await _classify(db, test_tenant.id, old.id, case.id, "betwisting")
    new = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Nieuw verweer.", when=t0,
    )
    await _classify(db, test_tenant.id, new.id, case.id, "juridisch_verweer")

    category, _ = await last_inbound_defense(db, test_tenant.id, case.id)
    assert category == "juridisch_verweer"


@pytest.mark.asyncio
async def test_last_inbound_category_none_when_newest_inbound_unclassified(
    db, test_tenant, test_user, test_company, test_person
):
    """Staleness-regel: de allernieuwste inkomende mail is NIET geclassificeerd → None,
    ook al is een oudere mail wél als verweer geclassificeerd. We plakken geen oude
    verweer-context op een dossier met een verse, ongeclassificeerde mail."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    t0 = datetime.now(UTC)
    old = await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Oud verweer.", when=t0 - timedelta(days=5),
    )
    await _classify(db, test_tenant.id, old.id, case.id, "juridisch_verweer")
    # Nieuwste inbound zonder classificatie.
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="inbound",
        body="Verse vraag, nog niet geclassificeerd.", when=t0,
    )

    assert await last_inbound_defense(db, test_tenant.id, case.id) == (None, None)


@pytest.mark.asyncio
async def test_last_inbound_category_none_without_inbound(
    db, test_tenant, test_user, test_company, test_person
):
    """Geen inkomende mail op het dossier → None (niets om op te matchen)."""
    case = await create_incasso_case(
        db, test_tenant.id, test_company, test_person, test_user, step=None
    )
    acc = await _account(db, test_tenant.id, test_user.id)
    # Alleen een uitgaande mail — telt niet als inbound.
    await _email(
        db, test_tenant.id, acc.id, case_id=case.id, direction="outbound",
        body="Onze sommatie.", when=datetime.now(UTC),
    )
    assert await last_inbound_defense(db, test_tenant.id, case.id) == (None, None)


# ── V4: gerichte matching op verweer-type + één pool ─────────────────────


def _approved(tenant_id, *, category, defense_type, body, when):
    return LearnedAnswer(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        category=category,
        body=f"raw {body}",
        anonymized_body=body,
        defense_type=defense_type,
        status=STATUS_APPROVED,
        is_active=True,
        use_count=0,
        reviewed_at=when,
    )


@pytest.mark.asyncio
async def test_get_learned_examples_prioritizes_matching_defense_type(db, test_tenant):
    """V4-kern: een voorbeeld van het gevraagde verweer-type krijgt voorrang, óók als een
    ander type een NIEUWERE goedkeuring heeft (die anders bovenaan zou staan)."""
    now = datetime.now(UTC)
    db.add(_approved(
        test_tenant.id, category="betwisting", defense_type="reeds_betaald_verrekening",
        body="NIEUWER voorbeeld over reeds betaald, met genoeg lengte hiervoor.", when=now,
    ))
    db.add(_approved(
        test_tenant.id, category="betwisting", defense_type="verlenging_opzegging",
        body="OUDER voorbeeld over stilzwijgende verlenging, lang genoeg.",
        when=now - timedelta(days=10),
    ))
    await db.flush()

    # Zonder type: nieuwste (reeds_betaald) staat vooraan.
    plain = await get_learned_examples(db, test_tenant.id, "betwisting")
    assert plain[0].defense_type == "reeds_betaald_verrekening"

    # Mét type verlenging_opzegging: dat voorbeeld staat nu vooraan, ondanks ouder.
    typed = await get_learned_examples(
        db, test_tenant.id, "betwisting", defense_type="verlenging_opzegging"
    )
    assert typed[0].defense_type == "verlenging_opzegging"


@pytest.mark.asyncio
async def test_get_learned_examples_merges_verweer_categories_into_one_pool(db, test_tenant):
    """V4: juridisch_verweer en betwisting vormen één pool — een onder 'betwisting'
    goedgekeurd voorbeeld is óók beschikbaar bij een 'juridisch_verweer'-vraag."""
    db.add(_approved(
        test_tenant.id, category="betwisting", defense_type="verlenging_opzegging",
        body="Voorbeeld goedgekeurd onder betwisting, lang genoeg voor de test.",
        when=datetime.now(UTC),
    ))
    await db.flush()

    got = await get_learned_examples(db, test_tenant.id, "juridisch_verweer")
    assert len(got) == 1
    assert got[0].category == "betwisting"  # over de categorie-grens heen gevonden


@pytest.mark.asyncio
async def test_get_learned_examples_type_match_survives_many_newer_approvals(db, test_tenant):
    """S175-fix: het type-matchende voorbeeld wordt óók gevonden als er daarna véél
    andere goedkeuringen bijkomen. De oude query-cap (12 nieuwste) liet het gevraagde
    type stil buiten beeld vallen zodra Lisanne meer dan 12 kandidaten goedkeurde —
    precies het moment waarop V4 zijn werk moet doen."""
    now = datetime.now(UTC)
    # Het gezochte type is de OUDSTE goedkeuring...
    db.add(_approved(
        test_tenant.id, category="betwisting", defense_type="reeds_betaald_verrekening",
        body="Het enige reeds-betaald-voorbeeld, goedgekeurd vóór alle andere.",
        when=now - timedelta(days=30),
    ))
    # ...gevolgd door 15 nieuwere goedkeuringen van een ander type.
    for i in range(15):
        db.add(_approved(
            test_tenant.id, category="betwisting", defense_type="verlenging_opzegging",
            body=f"Nieuwer verlenging-voorbeeld nummer {i}, ruim lang genoeg hiervoor.",
            when=now - timedelta(days=i),
        ))
    await db.flush()

    got = await get_learned_examples(
        db, test_tenant.id, "betwisting", defense_type="reeds_betaald_verrekening"
    )
    assert got and got[0].defense_type == "reeds_betaald_verrekening"


@pytest.mark.asyncio
async def test_get_learned_examples_matches_across_legacy_type_alias(db, test_tenant):
    """Een oude library-key op een goedgekeurd voorbeeld matcht op zijn nieuwe type:
    defense_type='afwikkeling_intrekking' vindt een rij met de oude 'annuleringskosten_9_3'."""
    db.add(_approved(
        test_tenant.id, category="betwisting", defense_type="annuleringskosten_9_3",
        body="Oud-gelabeld 9.3-afwikkelingsvoorbeeld, ruim lang genoeg hiervoor.",
        when=datetime.now(UTC),
    ))
    await db.flush()

    got = await get_learned_examples(
        db, test_tenant.id, "betwisting", defense_type="afwikkeling_intrekking"
    )
    assert len(got) == 1
    assert got[0].defense_type == "annuleringskosten_9_3"
