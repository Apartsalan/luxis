"""S207: historische betalingsregelingen uit BaseNet alsnog importeren.

Zelfstandig (geen scripts.basenet-imports) zodat het in de productiecontainer
kan draaien, die alleen `app` + de prod-DB kent. Leest twee XML-bestanden uit
de BaseNet-export:
  * Incasso.xml                → systemid ↔ dossiernummer (inccode)
  * IncassoBetalingsRegeling.xml → termijnen (incbincassoid, incbdate, incbamount)

Fase 1b (S179) nam bewust alleen regelingen met ≥1 TOEKOMSTIGE termijn mee.
Demo 13-07 (Arsalan): alles moet letterlijk mee — óók afgeronde regelingen
horen zichtbaar te zijn onder Betalingen → Betalingsregelingen. Meting:
BaseNet heeft 37 regelingen, Luxis 13 → 24 ontbreken.

Status niet gokken maar METEN uit de echte betalingen op de zaak (payments,
sinds S179/S180/S195 compleet); som chronologisch tegen de termijnen afstrepen:
  * betaald ≥ regelingsom → 'completed', alle termijnen 'paid'
  * anders → 'defaulted'; termijnen chronologisch 'paid'/'partial'/'missed'
    ('missed', niet 'overdue' — historie mag het regeling-alarm niet triggeren)

Alleen zaken ZONDER bestaande regeling worden geraakt (de 13 actieve blijven
onaangeroerd). Idempotent via deterministische uuid5-id's + ON CONFLICT en een
notes-marker voor rollback.

    python /app/import_historical_arrangements.py --export-dir /pad --dry-run
    python /app/import_historical_arrangements.py --export-dir /pad --execute
    python /app/import_historical_arrangements.py --cleanup
"""

from __future__ import annotations

import argparse
import asyncio
import re
import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import async_session

# Zelfde uuid5-namespace als fase 1 (scripts/basenet/import_basenet.py) —
# geverifieerd: _uid("case", 714327) == de bestaande IN100197-zaak-id.
_NS = uuid.UUID("b47e5100-0000-4000-8000-000000000001")
_MARKER = "[BaseNet-import] historische regeling"
_ENTRY_RE = re.compile(r'<entry key="([^"]+)" value="([^"]*)"/>')
_BLOCK_RE = re.compile(r"<entrylist>(.*?)</entrylist>", re.S)


def _uid(kind: str, basenet_id: str) -> uuid.UUID:
    return uuid.uuid5(_NS, f"basenet:{kind}:{basenet_id}")


def _records(path: Path) -> list[dict]:
    text_data = path.read_text(encoding="utf-8", errors="replace")
    return [dict(_ENTRY_RE.findall(b)) for b in _BLOCK_RE.findall(text_data)]


def _find(export_dir: Path, needle: str) -> Path:
    for p in export_dir.glob("*.xml"):
        if needle.lower() in p.name.lower():
            return p
    raise SystemExit(f"XML-bestand met '{needle}' niet gevonden in {export_dir}")


def _build(export_dir: Path) -> list[dict]:
    inccode = {
        r["systemid"]: r.get("inccode", "").strip()
        for r in _records(_find(export_dir, "Incasso.xml"))
        if r.get("systemid")
    }
    termijnen: dict[str, list] = defaultdict(list)
    for r in _records(_find(export_dir, "IncassoBetalingsRegeling.xml")):
        iid = r.get("incbincassoid", "").strip()
        if not iid or not r.get("incbdate"):
            continue
        termijnen[iid].append(
            {
                "sysid": r["systemid"],
                "due_date": datetime.strptime(r["incbdate"].strip(), "%Y-%m-%d").date(),
                "amount": Decimal(r.get("incbamount", "0").strip() or "0"),
            }
        )
    out = []
    for iid, terms in termijnen.items():
        terms.sort(key=lambda t: (t["due_date"], t["sysid"]))
        out.append(
            {
                "incasso_sysid": iid,
                "inccode": inccode.get(iid, f"?{iid}"),
                "case_id": _uid("case", iid),
                "id": _uid("arr-hist", iid),
                "terms": terms,
                "total": sum((t["amount"] for t in terms), Decimal("0.00")),
            }
        )
    return out


