"""S209 round-trip: nieuwe import-velden werken écht, van mapping tot API.

Drie lagen, elk functioneel (niet alleen "staat het erin"):
1. mapping: land genormaliseerd (NL weg, buitenland nette naam), geboortedatum,
   provisie, notitie/waarschuwing in debtor_notes.
2. database: de gemapte dicts gaan via _insert_missing (de echte import-schrijfweg)
   de tabellen in en komen er identiek uit — bewijst kolomnamen + datatypes.
3. API: land wegschrijven via PUT (zoals het relatiescherm doet) en teruglezen
   via GET — bewijst het hele bewerk-pad voor de gebruiker.
"""

import sys
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

# scripts/ ligt in de repo-root (zie test_basenet_import.py voor de reden).
for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts" / "basenet").is_dir():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402

from scripts.basenet.import_basenet import _insert_missing  # noqa: E402
from scripts.basenet.mapping import (  # noqa: E402
    map_company,
    map_incasso,
    map_person,
)
from scripts.basenet.parse import BaseNetRecord  # noqa: E402


def _rec(fields: dict, systemid: str = "9990001") -> BaseNetRecord:
    return BaseNetRecord(entity="e", systemid=systemid, fields=fields)


# ── 1. Mapping: nieuwe velden ────────────────────────────────────────────────

def test_map_company_buitenland_genormaliseerd():
    out = map_company(_rec({
        "company": "Akzepta Test GmbH",
        "ocountry": "Duitsland", "mcountry": "BELGIE",
    }))
    assert out["visit_country"] == "Duitsland"
    assert out["postal_country"] == "België"  # rommelige spelling → nette naam


def test_map_company_nederland_blijft_leeg():
    out = map_company(_rec({"company": "NL BV", "ocountry": "NL", "mcountry": "Nederland"}))
    assert out["visit_country"] is None
    assert out["postal_country"] is None


def test_map_company_onbekend_land_blijft_behouden():
    out = map_company(_rec({"company": "X", "ocountry": "Atlantis"}))
    assert out["visit_country"] == "Atlantis"  # niet weggooien, niet vertalen


def test_map_person_geboortedatum_en_hcountry_fallback():
    out = map_person(_rec({
        "firstname": "Test", "lastname": "Persoon",
        "birthday": "1980-05-17 00:00:00.0",
        "hcountry": "Spanje",  # geen ocountry → valt terug op huisadres-land
    }))
    assert out["date_of_birth"] == date(1980, 5, 17)
    assert out["visit_country"] == "Spanje"


def test_map_incasso_provisie_en_notities():
    out = map_incasso(
        _rec({
            "inccode": "IN999901", "pstatus": "Lopend",
            "pdatestart": "2025-01-15 00:00:00.0",
            "incprovisie": "15.00",
            "incinteresttype": "8", "incssamengesteld": "false",
            "palert": "Failliet",
            "pmemo": "Debiteur is solvabel.<br />Arno langs",
        }),
        debtor_type="b2b", interest_type="commercial",
    )
    assert out["provisie_percentage"] == Decimal("15.00")
    notes = out["debtor_notes"]
    # waarschuwing bovenaan, herkomst-regel met rentetype-context, memo onderaan
    assert notes.startswith("[BaseNet-waarschuwing] Failliet")
    assert "rentetype BaseNet: 8" in notes
    assert "[BaseNet-notitie]\nDebiteur is solvabel.\nArno langs" in notes


def test_map_incasso_provisie_nul_blijft_leeg():
    out = map_incasso(
        _rec({"inccode": "IN999902", "pdatestart": "2025-01-15", "incprovisie": "0.00"}),
        debtor_type="b2b", interest_type="commercial",
    )
    assert out["provisie_percentage"] is None


# ── 2. Database: de echte import-schrijfweg ──────────────────────────────────

@pytest.mark.asyncio
async def test_insert_missing_schrijft_nieuwe_velden(db, test_tenant):
    contact_fields = map_person(_rec({
        "firstname": "Roundtrip", "lastname": "Tester",
        "birthday": "1975-07-03 00:00:00.0",
        "ocountry": "Turkije",
    }, systemid="9990002"))
    contact_fields["id"] = uuid.uuid4()
    contact_fields["tenant_id"] = test_tenant.id
    n = await _insert_missing(db, "contacts", [contact_fields], existing_ids=set())
    assert n == 1

    case_fields = map_incasso(
        _rec({
            "inccode": "IN999903", "pstatus": "Lopend",
            "pdatestart": "2025-02-01 00:00:00.0",
            "incprovisie": "15.00", "palert": "Regeling",
        }, systemid="9990003"),
        debtor_type="b2c", interest_type="statutory",
    )
    case_fields["id"] = uuid.uuid4()
    case_fields["tenant_id"] = test_tenant.id
    case_fields["client_id"] = contact_fields["id"]
    case_fields["opposing_party_id"] = None
    n = await _insert_missing(db, "cases", [case_fields], existing_ids=set())
    assert n == 1
    await db.commit()

    row = (await db.execute(
        text("SELECT date_of_birth, visit_country FROM contacts WHERE id=:i"),
        {"i": contact_fields["id"]},
    )).first()
    assert row.date_of_birth == date(1975, 7, 3)
    assert row.visit_country == "Turkije"

    row = (await db.execute(
        text("SELECT provisie_percentage, debtor_notes FROM cases WHERE id=:i"),
        {"i": case_fields["id"]},
    )).first()
    assert row.provisie_percentage == Decimal("15.00")
    assert row.debtor_notes.startswith("[BaseNet-waarschuwing] Regeling")


# ── 3. API: het bewerk-pad van het relatiescherm ─────────────────────────────

@pytest.mark.asyncio
async def test_land_via_api_schrijven_en_teruglezen(client, auth_headers, test_company):
    # zoals het scherm doet: PUT met land, daarna GET detail
    resp = await client.put(
        f"/api/relations/{test_company.id}",
        json={"visit_country": "België", "postal_country": "Duitsland"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["visit_country"] == "België"
    assert body["postal_country"] == "Duitsland"

    resp = await client.get(f"/api/relations/{test_company.id}", headers=auth_headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["visit_country"] == "België"
    assert detail["postal_country"] == "Duitsland"

    # leegmaken kan ook weer (NL = leeg is de conventie)
    resp = await client.put(
        f"/api/relations/{test_company.id}",
        json={"visit_country": None, "postal_country": None},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["visit_country"] is None
