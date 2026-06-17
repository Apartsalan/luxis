"""Shared validators for Dutch business identifiers (audit #66, #69).

Centralised so the relations (contacts) and trust-funds schemas validate
KvK / BTW / IBAN / e-mail the same way. Each helper *normalises* then
validates and returns the cleaned value; it raises ``ValueError`` on a
malformed value. Callers map an empty/whitespace value to ``None`` before
calling (see ``optional`` below) — these helpers reject the empty string.
"""

import re

# IBAN: 2 letters (country) + 2 check digits + 10-30 alnum (BBAN).
_IBAN_RE = re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}")
# Dutch Chamber of Commerce number: exactly 8 digits.
_KVK_RE = re.compile(r"\d{8}")
# Dutch VAT number: NL + 9 digits + B + 2 digits (e.g. NL123456789B01).
_BTW_NL_RE = re.compile(r"NL\d{9}B\d{2}")
# Pragmatic single-address e-mail check (no external dependency).
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def validate_iban(value: str) -> str:
    """Normalise and mod-97 validate an IBAN (audit #69).

    A disbursement with an invalid beneficiary IBAN would otherwise only fail
    at the bank after SEPA upload — far too late for derdengelden.
    """
    v = value.replace(" ", "").upper()
    if not _IBAN_RE.fullmatch(v):
        raise ValueError("Ongeldige IBAN: verkeerd formaat")
    rearranged = v[4:] + v[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    if int(digits) % 97 != 1:
        raise ValueError("Ongeldige IBAN: controlegetal klopt niet — controleer op typefouten")
    return v


def validate_kvk(value: str) -> str:
    """Validate a Dutch Chamber of Commerce (KvK) number — 8 digits."""
    v = value.replace(" ", "")
    if not _KVK_RE.fullmatch(v):
        raise ValueError("Ongeldig KvK-nummer: moet uit 8 cijfers bestaan")
    return v


def validate_btw(value: str) -> str:
    """Validate a Dutch VAT (BTW) number — format NL123456789B01."""
    v = value.replace(" ", "").replace(".", "").upper()
    if not _BTW_NL_RE.fullmatch(v):
        raise ValueError("Ongeldig BTW-nummer: verwacht formaat NL123456789B01")
    return v


def validate_email(value: str) -> str:
    """Validate an e-mail address (lenient single-address check)."""
    v = value.strip()
    if not _EMAIL_RE.fullmatch(v):
        raise ValueError("Ongeldig e-mailadres")
    return v


def optional(value: str | None, validator) -> str | None:
    """Run ``validator`` only on a non-empty value; map empty/blank to None.

    Keeps these identifier fields optional and non-breaking: a blank string
    from the frontend is stored as NULL rather than rejected.
    """
    if value is None or not str(value).strip():
        return None
    return validator(value)
