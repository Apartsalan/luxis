"""Exact Online sync service — one-way push of contacts, invoices, and payments.

All sync operations are idempotent: entities already in exact_sync_log are skipped.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.email.token_encryption import decrypt_token, encrypt_token
from app.exact_online.models import ExactOnlineConnection, ExactSyncLog
from app.exact_online.provider import ExactOnlineProvider, ExactRateLimitError, ExactTokens
from app.invoices.models import Invoice, InvoicePayment
from app.relations.models import Contact

logger = logging.getLogger(__name__)


async def get_connection(db: AsyncSession, tenant_id: uuid.UUID) -> ExactOnlineConnection | None:
    """Get the active Exact Online connection for a tenant."""
    result = await db.execute(
        select(ExactOnlineConnection).where(
            ExactOnlineConnection.tenant_id == tenant_id,
            ExactOnlineConnection.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def get_valid_token(
    db: AsyncSession, conn: ExactOnlineConnection
) -> str:
    """Get a valid access token, refreshing if expired.

    Exact Online tokens expire every ~10 minutes, so we refresh aggressively
    with a 2-minute buffer.
    """
    if conn.token_expiry and conn.token_expiry > datetime.now(UTC) + timedelta(minutes=2):
        return decrypt_token(conn.access_token_enc)

    logger.info("Exact Online token verlopen, verversing gestart...")
    provider = ExactOnlineProvider()
    refresh_token = decrypt_token(conn.refresh_token_enc)

    new_tokens = await provider.refresh_access_token(refresh_token)

    conn.access_token_enc = encrypt_token(new_tokens.access_token)
    conn.refresh_token_enc = encrypt_token(new_tokens.refresh_token)
    conn.token_expiry = datetime.now(UTC) + timedelta(seconds=new_tokens.expires_in)
    await db.flush()

    logger.info("Exact Online token ververst")
    return new_tokens.access_token


async def _get_sync_log(
    db: AsyncSession, tenant_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID
) -> ExactSyncLog | None:
    """Check if an entity has already been synced."""
    result = await db.execute(
        select(ExactSyncLog).where(
            ExactSyncLog.tenant_id == tenant_id,
            ExactSyncLog.entity_type == entity_type,
            ExactSyncLog.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


async def _create_sync_log(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    exact_id: str,
    exact_number: str | None = None,
    sync_status: str = "synced",
    error_message: str | None = None,
) -> ExactSyncLog:
    """Create a sync log entry."""
    log = ExactSyncLog(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        exact_id=exact_id,
        exact_number=exact_number,
        sync_status=sync_status,
        error_message=error_message,
    )
    db.add(log)
    await db.flush()
    return log


# ── Contact Sync ─────────────────────────────────────────────────────────────


async def sync_contact(
    db: AsyncSession,
    conn: ExactOnlineConnection,
    contact: Contact,
) -> str | None:
    """Push a single contact to Exact Online as a debtor account.

    Returns the Exact account ID, or None on failure.
    """
    existing = await _get_sync_log(db, conn.tenant_id, "contact", contact.id)
    if existing and existing.sync_status == "synced":
        return existing.exact_id

    provider = ExactOnlineProvider()
    token = await get_valid_token(db, conn)

    account_data = {
        "Name": contact.name,
        "Status": "C",  # Customer
        "Country": "NL",
    }
    if contact.email:
        account_data["Email"] = contact.email
    if contact.kvk_number:
        account_data["ChamberOfCommerce"] = contact.kvk_number
    if contact.btw_number:
        account_data["VATNumber"] = contact.btw_number
    if contact.visit_address:
        account_data["AddressLine1"] = contact.visit_address
    if contact.visit_postcode:
        account_data["Postcode"] = contact.visit_postcode
    if contact.visit_city:
        account_data["City"] = contact.visit_city
    if contact.phone:
        account_data["Phone"] = contact.phone

    try:
        result = await provider.find_account_by_name(token, conn.division_id, contact.name)
        if result:
            exact_id = result["ID"]
            logger.info(f"Contact '{contact.name}' bestaat al in Exact: {exact_id}")
        else:
            result = await provider.create_account(token, conn.division_id, account_data)
            exact_id = result["ID"]
            logger.info(f"Contact '{contact.name}' aangemaakt in Exact: {exact_id}")

        await _create_sync_log(db, conn.tenant_id, "contact", contact.id, exact_id)
        return exact_id

    except Exception as e:
        logger.error(f"Contact sync mislukt voor '{contact.name}': {e}")
        await _create_sync_log(
            db, conn.tenant_id, "contact", contact.id,
            exact_id="", sync_status="error", error_message=str(e),
        )
        return None


# ── Invoice Sync ─────────────────────────────────────────────────────────────


async def sync_invoice(
    db: AsyncSession,
    conn: ExactOnlineConnection,
    invoice: Invoice,
) -> str | None:
    """Push a single invoice to Exact Online as a sales invoice.

    Prerequisites: contact must be synced first, GL account must be configured.
    Returns the Exact invoice ID, or None on failure.
    """
    existing = await _get_sync_log(db, conn.tenant_id, "invoice", invoice.id)
    if existing and existing.sync_status == "synced":
        return existing.exact_id

    if not conn.default_revenue_gl:
        logger.error("Geen omzet-grootboekrekening geconfigureerd")
        return None

    # Ensure contact is synced
    contact_exact_id = await sync_contact(db, conn, invoice.contact)
    if not contact_exact_id:
        logger.error(f"Contact sync nodig voor factuur {invoice.invoice_number}")
        return None

    provider = ExactOnlineProvider()
    token = await get_valid_token(db, conn)

    # Build invoice lines
    invoice_lines = []
    for line in invoice.lines:
        exact_line = {
            "Description": line.description,
            "Quantity": float(line.quantity),
            "UnitPrice": float(line.unit_price),
            "GLAccount": conn.default_revenue_gl,
        }
        # Map BTW percentage to a VATCode
        # Common Dutch codes: 1 = 21%, 2 = 9%, 3 = 0%
        # These should be fetched from Exact and cached, but for now use description-based lookup
        if line.btw_percentage == Decimal("0.00"):
            exact_line["VATCode"] = "0"
        # Default: let Exact use the account's default VAT code
        invoice_lines.append(exact_line)

    invoice_data = {
        "InvoiceTo": contact_exact_id,
        "OrderDate": invoice.invoice_date.isoformat(),
        "Description": f"Factuur {invoice.invoice_number}",
        "YourRef": invoice.invoice_number,
        "Currency": "EUR",
        "SalesInvoiceLines": invoice_lines,
    }

    if conn.sales_journal_code:
        invoice_data["Journal"] = conn.sales_journal_code

    try:
        result = await provider.create_sales_invoice(
            token, conn.division_id, invoice_data
        )
        exact_id = result.get("InvoiceID", result.get("EntryID", ""))
        exact_number = result.get("InvoiceNumber", "")
        logger.info(
            f"Factuur {invoice.invoice_number} gesynchroniseerd naar Exact: {exact_id}"
        )

        await _create_sync_log(
            db, conn.tenant_id, "invoice", invoice.id,
            exact_id=str(exact_id), exact_number=str(exact_number),
        )
        return str(exact_id)

    except Exception as e:
        logger.error(f"Factuur sync mislukt voor {invoice.invoice_number}: {e}")
        await _create_sync_log(
            db, conn.tenant_id, "invoice", invoice.id,
            exact_id="", sync_status="error", error_message=str(e),
        )
        return None


# ── Payment Sync ─────────────────────────────────────────────────────────────


async def sync_payment(
    db: AsyncSession,
    conn: ExactOnlineConnection,
    payment: InvoicePayment,
    invoice: Invoice,
) -> str | None:
    """Push a single payment to Exact Online as a bank entry.

    Note: Exact Online does not support programmatic reconciliation.
    Payments are booked as standalone bank entries.
    """
    existing = await _get_sync_log(db, conn.tenant_id, "payment", payment.id)
    if existing and existing.sync_status == "synced":
        return existing.exact_id

    if not conn.bank_journal_code:
        logger.error("Geen bankjournaal geconfigureerd")
        return None

    provider = ExactOnlineProvider()
    token = await get_valid_token(db, conn)

    entry_data = {
        "Journal": conn.bank_journal_code,
        "BankEntryLines": [
            {
                "AmountDC": float(payment.amount),
                "Date": payment.payment_date.isoformat(),
                "Description": f"Betaling {invoice.invoice_number}",
            }
        ],
    }

    try:
        result = await provider.create_bank_entry(
            token, conn.division_id, entry_data
        )
        exact_id = result.get("EntryID", "")
        logger.info(
            f"Betaling voor {invoice.invoice_number} gesynchroniseerd naar Exact: {exact_id}"
        )

        await _create_sync_log(
            db, conn.tenant_id, "payment", payment.id, exact_id=str(exact_id),
        )
        return str(exact_id)

    except Exception as e:
        logger.error(f"Betaling sync mislukt: {e}")
        await _create_sync_log(
            db, conn.tenant_id, "payment", payment.id,
            exact_id="", sync_status="error", error_message=str(e),
        )
        return None


# ── Bulk Sync ────────────────────────────────────────────────────────────────


async def sync_all(
    db: AsyncSession, tenant_id: uuid.UUID
) -> dict:
    """Sync all unsynchronized contacts, invoices, and payments.

    Returns a summary dict with counts and errors.
    """
    conn = await get_connection(db, tenant_id)
    if not conn:
        return {"success": False, "message": "Geen Exact Online koppeling gevonden"}

    errors = []
    synced_contacts = 0
    synced_invoices = 0
    synced_payments = 0

    # 1. Sync contacts that have invoices
    invoices_result = await db.execute(
        select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.is_active.is_(True),
            Invoice.status.in_(["sent", "overdue", "partially_paid", "paid"]),
        )
    )
    invoices = invoices_result.scalars().all()

    # Collect unique contacts
    contact_ids_seen = set()
    contacts_to_sync = []
    for inv in invoices:
        if inv.contact_id not in contact_ids_seen:
            contact_ids_seen.add(inv.contact_id)
            contacts_to_sync.append(inv.contact)

    for contact in contacts_to_sync:
        try:
            result = await sync_contact(db, conn, contact)
            if result:
                synced_contacts += 1
        except ExactRateLimitError:
            errors.append("Rate limit bereikt — probeer later opnieuw")
            break
        except Exception as e:
            errors.append(f"Contact '{contact.name}': {e}")

    # 2. Sync invoices
    for invoice in invoices:
        try:
            result = await sync_invoice(db, conn, invoice)
            if result:
                synced_invoices += 1
        except ExactRateLimitError:
            errors.append("Rate limit bereikt — probeer later opnieuw")
            break
        except Exception as e:
            errors.append(f"Factuur {invoice.invoice_number}: {e}")

    # 3. Sync payments
    for invoice in invoices:
        for payment in invoice.payments:
            try:
                result = await sync_payment(db, conn, payment, invoice)
                if result:
                    synced_payments += 1
            except ExactRateLimitError:
                errors.append("Rate limit bereikt — probeer later opnieuw")
                break
            except Exception as e:
                errors.append(f"Betaling {payment.id}: {e}")

    # Update last sync timestamp
    conn.last_sync_at = datetime.now(UTC)
    await db.flush()

    return {
        "success": len(errors) == 0,
        "message": f"Sync voltooid: {synced_contacts} contacten, {synced_invoices} facturen, {synced_payments} betalingen",
        "synced_contacts": synced_contacts,
        "synced_invoices": synced_invoices,
        "synced_payments": synced_payments,
        "errors": errors,
    }
