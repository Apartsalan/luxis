"""Tests voor de BaseNet-import: parser + mapping (fase 1).

Puur Python, geen DB — draait mee in de gewone suite. Fixtures zijn afgeleid van
échte records uit de BaseNet-export (Xml_02-07-2026_2400.zip).
"""

import sys
import uuid
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
    map_betalingsregeling_termijn,
    map_company,
    map_contactpersoon,
    map_incasso,
    map_incassobetaling,
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


# ── Fase 1b: betalingen + regelingen ─────────────────────────────────────────

def test_map_incassobetaling_basic():
    rec = _rec(
        {
            "incppaydate": "2025-01-10",
            "incpamount": "108.34",
            "incpnote": "Betaald aan IVB",
            "incpincassoid": "691609",
            "incpuitsluitenkosten": "false",
        },
        systemid="456716",
    )
    out = map_incassobetaling(rec)
    assert out["amount"] == Decimal("108.34")
    assert out["payment_date"] == date(2025, 1, 10)
    assert out["incasso_sysid"] == "691609"
    assert out["is_credit"] is False
    assert out["exclude_costs"] is False
    # Marker maakt de import idempotent + herkenbaar voor rollback.
    assert "[BaseNet-betaling systemid=456716]" in out["description"]


def test_map_incassobetaling_credit_and_exclude_costs():
    rec = _rec(
        {
            "incppaydate": "2023-06-24",
            "incpamount": "6675.60",
            "incpnote": "Credit 2022-0304",
            "incpincassoid": "693614",
            "incpuitsluitenkosten": "true",
        },
        systemid="458019",
    )
    out = map_incassobetaling(rec)
    assert out["is_credit"] is True          # 'credit' in notitie → beslispunt
    assert out["exclude_costs"] is True      # BaseNet-vlag bewaard in omschrijving
    assert "kosten uitgesloten" in out["description"]


def test_map_incassobetaling_rejects_incomplete():
    # Geen bedrag → None (betaling zonder bedrag is geen betaling).
    assert map_incassobetaling(_rec({"incppaydate": "2025-01-01", "incpincassoid": "1"})) is None
    # Geen datum → None (betaaldatum bepaalt de rente-knip).
    assert map_incassobetaling(_rec({"incpamount": "50.00", "incpincassoid": "1"})) is None
    # Nul/negatief → None.
    assert map_incassobetaling(
        _rec({"incppaydate": "2025-01-01", "incpamount": "0.00", "incpincassoid": "1"})
    ) is None


def test_map_betalingsregeling_termijn():
    rec = _rec(
        {
            "incbdate": "2025-01-17",
            "incbdatestart": "2025-01-10",
            "incbamount": "108.34",
            "incbincassoid": "691609",
        },
        systemid="2596514",
    )
    out = map_betalingsregeling_termijn(rec)
    assert out["amount"] == Decimal("108.34")
    assert out["due_date"] == date(2025, 1, 17)
    assert out["start_date"] == date(2025, 1, 10)
    assert out["incasso_sysid"] == "691609"


def test_build_arrangements_keeps_only_future_termijnen(tmp_path):
    """Regeling-import mag ALLEEN toekomstige termijnen opnemen — verleden
    termijnen zeggen niet of ze betaald zijn (geen aanname), en zouden anders
    de dagelijkse overdue-job vollopen met valse achterstand."""
    from scripts.basenet.import_payments import build_arrangements

    incasso = (
        '<advocatuur.incasso><entityname>advocatuur.incasso</entityname>'
        '<systemid>700</systemid><entrylist>'
        '<entry key="systemid" value="700"/><entry key="inccode" value="IN100215"/>'
        '</entrylist></advocatuur.incasso>'
    )
    (tmp_path / "x.Incasso.xml").write_text(incasso, encoding="utf-8")

    def termijn(sysid, due, amount):
        return (
            '<advocatuur.incassobetalingsregeling>'
            '<entityname>advocatuur.incassobetalingsregeling</entityname>'
            f"<systemid>{sysid}</systemid><entrylist>"
            f'<entry key="systemid" value="{sysid}"/>'
            f'<entry key="incbincassoid" value="700"/>'
            f'<entry key="incbdate" value="{due}"/>'
            f'<entry key="incbamount" value="{amount}"/>'
            "</entrylist></advocatuur.incassobetalingsregeling>"
        )

    (tmp_path / "y.IncassoBetalingsRegeling.xml").write_text(
        termijn("1", "2025-01-01", "100.00")   # verleden → weg
        + termijn("2", "2099-07-12", "100.00")  # toekomst → blijft
        + termijn("3", "2099-08-12", "100.00"),  # toekomst → blijft
        encoding="utf-8",
    )

    tenant = uuid.UUID("00000000-0000-0000-0000-000000000001")
    built = build_arrangements(tmp_path, tenant, today=date(2026, 7, 6))
    assert built.total_termijnen == 3
    assert built.future_termijnen == 2
    assert len(built.arrangements) == 1
    a = built.arrangements[0]
    assert a["inccode"] == "IN100215"
    assert len(a["installments"]) == 2
    assert a["total_amount"] == Decimal("200.00")
    assert a["start_date"] == date(2099, 7, 12)
    assert [i["installment_number"] for i in a["installments"]] == [1, 2]


