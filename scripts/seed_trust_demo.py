"""Seed demo trust fund transactions for manual testing of /derdengelden.

DF120 (sessie 120, Lisanne demo 2026-04-08): Arsalan needs to test the
trust funds UI without manually clicking through 10 transactions for each
test scenario. This script picks N existing active cases for a tenant and
injects realistic demo data:

- 1× approved deposit (€5000-15000) ~30 days ago
- 1× approved disbursement (€500-2000) with fictional beneficiary ~10 days ago
- 1× pending_approval disbursement (€300-800) of today (for SEPA flow test)

All seeded transactions carry reference="seed:demo:sessie120" so they can
be cleanly removed via --clean.

USAGE:
    docker compose exec backend python -m scripts.seed_trust_demo \
        --tenant-slug kesting-legal --count 3
    docker compose exec backend python -m scripts.seed_trust_demo \
        --tenant-slug kesting-legal --clean

SAFETY:
- Refuses to run on a tenant that already has > 50 trust transactions
  unless --force is passed (production safety net)
- Requires --confirm-production when APP_ENV=production
"""

import argparse
import asyncio
import os
import random
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

# Import main so SQLAlchemy registers all model relationships before queries.
from app import main as _main_module  # noqa: F401
from app.auth.models import Tenant, User
from app.cases.models import Case
from app.database import async_session as async_session_maker
from app.trust_funds.models import TrustTransaction

SEED_REFERENCE = "seed:demo:sessie120"

FAKE_BENEFICIARIES = [
    ("Jansen Vastgoed B.V.", "NL02ABNA0123456789"),
    ("Pieter de Vries", "NL44RABO0654321098"),
    ("Mendoza Holding", "NL91INGB0001234567"),
    ("Stichting Vrienden van X", "NL18ABNA0987654321"),
    ("Boekhoud B.V.", "NL62RABO0112233445"),
]


