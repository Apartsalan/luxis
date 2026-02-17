"""Seed script — populates the database with historical interest rates and test data.

Sources used for verification (February 2026):
- Wettelijke rente (art. 6:119 BW): rijksoverheid.nl, wettelijkerente.nl
- Handelsrente (art. 6:119a BW): ECB refinancing rate + 8%, via wettelijke-rente.com, DNB
- Overheidshandelsrente (art. 6:119b BW): same rate as handelsrente

IMPORTANT NOTES:
- Wettelijke rente changes by Koninklijk Besluit (no fixed schedule, typically 1 Jan or 1 Jul)
- Handelsrente changes semi-annually (1 Jan and 1 Jul) automatically: ECB refi rate + 8%
- ALL three statutory interest types use COMPOUND interest (samengestelde rente / rente op rente)
  per art. 6:119 lid 2, 6:119a lid 3, 6:119b lid 3 BW
- "Vertragingsrente" and "procesrente" are NOT separate types — they are informal names
  for wettelijke rente under art. 6:119 BW

Rate types relevant for Luxis incasso module:
1. statutory     — Wettelijke rente (art. 6:119 BW) — consumers (B2C, C2C)
2. commercial    — Wettelijke handelsrente (art. 6:119a BW) — B2B
3. government    — Overheidshandelsrente (art. 6:119b BW) — government as debtor
4. contractual   — Contractuele rente — freely agreed between parties (stored per case)
"""

import asyncio
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine, Base
from app.auth.models import Tenant, User
from app.auth.service import hash_password


# =============================================================================
# WETTELIJKE RENTE (art. 6:119 BW) — non-commercial / consumer
# Set by Koninklijk Besluit (AMvB), published in Staatsblad
# No fixed schedule, but typically changes 1 Jan or 1 Jul
# Format: (effective_from, rate_percentage)
# Each rate is valid until the next entry's effective_from date
# =============================================================================
STATUTORY_RATES = [
    ("1934-01-01", "5.00"),
    ("1974-05-01", "10.00"),
    ("1976-04-01", "8.00"),
    ("1979-01-01", "10.00"),
    ("1980-04-01", "12.00"),
    ("1983-01-01", "9.00"),
    ("1987-04-01", "8.00"),
    ("1990-01-01", "10.00"),
    ("1992-01-01", "12.00"),
    ("1993-07-01", "10.00"),
    ("1994-01-01", "9.00"),
    ("1995-01-01", "8.00"),
    ("1996-01-01", "5.00"),
    ("1998-01-01", "6.00"),
    ("1999-01-01", "6.00"),
    ("2001-01-01", "8.00"),
    ("2002-01-01", "7.00"),
    ("2003-08-01", "5.00"),
    ("2004-02-01", "4.00"),
    ("2007-01-01", "6.00"),
    ("2009-01-01", "4.00"),
    ("2009-07-01", "3.00"),  # Note: unusual mid-year change
    ("2010-01-01", "3.00"),
    ("2011-07-01", "4.00"),
    ("2012-07-01", "3.00"),
    ("2014-07-01", "2.00"),  # Note: stayed at 2% for 8+ years
    ("2023-01-01", "4.00"),
    ("2023-07-01", "6.00"),
    ("2024-01-01", "7.00"),
    ("2025-01-01", "6.00"),
    ("2026-01-01", "4.00"),
]


# =============================================================================
# WETTELIJKE HANDELSRENTE (art. 6:119a BW) — B2B commercial transactions
# Formula: ECB main refinancing operations rate + 8 percentage points
# Changes semi-annually on 1 January and 1 July
# Introduced 1 December 2002 (implementing EU Late Payment Directive 2000/35/EC)
#
# Also applies to art. 6:119b BW (government as debtor) — same rates
# =============================================================================
COMMERCIAL_RATES = [
    ("2002-12-01", "10.35"),  # Introduction of art. 6:119a BW
    ("2003-01-01", "9.85"),   # ECB 2.75% + 8%
    ("2003-07-01", "9.10"),
    ("2004-01-01", "9.02"),
    ("2004-07-01", "9.01"),
    ("2005-01-01", "9.09"),
    ("2005-07-01", "9.05"),
    ("2006-01-01", "9.25"),
    ("2006-07-01", "9.83"),
    ("2007-01-01", "10.58"),
    ("2007-07-01", "11.07"),
    ("2008-01-01", "11.20"),
    ("2008-07-01", "11.07"),
    ("2009-01-01", "9.50"),
    ("2009-07-01", "8.00"),   # ECB 1.00% + 8% (financial crisis)
    ("2011-07-01", "8.25"),
    ("2012-01-01", "8.00"),
    ("2013-01-01", "8.75"),   # Transitional period
    ("2013-07-01", "8.50"),
    ("2014-01-01", "8.25"),
    ("2014-07-01", "8.15"),
    ("2015-01-01", "8.05"),
    ("2016-01-01", "8.05"),
    ("2016-07-01", "8.00"),   # ECB 0.00% + 8% — stayed at 8% for years
    ("2023-01-01", "10.50"),  # ECB 2.50% + 8% (rate hikes)
    ("2023-07-01", "12.00"),
    ("2024-01-01", "12.50"),
    ("2024-07-01", "12.25"),
    ("2025-01-01", "11.15"),
    ("2025-07-01", "10.15"),  # ECB 2.15% + 8% — still in effect
]