def test_build_bank_payments_exact_match_gate(tmp_path):
    """Bankregel-import (S180): alleen cache-only zaken, alleen positieve regels,
    en per zaak een hard slot — som moet op de cent gelijk zijn aan BaseNet's
    cachedpaymentsadmin, anders wordt de zaak overgeslagen (niets verzinnen)."""
    from scripts.basenet.import_payments import build_bank_payments

    def incasso(sysid, code, admin):
        return (
            "<advocatuur.incasso><entityname>advocatuur.incasso</entityname>"
            f"<systemid>{sysid}</systemid><entrylist>"
            f'<entry key="systemid" value="{sysid}"/>'
            f'<entry key="inccode" value="{code}"/>'
            f'<entry key="pstatus" value="Lopend"/>'
            f'<entry key="cachedpaymentsadmin" value="{admin}"/>'
            "</entrylist></advocatuur.incasso>"
        )

    def bankline(sysid, pcode, descr, amount, dt="2025-12-05"):
        return (
            "<admin.cashbankline><entityname>admin.cashbankline</entityname>"
            f"<systemid>{sysid}</systemid><entrylist>"
            f'<entry key="systemid" value="{sysid}"/>'
            f'<entry key="cblpcode" value="{pcode}"/>'
            f'<entry key="cbldescr" value="{descr}"/>'
            f'<entry key="cblamount" value="{amount}"/>'
            f'<entry key="cbldate" value="{dt}"/>'
            "</entrylist></admin.cashbankline>"
        )

    def betaling(sysid, incassoid):
        return (
            "<advocatuur.incassobetaling><entityname>advocatuur.incassobetaling</entityname>"
            f"<systemid>{sysid}</systemid><entrylist>"
            f'<entry key="systemid" value="{sysid}"/>'
            f'<entry key="incpincassoid" value="{incassoid}"/>'
            f'<entry key="incppaydate" value="2025-01-01"/>'
            f'<entry key="incpamount" value="10.00"/>'
            "</entrylist></advocatuur.incassobetaling>"
        )

    # Zaak 800: exact (100 + 50 = 150, negatieve -75 genegeerd) → import.
    # Zaak 801: som 40 ≠ cache 99 → SKIP (hard slot).
    # Zaak 802: heeft al een los betaal-record → NIET via bankregels (dubbel-dekking).
    (tmp_path / "a.Incasso.xml").write_text(
        incasso("800", "IN100800", "150.00")
        + incasso("801", "IN100801", "99.00")
        + incasso("802", "IN100802", "10.00"),
        encoding="utf-8",
    )
    (tmp_path / "b.IncassoBetalingAnders.xml").write_text(
        betaling("9001", "802"), encoding="utf-8"
    )
    (tmp_path / "c.CashBankLine.xml").write_text(
        bankline("1", "IN100800", "ontvangst", "100.00")
        # koppeling via IN-code in omschrijving (pcode leeg) moet ook werken:
        + bankline("2", "", "Incasso IN100800 / Incassocenter B.V.", "50.00")
        + bankline("3", "IN100800", "doorbetaald aan client", "-75.00")
        + bankline("4", "IN100801", "deel", "40.00")
        + bankline("5", "IN100802", "hoort bij 802 maar die heeft al records", "10.00"),
        encoding="utf-8",
    )

    tenant = uuid.UUID("00000000-0000-0000-0000-000000000001")
    built = build_bank_payments(tmp_path, tenant)

    assert [c[0] for c in built.exact_cases] == ["IN100800"]
    assert len(built.payments) == 2  # de twee positieve regels van IN100800
    assert {p["amount"] for p in built.payments} == {Decimal("100.00"), Decimal("50.00")}
    assert all("[BaseNet-bankregel systemid=" in p["description"] for p in built.payments)
    assert built.negative_skipped == 1
    assert [m[0] for m in built.mismatched_cases] == ["IN100801"]  # 40 ≠ 99 → skip


# ── Fase 2: e-mailimport (koppeling, richting, scope) ────────────────────────

_INCASSO_XML = """
<advocatuur.incasso>
    <entityname>advocatuur.incasso</entityname>
    <systemid>691311</systemid>
    <entrylist>
        <entry key="systemid" value="691311"/>
        <entry key="inccode" value="IN100000"/>
    </entrylist>
</advocatuur.incasso>
"""

