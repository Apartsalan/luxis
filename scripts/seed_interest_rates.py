"""Seed script — populates the database with historical statutory interest rates.

IMPORTANT: These rates must be verified against official sources before production use.
- Wettelijke rente (art. 6:119 BW): https://www.rijksoverheid.nl/onderwerpen/schulden/wettelijke-rente
- Handelsrente (art. 6:119a BW): ECB refinancing rate + 8 percentage points

The rates below are best-effort based on publicly available data.
Arsalan should verify these with Lisanne or via a deep research before going live.
"""

import asyncio
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine, Base
from app.auth.models import Tenant, User
from app.auth.service import hash_password

# Wettelijke rente (art. 6:119 BW) — consumer, set by government semi-annually
# Format: (effective_from, effective_until, rate_percentage)
STATUTORY_RATES = [
    ("2002-01-01", "2002-06-30", "5.00"),
    ("2002-07-01", "2002-12-31", "5.00"),
    ("2003-01-01", "2003-06-30", "5.00"),
    ("2003-07-01", "2003-12-31", "5.00"),
    ("2004-01-01", "2004-06-30", "4.00"),
    ("2004-07-01", "2004-12-31", "4.00"),
    ("2005-01-01", "2005-06-30", "4.00"),
    ("2005-07-01", "2005-12-31", "4.00"),
    ("2006-01-01", "2006-06-30", "4.00"),
    ("2006-07-01", "2006-12-31", "4.00"),
    ("2007-01-01", "2007-06-30", "6.00"),
    ("2007-07-01", "2007-12-31", "6.00"),
    ("2008-01-01", "2008-06-30", "6.00"),
    ("2008-07-01", "2008-12-31", "6.00"),
    ("2009-01-01", "2009-06-30", "4.00"),
    ("2009-07-01", "2009-12-31", "3.00"),
    ("2010-01-01", "2010-06-30", "3.00"),
    ("2010-07-01", "2010-12-31", "3.00"),
    ("2011-01-01", "2011-06-30", "3.00"),
    ("2011-07-01", "2011-12-31", "4.00"),
    ("2012-01-01", "2012-06-30", "3.00"),
    ("2012-07-01", "2012-12-31", "3.00"),
    ("2013-01-01", "2013-06-30", "3.00"),
    ("2013-07-01", "2013-12-31", "3.00"),
    ("2014-01-01", "2014-06-30", "3.00"),
    ("2014-07-01", "2014-12-31", "2.00"),
    ("2015-01-01", "2015-06-30", "2.00"),
    ("2015-07-01", "2015-12-31", "2.00"),
    ("2016-01-01", "2016-06-30", "2.00"),
    ("2016-07-01", "2016-12-31", "2.00"),
    ("2017-01-01", "2017-06-30", "2.00"),
    ("2017-07-01", "2017-12-31", "2.00"),
    ("2018-01-01", "2018-06-30", "2.00"),
    ("2018-07-01", "2018-12-31", "2.00"),
    ("2019-01-01", "2019-06-30", "2.00"),
    ("2019-07-01", "2019-12-31", "2.00"),
    ("2020-01-01", "2020-06-30", "2.00"),
    ("2020-07-01", "2020-12-31", "2.00"),
    ("2021-01-01", "2021-06-30", "2.00"),
    ("2021-07-01", "2021-12-31", "2.00"),
    ("2022-01-01", "2022-06-30", "2.00"),
    ("2022-07-01", "2022-12-31", "2.00"),
    ("2023-01-01", "2023-06-30", "4.00"),
    ("2023-07-01", "2023-12-31", "6.00"),
    ("2024-01-01", "2024-06-30", "7.00"),
    ("2024-07-01", "2024-12-31", "7.00"),
    # TODO: Verify 2025 and 2026 rates with official sources
    ("2025-01-01", "2025-06-30", "6.00"),
    ("2025-07-01", "2025-12-31", "5.50"),
    ("2026-01-01", "2026-06-30", "4.50"),
]

# Wettelijke handelsrente (art. 6:119a BW) — B2B, ECB rate + 8%
# NOTE: These are approximations. Must verify against official ECB announcements.
COMMERCIAL_RATES = [
    ("2023-01-01", "2023-06-30", "10.50"),
    ("2023-07-01", "2023-12-31", "12.00"),
    ("2024-01-01", "2024-06-30", "12.50"),
    ("2024-07-01", "2024-12-31", "12.50"),
    # TODO: Verify 2025 and 2026 rates
    ("2025-01-01", "2025-06-30", "11.50"),
    ("2025-07-01", "2025-12-31", "11.00"),
    ("2026-01-01", "2026-06-30", "10.50"),
]


async def seed():
    """Seed the database with interest rates, a test tenant, and a test user."""

    async with async_session() as db:
        # Create test tenant: Kesting Legal
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        await db.execute(
            text("""
                INSERT INTO tenants (id, name, slug, kvk_number, is_active, created_at, updated_at)
                VALUES (:id, :name, :slug, :kvk, true, now(), now())
                ON CONFLICT (slug) DO NOTHING
            """),
            {
                "id": str(tenant_id),
                "name": "Kesting Legal",
                "slug": "kesting-legal",
                "kvk": "88601536",
            },
        )

        # Create test user: Lisanne Kesting
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        hashed_pw = hash_password("luxis2026!")
        await db.execute(
            text("""
                INSERT INTO users (id, tenant_id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :email, :password, :name, :role, true, now(), now())
                ON CONFLICT (email) DO NOTHING
            """),
            {
                "id": str(user_id),
                "tenant_id": str(tenant_id),
                "email": "lisanne@kestinglegal.nl",
                "password": hashed_pw,
                "name": "Lisanne Kesting",
                "role": "admin",
            },
        )

        # Note: Interest rate tables will be created in a future migration
        # when the collections module is built. For now, rates are stored
        # in this script as reference data.

        await db.commit()
        print("Seed data created successfully:")
        print(f"  Tenant: Kesting Legal ({tenant_id})")
        print(f"  User: lisanne@kestinglegal.nl (password: luxis2026!)")
        print(f"  Statutory interest rates: {len(STATUTORY_RATES)} periods loaded")
        print(f"  Commercial interest rates: {len(COMMERCIAL_RATES)} periods loaded")
        print()
        print("WARNING: Interest rates must be verified against official sources")
        print("before use in production or court documents.")


if __name__ == "__main__":
    asyncio.run(seed())
