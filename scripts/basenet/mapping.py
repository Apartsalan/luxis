"""Transformatie BaseNet-record → Luxis-veldwaarden.

Puur Python, geen DB — zo unit-testbaar. De import-runner voegt daarna de FK's
(tenant_id, id, client_id, opposing_party_id, case_id) toe; deze functies leveren
alleen de inhoudelijke velden op, met geld als Decimal en datums als date-objecten
(asyncpg wil date-objecten, geen strings — bekende-fouten #5).

Scope fase 1: Company + Person → contacts, Incasso → cases, IncassoLine → claims.
Contactpersonen (rela.contact) + betalingen = fase 1b.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .parse import BaseNetRecord


# ── Kleine helpers ───────────────────────────────────────────────────────────

def _clean(value: str | None) -> str | None:
    """Getrimde string, of None bij leeg."""
    if value is None:
        return None
    v = value.strip()
    return v or None


def _decimal(value: str | None) -> Decimal | None:
    """Bedrag als Decimal, of None bij leeg/ongeldig. Nooit float (geld!)."""
    v = _clean(value)
    if v is None:
        return None
    try:
        return Decimal(v)
    except (InvalidOperation, ValueError):
        return None


def _date(value: str | None) -> date | None:
    """Datum uit 'YYYY-MM-DD' of 'YYYY-MM-DD HH:MM:SS.0'. None bij leeg/ongeldig."""
    v = _clean(value)
    if v is None:
        return None
    try:
        return datetime.strptime(v[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _address(rec: BaseNetRecord, prefix: str) -> str | None:
    """Combineer straat + huisnr + toevoeging tot één adresregel.
    prefix: 'o' (bezoek/vestiging), 'm' (post), 'h' (huis/privé)."""
    street = _clean(rec.get(f"{prefix}street"))
    if not street:
        return None
    houseno = _clean(rec.get(f"{prefix}houseno"))
    ext = _clean(rec.get(f"{prefix}housenoext"))
    parts = [street]
    if houseno:
        parts.append(houseno + (ext or ""))
    return " ".join(parts)


def _salutation(rec: BaseNetRecord) -> str:
    """BaseNet sex/saluation → Luxis salutation ('mr'/'mrs'/'unknown')."""
    sex = (rec.get("sex") or "").strip().upper()
    if sex == "M":
        return "mr"
    if sex in ("V", "F"):
        return "mrs"
    sal = (rec.get("saluation") or "").lower()
    if "heer" in sal:
        return "mr"
    if "mevrouw" in sal or "mevr" in sal:
        return "mrs"
    return "unknown"


# ── Relaties ─────────────────────────────────────────────────────────────────

def map_company(rec: BaseNetRecord) -> dict:
    """rela.company → contacts (contact_type='company')."""
    return {
        "contact_type": "company",
        "name": _clean(rec.get("company")) or "(naam onbekend)",
        "salutation": "unknown",
        "email": _clean(rec.get("email")),
        "phone": _clean(rec.get("tel1")) or _clean(rec.get("mobile")),
        "kvk_number": _clean(rec.get("kvk_nummer")),
        "visit_address": _address(rec, "o"),
        "visit_postcode": _clean(rec.get("ozipcode")),
        "visit_city": _clean(rec.get("ocity")),
        "postal_address": _address(rec, "m"),
        "postal_postcode": _clean(rec.get("mzipcode")),
        "postal_city": _clean(rec.get("mcity")),
        "is_active": (rec.get("rinactive") or "").lower() != "true",
        "notes": _basenet_note(rec, extra=_clean(rec.get("notes"))),
    }


def _person_name(rec: BaseNetRecord) -> str:
    """Volledige naam: voornaam [tussenvoegsel] achternaam."""
    first = _clean(rec.get("firstname"))
    middle = _clean(rec.get("middlename"))
    last = _clean(rec.get("lastname"))
    parts = [p for p in (first, middle, last) if p]
    return " ".join(parts) or "(naam onbekend)"


def map_person(rec: BaseNetRecord) -> dict:
    """rela.person → contacts (contact_type='person')."""
    return {
        "contact_type": "person",
        "name": _person_name(rec),
        "first_name": _clean(rec.get("firstname")),
        "last_name": _clean(rec.get("lastname")),
        "salutation": _salutation(rec),
        "email": _clean(rec.get("email")),
        "phone": _clean(rec.get("tel1")) or _clean(rec.get("mobile")),
        "visit_address": _address(rec, "o") or _address(rec, "h"),
        "visit_postcode": _clean(rec.get("ozipcode")) or _clean(rec.get("hzipcode")),
        "visit_city": _clean(rec.get("ocity")) or _clean(rec.get("hcity")),
        "postal_address": _address(rec, "m"),
        "postal_postcode": _clean(rec.get("mzipcode")),
        "postal_city": _clean(rec.get("mcity")),
        "is_active": (rec.get("rinactive") or "").lower() != "true",
        "notes": _basenet_note(rec, extra=_clean(rec.get("notes"))),
    }


def map_contactpersoon(rec: BaseNetRecord) -> dict:
    """rela.contact (rtype C) → contacts (contact_type='person').

    Contactpersonen bij een bedrijf. Sommige incasso-opdrachtgevers wijzen hiernaar
    (bv. een facturatie-contact). Naam valt terug op het bedrijfslabel als er geen
    persoonsnaam is. De persoon↔bedrijf-koppeling (ContactLink) = fase 1b.
    """
    out = map_person(rec)
    if out["name"] == "(naam onbekend)":
        out["name"] = _clean(rec.get("company")) or "(naam onbekend)"
    return out


def _basenet_note(rec: BaseNetRecord, extra: str | None = None) -> str:
    """Herkomst-notitie zodat elke geïmporteerde relatie traceerbaar is."""
    tag = f"[BaseNet-import] rcode={rec.get('rcode') or '?'} systemid={rec.systemid}"
    return f"{tag}\n{extra}" if extra else tag


# ── Dossiers (incasso) ───────────────────────────────────────────────────────

# BaseNet pstatus → leesbaar; alles komt binnen als Luxis-status 'afgesloten'
# (passief archief, besluit Arsalan). De originele status bewaren we in de notitie.
_INCASSO_STATUS_LABELS = {
    "Lopend": "lopend",
    "Wacht": "wachtend",
    "Gereed": "gereed",
    "Geannuleerd": "geannuleerd",
    "Offerte": "offerte",
}


def map_incasso(
    rec: BaseNetRecord,
    *,
    debtor_type: str,
    interest_type: str,
) -> dict:
    """advocatuur.incasso → cases. Archief: status 'afgesloten', geen pipeline-stap.

    FK's (client_id, opposing_party_id, tenant_id, id) voegt de runner toe.
    `debtor_type`/`interest_type` bepaalt de runner op basis van de wederpartij.
    """
    inccode = _clean(rec.get("inccode")) or _clean(rec.get("pcode"))
    date_opened = _date(rec.get("pdatestart")) or _date(rec.get("incactiondate"))
    date_closed = _date(rec.get("pdateend"))
    basenet_status = _clean(rec.get("pstatus")) or "?"
    interest_rate = _decimal(rec.get("incinterest"))

    return {
        "case_number": inccode,
        "case_type": "incasso",
        "status": "afgesloten",  # passief archief
        "is_active": True,  # zichtbaar als historie, maar terminale status → geen automatisering
        "debtor_type": debtor_type,
        "interest_type": interest_type,
        # Custom rente uit BaseNet alleen bewaren als contractueel percentage
        # (niet leidend voor archief; herberekening gebeurt niet).
        "contractual_rate": interest_rate if interest_type == "contractual" else None,
        "description": _clean(rec.get("pscode")),
        "reference": _clean(rec.get("inckenmerkclient")),  # cliënt-kenmerk (backlog #1)
        "bik_override": _decimal(rec.get("incincassocost")),
        "date_opened": date_opened,
        "date_closed": date_closed,
        # total_principal = som van de vorderingen (hoofdsom). De runner vult dit
        # na het bouwen van de claims. LET OP: BaseNet's cachedhoofdsom bevat rente
        # (cached = hoofdsom + rente) — dat is NIET de hoofdsom.
        "total_principal": Decimal("0.00"),
        "total_paid": Decimal("0.00"),  # betalingen = fase 1b
        "debtor_notes": (
            f"[BaseNet-import] {inccode} · systemid={rec.systemid} · "
            f"BaseNet-status: {basenet_status}"
        ),
    }


def resolve_debtor_type(opposing_contact_type: str | None) -> str:
    """Wederpartij is een persoon → b2c, bedrijf → b2b. Onbekend → b2b (default)."""
    return "b2c" if opposing_contact_type == "person" else "b2b"


def resolve_interest_type(debtor_type: str) -> str:
    """Luxis-conventie: b2c → wettelijke rente, b2b → handelsrente.
    (Voor archief niet leidend — dossiers worden niet herberekend.)"""
    return "statutory" if debtor_type == "b2c" else "commercial"


# ── Vorderingen (incassoline) ────────────────────────────────────────────────

def map_incassoline(rec: BaseNetRecord) -> dict:
    """advocatuur.incassoline → claims. case_id voegt de runner toe (via inclincassoid)."""
    invoice_number = _clean(rec.get("inclinvnr"))
    send_date = _date(rec.get("inclsenddate"))
    due_date = _date(rec.get("inclduedate"))
    amount = _decimal(rec.get("inclamount")) or Decimal("0.00")
    descr = _clean(rec.get("incldescr"))

    # description is verplicht (String 500). Bouw iets zinnigs op.
    label = descr or (f"Factuur {invoice_number}" if invoice_number else "Vordering")
    if send_date:
        label = f"{label} dd. {send_date.strftime('%d-%m-%Y')}"

    return {
        "description": label[:500],
        "principal_amount": amount,
        # verzuimdatum = vervaldatum (interest start); fallback verzenddatum.
        "default_date": due_date or send_date,
        "invoice_number": invoice_number,
        "invoice_date": send_date,
        "is_active": True,
    }


# ── Betalingen (fase 1b) ──────────────────────────────────────────────────────

def map_incassobetaling(rec: BaseNetRecord) -> dict | None:
    """advocatuur.incassobetaling → betaling-velden (case_id + tenant_id + id
    voegt de runner toe via incpincassoid). None bij ontbrekend bedrag/datum,
    want betaaldatum bepaalt de rente-knip en het bedrag de toerekening.

    incpuitsluitenkosten: BaseNet paste deze betaling toe ZONDER de kosten (BIK)
    aan te raken. Luxis' art. 6:44 kent die vlag niet — we bewaren hem in de
    notitie zodat de her-toerekening zichtbaar afwijkt, we verzinnen niets.
    """
    amount = _decimal(rec.get("incpamount"))
    pay_date = _date(rec.get("incppaydate"))
    incasso_sysid = _clean(rec.get("incpincassoid"))
    if amount is None or amount <= Decimal("0") or pay_date is None or not incasso_sysid:
        return None

    note = _clean(rec.get("incpnote"))
    exclude_costs = (rec.get("incpuitsluitenkosten") or "").lower() == "true"
    is_credit = bool(note and "credit" in note.lower())

    label_parts = [note] if note else []
    if exclude_costs:
        label_parts.append("(BaseNet: kosten uitgesloten)")
    label = " ".join(label_parts) if label_parts else "Betaling"
    # Marker maakt de import idempotent + herkenbaar voor rollback.
    description = f"{label} [BaseNet-betaling systemid={rec.systemid}]"[:500]

    return {
        "incasso_sysid": incasso_sysid,
        "amount": amount,
        "payment_date": pay_date,
        "description": description,
        "payment_method": "bank",
        "note": note,
        "exclude_costs": exclude_costs,
        "is_credit": is_credit,
    }


def map_betalingsregeling_termijn(rec: BaseNetRecord) -> dict | None:
    """advocatuur.incassobetalingsregeling → één termijn (installment).
    None bij ontbrekend bedrag/vervaldatum."""
    amount = _decimal(rec.get("incbamount"))
    due_date = _date(rec.get("incbdate"))
    incasso_sysid = _clean(rec.get("incbincassoid"))
    if amount is None or amount <= Decimal("0") or due_date is None or not incasso_sysid:
        return None
    return {
        "incasso_sysid": incasso_sysid,
        "termijn_sysid": rec.systemid,
        "amount": amount,
        "due_date": due_date,
        "start_date": _date(rec.get("incbdatestart")) or due_date,
    }
