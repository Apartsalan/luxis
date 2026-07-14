"""BaseNet → Luxis import-runner (fase 2: kantoorfacturen + regels + betalingen).

De kantoorfacturen die Lisanne aan haar opdrachtgevers stuurde. Alleen de
definitieve, conflictvrije facturen worden geïmporteerd; derdengelden-/
verrekenposten, Mollie/kop-conflicten en concepten blijven eruit. Recept en
onderbouwing: docs/research/S201-facturatie-recept.md.

Deterministische UUID5 (zelfde namespace als fase 1) → idempotent zonder
mapping-tabel. Relaties (op debiteurcode) en dossiers (op IN-projectcode) worden
gematcht op de al geïmporteerde fase-1-data; er worden GEEN nieuwe relaties of
dossiers aangemaakt. D-projecten hebben nog geen dossier in Luxis en komen
bewust binnen met case_id = NULL (koppelbaar zodra de D-dossiers geïmporteerd
zijn — de projectcode blijft in de marker staan).

Geld = Decimal + ROUND_HALF_UP. BaseNet-kopbedragen worden NIET herberekend
(bewaart o.a. de bekende 1-cent van factuur 100532). Betaaldatums worden niet
verzonnen: alleen 20 door Mollie bevestigde iDEAL-betalingen krijgen een echte
datum, de overige 305 krijgen payment_date = NULL ("Datum onbekend").

Gebruik (draait ín de backend-container, op de VPS voor de echte prod-match):
    python scripts/basenet/import_invoices.py --export-dir /pad/export --dry-run
    python scripts/basenet/import_invoices.py --export-dir /pad/export --execute

--dry-run (default) schrijft NIETS en dwingt alle controlepoorten af.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import async_session
from scripts.basenet.import_basenet import _MARKER, _uid
from scripts.basenet.parse import parse_entity

# ── Vaste classificatie-constanten (bewezen tegen de export, zie recept) ──────

# Product "Verrekening incassodossiers" = derdengelden/doorlopende cliëntgelden.
DERDENGELDEN_PRODUCT = "100013"
# Twee verreken-/correctieposten zonder 100013-regel die tóch tot de
# derdengelden-/verrekenfamilie horen (samen sluit de bruto op −€90.718,21).
DERDENGELDEN_EXTRA = {"100242", "100363"}
# Mollie zegt betaald, maar de factuurkop staat volledig open → menselijke
# reconciliatie (Lisanne/boekhouding), niet automatisch importeren.
MOLLIE_CONFLICT = {"100314", "100321", "100316", "100342", "100332", "100441", "100533"}
# Grens waarop een openstaande factuur "te laat" i.p.v. "verzonden" heet.
OVERDUE_BEFORE = date(2026, 7, 12)
# De gebruiker onder wiens naam de historische betalingen worden geboekt.
IMPORT_USER_EMAIL = "seidony@kestinglegal.nl"

CENT = Decimal("0.01")


def _dec(s: str | None) -> Decimal:
    return Decimal((s or "0").strip() or "0")


def _date(s: str | None) -> date | None:
    """BaseNet-datum ('2024-11-29 16:39:40.0' of '2024-12-20') → date."""
    s = (s or "").strip()
    return date.fromisoformat(s[:10]) if len(s) >= 10 else None


# ── Opgebouwde import-set (in geheugen, vóór schrijven) ───────────────────────


@dataclass
class BuiltInvoices:
    tenant_id: uuid.UUID
    invoices: list[dict] = field(default_factory=list)
    lines: list[dict] = field(default_factory=list)
    payments: list[dict] = field(default_factory=list)
    # Partitie-telling (alle 567 koppen)
    groups: dict[str, list[str]] = field(default_factory=dict)
    orphan_lines: int = 0                       # regels zonder factuurkop
    # Diagnostiek / poorten
    unresolved_contacts: list[str] = field(default_factory=list)  # invnr
    in_cases_matched: int = 0
    d_contact_only: int = 0
    credit_links: int = 0
    payments_dated: int = 0
    payments_undated: int = 0
    line_formula_mismatch: list[str] = field(default_factory=list)
    total_mismatch: list[tuple[str, Decimal, Decimal]] = field(default_factory=list)
    known_one_cent: list[str] = field(default_factory=list)


def _is_derdengelden(invnr: str, inv_lines: list) -> bool:
    if invnr in DERDENGELDEN_EXTRA:
        return True
    return any(ln.get("inlprodnr").strip() == DERDENGELDEN_PRODUCT for ln in inv_lines)


def _status_for(kop, invoice_type: str, due: date | None) -> str:
    paid = kop.get("invpaidstatus").strip()
    if invoice_type == "credit_note":
        return "paid" if paid == "1" else "sent"
    if paid == "1":
        return "paid"
    if paid == "9":            # nul-factuur, volledig geneutraliseerd
        return "paid"
    # open: te laat vs verzonden
    if due is not None and due < OVERDUE_BEFORE:
        return "overdue"
    return "sent"


def build_invoices(
    export_dir: str | Path,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    contact_by_rcode: dict[str, uuid.UUID],
    case_id_by_number: dict[str, uuid.UUID],
) -> BuiltInvoices:
    """Lees de export en bouw de volledige factuur-import in geheugen.

    contact_by_rcode / case_id_by_number = al bestaande fase-1-data. Pure functie
    (schrijft niets) zodat classificatie + bedragen los van de DB testbaar zijn.
    """
    out = BuiltInvoices(tenant_id=tenant_id)

    kop = parse_entity(export_dir, "OutgoingInvoice").records
    line_recs = parse_entity(export_dir, "OutgoingInvoiceLine").records
    products = parse_entity(export_dir, "Product").records
    payments = parse_entity(export_dir, "Payment").records
    mollie = parse_entity(export_dir, "MolliePaymentEntity").records

    ledger_by_prodnr = {p.get("prodnr").strip(): p.get("prodexledger").strip() for p in products}
    mollie_ref_by_payid = {m.get("payment_id").strip(): m.get("mollie_id").strip() for m in mollie}

    # Regels groeperen op factuurnummer (inlinv = invnr). Regels zonder inlinv
    # zijn losse conceptregels zonder kop → tellen als orphan.
    lines_by_invnr: dict[str, list] = {}
    for ln in line_recs:
        inv = ln.get("inlinv").strip()
        if inv:
            lines_by_invnr.setdefault(inv, []).append(ln)
        else:
            out.orphan_lines += 1

    kop_by_sysid = {r.systemid: r for r in kop}
    invnr_of_sysid = {r.systemid: r.get("invnr").strip() for r in kop}

    # 20 door Mollie bevestigde betalingen (payment_status=4) → factuur-systemid → invnr.
    mollie_paid: dict[str, tuple[date | None, str]] = {}   # invnr → (datum, mollie-ref)
    for p in payments:
        if p.get("payment_status").strip() != "4":
            continue
        inv = kop_by_sysid.get(p.get("entitysysid").strip())
        if inv is None:
            continue
        invnr = inv.get("invnr").strip()
        mollie_paid[invnr] = (_date(p.get("insertdate")), mollie_ref_by_payid.get(p.systemid, ""))

    # ── Classificeer alle 567 koppen ──────────────────────────────────────────
    groups: dict[str, list[str]] = {k: [] for k in ("auto", "mollie7", "wip", "leeg", "derdengelden")}
    for r in kop:
        invnr = r.get("invnr").strip()
        ilines = lines_by_invnr.get(invnr, [])
        if _is_derdengelden(invnr, ilines):
            groups["derdengelden"].append(invnr)
        elif invnr in MOLLIE_CONFLICT:
            groups["mollie7"].append(invnr)
        elif r.get("invstatus").strip() in ("5", "6"):
            groups["auto"].append(invnr)
        elif not ilines and _dec(r.get("invtobepaid")) == 0:
            groups["leeg"].append(invnr)
        else:
            groups["wip"].append(invnr)
    out.groups = groups

    # ── Bouw de auto-groep ────────────────────────────────────────────────────
    # Origineel → creditnummer (BaseNet zet invcredinv op de ORIGINELE factuur).
    credit_original_of: dict[str, str] = {}   # creditnr → origineel-systemid
    for r in kop:
        cred = r.get("invcredinv").strip()
        if cred:
            credit_original_of[cred] = r.systemid

    kop_by_invnr = {r.get("invnr").strip(): r for r in kop}

    for invnr in groups["auto"]:
        r = kop_by_invnr[invnr]
        sysid = r.systemid
        ilines = lines_by_invnr.get(invnr, [])
        inv_type = "credit_note" if r.get("invdebcred").strip() == "2" else "invoice"

        invoice_date = _date(r.get("invdatinv"))
        # Creditnota's hebben géén invduedate → terugval op factuurdatum.
        due = _date(r.get("invduedate")) or invoice_date

        # Bedragen: exact uit de bron, NIET herberekenen.
        subtotal = sum((_dec(ln.get("inlaantal")) * _dec(ln.get("inlprice"))).quantize(CENT, ROUND_HALF_UP)
                       for ln in ilines) or Decimal("0.00")
        btw_amount = (sum(_dec(ln.get("inlpricetot")) for ln in ilines) - subtotal) if ilines else Decimal("0.00")
        total = _dec(r.get("invtobepaid"))
        # Poort: kop == som regels (op de bekende 1-cent van 100532 na).
        if abs((subtotal + btw_amount) - total) > CENT:
            out.total_mismatch.append((invnr, subtotal + btw_amount, total))
        elif (subtotal + btw_amount) != total:
            out.known_one_cent.append(invnr)

        btw_pct = Decimal("21.00") if any(ln.get("inlvatcode").strip() == "1a" for ln in ilines) else Decimal("0.00")

        # Relatie (verplicht) via debiteurcode.
        contact_id = contact_by_rcode.get(r.get("invrcode").strip())
        if contact_id is None:
            out.unresolved_contacts.append(invnr)

        # Dossier: IN-project → bestaand dossier; D-project → NULL.
        pcode = r.get("invpcode").strip()
        case_id = None
        if pcode.startswith("IN"):
            case_id = case_id_by_number.get(pcode)
            if case_id is not None:
                out.in_cases_matched += 1
        elif pcode.startswith("D"):
            out.d_contact_only += 1

        status = _status_for(r, inv_type, due)
        paid_date = None
        marker = f"{_MARKER} factuur={invnr} · systemid={sysid} · project={pcode or '-'}"

        out.invoices.append({
            "id": _uid("invoice", sysid),
            "tenant_id": tenant_id,
            "invoice_number": invnr,
            "invoice_type": inv_type,
            "status": status,
            "linked_invoice_id": None,      # creditnota's later gekoppeld
            "contact_id": contact_id,
            "case_id": case_id,
            "invoice_date": invoice_date,
            "due_date": due,
            "paid_date": paid_date,
            "subtotal": subtotal,
            "btw_percentage": btw_pct,
            "btw_amount": btw_amount,
            "total": total,
            "reference": pcode or None,
            "notes": marker,
            "is_active": True,
        })

        for i, ln in enumerate(ilines, start=1):
            netto = (_dec(ln.get("inlaantal")) * _dec(ln.get("inlprice"))).quantize(CENT, ROUND_HALF_UP)
            # Poort: BaseNet-regelformule ROUND_HALF_UP(aantal×prijs×1,21) voor 1a.
            expect = (netto * Decimal("1.21")).quantize(CENT, ROUND_HALF_UP) if ln.get("inlvatcode").strip() == "1a" else netto
            if abs(expect - _dec(ln.get("inlpricetot"))) > CENT:
                out.line_formula_mismatch.append(f"{invnr}#{i}")
            out.lines.append({
                "id": _uid("invoice_line", ln.systemid),
                "tenant_id": tenant_id,
                "invoice_id": _uid("invoice", sysid),
                "line_number": i,
                "description": ln.get("inldescinv").strip(),
                "quantity": _dec(ln.get("inlaantal")),
                "unit_price": _dec(ln.get("inlprice")),
                "line_total": netto,
                "btw_percentage": Decimal("21.00") if ln.get("inlvatcode").strip() == "1a" else Decimal("0.00"),
                "gl_account_code": ledger_by_prodnr.get(ln.get("inlprodnr").strip()) or None,
            })

        # Betaling: alleen voor betaalde GEWONE facturen (niet credit, niet open).
        betaald = total - _dec(r.get("invopenamount"))
        if inv_type == "invoice" and r.get("invpaidstatus").strip() == "1" and betaald > 0:
            if invnr in mollie_paid:
                pdate, ref = mollie_paid[invnr]
                method, reference = "ideal", (ref or "Mollie")
                out.payments_dated += 1
            else:
                pdate, method, reference = None, "unknown", "BaseNet memoriaal"
                out.payments_undated += 1
            out.payments.append({
                "id": _uid("invoice_payment", sysid),
                "tenant_id": tenant_id,
                "invoice_id": _uid("invoice", sysid),
                "amount": betaald,
                "payment_date": pdate,
                "payment_method": method,
                "reference": reference,
                "description": None,
                "created_by": user_id,
            })

    # ── Creditnota's aan hun origineel koppelen ───────────────────────────────
    auto_invnrs = set(groups["auto"])
    for inv in out.invoices:
        if inv["invoice_type"] != "credit_note":
            continue
        orig_sysid = credit_original_of.get(inv["invoice_number"])
        if orig_sysid and invnr_of_sysid.get(orig_sysid) in auto_invnrs:
            inv["linked_invoice_id"] = _uid("invoice", orig_sysid)
            out.credit_links += 1

    return out


# ── Relaties/dossiers uit de bestaande fase-1-data resolven ───────────────────


def _rcode_to_contact(export_dir: str | Path) -> dict[str, uuid.UUID]:
    """Reconstrueer debiteurcode → contact-UUID exact zoals fase-1 dat deed
    (deterministische _uid('contact', relatie-systemid))."""
    by_rcode: dict[str, uuid.UUID] = {}
    for suffix in ("Company", "Person", "Contact"):
        for rec in parse_entity(export_dir, suffix).records:
            if not rec.systemid:
                continue
            rcode = rec.get("rcode").strip()
            if rcode:
                by_rcode[rcode] = _uid("contact", rec.systemid)
    return by_rcode


# ── Rapport ───────────────────────────────────────────────────────────────────


def _print_report(built: BuiltInvoices, execute: bool) -> None:
    g = built.groups
    total_koppen = sum(len(v) for v in g.values())
    auto_lines = len(built.lines)
    auto_bruto = sum(i["total"] for i in built.invoices)
    # Openstaand = alle niet-betaalde auto-koppen (open gewone facturen + open
    # creditnota's, die negatief meetellen) → matcht recept € 72.762,09.
    auto_open = sum(i["total"] for i in built.invoices if i["status"] in ("overdue", "sent"))
    derd_bruto = _group_bruto(built, "derdengelden")

    print("=" * 68)
    print("BaseNet-factuurimport — " + ("EXECUTE (schrijft na controle)" if execute else "DRY RUN (schrijft niets)"))
    print("=" * 68)
    print(f"\nTenant: {built.tenant_id}\n")
    print(f"Koppen gelezen: {total_koppen}   ·   regels in auto-groep: {auto_lines}   ·   losse regels zonder kop: {built.orphan_lines}")
    print("\nPartitie (alle koppen):")
    for name, want in (("auto", 439), ("mollie7", 7), ("wip", 12), ("leeg", 19), ("derdengelden", 90)):
        got = len(g[name])
        flag = "  ✓" if got == want else f"  ⚠ verwacht {want}"
        print(f"   {name:14s}: {got:4d}{flag}")

    print("\nAuto-groep (te importeren):")
    print(f"   facturen:   {len(built.invoices):4d}   (verwacht 439)")
    print(f"   regels:     {auto_lines:4d}   (verwacht 630)")
    print(f"   bruto:      € {auto_bruto:>12,.2f}   (verwacht € 302.750,39)")
    print(f"   openstaand: € {auto_open:>12,.2f}   (verwacht € 72.762,09)")
    print(f"   derdengelden bruto (uitgesloten): € {derd_bruto:,.2f}   (verwacht € -90.718,21)")

    print("\nKoppeling:")
    print(f"   relaties onopgelost (debiteurcode → geen fase-1-relatie): {len(built.unresolved_contacts)}")
    if built.unresolved_contacts:
        print(f"      bv. facturen {', '.join(built.unresolved_contacts[:8])}")
    print(f"   IN-facturen aan bestaand dossier gekoppeld: {built.in_cases_matched}   (verwacht 137)")
    print(f"   D-facturen zonder dossier (case_id=NULL):   {built.d_contact_only}   (verwacht 302)")
    print(f"   creditnota's aan origineel gekoppeld:       {built.credit_links}   (verwacht 23)")

    print("\nBetalingen:")
    print(f"   totaal betaalregels: {len(built.payments)}   (verwacht 325)")
    print(f"      met bewezen iDEAL-datum: {built.payments_dated}   (verwacht 20)")
    print(f"      'Datum onbekend':        {built.payments_undated}   (verwacht 305)")
    pay_sum = sum(p["amount"] for p in built.payments)
    print(f"   som betaald: € {pay_sum:,.2f}   (verwacht € 248.364,17)")

    print("\nControlepoorten:")
    print(f"   regelformule-afwijkingen (moet 0):        {len(built.line_formula_mismatch)}")
    print(f"   kop≠regels ECHTE afwijkingen (moet 0):    {len(built.total_mismatch)}")
    if built.total_mismatch:
        for nr, s, t in built.total_mismatch[:5]:
            print(f"      - {nr}: som regels € {s} vs kop € {t}")
    # Bronbedragen worden bewaard (geen per-groep-herberekening) → de bekende
    # 1-cent van 100532 blijft € 1.631,74 zoals in BaseNet.
    f532 = next((i for i in built.invoices if i["invoice_number"] == "100532"), None)
    if f532 is not None:
        print(f"   factuur 100532 bewaard totaal:            € {f532['total']}   (verwacht € 1631.74)")
    print("=" * 68)


def _group_bruto(built: BuiltInvoices, name: str) -> Decimal:
    # Bruto van een niet-geïmporteerde groep is niet in `invoices` opgenomen;
    # deze helper wordt gevuld door run() met de ruwe koppen. Placeholder 0 bij
    # pure aanroep zonder ruwe data.
    return getattr(built, "_derd_bruto", Decimal("0.00"))


# ── Uitvoeren ─────────────────────────────────────────────────────────────────


async def run(export_dir: str, execute: bool, tenant_arg: str | None) -> None:
    async with async_session() as db:
        if tenant_arg:
            tenant_id = uuid.UUID(tenant_arg)
        else:
            tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
            if len(tenants) != 1:
                raise SystemExit(f"Meerdere/geen tenants ({len(tenants)}); geef --tenant-id op.")
            tenant_id = tenants[0][0]

        # created_by op betalingen: expliciet de import-gebruiker seidony@ (op prod
        # bestaat óók Lisanne's account, dus "de enige actieve gebruiker" faalt daar).
        seidony = (await db.execute(
            text("SELECT id FROM users WHERE tenant_id = :t AND email = :e AND is_active = true"),
            {"t": tenant_id, "e": IMPORT_USER_EMAIL},
        )).all()
        if seidony:
            user_id = seidony[0][0]
        else:
            users = (await db.execute(
                text("SELECT id FROM users WHERE tenant_id = :t AND is_active = true"), {"t": tenant_id}
            )).all()
            user_id = users[0][0] if len(users) == 1 else None

        # Dossiernummer → id (voor IN-koppeling).
        case_id_by_number = {
            n: i for (i, n) in (await db.execute(
                text("SELECT id, case_number FROM cases WHERE tenant_id = :t"), {"t": tenant_id}
            )).all()
        }
        contact_by_rcode = _rcode_to_contact(export_dir)
        # Alleen relaties die ook echt in de DB staan tellen als opgelost.
        existing_contacts = {
            i for (i,) in (await db.execute(
                text("SELECT id FROM contacts WHERE tenant_id = :t"), {"t": tenant_id}
            )).all()
        }
        contact_by_rcode = {rc: cid for rc, cid in contact_by_rcode.items() if cid in existing_contacts}

        built = build_invoices(export_dir, tenant_id, user_id, contact_by_rcode, case_id_by_number)
        built._derd_bruto = _raw_group_bruto(export_dir, built.groups["derdengelden"])

        _print_report(built, execute)

        if not execute:
            return

        # Harde poorten vóór schrijven.
        problems = []
        if len(built.invoices) != 439:
            problems.append(f"auto-groep {len(built.invoices)} ≠ 439")
        if built.unresolved_contacts:
            problems.append(f"{len(built.unresolved_contacts)} onopgeloste relaties")
        if built.total_mismatch:
            problems.append(f"{len(built.total_mismatch)} kop≠regels-afwijkingen")
        if built.line_formula_mismatch:
            problems.append(f"{len(built.line_formula_mismatch)} regelformule-afwijkingen")
        if user_id is None:
            problems.append("geen unieke actieve gebruiker voor betalingen")
        existing_inv = (await db.execute(
            text("SELECT count(*) FROM invoices WHERE tenant_id = :t"), {"t": tenant_id}
        )).scalar_one()
        if existing_inv:
            problems.append(f"doeltabel invoices niet leeg ({existing_inv})")
        if problems:
            raise SystemExit("\nAFGEBROKEN — poorten niet groen:\n  - " + "\n  - ".join(problems))

        # Schrijven: originelen vóór creditnota's (FK linked_invoice_id).
        originals = [i for i in built.invoices if i["invoice_type"] != "credit_note"]
        credits = [i for i in built.invoices if i["invoice_type"] == "credit_note"]
        n_inv = await _insert(db, "invoices", originals + credits)
        n_lines = await _insert(db, "invoice_lines", built.lines)
        n_pay = await _insert(db, "invoice_payments", built.payments)
        await db.commit()
        print(f"\nGESCHREVEN — facturen: {n_inv}, regels: {n_lines}, betalingen: {n_pay}")


def _raw_group_bruto(export_dir: str, invnrs: list[str]) -> Decimal:
    kop = parse_entity(export_dir, "OutgoingInvoice").records
    by = {r.get("invnr").strip(): r for r in kop}
    return sum((_dec(by[n].get("invtobepaid")) for n in invnrs), Decimal("0.00"))


async def _insert(db, table: str, rows: list[dict]) -> int:
    existing = {i for (i,) in (await db.execute(text(f"SELECT id FROM {table}"))).all()}
    todo = [r for r in rows if r["id"] not in existing]
    for row in todo:
        cols = list(row.keys())
        await db.execute(
            text(f"INSERT INTO {table} ({', '.join(cols)}, created_at, updated_at) "
                 f"VALUES ({', '.join(':' + c for c in cols)}, now(), now()) ON CONFLICT (id) DO NOTHING"),
            row,
        )
    return len(todo)


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet → Luxis kantoorfacturen (fase 2)")
    p.add_argument("--export-dir", required=True, help="Map met uitgepakte BaseNet-XML")
    p.add_argument("--dry-run", action="store_true", help="Alleen rapporteren (default)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    p.add_argument("--tenant-id", default=None, help="Tenant-UUID (default: de enige tenant)")
    args = p.parse_args()
    asyncio.run(run(args.export_dir, execute=args.execute, tenant_arg=args.tenant_id))


if __name__ == "__main__":
    main()
