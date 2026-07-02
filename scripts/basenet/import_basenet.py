"""BaseNet → Luxis import-runner (fase 1: relaties + dossiers + vorderingen).

Deterministische UUID's (uuid5) → idempotent zonder mapping-tabel of migratie.
Cross-referenties (dossier → opdrachtgever/wederpartij) worden in-memory opgelost
uit de relatie-export. Geld = Decimal, datums = date-objecten.

Gebruik (draait ín de backend-container):
    python scripts/basenet/import_basenet.py --export-dir /pad/naar/export --dry-run
    python scripts/basenet/import_basenet.py --export-dir /pad/naar/export --execute

--dry-run schrijft NIETS en rapporteert: aantallen, onopgeloste referenties,
overlap met bestaande data (relaties op naam, dossiers op nummer) en financiële
drift (som vorderingen vs BaseNet-hoofdsom). --execute schrijft idempotent weg.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import async_session

from scripts.basenet import mapping
from scripts.basenet.parse import parse_entity

# Vaste namespace zodat dezelfde BaseNet-record altijd dezelfde Luxis-UUID krijgt
# (idempotente her-runs + resolvbare cross-referenties).
NS = uuid.UUID("b47e5100-0000-4000-8000-000000000001")


def _uid(kind: str, basenet_id: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"basenet:{kind}:{basenet_id}")


def _norm(name: str | None) -> str:
    """Normaliseer een naam voor overlap-detectie (lower, spaties samengevouwen)."""
    return re.sub(r"\s+", " ", (name or "").strip().lower())


# ── Opgebouwde import-set (puur in geheugen, vóór schrijven) ──────────────────

@dataclass
class BuiltImport:
    tenant_id: uuid.UUID
    contacts: list[dict] = field(default_factory=list)          # Contact-velden + id
    cases: list[dict] = field(default_factory=list)             # Case-velden + id
    claims: list[dict] = field(default_factory=list)            # Claim-velden + id
    # Diagnostiek voor het dry-run-rapport
    cases_without_client: list[str] = field(default_factory=list)   # inccodes
    cases_without_opposing: list[str] = field(default_factory=list)
    cases_without_date: list[str] = field(default_factory=list)     # geen date_opened
    orphan_claims: int = 0                                       # incassoline zonder dossier
    financial_drift: list[tuple[str, Decimal, Decimal]] = field(default_factory=list)
    truncated: int = 0                                           # afgekapte te lange strings


def build_import(export_dir: str | Path, tenant_id: uuid.UUID) -> BuiltImport:
    """Lees de export en bouw de volledige import-set in geheugen (schrijft niets)."""
    out = BuiltImport(tenant_id=tenant_id)

    # 1. Relaties (company + person) → contacts. Bouw resolvers op rcode én systemid.
    id_by_rcode: dict[str, uuid.UUID] = {}
    id_by_sysid: dict[str, uuid.UUID] = {}
    type_by_sysid: dict[str, str] = {}

    for suffix, mapper in (
        ("Company", mapping.map_company),
        ("Person", mapping.map_person),
        ("Contact", mapping.map_contactpersoon),  # contactpersonen (rtype C)
    ):
        for rec in parse_entity(export_dir, suffix).records:
            if not rec.systemid:
                continue
            cid = _uid("contact", rec.systemid)
            fields = mapper(rec)
            fields["id"] = cid
            fields["tenant_id"] = tenant_id
            out.contacts.append(fields)
            id_by_sysid[rec.systemid] = cid
            type_by_sysid[rec.systemid] = fields["contact_type"]
            rcode = rec.get("rcode").strip()
            if rcode:
                id_by_rcode[rcode] = cid

    # 2. Dossiers (incasso) → cases. Client = prcode (rcode), wederpartij = incwederid (systemid).
    case_by_incasso_sysid: dict[str, dict] = {}
    cached_by_sysid: dict[str, Decimal] = {}
    for rec in parse_entity(export_dir, "Incasso").records:
        if not rec.systemid:
            continue
        inccode = rec.get("inccode").strip() or rec.get("pcode").strip()
        client_id = id_by_rcode.get(rec.get("prcode").strip())
        opposing_sysid = rec.get("incwederid").strip()
        opposing_id = id_by_sysid.get(opposing_sysid)

        if client_id is None:
            out.cases_without_client.append(inccode)
            continue  # client_id is NOT NULL → dossier zonder opdrachtgever kan niet
        if opposing_id is None and opposing_sysid:
            out.cases_without_opposing.append(inccode)

        debtor_type = mapping.resolve_debtor_type(type_by_sysid.get(opposing_sysid))
        interest_type = mapping.resolve_interest_type(debtor_type)

        fields = mapping.map_incasso(rec, debtor_type=debtor_type, interest_type=interest_type)
        if fields["date_opened"] is None:
            out.cases_without_date.append(inccode)
            continue  # date_opened is NOT NULL → zonder datum kan het dossier niet
        fields["id"] = _uid("case", rec.systemid)
        fields["tenant_id"] = tenant_id
        fields["client_id"] = client_id
        fields["opposing_party_id"] = opposing_id
        out.cases.append(fields)
        case_by_incasso_sysid[rec.systemid] = fields
        cached_by_sysid[rec.systemid] = mapping._decimal(rec.get("cachedhoofdsom")) or Decimal("0.00")

    # 3. Vorderingen (incassoline) → claims. case via inclincassoid (= incasso systemid).
    #    Tel hoofdsom + rente per dossier voor de total_principal-vulling + de check.
    principal_by_case: dict[str, Decimal] = {}
    interest_by_case: dict[str, Decimal] = {}
    for rec in parse_entity(export_dir, "IncassoLine").records:
        incasso_sysid = rec.get("inclincassoid").strip()
        case_fields = case_by_incasso_sysid.get(incasso_sysid)
        if case_fields is None:
            out.orphan_claims += 1
            continue
        fields = mapping.map_incassoline(rec)
        # default_date is verplicht (NOT NULL) — zonder datum kan de claim niet.
        if fields["default_date"] is None:
            out.orphan_claims += 1
            continue
        fields["id"] = _uid("claim", rec.systemid or f"{incasso_sysid}:{len(out.claims)}")
        fields["tenant_id"] = tenant_id
        fields["case_id"] = case_fields["id"]
        out.claims.append(fields)
        principal_by_case[incasso_sysid] = (
            principal_by_case.get(incasso_sysid, Decimal("0.00")) + fields["principal_amount"]
        )
        interest = mapping._decimal(rec.get("inclcalculatedinterest")) or Decimal("0.00")
        interest_by_case[incasso_sysid] = interest_by_case.get(incasso_sysid, Decimal("0.00")) + interest

    # Vul total_principal = som van de vorderingen (hoofdsom) per dossier.
    for sysid, principal in principal_by_case.items():
        case_by_incasso_sysid[sysid]["total_principal"] = principal

    # Financiële validatie: BaseNet cachedhoofdsom moet == hoofdsom + rente (bewijst
    # dat we alle vorderingen correct hebben ingelezen). Alleen ECHTE mismatches melden.
    for sysid, cached in cached_by_sysid.items():
        principal = principal_by_case.get(sysid, Decimal("0.00"))
        interest = interest_by_case.get(sysid, Decimal("0.00"))
        if abs(cached - (principal + interest)) > Decimal("0.01"):
            code = case_by_incasso_sysid[sysid]["case_number"] or sysid
            out.financial_drift.append((code, cached, principal + interest))

    return out


# ── Rapport ──────────────────────────────────────────────────────────────────

async def _existing_overlap(db, built: BuiltImport) -> dict:
    """Overlap met al bestaande data: relaties op genormaliseerde naam, dossiers op nummer."""
    import_ids = {c["id"] for c in built.contacts}
    existing_contacts = (await db.execute(text("SELECT id, name FROM contacts"))).all()
    # Namen van bestaande relaties die NIET door onszelf zijn geïmporteerd.
    existing_names = {
        _norm(name) for cid, name in existing_contacts if cid not in import_ids
    }
    contact_name_overlap = [
        c["name"] for c in built.contacts if _norm(c["name"]) in existing_names
    ]

    existing_case_numbers = {
        n for (n,) in (await db.execute(text("SELECT case_number FROM cases"))).all()
    }
    existing_case_ids = {i for (i,) in (await db.execute(text("SELECT id FROM cases"))).all()}
    case_number_collision = [
        c["case_number"]
        for c in built.cases
        if c["case_number"] in existing_case_numbers and c["id"] not in existing_case_ids
    ]

    return {
        "contact_name_overlap": contact_name_overlap,
        "case_number_collision": case_number_collision,
        "existing_case_ids": existing_case_ids,
    }


def _print_report(built: BuiltImport, overlap: dict) -> None:
    print("=" * 64)
    print("BaseNet-import — DRY RUN (er wordt niets geschreven)")
    print("=" * 64)
    print(f"\nTenant: {built.tenant_id}\n")
    print("Te importeren:")
    print(f"  Relaties (contacts):   {len(built.contacts):5d}")
    print(f"  Dossiers  (cases):     {len(built.cases):5d}")
    print(f"  Vorderingen (claims):  {len(built.claims):5d}")

    print("\nAandachtspunten:")
    print(f"  Dossiers ZONDER opdrachtgever (overgeslagen): {len(built.cases_without_client)}")
    if built.cases_without_client:
        print(f"     bv. {', '.join(built.cases_without_client[:8])}")
    print(f"  Dossiers zonder (herkende) wederpartij:       {len(built.cases_without_opposing)}")
    print(f"  Dossiers zonder startdatum (overgeslagen):    {len(built.cases_without_date)}")
    print(f"  Vorderingen zonder dossier/datum (overgesl.): {built.orphan_claims}")
    print(f"  Te lange velden afgekapt op kolomlimiet:      {built.truncated}")

    print("\nOverlap met bestaande Luxis-data:")
    print(f"  Relaties met zelfde naam (mogelijk dubbel):   {len(overlap['contact_name_overlap'])}")
    if overlap["contact_name_overlap"]:
        for n in overlap["contact_name_overlap"][:10]:
            print(f"     - {n}")
    print(f"  Dossiernummers die al bestaan (BOTSING!):     {len(overlap['case_number_collision'])}")
    if overlap["case_number_collision"]:
        print(f"     bv. {', '.join(overlap['case_number_collision'][:8])}")

    print("\nFinanciële validatie (BaseNet cached == hoofdsom + rente):")
    print(f"  Dossiers met ECHTE mismatch (mogelijk dataverlies): {len(built.financial_drift)}")
    for code, cached, summed in built.financial_drift[:10]:
        print(f"     - {code}: BaseNet-cached €{cached}  vs  hoofdsom+rente €{summed}")
    if not built.financial_drift:
        print("  ✓ alle dossiers kloppen — geen vorderingen verloren")

    print("\nLET OP (fase 1): betalingen worden NOG NIET geïmporteerd → het openstaand")
    print("saldo op deze archief-dossiers is overschat tot fase 1b. Dossiers komen")
    print("binnen als 'afgesloten' (terminale status) → geen automatisering.")
    print("=" * 64)


# ── Lengtelimieten (buitenlandse adressen e.d. passen soms niet) ─────────────

async def _fetch_limits(db) -> dict[str, dict[str, int]]:
    """{tabel: {kolom: max_len}} voor varchar-kolommen van de doeltabellen."""
    rows = (
        await db.execute(
            text(
                "SELECT table_name, column_name, character_maximum_length "
                "FROM information_schema.columns "
                "WHERE table_name IN ('contacts','cases','claims') "
                "AND character_maximum_length IS NOT NULL"
            )
        )
    ).all()
    limits: dict[str, dict[str, int]] = {}
    for table, col, maxlen in rows:
        limits.setdefault(table, {})[col] = maxlen
    return limits


def _cap_rows(rows: list[dict], table_limits: dict[str, int]) -> int:
    """Kap te lange stringwaarden af op de kolomlimiet. Geeft aantal afgekapte terug."""
    truncated = 0
    for row in rows:
        for col, val in row.items():
            limit = table_limits.get(col)
            if limit and isinstance(val, str) and len(val) > limit:
                row[col] = val[:limit]
                truncated += 1
    return truncated


# ── Schrijven ────────────────────────────────────────────────────────────────

async def _insert_missing(db, table_name: str, rows: list[dict], existing_ids: set) -> int:
    """Insert alleen rijen waarvan de id nog niet bestaat. Geeft aantal nieuw."""
    to_insert = [r for r in rows if r["id"] not in existing_ids]
    for row in to_insert:
        cols = list(row.keys())
        placeholders = ", ".join(f":{c}" for c in cols)
        collist = ", ".join(cols)
        await db.execute(
            text(
                f"INSERT INTO {table_name} ({collist}, created_at, updated_at) "
                f"VALUES ({placeholders}, now(), now()) ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    return len(to_insert)


# Marker die elke geïmporteerde rij herkenbaar maakt (voor --cleanup / rollback).
_MARKER = "[BaseNet-import]"


async def cleanup() -> None:
    """Verwijder ALLE via deze import geschreven rijen (herkend aan de marker).
    Rollback-vangnet — draait claims → cases → contacts in FK-veilige volgorde."""
    async with async_session() as db:
        claims = await db.execute(
            text(
                "DELETE FROM claims WHERE case_id IN "
                "(SELECT id FROM cases WHERE debtor_notes LIKE :m) RETURNING id"
            ),
            {"m": f"%{_MARKER}%"},
        )
        n_claims = len(claims.fetchall())
        cases = await db.execute(
            text("DELETE FROM cases WHERE debtor_notes LIKE :m RETURNING id"),
            {"m": f"%{_MARKER}%"},
        )
        n_cases = len(cases.fetchall())
        contacts = await db.execute(
            text("DELETE FROM contacts WHERE notes LIKE :m RETURNING id"),
            {"m": f"%{_MARKER}%"},
        )
        n_contacts = len(contacts.fetchall())
        await db.commit()
        print(f"Verwijderd — vorderingen: {n_claims}, dossiers: {n_cases}, relaties: {n_contacts}")


async def run(export_dir: str, execute: bool, tenant_arg: str | None) -> None:
    async with async_session() as db:
        # Tenant bepalen (geen aanname): expliciet, of de enige tenant.
        if tenant_arg:
            tenant_id = uuid.UUID(tenant_arg)
        else:
            tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
            if len(tenants) != 1:
                raise SystemExit(
                    f"Meerdere/geen tenants ({len(tenants)}); geef --tenant-id op."
                )
            tenant_id = tenants[0][0]

        built = build_import(export_dir, tenant_id)

        # Kap te lange strings af op de kolomlimieten (bv. buitenlandse postcodes).
        limits = await _fetch_limits(db)
        built.truncated = (
            _cap_rows(built.contacts, limits.get("contacts", {}))
            + _cap_rows(built.cases, limits.get("cases", {}))
            + _cap_rows(built.claims, limits.get("claims", {}))
        )

        overlap = await _existing_overlap(db, built)
        _print_report(built, overlap)

        if not execute:
            return

        # Blokkeer bij een dossiernummer-botsing (zou de unique constraint breken).
        if overlap["case_number_collision"]:
            raise SystemExit(
                "\nAFGEBROKEN: dossiernummer-botsing gevonden — los eerst op "
                "(zie rapport). Er is niets geschreven."
            )

        existing_case_ids = overlap["existing_case_ids"]
        existing_contact_ids = {
            i for (i,) in (await db.execute(text("SELECT id FROM contacts"))).all()
        }
        existing_claim_ids = {
            i for (i,) in (await db.execute(text("SELECT id FROM claims"))).all()
        }

        n_contacts = await _insert_missing(db, "contacts", built.contacts, existing_contact_ids)
        n_cases = await _insert_missing(db, "cases", built.cases, existing_case_ids)
        n_claims = await _insert_missing(db, "claims", built.claims, existing_claim_ids)
        await db.commit()

        print("\n" + "=" * 64)
        print("GESCHREVEN (idempotent):")
        print(f"  Relaties nieuw:    {n_contacts}")
        print(f"  Dossiers nieuw:    {n_cases}")
        print(f"  Vorderingen nieuw: {n_claims}")
        print("=" * 64)


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet → Luxis import (fase 1)")
    p.add_argument("--export-dir", help="Map met uitgepakte BaseNet-XML (verplicht, behalve --cleanup)")
    p.add_argument("--dry-run", action="store_true", help="Alleen rapporteren (default)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    p.add_argument("--cleanup", action="store_true", help="Verwijder alle geïmporteerde rijen")
    p.add_argument("--tenant-id", default=None, help="Tenant-UUID (default: de enige tenant)")
    args = p.parse_args()
    if args.cleanup:
        asyncio.run(cleanup())
    else:
        if not args.export_dir:
            p.error("--export-dir is verplicht (behalve bij --cleanup)")
        asyncio.run(run(args.export_dir, execute=args.execute, tenant_arg=args.tenant_id))


if __name__ == "__main__":
    main()
