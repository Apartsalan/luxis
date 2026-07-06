"""S177: eenmalig de rente uit bestaande AV's lezen en op de cliënt zetten.

Dry-run (standaard) toont per cliënt wat er uit de AV gelezen wordt — de controlestap
die Arsalan wil zien vóór toepassing. Pas `--execute` schrijft de terms_interest_*-velden
weg. Raakt NOOIT de handmatige default_*-velden. Idempotent: her-lezen overschrijft
alleen de gelezen waarde.

    docker compose exec backend python -m scripts.backfill_terms_interest            # dry-run
    docker compose exec backend python -m scripts.backfill_terms_interest --execute
    docker compose exec backend python -m scripts.backfill_terms_interest --no-ai    # alleen regex
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select

from app.database import async_session
from app.relations.models import Contact, ContactTerms
from app.relations.service import refresh_terms_interest
from app.relations.terms_interest import read_terms_interest


async def run(execute: bool, use_ai: bool) -> None:
    async with async_session() as db:
        # Cliënten met minstens één AV-versie, nieuwste eerst.
        terms_rows = (
            await db.execute(
                select(ContactTerms).order_by(
                    ContactTerms.contact_id,
                    ContactTerms.valid_from.desc().nulls_last(),
                    ContactTerms.created_at.desc(),
                )
            )
        ).scalars().all()

        # Per cliënt de nieuwste AV.
        newest: dict = {}
        for t in terms_rows:
            newest.setdefault(t.contact_id, t)

        names = {
            c.id: c.name
            for c in (await db.execute(select(Contact))).scalars().all()
        }

        print("=" * 74)
        print("S177 — rente uit bestaande AV's", "(EXECUTE)" if execute else "(DRY RUN)")
        print("=" * 74)
        found = none = failed = 0
        for contact_id, terms in newest.items():
            naam = (names.get(contact_id) or str(contact_id))[:32]
            try:
                if execute:
                    result = await refresh_terms_interest(
                        db, terms.tenant_id, contact_id, terms.file_path, use_ai_fallback=use_ai
                    )
                else:
                    result = await read_terms_interest(terms.file_path, use_ai_fallback=use_ai)
            except Exception as e:  # noqa: BLE001 — één kapotte PDF mag de run niet stoppen
                failed += 1
                print(f"  {naam:34s}  !! LEESFOUT ({terms.file_name[:30]}): {e}")
                continue
            if result is None:
                none += 1
                print(f"  {naam:34s}  —  geen tarief gevonden ({terms.file_name[:30]})")
            else:
                found += 1
                comp = "samengesteld" if result.compound else "enkelvoudig"
                print(
                    f"  {naam:34s}  {result.rate}% {result.basis:7s} {comp:12s} "
                    f"[{result.method}]  {result.source}"
                )
        if execute:
            await db.commit()
        print("-" * 74)
        print(
            f"  cliënten met AV: {len(newest)}   tarief gevonden: {found}   "
            f"geen tarief: {none}   leesfouten: {failed}"
        )
        print(f"  {'GESCHREVEN op de cliënt' if execute else 'DRY RUN — niets geschreven'}")
        print("=" * 74)


def main() -> None:
    p = argparse.ArgumentParser(description="Rente uit bestaande AV's lezen (S177)")
    p.add_argument("--execute", action="store_true", help="Schrijf weg (anders dry-run)")
    p.add_argument("--no-ai", action="store_true", help="Alleen regex, geen Haiku-vangnet")
    args = p.parse_args()
    asyncio.run(run(execute=args.execute, use_ai=not args.no_ai))


if __name__ == "__main__":
    main()