_LETTER_XML_F2 = """
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>111</systemid>
    <entrylist>
        <entry key="letterno" value="500001"/>
        <entry key="leinout" value="3"/>
        <entry key="lepcode" value="IN100000"/>
        <entry key="ledate" value="2025-03-10 09:00:00.0"/>
        <entry key="lesubject" value="SOMMATIE TOT BETALING"/>
    </entrylist>
</rela.letter>
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>222</systemid>
    <entrylist>
        <entry key="letterno" value="500002"/>
        <entry key="leinout" value="4"/>
        <entry key="lepcode" value="IN100000"/>
        <entry key="ledate" value="2025-03-12 14:30:00.0"/>
        <entry key="lesubject" value="Re: SOMMATIE"/>
    </entrylist>
</rela.letter>
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>333</systemid>
    <entrylist>
        <entry key="letterno" value="500003"/>
        <entry key="leinout" value="6"/>
        <entry key="lepcode" value="IN100000"/>
        <entry key="ledate" value="2025-03-12 14:35:00.0"/>
        <entry key="lesubject" value="Geupload document"/>
    </entrylist>
</rela.letter>
"""


def _eml(from_addr: str, to_addr: str, subject: str, body: str) -> bytes:
    return (
        f"From: {from_addr}\r\n"
        f"To: {to_addr}\r\n"
        f"Subject: {subject}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        f"{body}\r\n"
    ).encode("utf-8")


def _build_fase2_export(tmp_path):
    """Zet een mini eml-map + xml-map neer die de echte structuur nabootst."""
    xml_dir = tmp_path / "xml"
    xml_dir.mkdir()
    (xml_dir / "a.Incasso.xml").write_text(_INCASSO_XML, encoding="utf-8")
    (xml_dir / "b.Letter.xml").write_text(_LETTER_XML_F2, encoding="utf-8")

    eml_dir = tmp_path / "eml"
    folder = eml_dir / "IN100000 Incassocenter B.V. _ Bliksem"
    folder.mkdir(parents=True)
    (folder / "500001_SOMMATIE.eml").write_bytes(
        _eml("incasso@kestinglegal.nl", "debiteur@x.nl", "SOMMATIE", "Betaal nu.")
    )
    (folder / "500002_Re_SOMMATIE.eml").write_bytes(
        _eml("debiteur@x.nl", "incasso@kestinglegal.nl", "Re: SOMMATIE", "Ik betwist dit.")
    )
    # leinout=6 → moet worden overgeslagen (geüpload document)
    (folder / "500003_document.eml").write_bytes(
        _eml("a@x.nl", "b@x.nl", "Document", "irrelevant")
    )
    # letterno niet in de XML-snapshot → moet worden overgeslagen (nieuwer)
    (folder / "599999_nieuwer.eml").write_bytes(
        _eml("a@x.nl", "b@x.nl", "Nieuwer", "na de export")
    )
    return eml_dir, xml_dir


def test_fase2_build_emails_koppelt_richting_en_scope(tmp_path):
    from scripts.basenet.import_basenet import _uid
    from scripts.basenet.import_emails import build_emails

    eml_dir, xml_dir = _build_fase2_export(tmp_path)
    rows, stats = build_emails(eml_dir, xml_dir)

    # 4 bestanden gevonden, 2 geïmporteerd (1 uit, 1 in), 2 overgeslagen.
    assert stats.total_files == 4
    assert stats.to_import == 2
    assert stats.by_direction == {"outbound": 1, "inbound": 1}
    assert stats.skip_direction == 1   # leinout=6
    assert stats.skip_no_meta == 1     # 599999 niet in XML

    by_dir = {r["direction"]: r for r in rows}
    # Koppeling: case_id == exact wat fase 1 aanmaakte voor incasso-systemid 691311.
    expected_case = _uid("case", "691311")
    assert by_dir["outbound"]["case_id"] == expected_case
    assert by_dir["inbound"]["case_id"] == expected_case
    # Dedup-sleutel op Letter.systemid, deterministische id op letterno.
    assert by_dir["outbound"]["provider_message_id"] == "basenet:111"
    assert by_dir["outbound"]["id"] == _uid("email", "500001")
    assert "betwist" in by_dir["inbound"]["body_text"].lower()


def test_fase2_import_is_idempotent_op_id(tmp_path):
    """Twee keer bouwen levert identieke deterministische id's → her-run schrijft niets dubbel."""
    from scripts.basenet.import_emails import build_emails

    eml_dir, xml_dir = _build_fase2_export(tmp_path)
    rows1, _ = build_emails(eml_dir, xml_dir)
    rows2, _ = build_emails(eml_dir, xml_dir)
    assert {r["id"] for r in rows1} == {r["id"] for r in rows2}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
