"""BaseNet → Luxis import fase 2: correspondentie (.eml) → synced_emails.

Leest de uitgepakte IN-dossier-.eml-bestanden + de XML-metadata (Letter + Incasso)
en schrijft elke e-mail als SyncedEmail onder een apart import-e-mailaccount
(provider='import', dat de 5-min-sync overslaat).

Koppeling & scope (geverifieerd in S168, ontwerpdoc §7):
  - bestand-prefix = Letter.letterno  → richting (leinout) + systemid uit metadata
  - Letter.lepcode (== dossiermap)     → inccode → case_id = uuid5("basenet:case:{sysid}")
  - alleen IN-dossiers, alleen leinout 3 (uitgaand) / 4 (inkomend)
  - dedup + idempotent op deterministische id uuid5("basenet:email:{letterno}")

Draait ín de prod-container (net als fase 1):
    python -m scripts.basenet.import_emails --eml-dir /tmp/eml --xml-dir /tmp/basenet_xml --dry-run
    python -m scripts.basenet.import_emails --eml-dir /tmp/eml --xml-dir /tmp/basenet_xml --execute
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path

from sqlalchemy import text

from app.database import async_session

from scripts.basenet.import_basenet import _uid
from scripts.basenet.parse import parse_entity

IMPORT_PROVIDER = "import"
IMPORT_EMAIL_ADDRESS = "basenet-import@kestinglegal.nl"

# leinout → richting. 3=uitgaand, 4=inkomend (empirisch geverifieerd). 6 = geüpload
# document (geen correspondentie-flow) → overslaan.
_DIRECTION = {"3": "outbound", "4": "inbound"}

_CODE_RE = re.compile(r"^([A-Z]+\d+)")


@dataclass
class EmailStats:
    total_files: int = 0
    to_import: int = 0
    by_direction: dict[str, int] = field(default_factory=dict)
    skip_no_meta: int = 0          # letterno niet in XML-snapshot (nieuwer dan export)
    skip_direction: int = 0        # leinout niet 3/4 (bv. geüpload document)
    skip_not_in: int = 0           # lepcode niet IN-dossier
    orphan_no_case: int = 0        # lepcode zonder gekoppeld Luxis-dossier
    parse_errors: int = 0          # .eml onparseerbaar / lege body


def _parse_ledate(value: str) -> datetime:
    """BaseNet 'YYYY-MM-DD HH:MM:SS.0' → tz-aware datetime (UTC, consistent).

    Absolute tz is voor een archief onbelangrijk; consistentie telt (de fase-3-
    backfill ordent inbound vs outbound per dossier op deze datum)."""
    try:
        return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=UTC)


def build_case_index(xml_dir: str | Path) -> dict[str, uuid.UUID]:
    """inccode (IN-nummer) → Luxis case_id, exact zoals fase 1 de cases aanmaakte."""
    index: dict[str, uuid.UUID] = {}
    for rec in parse_entity(xml_dir, "Incasso").records:
        code = rec.get("inccode").strip()
        if code and rec.systemid:
            index[code] = _uid("case", rec.systemid)
    return index


def build_letter_index(xml_dir: str | Path) -> dict[str, dict]:
    """letterno → {leinout, systemid, ledate, lepcode, subject}."""
    index: dict[str, dict] = {}
    for rec in parse_entity(xml_dir, "Letter").records:
        no = rec.get("letterno").strip()
        if not no:
            continue
        index[no] = {
            "leinout": rec.get("leinout").strip(),
            "systemid": rec.systemid,
            "ledate": rec.get("ledate").strip(),
            "lepcode": rec.get("lepcode").strip(),
            "subject": rec.get("lesubject").strip(),
        }
    return index


def _addr_list(msg, header: str) -> list[str]:
    """E-mailadressen uit een header als JSON-vriendelijke lijst."""
    raw = msg.get_all(header, [])
    return [addr for _name, addr in getaddresses(raw) if addr]


def extract_eml(path: Path) -> dict | None:
    """Parse één .eml → velddict, of None bij een onbruikbaar bericht."""
    try:
        with open(path, "rb") as fh:
            msg = BytesParser(policy=policy.default).parse(fh)
    except Exception:
        return None

    body_html = body_text = ""
    try:
        part = msg.get_body(preferencelist=("html",))
        if part is not None:
            body_html = part.get_content()
    except Exception:
        body_html = ""
    try:
        part = msg.get_body(preferencelist=("plain",))
        if part is not None:
            body_text = part.get_content()
    except Exception:
        body_text = ""

    if not (body_html or body_text):
        return None  # niets bruikbaars om te bewaren

    from_pairs = getaddresses(msg.get_all("From", []))
    from_name, from_email = (from_pairs[0] if from_pairs else ("", ""))
    has_att = any(True for _ in msg.iter_attachments())
    snippet = (body_text or "").strip().replace("\n", " ")[:200]

    return {
        "from_email": (from_email or "")[:320],
        "from_name": (from_name or "")[:200],
        "to_emails": json.dumps(_addr_list(msg, "To")),
        "cc_emails": json.dumps(_addr_list(msg, "Cc")),
        "body_html": body_html or "",
        "body_text": body_text or "",
        "snippet": snippet,
        "has_attachments": has_att,
    }


def build_emails(eml_dir: str | Path, xml_dir: str | Path) -> tuple[list[dict], EmailStats]:
    """Bouw de volledige SyncedEmail-rijenset (nog zonder tenant/account-FK's)."""
    cases = build_case_index(xml_dir)
    letters = build_letter_index(xml_dir)
    stats = EmailStats()
    rows: list[dict] = []

    for eml in sorted(Path(eml_dir).rglob("*.eml")):
        stats.total_files += 1
        letterno = eml.name.split("_", 1)[0]
        meta = letters.get(letterno)
        if meta is None:
            stats.skip_no_meta += 1
            continue
        direction = _DIRECTION.get(meta["leinout"])
        if direction is None:
            stats.skip_direction += 1
            continue
        lepcode = meta["lepcode"] or _code_from_folder(eml)
        if not lepcode.startswith("IN"):
            stats.skip_not_in += 1
            continue
        case_id = cases.get(lepcode)
        if case_id is None:
            stats.orphan_no_case += 1
            continue
        parsed = extract_eml(eml)
        if parsed is None:
            stats.parse_errors += 1
            continue

        rows.append(
            {
                "id": _uid("email", letterno),
                "case_id": case_id,
                "provider_message_id": f"basenet:{meta['systemid']}",
                "subject": (meta["subject"] or parsed["body_text"][:80])[:1000],
                "direction": direction,
                "email_date": _parse_ledate(meta["ledate"]),
                **parsed,
            }
        )
        stats.by_direction[direction] = stats.by_direction.get(direction, 0) + 1

    stats.to_import = len(rows)
    return rows, stats


def _code_from_folder(eml: Path) -> str:
    m = _CODE_RE.match(eml.parent.name)
    return m.group(1) if m else ""


# ── Schrijven ────────────────────────────────────────────────────────────────

async def _get_or_create_import_account(db, tenant_id, user_id) -> uuid.UUID:
    row = (
        await db.execute(
            text(
                "SELECT id FROM email_accounts "
                "WHERE tenant_id=:t AND provider=:p LIMIT 1"
            ),
            {"t": tenant_id, "p": IMPORT_PROVIDER},
        )
    ).first()
    if row:
        return row[0]
    account_id = _uid("email_account", "basenet-import")
    await db.execute(
        text(
            "INSERT INTO email_accounts "
            "(id, tenant_id, user_id, provider, email_address, "
            " access_token_enc, refresh_token_enc, connected_at, created_at, updated_at) "
            "VALUES (:id, :t, :u, :p, :addr, :tok, :tok, now(), now(), now())"
        ),
        {
            "id": account_id,
            "t": tenant_id,
            "u": user_id,
            "p": IMPORT_PROVIDER,
            "addr": IMPORT_EMAIL_ADDRESS,
            "tok": b"basenet-import-placeholder",
        },
    )
    return account_id


async def _insert_missing(db, account_id, tenant_id, rows: list[dict]) -> int:
    existing = {
        i for (i,) in (await db.execute(text("SELECT id FROM synced_emails"))).all()
    }
    to_insert = [r for r in rows if r["id"] not in existing]
    for r in to_insert:
        await db.execute(
            text(
                "INSERT INTO synced_emails "
                "(id, tenant_id, email_account_id, case_id, provider_message_id, "
                " subject, from_email, from_name, to_emails, cc_emails, snippet, "
                " body_text, body_html, direction, is_read, has_attachments, "
                " is_dismissed, is_bounce, matched_by, email_date, synced_at, "
                " created_at, updated_at) "
                "VALUES (:id, :tenant_id, :account_id, :case_id, :provider_message_id, "
                " :subject, :from_email, :from_name, :to_emails, :cc_emails, :snippet, "
                " :body_text, :body_html, :direction, true, :has_attachments, "
                " false, false, 'basenet_import', :email_date, now(), now(), now()) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {**r, "tenant_id": tenant_id, "account_id": account_id},
        )
    return len(to_insert)


def _print_report(stats: EmailStats, execute: bool) -> None:
    print("=" * 64)
    print("BaseNet fase 2 — e-mailimport", "(EXECUTE)" if execute else "(DRY RUN)")
    print("=" * 64)
    print(f"  .eml-bestanden gevonden:        {stats.total_files:6d}")
    print(f"  Te importeren:                  {stats.to_import:6d}")
    for d, n in sorted(stats.by_direction.items()):
        print(f"     - {d:9s}                  {n:6d}")
    print("\n  Overgeslagen:")
    print(f"     nieuwer dan XML-snapshot:    {stats.skip_no_meta:6d}")
    print(f"     leinout niet 3/4 (document): {stats.skip_direction:6d}")
    print(f"     niet-IN-dossier:             {stats.skip_not_in:6d}")
    print(f"     geen gekoppeld dossier:      {stats.orphan_no_case:6d}")
    print(f"     onparseerbaar / lege body:   {stats.parse_errors:6d}")
    print("=" * 64)


async def run(eml_dir: str, xml_dir: str, execute: bool) -> None:
    rows, stats = build_emails(eml_dir, xml_dir)
    _print_report(stats, execute)
    if not execute:
        return

    async with async_session() as db:
        tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
        if len(tenants) != 1:
            raise SystemExit(f"Meerdere/geen tenants ({len(tenants)}).")
        tenant_id = tenants[0][0]
        users = (
            await db.execute(text("SELECT id FROM users WHERE tenant_id=:t ORDER BY created_at LIMIT 1"), {"t": tenant_id})
        ).all()
        if not users:
            raise SystemExit("Geen user gevonden voor het import-account.")
        user_id = users[0][0]

        account_id = await _get_or_create_import_account(db, tenant_id, user_id)
        n = await _insert_missing(db, account_id, tenant_id, rows)
        await db.commit()

    print("\n" + "=" * 64)
    print(f"GESCHREVEN (idempotent): {n} nieuwe e-mails onder import-account {account_id}")
    print("=" * 64)


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet → Luxis e-mailimport (fase 2)")
    p.add_argument("--eml-dir", required=True, help="Map met uitgepakte IN-.eml (dossiermappen)")
    p.add_argument("--xml-dir", required=True, help="Map met BaseNet-XML (Letter + Incasso)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    args = p.parse_args()
    asyncio.run(run(args.eml_dir, args.xml_dir, execute=args.execute))


if __name__ == "__main__":
    main()
