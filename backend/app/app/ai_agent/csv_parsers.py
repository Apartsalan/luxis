"""CSV parsers for bank statement imports.

Supports Rabobank zakelijk CSV format (26 columns, comma-delimited).
Only credit transactions (incoming payments) are extracted since
this is a derdengeldrekening where all credits are incasso payments.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass
class ParsedTransaction:
    """A parsed bank transaction from CSV."""

    transaction_date: date
    amount: Decimal
    counterparty_name: str | None
    counterparty_iban: str | None
    description: str
    currency: str
    entry_date: date | None
    is_credit: bool


@dataclass
class ParseResult:
    """Result of parsing a bank statement CSV."""

    transactions: list[ParsedTransaction]
    account_iban: str | None
    total_rows: int
    credit_count: int
    debit_count: int
    skipped_count: int
    errors: list[str]


def parse_rabobank_csv(content: str) -> ParseResult:
    """Parse a Rabobank zakelijk CSV file.

    Rabobank CSV format (comma-delimited, 26 columns):
    0:  IBAN/BBAN (own account)
    1:  Munt (currency, e.g. "EUR")
    2:  BIC
    3:  Volgnr (sequence number)
    4:  Datum (transaction date, YYYY-MM-DD)
    5:  Rentedatum (entry date, YYYY-MM-DD)
    6:  Bedrag (amount, +/- with dot as decimal separator)
    7:  Saldo na trn (balance after transaction)
    8:  Tegenrekening IBAN/BBAN (counterparty IBAN)
    9:  Naam tegenpartij (counterparty name)
    10: Naam uiteindelijke partij (ultimate party name)
    11: Naam initiërende partij (initiating party name)
    12: BIC tegenpartij
    13: Code (transaction code)
    14: Batch ID
    15: Transactiereferentie
    16: Machtigingskenmerk
    17: Incassant ID
    18: Betalingskenmerk (payment reference)
    19: Omschrijving-1 (description line 1)
    20: Omschrijving-2
    21: Omschrijving-3
    22: Reden retour (return reason)
    23: Oorspr bedrag (original amount)
    24: Oorspr munt (original currency)
    25: Koers (exchange rate)
    """
    transactions: list[ParsedTransaction] = []
    errors: list[str] = []
    account_iban: str | None = None
    credit_count = 0
    debit_count = 0
    skipped_count = 0
    total_rows = 0

    reader = csv.reader(io.StringIO(content))

    # Skip header row if present
    first_row = next(reader, None)
    if first_row is None:
        return ParseResult(
            transactions=[],
            account_iban=None,
            total_rows=0,
            credit_count=0,
            debit_count=0,
            skipped_count=0,
            errors=["Leeg CSV-bestand"],
        )

    # Check if first row is a header by looking at column 4 (should be a date)
    is_header = False
    if first_row and len(first_row) >= 7:
        try:
            datetime.strptime(first_row[4].strip().strip('"'), "%Y-%m-%d")
        except (ValueError, IndexError):
            is_header = True

    rows_to_process = []
    if not is_header:
        rows_to_process.append(first_row)

    for row in reader:
        rows_to_process.append(row)

    for row_idx, row in enumerate(rows_to_process, start=1):
        total_rows += 1

        if len(row) < 20:
            skipped_count += 1
            errors.append(f"Rij {row_idx}: te weinig kolommen ({len(row)})")
            continue

        try:
            # Extract own account IBAN (from first valid row)
            if account_iban is None:
                raw_iban = row[0].strip().strip('"')
                if raw_iban:
                    account_iban = raw_iban

            # Parse date
            date_str = row[4].strip().strip('"')
            transaction_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Parse entry date
            entry_date_str = row[5].strip().strip('"')
            entry_date = None
            if entry_date_str:
                try:
                    entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

            # Parse amount
            amount_str = row[6].strip().strip('"').replace(",", "")
            amount = Decimal(amount_str)

            # Currency
            currency = row[1].strip().strip('"') or "EUR"

            # Counterparty
            counterparty_iban = row[8].strip().strip('"') or None
            counterparty_name = row[9].strip().strip('"') or None

            # Build description from all description fields + payment reference
            desc_parts = []
            payment_ref = row[18].strip().strip('"') if len(row) > 18 else ""
            if payment_ref:
                desc_parts.append(payment_ref)
            for i in range(19, min(22, len(row))):
                part = row[i].strip().strip('"')
                if part:
                    desc_parts.append(part)
            description = " ".join(desc_parts)

            # Determine credit/debit
            is_credit = amount > 0

            if is_credit:
                credit_count += 1
                transactions.append(
                    ParsedTransaction(
                        transaction_date=transaction_date,
                        amount=amount.copy_abs(),
                        counterparty_name=counterparty_name,
                        counterparty_iban=counterparty_iban,
                        description=description,
                        currency=currency,
                        entry_date=entry_date,
                        is_credit=True,
                    )
                )
            else:
                debit_count += 1
                # Skip debit transactions — not relevant for incasso matching

        except (ValueError, InvalidOperation) as e:
            skipped_count += 1
            errors.append(f"Rij {row_idx}: {e}")

    return ParseResult(
        transactions=transactions,
        account_iban=account_iban,
        total_rows=total_rows,
        credit_count=credit_count,
        debit_count=debit_count,
        skipped_count=skipped_count,
        errors=errors,
    )
