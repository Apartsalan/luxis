"""BaseNet → Luxis import-runner (fase 1b: betalingen + betalingsregelingen).

Twee brontypen uit `Xml_..._2400.zip`:
  * `*.IncassoBetalingAnders.xml`   → betalingen (Payment), met art. 6:44-toerekening
  * `*.IncassoBetalingsRegeling.xml` → betalingsregelingen (PaymentArrangement + termijnen)

Ontwerp (zoals fase 1, `import_basenet.py`):
  * Case-koppeling via `_uid("case", incpincassoid/incbincassoid)` — dezelfde uuid5 die
    fase 1 aan elk dossier gaf. Geen mapping-tabel nodig.
  * Idempotent: betalingen dragen een `[BaseNet-betaling systemid=..]`-marker in de
    omschrijving; regelingen/termijnen krijgen deterministische uuid5-id's (ON CONFLICT).
  * --dry-run schrijft NIETS en rapporteert: aantallen, reconciliatie tegen BaseNet's
    eigen betaal-cache (welke zaken hebben méér betalingen dan wij kunnen importeren),
    en de beslispunten (creditnota's + 'kosten uitsluiten'-vlag).

Betalingen lopen door de gedeelde `create_payment_for_case` (art. 6:44 + dossierrente),
maar met de workflow-hook + termijn-koppeling UIT: een historische betaling mag een
dossier niet automatisch op 'betaald' zetten of sluiten. Overbetaling t.o.v. het
(op de betaaldatum) openstaande bedrag wordt gecapt en per zaak gerapporteerd.

Regelingen: alleen termijnen mét een vervaldatum in de TOEKOMST worden opgenomen
(voorwaartse bewaking via de dagelijkse overdue-job) — verleden termijnen nemen we NIET
op, want de bron zegt niet welke daadwerkelijk betaald zijn (geen aanname).

Gebruik (draait ín de backend-container):
    python scripts/basenet/import_payments.py --export-dir /pad/naar/export --dry-run
    python scripts/basenet/import_payments.py --export-dir /pad/naar/export --execute
    python scripts/basenet/import_payments.py --cleanup   # rollback-vangnet
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.database import async_session

from scripts.basenet import mapping
from scripts.basenet.import_basenet import _uid  # zelfde uuid5-namespace als fase 1
from scripts.basenet.parse import parse_entity

_PAYMENT_MARKER = "[BaseNet-betaling systemid="


# ── Betalingen bouwen ─────────────────────────────────────────────────────────

@dataclass
class BuiltPayments:
    # per betaling: dict met case_id, amount, payment_date, description, ...
    payments: list[dict] = field(default_factory=list)
    # reconciliatie: BaseNet's eigen cache-totaal per incasso_sysid
    cache_by_sysid: dict[str, Decimal] = field(default_factory=dict)
    inccode_by_sysid: dict[str, str] = field(default_factory=dict)
    status_by_sysid: dict[str, str] = field(default_factory=dict)
    # diagnostiek
    skipped_incomplete: int = 0
    credits: list[str] = field(default_factory=list)          # descriptions
    exclude_costs: list[str] = field(default_factory=list)


def build_payments(export_dir, tenant_id: uuid.UUID) -> BuiltPayments:
    out = BuiltPayments()

    # BaseNet's eigen betaal-cache per zaak (reconciliatie-ijkpunt).
    for rec in parse_entity(export_dir, "Incasso").records:
        if not rec.systemid:
            continue
        klant = mapping._decimal(rec.get("cachedpaymentsklant")) or Decimal("0.00")
        anders = mapping._decimal(rec.get("cachedpaymentsanders")) or Decimal("0.00")
        admin = mapping._decimal(rec.get("cachedpaymentsadmin")) or Decimal("0.00")
        out.cache_by_sysid[rec.systemid] = klant + anders + admin
        out.inccode_by_sysid[rec.systemid] = (
            rec.get("inccode").strip() or rec.get("pcode").strip() or rec.systemid
        )
        out.status_by_sysid[rec.systemid] = rec.get("pstatus").strip() or "?"

    for rec in parse_entity(export_dir, "IncassoBetalingAnders").records:
        m = mapping.map_incassobetaling(rec)
        if m is None:
            out.skipped_incomplete += 1
            continue
        m["case_id"] = _uid("case", m["incasso_sysid"])
        m["tenant_id"] = tenant_id
        out.payments.append(m)
        if m["is_credit"]:
            out.credits.append(m["description"])
        if m["exclude_costs"]:
            out.exclude_costs.append(m["description"])

    return out


# ── Regelingen bouwen ─────────────────────────────────────────────────────────

@dataclass
class BuiltArrangements:
    # per zaak: {"case_id", "incasso_sysid", "inccode", "installments": [dict,...]}
    arrangements: list[dict] = field(default_factory=list)
    total_termijnen: int = 0
    future_termijnen: int = 0
    cases_with_termijnen: int = 0


def build_arrangements(export_dir, tenant_id: uuid.UUID, today: date) -> BuiltArrangements:
    out = BuiltArrangements()

    inccode_by_sysid: dict[str, str] = {}
    for rec in parse_entity(export_dir, "Incasso").records:
        if rec.systemid:
            inccode_by_sysid[rec.systemid] = (
                rec.get("inccode").strip() or rec.get("pcode").strip() or rec.systemid
            )

    by_case: dict[str, list[dict]] = defaultdict(list)
    for rec in parse_entity(export_dir, "IncassoBetalingsRegeling").records:
        m = mapping.map_betalingsregeling_termijn(rec)
        if m is None:
            continue
        out.total_termijnen += 1
        by_case[m["incasso_sysid"]].append(m)

    out.cases_with_termijnen = len(by_case)

    for incasso_sysid, termijnen in by_case.items():
        # Alleen toekomstige termijnen — verleden termijnen zeggen niet of ze betaald zijn.
        future = sorted(
            (t for t in termijnen if t["due_date"] >= today),
            key=lambda t: t["due_date"],
        )
        out.future_termijnen += len(future)
        if not future:
            continue

        installments = []
        for i, t in enumerate(future, start=1):
            installments.append(
                {
                    "id": _uid("installment", t["termijn_sysid"] or f"{incasso_sysid}:{i}"),
                    "tenant_id": tenant_id,
                    "installment_number": i,
                    "due_date": t["due_date"],
                    "amount": t["amount"],
                    "paid_amount": Decimal("0.00"),
                    "status": "pending",
                }
            )
        total = sum((t["amount"] for t in future), Decimal("0.00"))
        # Meest voorkomende termijnbedrag = het reguliere termijnbedrag.
        amounts = defaultdict(int)
        for t in future:
            amounts[t["amount"]] += 1
        installment_amount = max(amounts, key=amounts.get)

        out.arrangements.append(
            {
                "id": _uid("arrangement", incasso_sysid),
                "tenant_id": tenant_id,
                "case_id": _uid("case", incasso_sysid),
                "incasso_sysid": incasso_sysid,
                "inccode": inccode_by_sysid.get(incasso_sysid, incasso_sysid),
                "total_amount": total,
                "installment_amount": installment_amount,
                "start_date": min(t["due_date"] for t in future),
                "end_date": max(t["due_date"] for t in future),
                "installments": installments,
            }
        )

    return out


# ── Rapport ───────────────────────────────────────────────────────────────────

async def _existing_case_ids(db) -> set:
    return {i for (i,) in (await db.execute(text("SELECT id FROM cases"))).all()}


async def _already_imported_sysids(db) -> set:
    """systemids van betalingen die we al eerder importeerden (idempotentie)."""
    rows = (
        await db.execute(
            text("SELECT description FROM payments WHERE description LIKE :m"),
            {"m": f"%{_PAYMENT_MARKER}%"},
        )
    ).all()
    out = set()
    for (descr,) in rows:
        if descr and _PAYMENT_MARKER in descr:
            out.add(descr.split(_PAYMENT_MARKER, 1)[1].rstrip("]").strip())
    return out


def _print_report(
    pay: BuiltPayments,
    arr: BuiltArrangements,
    existing_case_ids: set,
    already: set,
    execute: bool,
) -> None:
    line = "=" * 68
    print(line)
    print(
        "Betalingen + regelingen — "
        + ("EXECUTE (schrijft na deze controle)" if execute else "DRY RUN (schrijft niets)")
    )
    print(line)

    # Splits betalingen op koppelbaarheid + reeds-geïmporteerd.
    importable, unmatched, dup = [], [], 0
    for p in pay.payments:
        sysid = p["description"].split(_PAYMENT_MARKER, 1)[1].rstrip("]").strip()
        if sysid in already:
            dup += 1
            continue
        if p["case_id"] not in existing_case_ids:
            unmatched.append(p)
        else:
            importable.append(p)

    print("\n── BETALINGEN ──")
    print(f"  Records in bron:                 {len(pay.payments) + pay.skipped_incomplete}")
    print(f"  Onvolledig (geen datum/bedrag):  {pay.skipped_incomplete}")
    print(f"  Al eerder geïmporteerd (skip):   {dup}")
    print(f"  Zonder dossier in Luxis (skip):  {len(unmatched)}")
    if unmatched:
        print(f"     bv. {', '.join(p['incasso_sysid'] for p in unmatched[:8])}")
    print(f"  TE IMPORTEREN:                   {len(importable)}")
    tot_import = sum((p["amount"] for p in importable), Decimal("0.00"))
    print(f"  Som te importeren:               EUR {tot_import}")

    print("\n  Beslispunten (met Arsalan):")
    print(f"    Creditnota's ('credit' in notitie): {len(pay.credits)}")
    for d in pay.credits[:6]:
        print(f"       - {d}")
    print(f"    'Kosten uitsluiten'-vlag (BaseNet): {len(pay.exclude_costs)}")

    # Reconciliatie tegen BaseNet's eigen cache: welke zaken hebben méér?
    import_by_sysid: dict[str, Decimal] = defaultdict(Decimal)
    for p in importable:
        import_by_sysid[p["incasso_sysid"]] += p["amount"]
    cache_only = []  # zaken met cache-betaling maar 0 importeerbare records
    undercount = []  # zaken waar cache > wat we importeren
    for sysid, cached in pay.cache_by_sysid.items():
        if cached <= Decimal("0.00"):
            continue
        imported = import_by_sysid.get(sysid, Decimal("0.00"))
        if imported == 0:
            cache_only.append((pay.inccode_by_sysid.get(sysid, sysid), cached, pay.status_by_sysid.get(sysid, "?")))
        elif abs(cached - imported) > Decimal("0.01"):
            undercount.append((pay.inccode_by_sysid.get(sysid, sysid), cached, imported))

    cache_only_lopend = [c for c in cache_only if c[2] == "Lopend"]
    print("\n  Reconciliatie tegen BaseNet's betaal-cache (eerlijkheid):")
    print(f"    Zaken met cache-betaling zónder importeerbaar record: {len(cache_only)}")
    print(f"       waarvan LOPEND (blijven te-open ogen):             {len(cache_only_lopend)}")
    som_cache_only_lopend = sum((c[1] for c in cache_only_lopend), Decimal("0.00"))
    print(f"       som daarvan:                                       EUR {som_cache_only_lopend}")
    for code, cached, _st in sorted(cache_only_lopend, key=lambda x: -x[1])[:8]:
        print(f"          - {code}: BaseNet-cache EUR {cached} (geen dated record → handmatig)")
    print(f"    Zaken waar cache ≠ import (deelbetalingen elders):    {len(undercount)}")
    for code, cached, imported in sorted(undercount, key=lambda x: -(x[1] - x[2]))[:6]:
        print(f"          - {code}: cache EUR {cached}  vs  import EUR {imported}")

    print("\n── BETALINGSREGELINGEN ──")
    print(f"  Termijnen in bron:               {arr.total_termijnen}")
    print(f"  Zaken met termijnen:             {arr.cases_with_termijnen}")
    print(f"  Toekomstige termijnen:           {arr.future_termijnen}")
    importable_arr = [a for a in arr.arrangements if a["case_id"] in existing_case_ids]
    print(f"  Regelingen TE IMPORTEREN (zaak bestaat, ≥1 toekomstige termijn): {len(importable_arr)}")
    for a in sorted(importable_arr, key=lambda a: a["start_date"]):
        eerste = a["installments"][0]["due_date"]
        print(
            f"     - {a['inccode']}: {len(a['installments'])} termijnen, "
            f"eerste {eerste}, totaal EUR {a['total_amount']}"
        )
    missing_case = [a for a in arr.arrangements if a["case_id"] not in existing_case_ids]
    if missing_case:
        print(f"  Regelingen zonder dossier in Luxis (skip): {len(missing_case)}")

    print(line)


# ── Schrijven ─────────────────────────────────────────────────────────────────

async def _write_payments(db, tenant_id, importable: list[dict]) -> tuple[int, list[tuple]]:
    """Boek elke betaling via de gedeelde helper (art. 6:44 + dossierrente),
    workflow-hook + termijn-koppeling UIT. Chronologisch per zaak zodat de
    rente-knip van latere betalingen de eerdere ziet. Geeft (aantal, caps)."""
    from app.collections.schemas import PaymentCreate
    from app.collections.service import create_payment_for_case

    by_case: dict[uuid.UUID, list[dict]] = defaultdict(list)
    for p in importable:
        by_case[p["case_id"]].append(p)

    written = 0
    caps: list[tuple] = []
    for case_id, payments in by_case.items():
        for p in sorted(payments, key=lambda x: x["payment_date"]):
            data = PaymentCreate(
                amount=p["amount"],
                payment_date=p["payment_date"],
                description=p["description"],
                payment_method=p["payment_method"],
            )
            payment = await create_payment_for_case(
                db,
                tenant_id,
                case_id,
                data,
                user_id=None,
                _skip_installment_link=True,
                _skip_workflow_hook=True,
                cap_to_outstanding=True,
            )
            if payment.amount < p["amount"]:
                caps.append((p["description"], p["amount"], payment.amount))
            written += 1
    return written, caps


async def _write_arrangements(db, importable_arr: list[dict]) -> int:
    written = 0
    for a in importable_arr:
        await db.execute(
            text(
                "INSERT INTO payment_arrangements "
                "(id, tenant_id, case_id, total_amount, installment_amount, frequency, "
                " start_date, end_date, status, notes, created_at, updated_at) "
                "VALUES (:id, :tenant_id, :case_id, :total_amount, :installment_amount, "
                " 'monthly', :start_date, :end_date, 'active', :notes, now(), now()) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": a["id"],
                "tenant_id": a["tenant_id"],
                "case_id": a["case_id"],
                "total_amount": a["total_amount"],
                "installment_amount": a["installment_amount"],
                "start_date": a["start_date"],
                "end_date": a["end_date"],
                "notes": f"[BaseNet-import] regeling incasso={a['incasso_sysid']} "
                f"— alleen toekomstige termijnen overgenomen",
            },
        )
        for inst in a["installments"]:
            await db.execute(
                text(
                    "INSERT INTO payment_arrangement_installments "
                    "(id, tenant_id, arrangement_id, installment_number, due_date, amount, "
                    " paid_amount, status, created_at, updated_at) "
                    "VALUES (:id, :tenant_id, :arrangement_id, :installment_number, :due_date, "
                    " :amount, :paid_amount, :status, now(), now()) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {**inst, "arrangement_id": a["id"]},
            )
        written += 1
    return written


# ── Rollback-vangnet ──────────────────────────────────────────────────────────

async def cleanup() -> None:
    """Verwijder alle via deze import geschreven betalingen + regelingen."""
    async with async_session() as db:
        inst = await db.execute(
            text(
                "DELETE FROM payment_arrangement_installments WHERE arrangement_id IN "
                "(SELECT id FROM payment_arrangements WHERE notes LIKE :m) RETURNING id"
            ),
            {"m": "%[BaseNet-import] regeling%"},
        )
        n_inst = len(inst.fetchall())
        arr = await db.execute(
            text("DELETE FROM payment_arrangements WHERE notes LIKE :m RETURNING id"),
            {"m": "%[BaseNet-import] regeling%"},
        )
        n_arr = len(arr.fetchall())
        pay = await db.execute(
            text("DELETE FROM payments WHERE description LIKE :m RETURNING case_id"),
            {"m": f"%{_PAYMENT_MARKER}%"},
        )
        case_ids = {row[0] for row in pay.fetchall()}
        await db.commit()

        # Case-financials herstellen voor geraakte dossiers.
        from app.collections.service import _refresh_case_financials

        tenant_id = (await db.execute(text("SELECT id FROM tenants LIMIT 1"))).scalar()
        for cid in case_ids:
            await _refresh_case_financials(db, tenant_id, cid)
        await db.commit()
        print(
            f"Verwijderd — betalingen: {len(case_ids)} zaken geraakt, "
            f"regelingen: {n_arr}, termijnen: {n_inst}"
        )


# ── Runner ────────────────────────────────────────────────────────────────────

async def run(export_dir: str, execute: bool, tenant_arg: str | None) -> None:
    async with async_session() as db:
        if tenant_arg:
            tenant_id = uuid.UUID(tenant_arg)
        else:
            tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
            if len(tenants) != 1:
                raise SystemExit(f"Meerdere/geen tenants ({len(tenants)}); geef --tenant-id op.")
            tenant_id = tenants[0][0]

        today = date.today()
        pay = build_payments(export_dir, tenant_id)
        arr = build_arrangements(export_dir, tenant_id, today)

        existing_case_ids = await _existing_case_ids(db)
        already = await _already_imported_sysids(db)
        _print_report(pay, arr, existing_case_ids, already, execute=execute)

        if not execute:
            return

        importable = [
            p
            for p in pay.payments
            if p["case_id"] in existing_case_ids
            and p["description"].split(_PAYMENT_MARKER, 1)[1].rstrip("]").strip() not in already
        ]
        importable_arr = [a for a in arr.arrangements if a["case_id"] in existing_case_ids]

        n_pay, caps = await _write_payments(db, tenant_id, importable)
        n_arr = await _write_arrangements(db, importable_arr)
        await db.commit()

        print("\n" + "=" * 68)
        print("GESCHREVEN (idempotent):")
        print(f"  Betalingen geboekt:  {n_pay}")
        print(f"  Regelingen geboekt:  {n_arr}")
        if caps:
            print(f"  Gecapt op openstaand ({len(caps)} — overschot niet geboekt):")
            for descr, orig, capped in caps[:10]:
                print(f"     - {descr[:50]}: EUR {orig} → EUR {capped}")
        print("=" * 68)


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet → Luxis import (fase 1b: betalingen + regelingen)")
    p.add_argument("--export-dir", help="Map met uitgepakte BaseNet-XML")
    p.add_argument("--dry-run", action="store_true", help="Alleen rapporteren (default)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    p.add_argument("--cleanup", action="store_true", help="Verwijder alle geïmporteerde betalingen+regelingen")
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
