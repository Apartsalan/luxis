"""Payment matching algorithm — matches bank transactions to incasso cases.

5 matching methods with confidence scores:
1. Case number (dossiernummer) in description: 95
2. Invoice number (factuurnummer) in description: 90
3. IBAN of sender matches opposing party: 85
4. Amount matches outstanding balance: 70
5. Name of sender matches opposing party: 50
"""

import re
import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.ai_agent.payment_matching_models import MATCH_CONFIDENCE, MatchMethod


@dataclass
class MatchCandidate:
    """A potential match between a transaction and a case."""

    case_id: uuid.UUID
    match_method: str
    confidence: int
    details: str


@dataclass
class CaseMatchData:
    """Case data needed for matching."""

    id: uuid.UUID
    case_number: str
    opposing_party_name: str | None
    opposing_party_iban: str | None
    outstanding_amount: Decimal
    invoice_numbers: list[str]


def _normalize(text: str) -> str:
    """Normalize text for matching: lowercase, strip whitespace, remove common chars."""
    return re.sub(r"[\s\-_./,]", "", text.lower())


def _name_similarity(name1: str, name2: str) -> bool:
    """Check if two names match (case-insensitive, partial matching).

    Returns True if:
    - Exact match (normalized)
    - One name contains the other
    - All words of the shorter name appear in the longer name
    """
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()

    if not n1 or not n2:
        return False

    # Exact match
    if n1 == n2:
        return True

    # Containment
    if n1 in n2 or n2 in n1:
        return True

    # Word overlap: all words of shorter name must appear in longer
    words1 = set(n1.split())
    words2 = set(n2.split())

    # Remove common Dutch prefixes/articles
    stop_words = {"de", "het", "van", "der", "den", "en", "bv", "b.v.", "nv", "n.v."}
    words1 -= stop_words
    words2 -= stop_words

    if not words1 or not words2:
        return False

    shorter = words1 if len(words1) <= len(words2) else words2
    longer = words1 if len(words1) > len(words2) else words2

    return shorter.issubset(longer)


def find_matches(
    transaction_description: str,
    transaction_amount: Decimal,
    counterparty_name: str | None,
    counterparty_iban: str | None,
    cases: list[CaseMatchData],
) -> list[MatchCandidate]:
    """Find matching cases for a bank transaction.

    Returns a list of match candidates sorted by confidence (highest first).
    Only returns the highest-confidence match per case.
    """
    candidates: dict[uuid.UUID, MatchCandidate] = {}
    desc_normalized = _normalize(transaction_description) if transaction_description else ""

    for case in cases:
        best_match: MatchCandidate | None = None

        # 1. Case number in description (confidence: 95)
        if case.case_number and desc_normalized:
            case_num_normalized = _normalize(case.case_number)
            if case_num_normalized and case_num_normalized in desc_normalized:
                match = MatchCandidate(
                    case_id=case.id,
                    match_method=MatchMethod.CASE_NUMBER,
                    confidence=MATCH_CONFIDENCE[MatchMethod.CASE_NUMBER],
                    details=f"Dossiernummer '{case.case_number}' gevonden in omschrijving",
                )
                if not best_match or match.confidence > best_match.confidence:
                    best_match = match

        # 2. Invoice number in description (confidence: 90)
        if case.invoice_numbers and desc_normalized:
            for inv_num in case.invoice_numbers:
                if not inv_num:
                    continue
                inv_normalized = _normalize(inv_num)
                if inv_normalized and inv_normalized in desc_normalized:
                    match = MatchCandidate(
                        case_id=case.id,
                        match_method=MatchMethod.INVOICE_NUMBER,
                        confidence=MATCH_CONFIDENCE[MatchMethod.INVOICE_NUMBER],
                        details=f"Factuurnummer '{inv_num}' gevonden in omschrijving",
                    )
                    if not best_match or match.confidence > best_match.confidence:
                        best_match = match
                    break

        # 3. IBAN match (confidence: 85)
        if counterparty_iban and case.opposing_party_iban:
            if _normalize(counterparty_iban) == _normalize(case.opposing_party_iban):
                match = MatchCandidate(
                    case_id=case.id,
                    match_method=MatchMethod.IBAN,
                    confidence=MATCH_CONFIDENCE[MatchMethod.IBAN],
                    details=f"IBAN {counterparty_iban} komt overeen met debiteur",
                )
                if not best_match or match.confidence > best_match.confidence:
                    best_match = match

        # 4. Amount match (confidence: 70)
        if case.outstanding_amount > 0 and transaction_amount > 0:
            if transaction_amount == case.outstanding_amount:
                match = MatchCandidate(
                    case_id=case.id,
                    match_method=MatchMethod.AMOUNT,
                    confidence=MATCH_CONFIDENCE[MatchMethod.AMOUNT],
                    details=f"Bedrag {transaction_amount} komt exact overeen met openstaand bedrag",
                )
                if not best_match or match.confidence > best_match.confidence:
                    best_match = match

        # 5. Name match (confidence: 50)
        if counterparty_name and case.opposing_party_name:
            if _name_similarity(counterparty_name, case.opposing_party_name):
                match = MatchCandidate(
                    case_id=case.id,
                    match_method=MatchMethod.NAME,
                    confidence=MATCH_CONFIDENCE[MatchMethod.NAME],
                    details=(
                        f"Naam '{counterparty_name}' komt overeen met "
                        f"debiteur '{case.opposing_party_name}'"
                    ),
                )
                if not best_match or match.confidence > best_match.confidence:
                    best_match = match

        if best_match:
            candidates[case.id] = best_match

    # Sort by confidence descending
    return sorted(candidates.values(), key=lambda c: c.confidence, reverse=True)
