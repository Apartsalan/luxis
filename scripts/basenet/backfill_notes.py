"""BaseNet-backfill: dossiernotities (pmemo) + waarschuwingen (palert) → Case.debtor_notes.

De import gebruikte het Incasso-bestand voor de dossiers maar liet twee tekstvelden
liggen: `pmemo` (99 werknotities van Lisanne) en `palert` (13 waarschuwingsbanners,
o.a. "Failliet", "NIET REAGEREN - procedure aanhangig"). Juist die context stuurt de
eerste actie bij een heropening, dus horen ze in de dossiernotitie.

Format van de bijgewerkte notitie:
    [BaseNet-waarschuwing] <alert>      <- alleen bij palert, bovenaan

    <bestaande debtor_notes>            <- blijft ongemoeid (o.a. de herkomst-regel)

    [BaseNet-notitie]                   <- alleen bij pmemo, onderaan
    <memo>

Idempotent: een dossier dat de betreffende marker al bevat wordt overgeslagen, dus
her-runnen (of een gedeeltelijke her-run) plakt nooit dubbel.

Draait ín de prod-container:
    python -m scripts.basenet.backfill_notes <export-map>            # dry-run (telt, wijzigt niets)
    python -m scripts.basenet.backfill_notes <export-map> --commit   # schrijft weg

Zelf-test van de opschoon-functie:
    python -m scripts.basenet.backfill_notes --selftest

S209 (14 juli 2026): eenmalig uitgevoerd op 109 dossiers (99 notitie + 13 waarschuwing),
tel-geverifieerd op prod.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import re
import sys

# App-/DB-imports staan bewust ín run(): zo draaien clean()/build_new_notes() +
# de zelf-test standalone (zonder de hele app-omgeving).

ALERT_MARK = "[BaseNet-waarschuwing]"
NOTE_MARK = "[BaseNet-notitie]"


def clean(s: str | None) -> str:
    """BaseNet rich-text (<br>, &nbsp;, HTML-entiteiten) → leesbare platte tekst."""
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)  # <br> → nieuwe regel
    s = re.sub(r"<[^>]+>", "", s)  # overige tags weg
    s = s.replace("&nbsp;", " ")
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def build_new_notes(existing: str | None, alert: str, memo: str) -> str:
    """Waarschuwing bovenaan, bestaande notitie in het midden, werknotitie onderaan."""
    parts: list[str] = []
    if alert:
        parts.append(f"{ALERT_MARK} {alert}")
    if existing:
        parts.append(existing)
    if memo:
        parts.append(f"{NOTE_MARK}\n{memo}")
    return "\n\n".join(parts)


async def run(export_dir: str, commit: bool) -> None:
    # Alle ORM-modellen importeren zodat de SQLAlchemy-mapper volledig configureert.
    from app.auth.models import Tenant, User  # noqa: F401
    from app.cases.models import Case, CaseActivity, CaseParty  # noqa: F401
    from app.collections.models import Claim, Payment, PaymentArrangement  # noqa: F401
    from app.relations.models import Contact, ContactLink, ContactTerms  # noqa: F401
    from sqlalchemy import text
    from app.database import async_session

    from .parse import parse_entity

    recs = parse_entity(export_dir, "Incasso").records
    todo = []
    for r in recs:
        alert = clean(r.get("palert"))
        memo = clean(r.get("pmemo"))
        if not alert and not memo:
            continue
        code = (r.get("inccode") or r.get("pcode") or "").strip()
        if code:
            todo.append((code, alert, memo))
    print(f"Bron: {len(todo)} dossiers met notitie en/of waarschuwing")

    async with async_session() as db:
        tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
        if len(tenants) != 1:
            raise SystemExit(f"Verwacht 1 tenant, vond {len(tenants)}.")
        tid = tenants[0][0]

        n_note = n_alert = n_skip = n_missing = 0
        for code, alert, memo in todo:
            row = (
                await db.execute(
                    text(
                        "SELECT debtor_notes FROM cases "
                        "WHERE case_number=:c AND tenant_id=:t"
                    ),
                    {"c": code, "t": tid},
                )
            ).first()
            if row is None:
                n_missing += 1
                print(f"  ONTBREEKT in Luxis: {code}")
                continue
            existing = row[0] or ""
            # idempotent: sla het al-geplakte deel over
            put_alert = bool(alert) and ALERT_MARK not in existing
            put_memo = bool(memo) and NOTE_MARK not in existing
            if not put_alert and not put_memo:
                n_skip += 1
                continue
            new = build_new_notes(
                existing,
                alert if put_alert else "",
                memo if put_memo else "",
            )
            if put_alert:
                n_alert += 1
            if put_memo:
                n_note += 1
            if commit:
                await db.execute(
                    text(
                        "UPDATE cases SET debtor_notes=:n "
                        "WHERE case_number=:c AND tenant_id=:t"
                    ),
                    {"n": new, "c": code, "t": tid},
                )
        if commit:
            await db.commit()

        actie = "Weggeschreven" if commit else "Zou wegschrijven (dry-run)"
        print(f"{actie}: {n_note} notities + {n_alert} waarschuwingen")
        print(f"Overgeslagen (al aanwezig): {n_skip} | Ontbrekend: {n_missing}")
        if not commit:
            print("(dry-run — niets gewijzigd. Draai --commit om weg te schrijven.)")


def _selftest() -> None:
    assert clean("Debiteur is solvabel.<br /> Arno langs<br />") == (
        "Debiteur is solvabel.\nArno langs"
    )
    assert clean("a&nbsp;&amp;&nbsp;b") == "a & b"
    assert clean("<p>x</p>\r\n\r\n\r\ny") == "x\n\ny"
    assert clean("") == ""
    assert build_new_notes("HERKOMST", "Failliet", "info") == (
        "[BaseNet-waarschuwing] Failliet\n\nHERKOMST\n\n[BaseNet-notitie]\ninfo"
    )
    assert build_new_notes("HERKOMST", "", "info") == (
        "HERKOMST\n\n[BaseNet-notitie]\ninfo"
    )
    print("selftest OK")


def main() -> None:
    if "--selftest" in sys.argv:
        _selftest()
        return
    p = argparse.ArgumentParser(description="BaseNet pmemo/palert → dossiernotitie")
    p.add_argument("export_dir", help="Map met de uitgepakte BaseNet-XML-export")
    p.add_argument("--commit", action="store_true", help="Schrijf weg (anders dry-run)")
    args = p.parse_args()
    asyncio.run(run(args.export_dir, args.commit))


if __name__ == "__main__":
    main()
