"""AI-antwoord-testronde ("het proefwerk") — S221 blok 4.3 sluitstuk.

Toetst de begrip-eerst-antwoordroute (unified_draft_service._REPLY_PROMPT) op een
vaste set proefmails en laat een tweede AI ("corrector") per antwoord een checklist
nakijken. Uitkomst = één markdown-rapport.

VEILIG: er wordt NIETS verstuurd en NIETS op echte dossiers geschreven. Elk antwoord
wordt direct via de AI gegenereerd (call_intake_ai) — de ai_drafts-wachtrij en het
verzendpad worden niet aangeraakt.

Gebruik (in de backend-container):
    python -m scripts.ai.antwoord_testronde --out /tmp/antwoord-rapport.md
    python -m scripts.ai.antwoord_testronde --goud 40 --tenant-id <uuid> --out ...

Zonder --goud draait alleen de zelfgeschreven proefset (geen DB nodig). Met --goud
worden goedgekeurde bibliotheek-antwoorden (learned_answers) met hun echte bron-mail
erbij gehaald en het AI-antwoord naast Lisanne's echte antwoord gelegd.

Analyse/iteratie van de uitkomst = Fable-werk (S222): foutpatronen → spelregels in
_REPLY_PROMPT bijschaven → dezelfde set opnieuw draaien → score vergelijken.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.ai_agent.kimi_client import CLAUDE_SONNET_MODEL, call_intake_ai  # noqa: E402
from app.ai_agent.unified_draft_service import (  # noqa: E402
    _REPLY_PROMPT,
    UNIFIED_DRAFT_SCHEMA,
)

# ── Zelfgeschreven proefset ────────────────────────────────────────────────
# Een compacte, representatieve startset (Fable breidt uit). Elk geval draagt een
# vast feitenblok (zoals _build_dossier_facts dat oplevert) zodat we kunnen toetsen
# of de AI feiten uit het dossier haalt i.p.v. ze te verzinnen.

_FACTS_A = (
    "--- Dossiergegevens (enige toegestane feitenbron) ---\n"
    "Opdrachtgever (onze cliënt): LegalWork B.V.\n"
    "Debiteur (wederpartij): Bakker Transport V.O.F.\n"
    "Openstaand bedrag (incl. rente + kosten): € 4.212,55\n"
    "Vorderingen:\n"
    "  - factuur 2025-0481 d.d. 2025-11-03: hoofdsom € 3.500,00"
)
_FACTS_B = (
    "--- Dossiergegevens (enige toegestane feitenbron) ---\n"
    "Opdrachtgever (onze cliënt): Incassocenter B.V.\n"
    "Debiteur (wederpartij): J. de Vries\n"
    "Openstaand bedrag (incl. rente + kosten): € 812,40\n"
    "Vorderingen:\n"
    "  - factuur 90021 d.d. 2026-01-12: hoofdsom € 700,00"
)

# (categorie, gewenste toon, feitenblok, van, onderwerp, body)
SEED_CASES: list[dict] = [
    {
        "id": "identiteitsvraag",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Wie zijn jullie?",
        "body": "Wie zijn jullie en wie is jullie klant? Ik heb hier nooit iets van gehoord.",
    },
    {
        "id": "betwisting_met_reden",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Klopt niet",
        "body": "Deze factuur klopt niet, de levering was onvolledig — er ontbraken 3 pallets.",
    },
    {
        "id": "betwisting_zonder_reden",
        "tone": "zakelijk", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Oneens",
        "body": "Ik ben het er niet mee eens.",
    },
    {
        "id": "beweert_betaald_zonder_bewijs",
        "tone": "zakelijk", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Al betaald",
        "body": "Ik heb dit allang betaald, volgens mij vorige maand.",
    },
    {
        "id": "betaalbelofte",
        "tone": "mild", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Betaling",
        "body": "Ik betaal volgende week vrijdag, het lukt nu even niet.",
    },
    {
        "id": "regeling_verzoek",
        "tone": "mild", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Regeling",
        "body": "Kunnen we een betalingsregeling afspreken van 200 euro per maand?",
    },
    {
        "id": "deelbetaling_claim",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Deel betaald",
        "body": "Ik heb vorige week al 1000 euro overgemaakt, de rest volgt.",
    },
    {
        "id": "boze_dreigende_mail",
        "tone": "streng", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Stop hiermee",
        "body": "Stop met dit geïntimideer anders schakel ik zelf een advocaat in!",
    },
    {
        "id": "advocatenbrief_tegenpartij",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "mr.jansen@advocaten.nl",
        "subject": "Namens cliënt Bakker Transport",
        "body": "Namens cliënte betwist ik de vordering integraal; ik verzoek u alle "
                "onderbouwing toe te zenden en verdere incassohandelingen te staken.",
    },
    {
        "id": "faillissement_melding",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Faillissement",
        "body": "Ons bedrijf is failliet verklaard, u kunt bij de curator terecht.",
    },
    {
        "id": "engels",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Question about invoice",
        "body": "I do not understand this invoice. Who are you and who is your client?",
    },
    {
        "id": "lege_onzin_mail",
        "tone": "zakelijk", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "",
        "body": "asdf ...",
    },
    {
        "id": "ander_dossier",
        "tone": "zakelijk", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Andere zaak",
        "body": "Dit gaat over factuur 11111 van een heel ander bedrijf, niet die van u.",
    },
    {
        "id": "kwijtschelding_verzoek",
        "tone": "mild", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "Kwijtschelding",
        "body": "Ik heb geen geld, kunt u de schuld kwijtschelden?",
    },
    {
        "id": "klacht_over_advocaat",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Klacht",
        "body": "Uw mevrouw Kesting gedraagt zich onbeschoft, ik dien een klacht in.",
    },
    {
        "id": "uitstel_verzoek",
        "tone": "mild", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Uitstel",
        "body": "Kan ik twee weken uitstel krijgen voor de betaling?",
    },
    {
        "id": "avg_privacyverzoek",
        "tone": "zakelijk", "facts": _FACTS_B,
        "from_email": "jdevries@example.com",
        "subject": "AVG-verzoek",
        "body": "Ik doe een beroep op de AVG: welke persoonsgegevens heeft u van mij en "
                "waarom? Ik wil inzage en verwijdering.",
    },
    {
        "id": "combinatie_vraag_en_betwisting",
        "tone": "zakelijk", "facts": _FACTS_A,
        "from_email": "info@bakkertransport.nl",
        "subject": "Vragen",
        "body": "Wie is uw opdrachtgever precies? En bovendien klopt het bedrag niet, "
                "ik had een creditnota gekregen.",
    },
]


def _build_user_msg(case: dict) -> str:
    """Zelfde vorm als unified_draft_service._build_reply_user_msg, maar uit strings."""
    parts = [
        "Dossier: (proef)",
        "Zaaktype: incasso",
        f"Gewenste toon: {case.get('tone', 'zakelijk')}",
        "\n" + case["facts"],
        "\n--- Inkomende email ---",
        f"Van: {case['from_email']}",
        f"Onderwerp: {case['subject']}",
        case["body"],
    ]
    return "\n".join(parts)


_CORRECTOR_PROMPT = (
    "Je bent kwaliteitscontroleur van een incassokantoor. Je beoordeelt of een "
    "concept-ANTWOORD op een debiteursmail deugt. Je krijgt de inkomende mail, de "
    "dossierfeiten en het concept-antwoord. Beoordeel streng.\n\n"
    "KALIBRATIE (vastgesteld door kantoor, 16-07-2026) — pas dit PRECIES toe, "
    "generaliseer niet verder:\n"
    "- Betaalbelofte of verzoek om KORT uitstel (dagen tot enkele weken): 'voor "
    "kennisgeving aannemen' + volledige betaling uiterlijk op de genoemde datum vragen "
    "is TOEGESTAAN — geen toezegging, mits niet gezegd wordt dat de invordering stilligt.\n"
    "- ALLEEN bij een KWIJTSCHELDINGSVERZOEK is 'voorleggen aan de cliënt' of "
    "terugkoppeling beloven een FOUT — kwijtschelding wordt afgewezen, punt.\n"
    "- Al het ÓVERIGE voorleggen/navragen bij de cliënt is normaal incassowerk en "
    "TOEGESTAAN, óók met de belofte van terugkoppeling: betwistingen, verweer, "
    "specificatie- of bewijsverzoeken, betalingsregeling-voorstellen, vragen over de "
    "onderbouwing. Reken dat NOOIT als toezegging.\n"
    "- Bedragen moeten uit de dossierfeiten komen; het dossierbedrag is actueler dan "
    "bedragen in oudere mails in de wisseling — een verschil met een oude mail is GEEN "
    "fout zolang het dossierbedrag wordt gebruikt.\n"
    "- Feiten die letterlijk in de INKOMENDE MAIL staan (zoals een dossiernummer in de "
    "onderwerpregel) mag het antwoord overnemen; dat is niet verzonnen.\n"
    "- Zijn het antwoordbedrag en het dossierbedrag gelijk, dan is er GEEN bedragfout.\n\n"
    "Geef ALLEEN valide JSON terug met deze velden (elke check true/false):\n"
    "{\n"
    '  "beantwoordt_de_vraag": bool,        // reageert het op wat de debiteur echt vroeg?\n'
    '  "feiten_kloppen": bool,              // geen verzonnen bedrag/naam/factuurnummer; alles uit de dossierfeiten\n'
    '  "geen_toezegging": bool,             // geen kwijtschelding/uitstel/regeling/excuses namens de cliënt bevestigd (zie kalibratie)\n'
    '  "escaleert_indien_nodig": bool,      // bij advocatenbrief/AVG/dreiging: ontvangstbevestiging + intern, geen inhoudelijk standpunt\n'
    '  "toon_passend": bool,                // zakelijk, geen ongepaste dreiging\n'
    '  "zware_fout": bool,                  // true als er een verzonnen bedrag OF een niet-toegestane toezegging in staat\n'
    '  "toelichting": "<één zin>"\n'
    "}"
)

# Schema hoort 1-op-1 bij de JSON-instructie in _CORRECTOR_PROMPT hierboven (S238).
_CORRECTOR_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "beantwoordt_de_vraag": {"type": "boolean"},
        "feiten_kloppen": {"type": "boolean"},
        "geen_toezegging": {"type": "boolean"},
        "escaleert_indien_nodig": {"type": "boolean"},
        "toon_passend": {"type": "boolean"},
        "zware_fout": {"type": "boolean"},
        "toelichting": {"type": "string"},
    },
    "required": [
        "beantwoordt_de_vraag", "feiten_kloppen", "geen_toezegging",
        "escaleert_indien_nodig", "toon_passend", "zware_fout", "toelichting",
    ],
    "additionalProperties": False,
}


async def _correct(case: dict, answer_body: str) -> dict:
    user = (
        f"{case['facts']}\n\n--- Inkomende mail ---\n{case['body']}\n\n"
        f"--- Concept-antwoord ---\n{answer_body}"
    )
    try:
        result, _ = await call_intake_ai(
            _CORRECTOR_PROMPT, user,
            schema=_CORRECTOR_SCHEMA, purpose="testronde_corrector",
            model=CLAUDE_SONNET_MODEL,
        )
        return result
    except Exception as e:  # corrector-fout mag de ronde niet stoppen
        return {"corrector_error": str(e)}


async def _run_case(case: dict, *, corrector: bool) -> dict:
    user_msg = _build_user_msg(case)
    try:
        result, model = await call_intake_ai(
            _REPLY_PROMPT, user_msg,
            schema=UNIFIED_DRAFT_SCHEMA, purpose="testronde_reply",
            model=CLAUDE_SONNET_MODEL,
        )
    except Exception as e:
        return {"id": case["id"], "error": str(e)}
    answer_body = (result.get("body") or "").strip()
    row = {
        "id": case["id"],
        "tone": case.get("tone"),
        "subject_in": case["subject"],
        "answer_subject": result.get("subject"),
        "answer_body": answer_body,
        "model": model,
    }
    if "reference_answer" in case:
        row["reference_answer"] = case["reference_answer"]
    if corrector:
        row["check"] = await _correct(case, answer_body)
    return row


async def _load_goud(tenant_id: str, limit: int) -> list[dict]:
    """Trek goedgekeurde bibliotheek-antwoorden met hun echte bron-mail + dossier."""
    from sqlalchemy import select, text

    # Volledige model-registry laden (zelfde lijst als alembic/env.py) — de mappers
    # van Case/SyncedEmail verwijzen naar modellen die anders nooit geïmporteerd
    # worden in dit losse script (IncassoPipelineStep, EmailAccount, ...).
    import app.ai_agent.followup_models  # noqa: F401
    import app.ai_agent.intake_models  # noqa: F401
    import app.ai_agent.payment_matching_models  # noqa: F401
    import app.calendar.models  # noqa: F401
    import app.collections.models  # noqa: F401
    import app.documents.models  # noqa: F401
    import app.email.attachment_models  # noqa: F401
    import app.email.models  # noqa: F401
    import app.email.oauth_models  # noqa: F401
    import app.exact_online.models  # noqa: F401
    import app.incasso.models  # noqa: F401
    import app.invoices.models  # noqa: F401
    import app.notifications.models  # noqa: F401
    import app.products.models  # noqa: F401
    import app.relations.kyc_models  # noqa: F401
    import app.relations.models  # noqa: F401
    import app.time_entries.models  # noqa: F401
    import app.trust_funds.models  # noqa: F401
    import app.workflow.models  # noqa: F401
    from app.ai_agent.models import LearnedAnswer
    from app.ai_agent.unified_draft_service import _build_dossier_facts
    from app.cases.models import Case
    from app.database import async_session
    from app.email.synced_email_models import SyncedEmail

    cases: list[dict] = []
    async with async_session() as db:
        await db.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
        rows = (
            await db.execute(
                select(LearnedAnswer)
                .where(
                    LearnedAnswer.tenant_id == tenant_id,
                    LearnedAnswer.status == "goedgekeurd",
                    LearnedAnswer.source_synced_email_id.isnot(None),
                    LearnedAnswer.source_case_id.isnot(None),
                )
                .limit(limit)
            )
        ).scalars().all()
        for la in rows:
            answer_mail = await db.get(SyncedEmail, la.source_synced_email_id)
            case = await db.get(Case, la.source_case_id)
            if not answer_mail or not case:
                continue
            # source_synced_email_id = Lisanne's VERSTUURDE antwoord (zo is het veld
            # gedefinieerd, zie LearnedAnswer). De vraag die de AI moet beantwoorden is
            # de laatste INKOMENDE mail in dezelfde zaak vóór dat antwoord — anders
            # voeren we de AI haar eigen antwoord ("beantwoord deze uitgaande mail")
            # en meet de ronde niets (S222-vondst).
            question = (
                await db.execute(
                    select(SyncedEmail)
                    .where(
                        SyncedEmail.tenant_id == case.tenant_id,
                        SyncedEmail.case_id == case.id,
                        SyncedEmail.direction == "inbound",
                        SyncedEmail.from_email.notilike("%kestinglegal%"),
                        SyncedEmail.email_date < answer_mail.email_date,
                    )
                    .order_by(SyncedEmail.email_date.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if not question or not (question.body_text or "").strip():
                continue  # geen bruikbare voorafgaande debiteurenvraag → overslaan
            facts = await _build_dossier_facts(db, case.tenant_id, case)
            cases.append(
                {
                    "id": f"goud:{la.id}",
                    "tone": "zakelijk",
                    "facts": facts,
                    "from_email": question.from_email or "",
                    "subject": question.subject or "",
                    "body": (question.body_text or "")[:2000],
                    "reference_answer": (la.anonymized_body or la.body or "")[:2000],
                }
            )
    return cases


def _render_report(rows: list[dict]) -> str:
    lines = ["# AI-antwoord-testronde — rapport\n"]
    n = len(rows)
    zware = sum(1 for r in rows if r.get("check", {}).get("zware_fout"))
    errors = sum(1 for r in rows if r.get("error"))
    lines.append(f"- Gevallen: **{n}**  ·  Zware fouten: **{zware}**  ·  Generatie-fouten: **{errors}**\n")
    for r in rows:
        lines.append(f"\n## {r['id']}")
        if r.get("error"):
            lines.append(f"\n**FOUT:** {r['error']}")
            continue
        lines.append(f"\n**Ingekomen (onderwerp):** {r.get('subject_in','')}")
        lines.append(f"\n**Antwoord-onderwerp:** {r.get('answer_subject','')}\n")
        lines.append("**Antwoord:**\n")
        lines.append("> " + (r.get("answer_body", "").replace("\n", "\n> ")))
        if r.get("reference_answer"):
            lines.append("\n**Referentie (Lisanne):**\n")
            lines.append("> " + r["reference_answer"].replace("\n", "\n> "))
        if r.get("check"):
            lines.append("\n**Corrector:** `" + json.dumps(r["check"], ensure_ascii=False) + "`")
    return "\n".join(lines)


async def main() -> None:
    ap = argparse.ArgumentParser(description="AI-antwoord-testronde (veilig, niets verstuurd)")
    ap.add_argument("--out", default="/tmp/antwoord-testronde-rapport.md")
    ap.add_argument("--goud", type=int, default=0, help="max aantal goud-gevallen uit de bibliotheek")
    ap.add_argument("--tenant-id", default=None, help="verplicht bij --goud")
    ap.add_argument("--limit", type=int, default=0, help="cap op zelfgeschreven gevallen (0=alle)")
    ap.add_argument("--no-corrector", action="store_true")
    args = ap.parse_args()

    cases = list(SEED_CASES)
    if args.limit:
        cases = cases[: args.limit]
    if args.goud:
        if not args.tenant_id:
            ap.error("--goud vereist --tenant-id")
        cases += await _load_goud(args.tenant_id, args.goud)

    print(f"Draai {len(cases)} proefgevallen (corrector={'uit' if args.no_corrector else 'aan'})...")
    rows: list[dict] = []
    for i, case in enumerate(cases, 1):
        rows.append(await _run_case(case, corrector=not args.no_corrector))
        print(f"  {i}/{len(cases)} — {case['id']}")

    report = _render_report(rows)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report)
    zware = sum(1 for r in rows if r.get("check", {}).get("zware_fout"))
    print(f"\nKlaar. Rapport: {args.out}  ·  zware fouten: {zware}")


if __name__ == "__main__":
    asyncio.run(main())
