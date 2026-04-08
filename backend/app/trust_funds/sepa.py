"""SEPA pain.001.001.03 generation for trust fund disbursements.

Builds a SEPA Credit Transfer XML batch from approved trust transactions
that can be uploaded to the bank portal (Rabobank zakelijk for Kesting Legal).

References:
- ISO 20022 pain.001.001.03 schema
- Rabobank Customer SCT pain.001 implementation guide
- sepaxml library docs (https://github.com/raphaelm/python-sepaxml)
"""

from datetime import date
from decimal import Decimal

from sepaxml import SepaTransfer

from app.auth.models import Tenant
from app.shared.exceptions import BadRequestError
from app.trust_funds.models import TrustTransaction


def build_sepa_xml(
    tenant: Tenant,
    transactions: list[TrustTransaction],
    execution_date: date,
) -> bytes:
    """Generate a pain.001.001.03 SEPA Credit Transfer XML for the batch.

    All amounts in `transactions` must use Decimal with 2 decimal places.
    The Stichting Derdengelden bank account on the tenant is used as the
    debtor (initiator) account.

    Raises BadRequestError if the tenant is missing trust account fields,
    if the batch is empty, or if any transaction lacks a beneficiary IBAN.
    """
    if not tenant.trust_account_iban or not tenant.trust_account_holder:
        raise BadRequestError(
            "Stichting Derdengelden bank-gegevens ontbreken op het tenant "
            "(IBAN en tenaamstelling). Vul deze in via Instellingen → "
            "Stichting Derdengelden voordat je een SEPA-batch genereert."
        )
    if not transactions:
        raise BadRequestError("Geen transacties geselecteerd voor SEPA-export.")

    config: dict = {
        "name": tenant.trust_account_holder,
        "IBAN": tenant.trust_account_iban.replace(" ", ""),
        "batch": True,
        "currency": "EUR",
    }
    if tenant.trust_account_bic:
        config["BIC"] = tenant.trust_account_bic.replace(" ", "")

    sepa = SepaTransfer(config, clean=True)

    for tx in transactions:
        if not tx.beneficiary_iban:
            raise BadRequestError(
                f"Transactie {tx.id} mist een begunstigde IBAN — kan niet "
                f"worden opgenomen in een SEPA-batch."
            )
        if not tx.beneficiary_name:
            raise BadRequestError(
                f"Transactie {tx.id} mist een begunstigde naam."
            )
        # sepaxml expects amount in cents (integer)
        amount_cents = int((tx.amount * Decimal("100")).to_integral_value())
        payment = {
            "name": tx.beneficiary_name,
            "IBAN": tx.beneficiary_iban.replace(" ", ""),
            "amount": amount_cents,
            "execution_date": execution_date,
            "description": (tx.description or "")[:140],
            "endtoend_id": str(tx.id).replace("-", "")[:35],
        }
        sepa.add_payment(payment)

    return sepa.export(validate=True)
