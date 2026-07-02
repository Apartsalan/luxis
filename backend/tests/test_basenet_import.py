"""Tests voor de BaseNet-import: parser + mapping (fase 1).

Puur Python, geen DB — draait mee in de gewone suite. Fixtures zijn afgeleid van
échte records uit de BaseNet-export (Xml_02-07-2026_2400.zip).
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# scripts/ ligt in de REPO-ROOT, niet in backend/. In de dev-container is het op
# /app/scripts gemount, maar CI draait pytest vanuit backend/ (volledige checkout)
# — daar is scripts/ pas één map hoger. Zoek de dichtstbijzijnde ouder die
# scripts/basenet bevat en maak die importeerbaar. (CI brak hierop in S166.)
for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts" / "basenet").is_dir():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

import pytest  # noqa: E402
from scripts.basenet.mapping import (  # noqa: E402
    map_company,
    map_contactpersoon,
    map_incasso,
    map_incassoline,
    map_person,
    resolve_debtor_type,
    resolve_interest_type,
)
from scripts.basenet.parse import BaseNetRecord, detect_entity, parse_file  # noqa: E402

# ── Echte-data-fixtures ──────────────────────────────────────────────────────

COMPANY_XML = """
<rela.company>
    <entityname>rela.company</entityname>
    <systemid>26148127</systemid>
    <entrylist>
        <entry key="systemid" value="26148127"/>
        <entry key="rcode" value="100003"/>
        <entry key="rtype" value="B"/>
        <entry key="rinactive" value="false"/>
        <entry key="company" value="Fresh Burger 7"/>
        <entry key="kvk_nummer" value="12345678"/>
        <entry key="ostreet" value="Van Woustraat"/>
        <entry key="ohouseno" value="116"/>
        <entry key="ohousenoext" value="H"/>
        <entry key="ocity" value="AMSTERDAM"/>
        <entry key="ozipcode" value="1073 LS"/>
        <entry key="email" value="info@freshburger.nl"/>
        <entry key="tel1" value="020-1234567"/>
    </entrylist>
</rela.company>
"""

# Twee records + een kapot record ertussen (om per-record foutisolatie te testen).
LETTER_XML = """
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>1</systemid>
    <entrylist>
        <entry key="systemid" value="1"/>
        <entry key="lepcode" value="IN100000"/>
        <entry key="leinout" value="3"/>
        <entry key="lefrom" value="Lisanne Kesting &lt;kesting@kestinglegal.nl&gt;"/>
    </entrylist>
</rela.letter>
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>2</systemid>
    <entrylist>
        <entry key="systemid" value="2" value="kapot"/>
    </entrylist>
</rela.letter>
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>3</systemid>
    <entrylist>
        <entry key="systemid" value="3"/>
        <entry key="lepcode" value="D100002"/>
    </entrylist>