async def _get_tenant_and_admin(
    db: AsyncSession, slug: str
) -> tuple[Tenant, User]:
    """Resolve tenant by slug and pick the first admin user as transaction creator."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        sys.exit(f"Tenant met slug '{slug}' niet gevonden")

    user_result = await db.execute(
        select(User)
        .where(User.tenant_id == tenant.id, User.is_active.is_(True))
        .order_by(User.created_at.asc())
        .limit(1)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        sys.exit(f"Geen actieve gebruiker gevonden voor tenant {slug}")
    return tenant, user


async def _check_existing_count(db: AsyncSession, tenant_id) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(TrustTransaction)
        .where(TrustTransaction.tenant_id == tenant_id)
    )
    return int(result.scalar_one())


async def _pick_cases(db: AsyncSession, tenant_id, count: int) -> list[Case]:
    """Pick N active cases that have a client and are not already heavily seeded."""
    result = await db.execute(
        select(Case)
        .where(
            Case.tenant_id == tenant_id,
            Case.status != "afgesloten",
        )
        .order_by(Case.created_at.desc())
        .limit(count * 3)  # over-fetch in case some are already seeded
    )
    candidates = list(result.scalars().all())
    if len(candidates) < count:
        sys.exit(
            f"Niet genoeg actieve dossiers gevonden ({len(candidates)} < {count})"
        )

    # Filter out cases that already have a seeded transaction
    already_seeded_result = await db.execute(
        select(TrustTransaction.case_id)
        .where(
            TrustTransaction.tenant_id == tenant_id,
            TrustTransaction.reference == SEED_REFERENCE,
        )
        .distinct()
    )
    seeded_case_ids = {row[0] for row in already_seeded_result.all()}
    fresh = [c for c in candidates if c.id not in seeded_case_ids]
    if len(fresh) < count:
        sys.exit(
            f"Slechts {len(fresh)} ongeseede dossiers beschikbaar (gevraagd: {count}). "
            f"Run met --clean om eerdere seeds te verwijderen."
        )
    return fresh[:count]


async def seed(
    slug: str,
    count: int,
    *,
    force: bool,
    confirm_production: bool,
) -> None:
    if os.environ.get("APP_ENV") == "production" and not confirm_production:
        sys.exit(
            "APP_ENV=production. Voeg --confirm-production toe om door te gaan."
        )

    async with async_session_maker() as db:
        tenant, admin = await _get_tenant_and_admin(db, slug)

        existing = await _check_existing_count(db, tenant.id)
        if existing > 50 and not force:
            sys.exit(
                f"Tenant {slug} heeft al {existing} trust transactions. "
                f"Gebruik --force om alsnog door te gaan."
            )

        cases = await _pick_cases(db, tenant.id, count)

        deposit_total = 0
        disbursement_total = 0
        pending_total = 0

        for i, case in enumerate(cases):
            beneficiary_name, beneficiary_iban = FAKE_BENEFICIARIES[
                i % len(FAKE_BENEFICIARIES)
            ]

            # 1. Approved deposit ~30 days ago
            deposit_amount = Decimal(str(random.randint(5000, 15000))) + Decimal(
                f"0.{random.randint(0, 99):02d}"
            )
            now = datetime.now(UTC)
            deposit_date = (date.today() - timedelta(days=30)).isoformat()
            db.add(
                TrustTransaction(
                    tenant_id=tenant.id,
                    case_id=case.id,
                    contact_id=case.client_id,
                    transaction_type="deposit",
                    amount=deposit_amount,
                    transaction_date=date.today() - timedelta(days=30),
                    description=f"[demo] Storting van cliënt {deposit_date}",
                    payment_method="bank",
                    reference=SEED_REFERENCE,
                    status="approved",
                    approved_by_1=admin.id,
                    approved_at_1=now - timedelta(days=30),
                    approved_by_2=admin.id,
                    approved_at_2=now - timedelta(days=30),
                    created_by=admin.id,
                )
            )
            deposit_total += 1

            # 2. Approved disbursement ~10 days ago
            disb_amount = Decimal(str(random.randint(500, 2000))) + Decimal(
                f"0.{random.randint(0, 99):02d}"
            )
            db.add(
                TrustTransaction(
                    tenant_id=tenant.id,
                    case_id=case.id,
                    contact_id=case.client_id,
                    transaction_type="disbursement",
                    amount=disb_amount,
                    transaction_date=date.today() - timedelta(days=10),
                    description=f"[demo] Uitbetaling aan {beneficiary_name}",
                    payment_method="bank",
                    reference=SEED_REFERENCE,
                    beneficiary_name=beneficiary_name,
                    beneficiary_iban=beneficiary_iban,
                    status="approved",
                    approved_by_1=admin.id,
                    approved_at_1=now - timedelta(days=10),
                    approved_by_2=admin.id,
                    approved_at_2=now - timedelta(days=10),
                    created_by=admin.id,
                )
            )
            disbursement_total += 1

            # 3. Pending disbursement (today) — for SEPA-flow test
            pending_amount = Decimal(str(random.randint(300, 800))) + Decimal(
                f"0.{random.randint(0, 99):02d}"
            )
            db.add(
                TrustTransaction(
                    tenant_id=tenant.id,
                    case_id=case.id,
                    contact_id=case.client_id,
                    transaction_type="disbursement",
                    amount=pending_amount,
                    transaction_date=date.today(),
                    description=f"[demo] Geplande uitbetaling aan {beneficiary_name}",
                    payment_method="bank",
                    reference=SEED_REFERENCE,
                    beneficiary_name=beneficiary_name,
                    beneficiary_iban=beneficiary_iban,
                    status="pending_approval",
                    created_by=admin.id,
                )
            )
            pending_total += 1

        await db.commit()
        print(
            f"Seeded {deposit_total} deposits, {disbursement_total} disbursements, "
            f"{pending_total} pending op {len(cases)} dossiers van tenant {slug}."
        )
        print(f"Case IDs: {[str(c.id) for c in cases]}")


async def clean(slug: str, *, confirm_production: bool) -> None:
    if os.environ.get("APP_ENV") == "production" and not confirm_production:
        sys.exit(
            "APP_ENV=production. Voeg --confirm-production toe om door te gaan."
        )

    async with async_session_maker() as db:
        tenant_result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        tenant = tenant_result.scalar_one_or_none()
        if tenant is None:
            sys.exit(f"Tenant met slug '{slug}' niet gevonden")

        result = await db.execute(
            select(TrustTransaction).where(
                TrustTransaction.tenant_id == tenant.id,
                TrustTransaction.reference == SEED_REFERENCE,
            )
        )
        rows = list(result.scalars().all())
        for tx in rows:
            await db.delete(tx)
        await db.commit()
        print(f"Removed {len(rows)} demo transactions from tenant {slug}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-slug", required=True)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--confirm-production", action="store_true")
    args = parser.parse_args()

    if args.clean:
        asyncio.run(
            clean(args.tenant_slug, confirm_production=args.confirm_production)
        )
    else:
        asyncio.run(
            seed(
                args.tenant_slug,
                args.count,
                force=args.force,
                confirm_production=args.confirm_production,
            )
        )


if __name__ == "__main__":
    main()
