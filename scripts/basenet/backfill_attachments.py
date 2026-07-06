"""BaseNet fase 3: bijlagen-backfill.

De fase-2-import (import_emails.py) zette alleen `has_attachments=true` op de mails;
de bijlagen zelf zijn nooit uitgepakt. Dit script herstelt dat in twee fasen:

  extract  — LOKAAL. Leest de .eml's rechtstreeks uit de dossier-zips (geen 8,5 GB
             uitpakken), haalt de bijlagen eruit, schrijft ze naar een staging-map
             + `manifest.json`. Raakt geen database. `--dry-run` telt alleen.
  load     — IN de prod-container. Leest manifest + staging, verifieert per bijlage
             de bijbehorende `synced_email`, kopieert het bestand naar het
             email_attachments-volume (exact het pad dat de live Graph-sync gebruikt)
             en schrijft een idempotent `email_attachments`-record.

Koppeling (geen fuzzy matching): bestand-prefix = `Letter.letterno` →
`email_id = uuid5(NS, "basenet:email:{letterno}")`, precies zoals fase 2 de mails
aanmaakte. Bijlagen van .eml's die fase 2 oversloeg (niet-IN, document-richting,
geen dossier) matchen simpelweg geen synced_email en worden in `load` overgeslagen.

Inline vs echte bijlage: `has_attachments` telt ook inline handtekening-logootjes mee.
Standaard importeert `load` alleen ECHTE bijlagen (Content-Disposition: attachment,
of met bestandsnaam en niet-inline). `--include-inline` neemt ook inline mee.

Gebruik:
    # 1. lokaal meten (niets schrijven)
    python -m scripts.basenet.backfill_attachments extract --zip-dir . --dry-run
    # 2. lokaal uitpakken naar staging
    python -m scripts.basenet.backfill_attachments extract --zip-dir . --out /tmp/att_staging
    # 3. staging + manifest naar VPS rsync'en, dan in de container:
    python -m scripts.basenet.backfill_attachments load --staging /tmp/att_staging --dry-run
    python -m scripts.basenet.backfill_attachments load --staging /tmp/att_staging --execute
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from pathlib import Path

# NB: identiek aan import_basenet._uid — hier ingelijnd zodat de extract-fase LOKAAL
# draait zonder de DB-gekoppelde `app`-import mee te slepen. Waarden MOETEN gelijk
# blijven, anders matcht email_id niet met de fase-2-import.
# ponytail: 2-regel pure functie dupliceren < heel import_basenet lokaal binnentrekken.
_NS = uuid.UUID("b47e5100-0000-4000-8000-000000000001")


def _uid(kind: str, basenet_id: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"basenet:{kind}:{basenet_id}")


MANIFEST_NAME = "manifest.json"


def _is_real_attachment(part) -> bool:
    """Echte bijlage vs inline handtekening-logootje.

    Inline (Content-Disposition: inline) met een image/* type is vrijwel altijd een
    logo of tracking-pixel in de handtekening — geen document dat Lisanne wil openen.
    Alles met dispositie 'attachment' of met een echte bestandsnaam en niet-inline
    telt als echt.
    """
    disp = (part.get_content_disposition() or "").lower()
    if disp == "attachment":
        return True
    if disp == "inline":
        return False
    # Geen expliciete dispositie: houd het als het een bestandsnaam heeft en geen image is.
    return bool(part.get_filename()) and not part.get_content_type().startswith("image/")


@dataclass
class ExtractStats:
    zips: int = 0
    eml_files: int = 0
    eml_with_parts: int = 0
    real_parts: int = 0
    inline_parts: int = 0
    real_bytes: int = 0
    inline_bytes: int = 0
    empty_parts: int = 0
    parse_errors: int = 0
    matched_parts: int = 0   # echte bijlagen waarvan de mail op prod bestaat
    matched_bytes: int = 0
    matched_emails: set = field(default_factory=set)
    by_ext: Counter = field(default_factory=Counter)
    samples: list[dict] = field(default_factory=list)


def _iter_eml(zip_paths: list[Path]):
    """Yield (letterno, raw_bytes) voor elke .eml in de zips."""
    for zp in zip_paths:
        with zipfile.ZipFile(zp) as zf:
            for info in zf.infolist():
                name = info.filename
                if info.is_dir() or not name.lower().endswith(".eml"):
                    continue
                letterno = Path(name).name.split("_", 1)[0]
                if not letterno.isdigit():
                    continue
                yield letterno, zf.read(info)


def extract(
    zip_dir: str,
    out: str | None,
    include_inline: bool,
    dry_run: bool,
    known_emails: str | None = None,
) -> ExtractStats:
    zip_paths = sorted(Path(zip_dir).glob("1601*.zip"))
    stats = ExtractStats(zips=len(zip_paths))
    manifest: list[dict] = []
    out_dir = Path(out) if out else None
    # Optioneel: set van bestaande synced_email-id's (van prod) om de ECHTE match
    # vooraf te tellen — zo weten we vóór het uploaden hoeveel Lisanne echt ziet.
    known = None
    if known_emails:
        known = {ln.strip() for ln in Path(known_emails).read_text().splitlines() if ln.strip()}

    for letterno, raw in _iter_eml(zip_paths):
        stats.eml_files += 1
        try:
            msg = BytesParser(policy=policy.default).parsebytes(raw)
        except Exception:
            stats.parse_errors += 1
            continue

        email_id = _uid("email", letterno)
        has_part = False
        for idx, part in enumerate(msg.iter_attachments()):
            payload = part.get_payload(decode=True)
            if not payload:
                stats.empty_parts += 1
                continue
            real = _is_real_attachment(part)
            size = len(payload)
            if real:
                stats.real_parts += 1
                stats.real_bytes += size
            else:
                stats.inline_parts += 1
                stats.inline_bytes += size
            if not real and not include_inline:
                continue
            has_part = True
            matched = known is not None and str(email_id) in known
            if matched:
                stats.matched_parts += 1
                stats.matched_bytes += size
                stats.matched_emails.add(str(email_id))
            # Met --known-emails schrijven we alleen wat écht bij een mail hoort —
            # scheelt gigabytes staging + upload. Zonder known: alles (load filtert).
            if known is not None and not matched:
                continue

            filename = part.get_filename() or f"bijlage_{idx}"
            ext = os.path.splitext(filename)[1].lower()
            stats.by_ext[ext or "(geen)"] += 1
            # Deterministisch → idempotente her-runs zonder mapping-tabel.
            stored_filename = f"{_uid('attachment', f'{letterno}:{idx}')}{ext}"
            entry = {
                "letterno": letterno,
                "email_id": str(email_id),
                "provider_attachment_id": f"basenet:{letterno}:{idx}",
                "filename": filename[:500],
                "stored_filename": stored_filename,
                "content_type": part.get_content_type(),
                "file_size": size,
                "inline": not real,
            }
            manifest.append(entry)
            if len(stats.samples) < 25:
                stats.samples.append(
                    {k: entry[k] for k in ("letterno", "filename", "content_type", "file_size", "inline")}
                )

            if out_dir and not dry_run:
                dest = out_dir / str(email_id) / stored_filename
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(payload)

        if has_part:
            stats.eml_with_parts += 1

    if out_dir and not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

    _print_extract(stats, include_inline, dry_run, out)
    return stats


def _print_extract(stats: ExtractStats, include_inline: bool, dry_run: bool, out: str | None) -> None:
    print("=" * 68)
    print("BaseNet fase 3 — bijlagen-backfill (extract)", "(DRY RUN)" if dry_run else "")
    print("=" * 68)
    print(f"  zips gescand:                 {stats.zips:8d}")
    print(f"  .eml-bestanden:               {stats.eml_files:8d}")
    print(f"  .eml met meegenomen bijlage:  {stats.eml_with_parts:8d}")
    print(f"  onparseerbaar:                {stats.parse_errors:8d}")
    print(f"  lege delen (0 bytes):         {stats.empty_parts:8d}")
    print("  ---")
    print(f"  ECHTE bijlagen:               {stats.real_parts:8d}  ({stats.real_bytes/1e6:8.1f} MB)")
    print(f"  inline (logo/handtekening):   {stats.inline_parts:8d}  ({stats.inline_bytes/1e6:8.1f} MB)")
    if stats.matched_parts or stats.matched_emails:
        print("  ---")
        print(f"  >> HOORT BIJ EEN BESTAANDE MAIL (wat Lisanne echt krijgt):")
        print(f"     bijlagen:                  {stats.matched_parts:8d}  ({stats.matched_bytes/1e6:8.1f} MB)")
        print(f"     verdeeld over mails:       {len(stats.matched_emails):8d}")
    print(f"  -> import-modus: {'ECHT + INLINE' if include_inline else 'alleen ECHTE bijlagen'}")
    print("  ---")
    print("  Top bestandstypen (meegenomen):")
    for ext, n in stats.by_ext.most_common(12):
        print(f"     {ext:12s} {n:6d}")
    print("\n  Steekproef (eerste 25 meegenomen bijlagen):")
    for s in stats.samples:
        tag = "inline" if s["inline"] else "ECHT"
        print(f"     [{tag:6s}] {s['content_type']:28s} {s['file_size']:9d}  {s['filename'][:60]}")
    if out and not dry_run:
        print(f"\n  Geschreven naar: {out}  (+ {MANIFEST_NAME})")
    print("=" * 68)


# ── losse dossier-documenten → case_files ("Bestanden"-tab) ──────────────────
# De zip-mappen bevatten naast .eml ook losse bestanden (PDF's, .msg, Excel): de
# BaseNet-"documenten" (leinout=6). Die zijn nooit geïmporteerd. Koppeling exact als
# de mails: bestand-prefix = Letter.letterno -> lepcode (dossier) -> case_id. Geen
# fuzzy matching; letterno's die niet in de XML-snapshot staan worden overgeslagen.

_DOC_DIRECTION = {"3": "uitgaand", "4": "inkomend"}  # 6 = geüpload document -> None


@dataclass
class DocStats:
    zips: int = 0
    loose_files: int = 0
    skip_no_letterno: int = 0
    skip_no_meta: int = 0       # letterno niet in XML-snapshot
    skip_not_in: int = 0        # lepcode geen IN-dossier
    skip_no_case: int = 0       # IN-dossier zonder Luxis-case
    matched: int = 0
    matched_bytes: int = 0
    matched_cases: set = field(default_factory=set)
    by_ext: Counter = field(default_factory=Counter)
    samples: list[dict] = field(default_factory=list)


def _build_letter_case_index(xml_dir: str):
    """(letterno -> {leinout,lepcode,subject}, inccode -> case_id-str). Lokaal-only."""
    from scripts.basenet.parse import parse_entity  # puur, geen app/DB

    letters: dict[str, dict] = {}
    for rec in parse_entity(xml_dir, "Letter").records:
        no = rec.get("letterno").strip()
        if no:
            letters[no] = {
                "leinout": rec.get("leinout").strip(),
                "lepcode": rec.get("lepcode").strip(),
                "subject": rec.get("lesubject").strip(),
            }
    cases: dict[str, str] = {}
    for rec in parse_entity(xml_dir, "Incasso").records:
        code = rec.get("inccode").strip()
        if code and rec.systemid:
            cases[code] = str(_uid("case", rec.systemid))
    return letters, cases


def extract_docs(
    zip_dir: str, xml_dir: str, out: str | None, dry_run: bool, known_cases: str | None
) -> DocStats:
    import mimetypes

    letters, cases = _build_letter_case_index(xml_dir)
    known = None
    if known_cases:
        known = {ln.strip() for ln in Path(known_cases).read_text().splitlines() if ln.strip()}
    zip_paths = sorted(Path(zip_dir).glob("1601*.zip"))
    stats = DocStats(zips=len(zip_paths))
    manifest: list[dict] = []
    out_dir = Path(out) if out else None

    for zp in zip_paths:
        with zipfile.ZipFile(zp) as zf:
            for info in zf.infolist():
                name = info.filename
                if info.is_dir() or name.lower().endswith(".eml"):
                    continue
                stats.loose_files += 1
                base = Path(name).name
                letterno = base.split("_", 1)[0]
                if not letterno.isdigit():
                    stats.skip_no_letterno += 1
                    continue
                meta = letters.get(letterno)
                if meta is None:
                    stats.skip_no_meta += 1
                    continue
                if not meta["lepcode"].startswith("IN"):
                    stats.skip_not_in += 1
                    continue
                case_id = cases.get(meta["lepcode"])
                if case_id is None:
                    stats.skip_no_case += 1
                    continue

                # Bestandsnaam ontdaan van de letterno-prefix, voor de UI.
                display = base.split("_", 1)[1] if "_" in base else base
                ext = os.path.splitext(base)[1].lower()
                content_type = mimetypes.types_map.get(ext, "application/octet-stream")
                stored_filename = f"{_uid('casefile', name)}{ext}"
                matched = known is None or case_id in known
                stats.by_ext[ext or "(geen)"] += 1
                if matched:
                    stats.matched += 1
                    stats.matched_bytes += info.file_size
                    stats.matched_cases.add(case_id)
                    if len(stats.samples) < 25:
                        stats.samples.append(
                            {"lepcode": meta["lepcode"], "filename": display[:60],
                             "ext": ext, "size": info.file_size,
                             "dir": _DOC_DIRECTION.get(meta["leinout"], "-")}
                        )
                if known is not None and not matched:
                    continue

                manifest.append({
                    "letterno": letterno,
                    "case_id": case_id,
                    "original_filename": display[:500],
                    "stored_filename": stored_filename,
                    "content_type": content_type,
                    "file_size": info.file_size,
                    "document_direction": _DOC_DIRECTION.get(meta["leinout"]),
                    "description": (meta["subject"] or None),
                })
                if out_dir and not dry_run:
                    dest = out_dir / case_id / stored_filename
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(zf.read(info))

    if out_dir and not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

    _print_docs(stats, dry_run, out)
    return stats


def _print_docs(stats: DocStats, dry_run: bool, out: str | None) -> None:
    print("=" * 68)
    print("BaseNet fase 3b — losse documenten -> Bestanden", "(DRY RUN)" if dry_run else "")
    print("=" * 68)
    print(f"  zips gescand:                 {stats.zips:8d}")
    print(f"  losse bestanden (geen .eml):  {stats.loose_files:8d}")
    print(f"  overgeslagen: geen letterno   {stats.skip_no_letterno:8d}")
    print(f"                niet in XML     {stats.skip_no_meta:8d}")
    print(f"                geen IN-dossier {stats.skip_not_in:8d}")
    print(f"                geen Luxis-case {stats.skip_no_case:8d}")
    print("  ---")
    print(f"  >> TE IMPORTEREN (bij een bestaand dossier):")
    print(f"     documenten:                {stats.matched:8d}  ({stats.matched_bytes/1e6:8.1f} MB)")
    print(f"     verdeeld over dossiers:    {len(stats.matched_cases):8d}")
    print("  ---")
    print("  Top bestandstypen:")
    for ext, n in stats.by_ext.most_common(12):
        print(f"     {ext:12s} {n:6d}")
    print("\n  Steekproef (eerste 25):")
    for s in stats.samples:
        print(f"     [{s['dir']:8s}] {s['ext']:6s} {s['size']:9d}  {s['lepcode']:10s} {s['filename']}")
    if out and not dry_run:
        print(f"\n  Geschreven naar: {out}")
    print("=" * 68)


async def load_docs(staging: str, execute: bool) -> None:
    from sqlalchemy import text

    from app.database import async_session

    staging_dir = Path(staging)
    manifest = json.loads((staging_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    base = Path("/app/uploads")

    matched = written = skipped_no_case = skipped_exists = missing_file = 0
    async with async_session() as db:
        case_tenant = {
            str(i): t
            for i, t in (await db.execute(text("SELECT id, tenant_id FROM cases"))).all()
        }
        tenant_id = next(iter(set(case_tenant.values())), None)
        user_row = (
            await db.execute(
                text("SELECT id FROM users WHERE tenant_id=:t ORDER BY created_at LIMIT 1"),
                {"t": tenant_id},
            )
        ).first() if tenant_id else None
        uploaded_by = user_row[0] if user_row else None
        existing = {
            sf for (sf,) in (
                await db.execute(text("SELECT stored_filename FROM case_files"))
            ).all()
        }

        for m in manifest:
            tenant = case_tenant.get(m["case_id"])
            if tenant is None:
                skipped_no_case += 1
                continue
            matched += 1
            if m["stored_filename"] in existing:
                skipped_exists += 1
                continue
            src = staging_dir / m["case_id"] / m["stored_filename"]
            if not src.exists():
                missing_file += 1
                continue
            if not execute:
                written += 1
                continue
            dest = base / str(tenant) / m["case_id"] / m["stored_filename"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            await db.execute(
                text(
                    "INSERT INTO case_files "
                    "(id, tenant_id, case_id, original_filename, stored_filename, "
                    " file_size, content_type, document_direction, description, "
                    " uploaded_by, is_active, created_at, updated_at) "
                    "VALUES (:id, :t, :c, :ofn, :sf, :fs, :ct, :dir, :descr, :ub, true, now(), now()) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": _uid("casefile_row", m["stored_filename"]),
                    "t": tenant,
                    "c": m["case_id"],
                    "ofn": m["original_filename"],
                    "sf": m["stored_filename"],
                    "fs": m["file_size"],
                    "ct": m["content_type"],
                    "dir": m["document_direction"],
                    "descr": m["description"],
                    "ub": uploaded_by,
                },
            )
            written += 1
        if execute:
            await db.commit()

    print("=" * 68)
    print("BaseNet fase 3b — losse documenten (load)", "(EXECUTE)" if execute else "(DRY RUN)")
    print("=" * 68)
    print(f"  manifest-regels:              {len(manifest):8d}")
    print(f"  gematcht aan een dossier:     {matched:8d}")
    print(f"  geen dossier:                 {skipped_no_case:8d}")
    print(f"  al aanwezig (idempotent):     {skipped_exists:8d}")
    print(f"  bestand mist in staging:      {missing_file:8d}")
    print(f"  {'GESCHREVEN' if execute else 'zou schrijven'}:                 {written:8d}")
    print("=" * 68)


# ── load (in de prod-container) ──────────────────────────────────────────────

async def load(staging: str, execute: bool) -> None:
    from sqlalchemy import text

    from app.database import async_session

    staging_dir = Path(staging)
    manifest = json.loads((staging_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    base = Path("/app/uploads/email_attachments")

    matched = written = skipped_no_email = skipped_exists = missing_file = 0
    async with async_session() as db:
        # Alle geïmporteerde mail-id's + hun tenant, in één keer.
        rows = (await db.execute(text("SELECT id, tenant_id FROM synced_emails"))).all()
        email_tenant = {str(i): t for i, t in rows}
        existing = {
            (str(e), pid)
            for e, pid in (
                await db.execute(
                    text("SELECT synced_email_id, provider_attachment_id FROM email_attachments")
                )
            ).all()
        }

        for m in manifest:
            tenant_id = email_tenant.get(m["email_id"])
            if tenant_id is None:
                skipped_no_email += 1
                continue
            matched += 1
            if (m["email_id"], m["provider_attachment_id"]) in existing:
                skipped_exists += 1
                continue
            src = staging_dir / m["email_id"] / m["stored_filename"]
            if not src.exists():
                missing_file += 1
                continue
            if not execute:
                written += 1
                continue
            dest = base / str(tenant_id) / m["email_id"] / m["stored_filename"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            await db.execute(
                text(
                    "INSERT INTO email_attachments "
                    "(id, tenant_id, synced_email_id, provider_attachment_id, filename, "
                    " stored_filename, content_type, file_size, downloaded_at) "
                    "VALUES (:id, :t, :e, :pid, :fn, :sf, :ct, :fs, now()) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": _uid("attachment_row", m["provider_attachment_id"]),
                    "t": tenant_id,
                    "e": m["email_id"],
                    "pid": m["provider_attachment_id"],
                    "fn": m["filename"],
                    "sf": m["stored_filename"],
                    "ct": m["content_type"],
                    "fs": m["file_size"],
                },
            )
            written += 1
        if execute:
            await db.commit()

    print("=" * 68)
    print("BaseNet fase 3 — bijlagen-backfill (load)", "(EXECUTE)" if execute else "(DRY RUN)")
    print("=" * 68)
    print(f"  manifest-regels:              {len(manifest):8d}")
    print(f"  gematcht aan een mail:        {matched:8d}")
    print(f"  geen bijbehorende mail:       {skipped_no_email:8d}")
    print(f"  al aanwezig (idempotent):     {skipped_exists:8d}")
    print(f"  bestand mist in staging:      {missing_file:8d}")
    print(f"  {'GESCHREVEN' if execute else 'zou schrijven'}:                 {written:8d}")
    print("=" * 68)


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet bijlagen-backfill (fase 3)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="Lokaal: bijlagen uit de zips halen")
    pe.add_argument("--zip-dir", required=True, help="Map met de 1601*.zip dossier-zips")
    pe.add_argument("--out", help="Staging-map om bijlagen + manifest te schrijven")
    pe.add_argument("--include-inline", action="store_true", help="Ook inline logo's meenemen")
    pe.add_argument("--dry-run", action="store_true", help="Alleen tellen, niets schrijven")
    pe.add_argument("--known-emails", help="Bestand met bestaande synced_email-id's (1 per regel) om de echte match te tellen")

    pl = sub.add_parser("load", help="In-container: staging → volume + DB")
    pl.add_argument("--staging", required=True, help="Staging-map (van extract, op de VPS)")
    pl.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")

    ped = sub.add_parser("extract-docs", help="Lokaal: losse documenten uit de zips halen")
    ped.add_argument("--zip-dir", required=True, help="Map met de 1601*.zip dossier-zips")
    ped.add_argument("--xml-dir", required=True, help="Map met BaseNet-XML (Letter + Incasso)")
    ped.add_argument("--out", help="Staging-map om documenten + manifest te schrijven")
    ped.add_argument("--dry-run", action="store_true", help="Alleen tellen, niets schrijven")
    ped.add_argument("--known-cases", help="Bestand met bestaande case-id's (1 per regel)")

    pld = sub.add_parser("load-docs", help="In-container: documenten-staging → volume + case_files")
    pld.add_argument("--staging", required=True, help="Documenten-staging-map (op de VPS)")
    pld.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")

    args = p.parse_args()
    if args.cmd == "extract":
        extract(args.zip_dir, args.out, args.include_inline, args.dry_run, args.known_emails)
    elif args.cmd == "extract-docs":
        extract_docs(args.zip_dir, args.xml_dir, args.out, args.dry_run, args.known_cases)
    elif args.cmd == "load-docs":
        asyncio.run(load_docs(args.staging, args.execute))
    else:
        asyncio.run(load(args.staging, args.execute))


if __name__ == "__main__":
    main()
