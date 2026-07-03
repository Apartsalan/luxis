"""BaseNet fase 3 — gerichte classificatie + verweer-bibliotheek backfill (S168).

Doel: de verweer-antwoord-bibliotheek voeden met KANDIDATEN uit Lisanne's echte
correspondentie. De backfill eist per uitgaand verweer-antwoord dat de meest recente
INKOMENDE mail ervóór een classificatie met een verweer-categorie heeft. Geïmporteerde
archief-mails hebben die niet → hier classificeren we ALLEEN die voorafgaande inkomende
mails (niet alle 3.100 — dat zou onnodig veel AI-kosten zijn; het sleepnet mijdt archief
sinds de fix in deze sessie). Daarna draait de backfill die kandidaten maakt.

Idempotent: classify_email slaat al-geclassificeerde mails over; de backfill dedupt op
bron-mail. Her-runnen is veilig.

Draait ín de prod-container:
    python -m scripts.basenet.classify_and_backfill            # dry-run: toont aantal
    python -m scripts.basenet.classify_and_backfill --execute  # classificeert + backfill

Kosten: Claude Haiku 4.5, ~1 call per doel-mail.
"""

from __future__ import annotations

# Alle ORM-modellen importeren zodat de SQLAlchemy-mapper volledig configureert
# (anders faalt bv. Case->Contact). Zelfde set als alembic/env.py.
from app.auth.models import Tenant, User  # noqa: F401
from app.cases.models import Case, CaseActivity, CaseParty  # noqa: F401
from app.collections.models import Claim, Payment, PaymentArrangement  # noqa: F401
from app.documents.models import DocumentTemplate, GeneratedDocument  # noqa: F401
from app.email.attachment_models import EmailAttachment  # noqa: F401
from app.email.models import EmailLog  # noqa: F401
from app.email.oauth_models import EmailAccount  # noqa: F401
from app.email.synced_email_models import SyncedEmail  # noqa: F401
from app.ai_agent.followup_models import FollowupRecommendation  # noqa: F401
from app.ai_agent.intake_models import IntakeRequest  # noqa: F401
from app.ai_agent.models import AIDraft, EmailClassification, ResponseTemplate  # noqa: F401
from app.calendar.models import CalendarEvent  # noqa: F401
from app.exact_online.models import ExactOnlineConnection, ExactSyncLog  # noqa: F401
from app.incasso.models import IncassoPipelineStep, StepTransition  # noqa: F401
from app.invoices.models import Expense, Invoice, InvoiceLine, InvoicePayment  # noqa: F401
from app.notifications.models import Notification  # noqa: F401
from app.products.models import Product  # noqa: F401
from app.relations.kyc_models import KycVerification  # noqa: F401
from app.relations.models import Contact, ContactLink, ContactTerms  # noqa: F401
from app.time_entries.models import TimeEntry  # noqa: F401
from app.trust_funds.models import TrustTransaction  # noqa: F401
from app.workflow.models import WorkflowRule, WorkflowStatus, WorkflowTask  # noqa: F401

import argparse  # noqa: E402
import asyncio  # noqa: E402

from sqlalchemy import text  # noqa: E402

from app.ai_agent.learned_answers import (  # noqa: E402
    _looks_like_rebuttal,
    _rebuttal_substance,
    backfill_learned_answers,
    extract_rebuttal,
)
from app.ai_agent.prompts import strip_html  # noqa: E402
from app.ai_agent.service import classify_email  # noqa: E402
from app.database import async_session  # noqa: E402


async def _target_inbound_ids(db, tenant_id) -> list:
    """De inkomende mails die vlak vóór een substantieel uitgaand verweer-antwoord kwamen.

    Exact de filter die de backfill straks nodig heeft: een uitgaande mail telt alleen
    als hij een echte weerlegging bevat (_looks_like_rebuttal) met genoeg substantie
    (>=60 tekens na het strippen van intro-boilerplate). Per zo'n mail pakken we de
    meest recente inkomende mail ervóór op hetzelfde dossier."""
    outbound = (
        await db.execute(
            text(
                "SELECT case_id, email_date, subject, body_text, body_html "
                "FROM synced_emails WHERE tenant_id=:t AND direction='outbound' "
                "AND case_id IS NOT NULL AND is_bounce=false"
            ),
            {"t": tenant_id},
        )
    ).all()

    ids: list = []
    seen: set = set()
    for row in outbound:
        body = row.body_text or strip_html(row.body_html or "") or ""
        if " XXX " in body:
            continue
        if not _looks_like_rebuttal(row.subject, body):
            continue
        core = extract_rebuttal(row.subject, body)
        if len(_rebuttal_substance(core)) < 60:
            continue
        inbound = (
            await db.execute(
                text(
                    "SELECT id FROM synced_emails WHERE tenant_id=:t AND case_id=:c "
                    "AND direction='inbound' AND email_date <= :b "
                    "ORDER BY email_date DESC LIMIT 1"
                ),
                {"t": tenant_id, "c": row.case_id, "b": row.email_date},
            )
        ).first()
        if inbound and inbound[0] not in seen:
            seen.add(inbound[0])
            ids.append(inbound[0])
    return ids


async def run(execute: bool, backfill_only: bool = False) -> None:
    async with async_session() as db:
        tenants = (await db.execute(text("SELECT id FROM tenants"))).all()
        if len(tenants) != 1:
            raise SystemExit(f"Meerdere/geen tenants ({len(tenants)}).")
        tenant_id = tenants[0][0]

        # Her-oogst na drempel-fixes: classificaties staan er al, alleen backfill opnieuw.
        if backfill_only:
            added = await backfill_learned_answers(db, tenant_id)
            await db.commit()
            print(f"Backfill: {added} nieuwe verweer-KANDIDATEN in 'Slim leren'.")
            return

        ids = await _target_inbound_ids(db, tenant_id)
        print(f"Te classificeren inkomende mails: {len(ids)}")
        if not execute:
            print("(dry-run — geen AI-calls, geen kosten. Draai --execute om te classificeren.)")
            return

        classified = 0
        for i, eid in enumerate(ids, 1):
            c = await classify_email(db, eid, tenant_id)
            await db.commit()
            if c is not None:
                classified += 1
            if i % 25 == 0:
                print(f"  ... {i}/{len(ids)} verwerkt ({classified} nieuw geclassificeerd)")
        print(f"Klaar met classificeren: {classified} nieuw ({len(ids) - classified} al gedaan/leeg).")

        added = await backfill_learned_answers(db, tenant_id)
        await db.commit()
        print(f"Backfill: {added} nieuwe verweer-KANDIDATEN in 'Slim leren'.")


def main() -> None:
    p = argparse.ArgumentParser(description="BaseNet fase 3: gerichte classificatie + backfill")
    p.add_argument("--execute", action="store_true", help="Classificeer + backfill (anders dry-run)")
    p.add_argument("--backfill-only", action="store_true",
                   help="Sla classificatie over, draai alleen de backfill (her-oogst na fixes)")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute or args.backfill_only, backfill_only=args.backfill_only))


if __name__ == "__main__":
    main()
