"""Regressietest voor de BaseNet-factuurimport-classificatie (S201/S214).

Toetst de risicovolle pure logica — datumparser, derdengelden-herkenning,
statusmapping en de BaseNet-regelformule — zonder de volledige export. De
integrale telling (439/90/630/€302.750,39) wordt door de droogloop op de
export bewezen; deze test vangt regressies in de losse beslisregels.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from scripts.basenet.import_invoices import (
    CENT,
    _date,
    _dec,
    _is_derdengelden,
    _status_for,
)
from scripts.basenet.parse import BaseNetRecord


def _line(prodnr: str) -> BaseNetRecord:
    return BaseNetRecord(entity="OutgoingInvoiceLine", systemid="1", fields={"inlprodnr": prodnr})


def _kop(**f) -> BaseNetRecord:
    return BaseNetRecord(entity="OutgoingInvoice", systemid="1", fields=f)


def test_date_parsing():
    assert _date("2024-11-29 16:39:40.0") == date(2024, 11, 29)  # datetime → date
    assert _date("2024-12-20") == date(2024, 12, 20)             # date-only
    assert _date("") is None
    assert _date(None) is None


def test_derdengelden_recognition():
    # Product 100013 ("Verrekening incassodossiers") = derdengelden.
    assert _is_derdengelden("100100", [_line("100013")]) is True
    # De twee correctieposten zonder 100013-regel horen er ook bij.
    assert _is_derdengelden("100242", [_line("100000")]) is True
    assert _is_derdengelden("100363", [_line("100039")]) is True
    # Gewone honorariumfactuur is géén derdengeld.
    assert _is_derdengelden("100100", [_line("100000")]) is False


def test_status_mapping():
    # Betaalde gewone factuur → paid.
    assert _status_for(_kop(invpaidstatus="1"), "invoice", date(2026, 1, 1)) == "paid"
    # Open + vervaldatum vóór de peildatum → overdue.
    assert _status_for(_kop(invpaidstatus="0"), "invoice", date(2026, 1, 1)) == "overdue"
    # Open + vervaldatum ná de peildatum → sent.
    assert _status_for(_kop(invpaidstatus="0"), "invoice", date(2026, 12, 31)) == "sent"
    # Nul-factuur (status 9) → paid.
    assert _status_for(_kop(invpaidstatus="9"), "invoice", date(2026, 1, 1)) == "paid"
    # Creditnota: betaald → paid, anders sent (nooit overdue).
    assert _status_for(_kop(invpaidstatus="1"), "credit_note", date(2020, 1, 1)) == "paid"
    assert _status_for(_kop(invpaidstatus="0"), "credit_note", date(2020, 1, 1)) == "sent"


def test_basenet_line_formula():
    # 100006: 1548,00 × 1 × 1,21 = 1873,08 (btw-code 1a), exact per regel.
    netto = (_dec("1.00") * _dec("1548.00")).quantize(CENT, ROUND_HALF_UP)
    assert netto == Decimal("1548.00")
    bruto = (netto * Decimal("1.21")).quantize(CENT, ROUND_HALF_UP)
    assert bruto == Decimal("1873.08")
