"""S146 follow-up: backfill ai_draft_ready notifications voor bestaande AIDrafts.

Achtergrond: in S146 hebben we een hook toegevoegd in UnifiedDraftService die
bij elke AIDraft.status='generated' een 'ai_draft_ready' notification aanmaakt.
Drafts van vóór S146 hebben die notification NIET — dus zijn ze onbereikbaar
via de nieuwe CaseActionFeed widget.

Dit script:
1. Vindt alle AIDrafts met status='generated' van laatste 90 dagen
2. Skipt drafts die al een ai_draft_ready notification hebben (idempotent)
3. Maakt voor elke missende draft een notification aan, gericht op alle
   actieve users van de tenant

--dry-run flag: alleen rapporteren, niets schrijven.

Run productie:
    docker compose exec backend python scripts/backfill_draft_ready_notifications.py --dry-run
    docker compose exec backend python scripts/backfill_draft_ready_notifications.py
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import sys
from datetime import UTC, datetime, timedelta

# Import every model module up-front so SQLAlchemy can resolve relationship()
# string references (same trick as in tests/conftest.py).
for _mod in [
    "app.auth.models",
    "app.relations.models",
    "app.workflow.models",
    "app.ai_agent.followup_models",
    "app.ai_agent.intake_models",
    "app.ai_agent.models",
    "app.ai_agent.payment_matching_models",
    "app.calendar.models",
    "app.cases.models",
    "app.collections.models",
    "app.documents.models",
    "app.email.attachment_models",
    "app.email.models",
    "app.email.oauth_models",
    "app.email.synced_email_models",
    "app.exact_online.models",
    "app.incasso.models",
    "app.invoices.models",
    "app.products.models",
    "app.notifications.models",
    "app.relations.kyc_models",
    "app.time_entries.models",
    "app.trust_funds.models",
]:
    importlib.import_module(_mod)

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai_agent.models import AIDraft, DraftStatus
from app.ai_agent.prompts import strip_html
from app.cases.models import Case
from app.database import async_session
from app.notifications.models import Notification
from app.notifications.service import (
    NOTIF_AI_DRAFT_READY,
    create_draft_ready_notification,
)


async def main(dry_run: bool) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=90)
    created_total = 0
    skipped_total = 0

    async with async_session() as session:
        # Find drafts in 'generated' state from the last 90 days
        result = await session.execute(
            select(AIDraft)
            .options(selectinload(AIDraft.case))
            .where(
                AIDraft.status == DraftStatus.GENERATED,
                AIDraft.created_at >= cutoff,
            )
            .order_by(AIDraft.created_at.desc())
        )
        drafts = list(result.scalars().all())
        print(f"Found {len(drafts)} drafts in generated state since {cutoff:%Y-%m-%d}")

        for draft in drafts:
            case: Case | None = draft.case
            if not case:
                continue

            # Skip if a draft_ready notification for this case already exists
            existing = await session.execute(
                select(Notification.id).where(
                    Notification.tenant_id == draft.tenant_id,
                    Notification.case_id == case.id,
                    Notification.type == NOTIF_AI_DRAFT_READY,
                ).limit(1)
            )
            if existing.scalar_one_or_none():
                skipped_total += 1
                continue

            # No body field consistently — fall back to subject
            preview_source = (draft.body or "").strip() or (draft.subject or "")
            preview = strip_html(preview_source) if preview_source else ""
            intent = "next_step"  # historical default — exact intent isn't stored

            if dry_run:
                print(
                    f"  [DRY] would notify for draft {draft.id} on case {case.case_number}"
                )
                created_total += 1
                continue

            n = await create_draft_ready_notification(
                session,
                draft.tenant_id,
                case.id,
                case.case_number,
                intent,
                preview,
            )
            created_total += n
            print(
                f"  created {n} notification(s) for draft {draft.id} on case {case.case_number}"
            )

        if not dry_run:
            await session.commit()

    print(
        f"\nBackfill done: created={created_total}, skipped_existing={skipped_total}"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))
