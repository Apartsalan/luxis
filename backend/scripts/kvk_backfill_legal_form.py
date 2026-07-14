"""S211: eenmalige backfill van `legal_form` op wederpartijen met KvK-nummer.

Loopt alle relaties met een KvK-nummer en een lege rechtsvorm af, haalt de
rechtsvorm uit het KvK-basisprofiel en slaat die op (source="kvk"). Bedoeld om
in één keer de ~438 zakelijke wederpartijen te vullen zodat de renteoverzicht-
bijlage-beslissing (should_attach_rente_bijlage) op echte data draait i.p.v.
op "onbekend → wél bijlage" (besluit B).

⚠️ NIET DRAAIEN met de test-sleutel — die kent alleen nepbedrijven en zou echte
relaties met None (of erger: verkeerde data) vullen. Pas draaien zodra de ECHTE
productie-sleutel als KVK_API_KEY/KVK_API_BASE op de VPS staat. Kosten ± €0,02
per bevraging (± €9 totaal). Recept-aanpak S209: eerst --dry-run, dan akkoord,
dan echt, dan natelling.

Run:
    docker compose run --rm backend python scripts/kvk_backfill_legal_form.py --dry-run
    docker compose run --rm backend python scripts/kvk_backfill_legal_form.py
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import select, text

# Importeer main om alle SQLAlchemy modellen te registreren
import app.main  # noqa: F401
from app.auth.models import Tenant
from app.database import async_session
from app.integrations.kvk_service import get_rechtsvorm
from app.relations.models import Contact


async def backfill(dry_run: bool) -> None:
    async with async_session() as session:
        tenants = list((await session.execute(select(Tenant))).scalars().all())

    total_found = 0
    total_filled = 0
    total_none = 0

    for tenant in tenants:
        async with async_session() as session:
            # RLS-context; UUID is een gevalideerd type uit de DB → veilig te interpoleren.
            await session.execute(text(f"SET LOCAL app.current_tenant = '{tenant.id}'"))

            contacts = list(
                (
                    await session.execute(
                        select(Contact).where(
                            Contact.tenant_id == tenant.id,
                            Contact.kvk_number.isnot(None),
                            Contact.kvk_number != "",
                            Contact.legal_form.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )

            if not contacts:
                print(f"[{tenant.name}] geen relaties met KvK-nummer en lege rechtsvorm")
                continue

            print(
                f"[{tenant.name}] {len(contacts)} relaties met KvK-nummer, rechtsvorm leeg"
            )
            total_found += len(contacts)

            from datetime import UTC, datetime

            for contact in contacts:
                rechtsvorm = await get_rechtsvorm(contact.kvk_number)
                if rechtsvorm is None:
                    total_none += 1
                    print(f"  - {contact.name} (KvK {contact.kvk_number}): geen rechtsvorm")
                    continue

                if dry_run:
                    print(
                        f"  [DRY-RUN] {contact.name} (KvK {contact.kvk_number}) "
                        f"→ {rechtsvorm}"
                    )
                    total_filled += 1
                    continue

                contact.legal_form = rechtsvorm
                contact.legal_form_source = "kvk"
                contact.legal_form_checked_at = datetime.now(UTC)
                total_filled += 1
                print(f"  GEVULD {contact.name} (KvK {contact.kvk_number}) → {rechtsvorm}")

            if not dry_run:
                await session.commit()

    print("---")
    print(f"Totaal met KvK-nummer + lege rechtsvorm: {total_found}")
    print(f"Rechtsvorm gevonden: {total_filled}")
    print(f"Geen rechtsvorm (blijft leeg → besluit B: wél bijlage): {total_none}")
    if dry_run:
        print("Dry-run: niets geschreven.")


def main() -> None:
    parser = argparse.ArgumentParser(description="S211 backfill legal_form uit KvK")
    parser.add_argument(
        "--dry-run", action="store_true", help="Alleen rapporteren, niets schrijven"
    )
    args = parser.parse_args()
    asyncio.run(backfill(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
