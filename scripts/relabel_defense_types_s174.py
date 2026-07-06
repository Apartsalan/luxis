"""S174 V3 — eenmalige her-labeling van verweer-KANDIDATEN met de trefwoord-pre-labeler.

Zet `defense_type` op elke kandidaat (status='kandidaat') via
`defense_types.prelabel_defense_type` — het mechanisme dat sinds S174 de difflib-gelijkenis
vervangt (audit S172 §5, gevalideerd op 102 prod-kandidaten in
`docs/audit/prelabel-dryrun-2026-07-06.md`). Goedgekeurde/afgewezen rijen blijven ONGEMOEID.

Data-only + idempotent. Standaard DRY-RUN (rapporteert alleen, rollback); `--apply` schrijft.

    docker compose exec backend python scripts/relabel_defense_types_s174.py           # dry-run
    docker compose exec backend python scripts/relabel_defense_types_s174.py --apply    # schrijven
"""

import asyncio
import sys
from collections import Counter

from sqlalchemy import select, text

import app.main  # noqa: F401  — load all models
from app.ai_agent.defense_types import (
    DEFENSE_TYPE_LABELS,
    normalize_defense_type,
    prelabel_defense_type,
)
from app.ai_agent.learned_answers import STATUS_CANDIDATE
from app.ai_agent.models import LearnedAnswer
from app.auth.models import Tenant
from app.database import async_session


def _target_type(row: LearnedAnswer) -> str:
    """Nieuw verweer-type voor een kandidaat: pre-labeler op de body, met de oude
    library-key als betekenisvolle bodem wanneer de pre-labeler 'overig' oplevert."""
    t = prelabel_defense_type(row.body or "")
    if t == "overig":
        t = normalize_defense_type(row.defense_type)
    return t


async def main() -> int:
    apply = "--apply" in sys.argv
    async with async_session() as session:
        tenants = (
            await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))
        ).scalars().all()

        grand_changed = 0
        for tenant in tenants:
            await session.execute(text(f"SET app.current_tenant = '{tenant.id}'"))
            rows = (
                await session.execute(
                    select(LearnedAnswer).where(
                        LearnedAnswer.tenant_id == tenant.id,
                        LearnedAnswer.status == STATUS_CANDIDATE,
                    )
                )
            ).scalars().all()
            if not rows:
                continue

            after: Counter[str] = Counter()
            changed = 0
            for r in rows:
                new = _target_type(r)
                after[new] += 1
                if new != r.defense_type:
                    changed += 1
                    if apply:
                        r.defense_type = new

            suffix = "" if apply else " (DRY-RUN, niets geschreven)"
            print(f"\n{tenant.name}: {len(rows)} kandidaten, {changed} gewijzigd{suffix}")
            print("  verdeling ná pre-labeling:")
            for key in DEFENSE_TYPE_LABELS:
                if after.get(key):
                    print(f"    {key:34s} {after[key]}")
            grand_changed += changed

            if apply:
                await session.commit()
            else:
                await session.rollback()

        print(f"\nTotaal gewijzigd: {grand_changed}{'' if apply else ' (DRY-RUN)'}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