</rela.letter>
"""


def _rec(fields: dict, systemid: str = "1", entity: str = "e") -> BaseNetRecord:
    return BaseNetRecord(entity=entity, systemid=systemid, fields=fields)


# ── Parser ───────────────────────────────────────────────────────────────────

def test_detect_entity():
    assert detect_entity(COMPANY_XML) == "rela.company"
    assert detect_entity("   \n\n") is None


def test_parse_file_company(tmp_path):
    f = tmp_path / "company.xml"
    f.write_text(COMPANY_XML, encoding="utf-8")
    res = parse_file(f)
    assert res.entity == "rela.company"
    assert len(res.records) == 1
    assert res.failed == 0
    rec = res.records[0]
    assert rec.systemid == "26148127"
    assert rec.get("company") == "Fresh Burger 7"
    assert rec.get("kvk_nummer") == "12345678"


def test_parse_file_unescapes_xml_entities(tmp_path):
    """&lt; en &gt; in attribuutwaarden moeten terug naar < en >."""
    f = tmp_path / "letter.xml"
    f.write_text(LETTER_XML, encoding="utf-8")
    res = parse_file(f)
    assert res.records[0].get("lefrom") == "Lisanne Kesting <kesting@kestinglegal.nl>"


def test_parse_file_isolates_broken_record(tmp_path):
    """Eén kapot record (dubbel value-attribuut) mag de rest niet slopen."""
    f = tmp_path / "letter.xml"
    f.write_text(LETTER_XML, encoding="utf-8")
    res = parse_file(f)
    # Record 1 en 3 parsen, record 2 (kapot) telt als failed.
    assert len(res.records) == 2
    assert res.failed == 1
    assert {r.systemid for r in res.records} == {"1", "3"}


# ── Mapping: relaties ────────────────────────────────────────────────────────

def test_map_company():
    rec = _rec(
        {
            "systemid": "26148127",
            "rcode": "100003",
            "company": "Fresh Burger 7",
            "kvk_nummer": "12345678",
            "ostreet": "Van Woustraat",
            "ohouseno": "116",
            "ohousenoext": "H",
            "ocity": "AMSTERDAM",
            "ozipcode": "1073 LS",
            "email": "info@freshburger.nl",
            "tel1": "020-1234567",
            "rinactive": "false",
        }
    )
    out = map_company(rec)
    assert out["contact_type"] == "company"
    assert out["name"] == "Fresh Burger 7"
    assert out["kvk_number"] == "12345678"
    assert out["visit_address"] == "Van Woustraat 116H"
    assert out["visit_city"] == "AMSTERDAM"
    assert out["email"] == "info@freshburger.nl"
    assert out["is_active"] is True
    assert "rcode=100003" in out["notes"]


def test_map_company_inactive():
    rec = _rec({"company": "Oud BV", "rinactive": "true"})
    assert map_company(rec)["is_active"] is False


def test_map_person_name_and_salutation():
    rec = _rec(
        {
            "firstname": "Edwin",
            "middlename": "van",
            "lastname": "Huisman",
            "sex": "M",
            "mcity": "Hellevoetsluis",
        }
    )
    out = map_person(rec)
    assert out["contact_type"] == "person"
    assert out["name"] == "Edwin van Huisman"
    assert out["first_name"] == "Edwin"
    assert out["last_name"] == "Huisman"
    assert out["salutation"] == "mr"


def test_map_person_salutation_female():
    rec = _rec({"lastname": "Jansen", "saluation": "Geachte mevrouw"})
    assert map_person(rec)["salutation"] == "mrs"


def test_map_contactpersoon_falls_back_to_company():
    """rtype-C zonder persoonsnaam → naam valt terug op het bedrijfslabel."""
    rec = _rec({"company": "LegalWork B.V.", "firstname": "", "lastname": ""})
    out = map_contactpersoon(rec)
    assert out["contact_type"] == "person"
    assert out["name"] == "LegalWork B.V."


def test_map_contactpersoon_uses_person_name_when_present():
    rec = _rec({"company": "LegalWork B.V.", "firstname": "Jan", "lastname": "de Vries"})
    assert map_contactpersoon(rec)["name"] == "Jan de Vries"


# ── Mapping: dossiers + vorderingen ──────────────────────────────────────────

def test_map_incasso_archive():
    rec = _rec(
        {
            "inccode": "IN100000",
            "pscode": "Incassocenter B.V. / Bliksem Elektrotechniek Ede",
            "inckenmerkclient": "IN121388",
            "incincassocost": "40.00",
            "incinterest": "2.00",
            "cachedhoofdsom": "201.68",
            "pdatestart": "2024-12-17 18:17:14.0",
            "pdateend": "2025-08-11 12:07:30.0",
            "pstatus": "Lopend",
        },
        systemid="691311",
    )
    out = map_incasso(rec, debtor_type="b2b", interest_type="commercial")
    assert out["case_number"] == "IN100000"
    assert out["status"] == "afgesloten"  # passief archief
    assert out["is_active"] is True
    assert out["debtor_type"] == "b2b"
    assert out["reference"] == "IN121388"  # cliënt-kenmerk (backlog #1)
    assert out["bik_override"] == Decimal("40.00")
    # total_principal = 0 in de mapping; de runner vult de som van de vorderingen.
    # (BaseNet cachedhoofdsom 201.68 bevat rente en is dus NIET de hoofdsom.)
    assert out["total_principal"] == Decimal("0.00")
    assert out["total_paid"] == Decimal("0.00")
    assert out["date_opened"] == date(2024, 12, 17)
    assert out["date_closed"] == date(2025, 8, 11)
    assert "Lopend" in out["debtor_notes"]


def test_map_incassoline():
    rec = _rec(
        {
            "inclincassoid": "691311",
            "inclinvnr": "136849",
            "inclsenddate": "2024-10-25",
            "inclduedate": "2024-11-08",
            "inclamount": "193.60",
        },
        systemid="1361893",
    )
    out = map_incassoline(rec)
    assert out["principal_amount"] == Decimal("193.60")
    assert out["invoice_number"] == "136849"
    assert out["invoice_date"] == date(2024, 10, 25)
    assert out["default_date"] == date(2024, 11, 8)  # vervaldatum = verzuim
    assert "136849" in out["description"]


def test_resolve_debtor_and_interest():
    assert resolve_debtor_type("person") == "b2c"
    assert resolve_debtor_type("company") == "b2b"
    assert resolve_debtor_type(None) == "b2b"
    assert resolve_interest_type("b2c") == "statutory"
    assert resolve_interest_type("b2b") == "commercial"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