async def run(export_dir: Path, execute: bool) -> None:
    arrangements = _build(export_dir)
    async with async_session() as db:
        tenant_id = (await db.execute(text("SELECT id FROM tenants LIMIT 1"))).scalar()
        existing_arr = {
            row[0] for row in await db.execute(text("SELECT case_id FROM payment_arrangements"))
        }
        existing_cases = {row[0] for row in await db.execute(text("SELECT id FROM cases"))}
        paid_by_case = {
            row[0]: row[1]
            for row in await db.execute(
                text("SELECT case_id, sum(amount) FROM payments WHERE is_active GROUP BY case_id")
            )
        }

        todo = [
            a
            for a in arrangements
            if a["case_id"] in existing_cases and a["case_id"] not in existing_arr
        ]
        skipped_existing = [a for a in arrangements if a["case_id"] in existing_arr]
        skipped_nocase = [a for a in arrangements if a["case_id"] not in existing_cases]

        print("=" * 74)
        print("S207 — historische betalingsregelingen", "(EXECUTE)" if execute else "(DRY RUN)")
        print("=" * 74)
        print(f"  regelingen in BaseNet-export : {len(arrangements)}")
        print(f"  al in Luxis (skip)           : {len(skipped_existing)}")
        print(f"  zonder dossier (skip)        : {len(skipped_nocase)}")
        print(f"  TE IMPORTEREN                : {len(todo)}")
        print()

        n_completed = n_defaulted = 0
        for a in sorted(todo, key=lambda a: a["inccode"]):
            paid = paid_by_case.get(a["case_id"], Decimal("0.00"))
            completed = paid >= a["total"] - Decimal("0.01")
            status = "completed" if completed else "defaulted"
            n_completed += completed
            n_defaulted += not completed
            print(
                f"  {a['inccode']}: {len(a['terms']):2d} termijnen x "
                f"{a['terms'][0]['amount']:>8}  totaal {a['total']:>9}  "
                f"betaald {paid:>9}  -> {status}"
            )
            if not execute:
                continue

            await db.execute(
                text(
                    "INSERT INTO payment_arrangements "
                    "(id, tenant_id, case_id, total_amount, installment_amount, frequency, "
                    " start_date, end_date, status, notes, created_at, updated_at) "
                    "VALUES (:id, :tenant, :case_id, :total, :inst, 'monthly', :start, :end, "
                    " :status, :notes, now(), now()) ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": a["id"],
                    "tenant": tenant_id,
                    "case_id": a["case_id"],
                    "total": a["total"],
                    "inst": a["terms"][0]["amount"],
                    "start": a["terms"][0]["due_date"],
                    "end": a["terms"][-1]["due_date"],
                    "status": status,
                    "notes": f"{_MARKER} incasso={a['incasso_sysid']} — status uit meting: "
                    f"betaald {paid} van {a['total']}",
                },
            )
            rest = paid
            for i, t in enumerate(a["terms"], start=1):
                if rest >= t["amount"]:
                    t_status, t_paid = "paid", t["amount"]
                elif rest > Decimal("0.00"):
                    t_status, t_paid = "partial", rest
                else:
                    t_status, t_paid = "missed", Decimal("0.00")
                rest = max(Decimal("0.00"), rest - t["amount"])
                await db.execute(
                    text(
                        "INSERT INTO payment_arrangement_installments "
                        "(id, tenant_id, arrangement_id, installment_number, due_date, amount, "
                        " paid_amount, status, created_at, updated_at) "
                        "VALUES (:id, :tenant, :arr, :nr, :due, :amount, :paid, :status, "
                        " now(), now()) ON CONFLICT (id) DO NOTHING"
                    ),
                    {
                        "id": _uid("arr-hist-term", t["sysid"]),
                        "tenant": tenant_id,
                        "arr": a["id"],
                        "nr": i,
                        "due": t["due_date"],
                        "amount": t["amount"],
                        "paid": t_paid,
                        "status": t_status,
                    },
                )

        if execute:
            await db.commit()
        print("-" * 74)
        print(f"  voldaan (completed): {n_completed}   gebroken (defaulted): {n_defaulted}")
        print(f"  {'GESCHREVEN' if execute else 'DRY RUN — niets geschreven'}")
        print("=" * 74)


async def cleanup() -> None:
    async with async_session() as db:
        inst = await db.execute(
            text(
                "DELETE FROM payment_arrangement_installments WHERE arrangement_id IN "
                "(SELECT id FROM payment_arrangements WHERE notes LIKE :m) RETURNING id"
            ),
            {"m": f"%{_MARKER}%"},
        )
        n_inst = len(inst.fetchall())
        arr = await db.execute(
            text("DELETE FROM payment_arrangements WHERE notes LIKE :m RETURNING id"),
            {"m": f"%{_MARKER}%"},
        )
        n_arr = len(arr.fetchall())
        await db.commit()
        print(f"Verwijderd: {n_arr} regelingen, {n_inst} termijnen")


def main() -> None:
    p = argparse.ArgumentParser(description="Historische regelingen importeren (S207)")
    p.add_argument("--export-dir", help="Map met de twee BaseNet-XML-bestanden")
    p.add_argument("--dry-run", action="store_true", help="Alleen rapporteren (default)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg")
    p.add_argument("--cleanup", action="store_true", help="Rollback: verwijder deze import")
    args = p.parse_args()
    if args.cleanup:
        asyncio.run(cleanup())
        return
    if not args.export_dir:
        p.error("--export-dir is verplicht (behalve bij --cleanup)")
    asyncio.run(run(Path(args.export_dir), execute=args.execute))


if __name__ == "__main__":
    main()