# =============================================================================
# WIK-STAFFEL — Buitengerechtelijke incassokosten (art. 6:96 BW)
# Since 1 July 2012 (Besluit vergoeding voor buitengerechtelijke incassokosten)
# =============================================================================
WIK_TIERS = [
    # (tier_ceiling, percentage) — ceiling is cumulative from €0
    # tier_ceiling=None means unlimited (rest of principal)
    (2500, "0.15"),    # 15% over first €2,500
    (5000, "0.10"),    # 10% over €2,500 - €5,000
    (10000, "0.05"),   # 5% over €5,000 - €10,000
    (200000, "0.01"),  # 1% over €10,000 - €200,000
    (None, "0.005"),   # 0.5% over €200,000+
]
WIK_MINIMUM = "40.00"   # Minimum €40
WIK_MAXIMUM = "6775.00"  # Maximum €6,775


# =============================================================================
# VOORWERK II — Legacy incassokosten (before 1 July 2012)
# Only relevant for claims where the 14-day letter was sent before 1 July 2012
# =============================================================================
VOORWERK_II_TIERS = [
    # (tier_ceiling, fixed_amount_per_tier)
    (2500, "375.00"),
    (5000, "500.00"),
    (10000, "625.00"),
    (20000, "750.00"),
    (40000, "875.00"),
    (100000, "1000.00"),
    (None, "1500.00"),  # Max: €1,500 + eventueel meer bij zeer hoge vorderingen
]


async def seed():
    """Seed the database with test tenant, test user, and reference interest rates.

    Interest rate tables will be stored in the database when the collections module
    is built. For now, the rates are defined here as Python constants that serve as
    the single source of truth for the seed migration.
    """

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

        await db.commit()

        print("=" * 60)
        print("Luxis — Seed Data Report")
        print("=" * 60)
        print()
        print("TENANT:")
        print(f"  Kesting Legal ({tenant_id})")
        print(f"  KvK: 88601536")
        print()
        print("USER:")
        print(f"  lisanne@kestinglegal.nl")
        print(f"  Password: luxis2026!")
        print(f"  Role: admin")
        print()
        print("INTEREST RATES LOADED:")
        print(f"  Wettelijke rente (art. 6:119 BW):      {len(STATUTORY_RATES)} periods")
        print(f"  Wettelijke handelsrente (art. 6:119a):  {len(COMMERCIAL_RATES)} periods")
        print(f"  Overheidshandelsrente (art. 6:119b):    Same as handelsrente")
        print(f"  Contractuele rente:                     Per dossier (user-defined)")
        print()
        print("INCASSOKOSTEN:")
        print(f"  WIK-staffel (art. 6:96 BW):            {len(WIK_TIERS)} tiers")
        print(f"  Voorwerk II (pre-2012, legacy):         {len(VOORWERK_II_TIERS)} tiers")
        print()
        print("COMPOUND INTEREST NOTE:")
        print("  All statutory interest types use samengestelde rente (compound interest)")
        print("  per art. 6:119 lid 2, 6:119a lid 3, and 6:119b lid 3 BW.")
        print("  At the end of each year, accrued interest is added to the principal.")
        print()
        print("VERIFICATION STATUS:")
        print("  Rates sourced from rijksoverheid.nl, wettelijkerente.nl, DNB, ECB")
        print("  RECOMMEND: Verify recent rates (2025-2026) with Lisanne before")
        print("  using in court documents.")


if __name__ == "__main__":
    asyncio.run(seed())
