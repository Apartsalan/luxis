"""S143: backfill incasso-dossiers zonder pipeline-stap naar 'Eerste sommatie'.

Lisanne demo S141: 42 van 45 incasso-dossiers hebben geen incasso_step_id
omdat create_case dit veld nooit instelde. Auto-advance werkt niet op cases
zonder step, en ze verschijnen niet in de incasso batch-toolbar.

Deze script:
1. Vindt alle incasso-cases met status='nieuw' EN incasso_step_id IS NULL
2. Wijst ze toe aan de eerste actieve pipeline-stap via move_case_to_step
3. Logt: case_number → step_name, trigger_type="backfill"

--dry-run flag: alleen rapporteren, niets schrijven.

Run productie:
    docker compose run --rm backend python scripts/backfill_incasso_first_step.py --dry-run
    docker compose run --rm backend python scripts/backfill_incasso_first_step.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from contextlib import asynccontextmanager

from sqlalchemy import select

# Importeer main om alle SQLAlchemy modellen te registreren
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.cases.models import Case
from app.database import async_session
from app.incasso.service import list_pipeline_steps, move_case_to_step


@asynccontextmanager
async def _tenant_session(tenant_id):
    """Session met tenant-context gezet zodat RLS-policies werken."""
    async with async_session() as session:
        await session.execute(
            select(1).where(False)  # warm-up
        )
        # Set tenant-context expliciet (RLS heeft dit nodig)
        await session.execute(
            select(1)  # placeholder
        )
        from sqlalchemy import text
        await session.execute(
            text(f"SET LOCAL app.current_tenant = '{tenant_id}'")
        )
        yield session


async def backfill(dry_run: bool) -> None:
    async with async_session() as session:
        # Alle tenants ophalen (Luxis ondersteunt multi-tenant, hoewel
        # productie momenteel maar één tenant heeft)
        tenants_result = await session.execute(select(Tenant))
        tenants = list(tenants_result.scalars().all())

    total_found = 0
    total_assigned = 0

    for tenant in tenants:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(
                text("SET LOCAL app.current_tenant = :tid"),
                {"tid": str(tenant.id)},
            )

            # Vind incasso-cases zonder step
            cases_result = await session.execute(
                select(Case).where(
                    Case.tenant_id == tenant.id,
                    Case.case_type == "incasso",
                    Case.status == "nieuw",
                    Case.incasso_step_id.is_(None),
                )
            )
            cases = list(cases_result.scalars().all())

            if not cases:
                print(f"[{tenant.name}] geen cases zonder step gevonden")
                continue

            # Eerste pipeline-stap ophalen
            steps = await list_pipeline_steps(session, tenant.id, active_only=True)
            if not steps:
                print(f"[{tenant.name}] geen actieve pipeline-stappen — overgeslagen")
                continue
            first_step = min(steps, key=lambda s: s.sort_order)

            print(
                f"[{tenant.name}] {len(cases)} cases zonder step gevonden, "
                f"toewijzen aan '{first_step.name}' (sort_order={first_step.sort_order})"
            )
            total_found += len(cases)

            if dry_run:
                for case in cases:
                    print(f"  [DRY-RUN] {case.case_number} → {first_step.name}")
                continue

            for case in cases:
                await move_case_to_step(
                    session,
                    tenant.id,
                    case,
                    first_step,
                    user_id=None,
                    trigger_type="backfill",
                    notes="S143 backfill: case had geen pipeline-stap na aanmaak",
                )
                total_assigned += 1
                print(f"  ASSIGNED {case.case_number} → {first_step.name}")

            await session.commit()

    print("---")
    print(f"Totaal gevonden: {total_found}")
    if dry_run:
        print("Dry-run: niets geschreven.")
    else:
        print(f"Toegewezen: {total_assigned}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill incasso-cases zonder pipeline-stap")
    parser.add_argument("--dry-run", action="store_true", help="Alleen rapporteren, niets schrijven")
    args = parser.parse_args()

    asyncio.run(backfill(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
