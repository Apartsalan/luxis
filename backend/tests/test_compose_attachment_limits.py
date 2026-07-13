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
    MAX_ATTACHMENTS,
    ComposeRequest,
    InlineAttachment,
)


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


def test_too_many_inline_attachments_rejected_by_schema():
    """Meer dan MAX_ATTACHMENTS items in de lijst -> het schema weigert al,
    vóór de handmatige teller in _resolve_attachments ooit bereikt wordt."""
    tiny_b64 = base64.b64encode(b"x").decode()
    items = [
        {"filename": f"f{i}.pdf", "data_base64": tiny_b64, "content_type": "application/pdf"}
        for i in range(MAX_ATTACHMENTS + 1)
    ]
    with pytest.raises(ValidationError, match="inline_attachments"):
        ComposeRequest(
            to=["debiteur@example.nl"],
            subject="Test",
            body_html="<p>test</p>",
            inline_attachments=items,
        )
