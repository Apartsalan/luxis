"""S202 L4 — bijlage-caps gelden op het schema, vóór base64 gedecodeerd wordt.

Zonder dit decodeerde de code een onbegrensde base64-string volledig (en hield
die decodering in het geheugen) voordat de 3 MB-grens werd gecontroleerd. Nu
weigert Pydantic een te grote payload al bij het parsen van de request-body,
vóór er ook maar één byte gedecodeerd is.
"""

import base64

import pytest
from pydantic import ValidationError

from app.email.compose_router import (
    MAX_ATTACHMENT_B64_LEN,
    MAX_TOTAL_ATTACHMENT_SIZE,
    InlineAttachment,
    _assert_total_attachment_size,
)
from app.email.providers.base import OutgoingAttachment
from app.shared.exceptions import BadRequestError


def test_oversized_base64_rejected_before_decode():
    """Eén byte boven de toegestane gedecodeerde grootte (3 MB) -> het SCHEMA
    weigert de ruwe base64-string, niet pas na volledig decoderen."""
    too_long_b64 = "A" * (MAX_ATTACHMENT_B64_LEN + 4)
    with pytest.raises(ValidationError, match="data_base64"):
        InlineAttachment(
            filename="bijlage.pdf", data_base64=too_long_b64, content_type="application/pdf"
        )


def test_base64_at_the_cap_is_accepted():
    """De grens zelf (een geldige, gedecodeerd-precies-3MB bijlage) mag door."""
    exact_size_data = b"x" * (3 * 1024 * 1024)
    b64 = base64.b64encode(exact_size_data).decode()
    assert len(b64) == MAX_ATTACHMENT_B64_LEN
    att = InlineAttachment(filename="max.pdf", data_base64=b64, content_type="application/pdf")
    assert att.filename == "max.pdf"


def _att(size: int) -> OutgoingAttachment:
    return OutgoingAttachment(
        filename="f.pdf", data=b"x" * size, content_type="application/pdf"
    )


def test_many_small_attachments_allowed():
    """S232 (wens Arsalan): GEEN aantal-limiet meer — veel kleine bijlagen mag,
    zolang de TOTALE grootte onder de grens blijft."""
    # 50 bijlagen van 100 KB = 5 MB totaal, ruim onder de 25 MB-grens.
    _assert_total_attachment_size([_att(100 * 1024) for _ in range(50)])


def test_total_size_over_cap_rejected():
    """De echte beperking is de totale mailgrootte, niet het aantal."""
    over = MAX_TOTAL_ATTACHMENT_SIZE + 1
    with pytest.raises(BadRequestError, match="samen te groot"):
        _assert_total_attachment_size([_att(over)])


def test_total_size_at_cap_accepted():
    """Precies op de grens mag door."""
    _assert_total_attachment_size([_att(MAX_TOTAL_ATTACHMENT_SIZE)])
