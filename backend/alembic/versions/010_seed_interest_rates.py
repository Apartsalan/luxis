"""Seed official Dutch interest rates 2002-2026.

Sources:
- Wettelijke rente (art. 6:119 BW): rijksoverheid.nl, wettelijkerente.nl
- Handelsrente (art. 6:119a BW): wettelijkerente.nl/tarieven
- Overheidshandelsrente (art. 6:119b BW): same as commercial per art. 6:120(2) BW

Verified: 2026-02-18 against rijksoverheid.nl and wettelijkerente.nl

Revision ID: 010
Revises: 009
Create Date: 2026-02-18
"""

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ── Official rate data ──────────────────────────────────────────────────────
# Format: (effective_from, rate_percentage, source_reference)

STATUTORY_RATES: list[tuple[str, str, str]] = [
    # Art. 6:119 BW — wettelijke rente (niet-handelstransacties)
    ("2002-01-01", "7.00", "Stb. 2001, 581"),
    ("2003-08-01", "5.00", "Stb. 2003, 302"),
    ("2004-02-01", "4.00", "Stb. 2004, 28"),
    ("2007-01-01", "6.00", "Stb. 2006, 660"),
    ("2009-07-01", "4.00", "Stb. 2009, 245"),
    ("2010-01-01", "3.00", "Stb. 2009, 554"),
    ("2011-07-01", "4.00", "Stb. 2011, 325"),
    ("2012-07-01", "3.00", "Stb. 2012, 286"),
    ("2015-01-01", "2.00", "Stb. 2014, 516"),
    ("2023-01-01", "4.00", "Stb. 2022, 517"),
    ("2023-07-01", "6.00", "Stb. 2023, 215"),
    ("2024-01-01", "7.00", "Stb. 2023, 462"),
    ("2025-01-01", "6.00", "Stb. 2024, 409"),
    ("2026-01-01", "4.00", "Stb. 2025, 427"),
]

COMMERCIAL_RATES: list[tuple[str, str, str]] = [
    # Art. 6:119a BW — handelsrente
    # Note: commercial rates existed since 08-08-2002 (Wet bestrijding
    # betalingsachterstand bij handelstransacties)
    ("2002-08-08", "10.35", "Stb. 2002, 425"),
    ("2002-12-01", "10.35", "Stb. 2002, 531"),
    ("2003-01-01", "9.85", "Stb. 2002, 616"),
    ("2003-07-01", "9.10", "Stb. 2003, 255"),
    ("2003-08-01", "9.10", "Stb. 2003, 302"),
    ("2004-01-01", "9.02", "Stb. 2003, 521"),
    ("2004-02-01", "9.02", "Stb. 2004, 28"),
    ("2004-07-01", "9.01", "Stb. 2004, 289"),
    ("2005-01-01", "9.09", "Stb. 2004, 659"),
    ("2005-07-01", "9.05", "Stb. 2005, 317"),
    ("2006-01-01", "9.25", "Stb. 2005, 622"),
    ("2006-07-01", "9.83", "Stb. 2006, 289"),
    ("2007-01-01", "10.58", "Stb. 2006, 660"),
    ("2007-07-01", "11.07", "Stb. 2007, 249"),
    ("2008-01-01", "11.20", "Stb. 2007, 504"),
    ("2008-07-01", "11.07", "Stb. 2008, 266"),
    ("2009-01-01", "9.50", "Stb. 2008, 555"),
    ("2009-07-01", "8.00", "Stb. 2009, 245"),
    ("2010-01-01", "8.00", "Stb. 2009, 554"),
    ("2010-07-01", "8.00", "Stb. 2010, 289"),
    ("2011-01-01", "8.00", "Stb. 2010, 834"),
    ("2011-07-01", "8.25", "Stb. 2011, 325"),
    ("2012-01-01", "8.00", "Stb. 2011, 616"),
    ("2012-07-01", "8.00", "Stb. 2012, 286"),
    ("2013-01-01", "7.75", "Stb. 2012, 658"),
    ("2013-03-16", "8.75", "Stb. 2013, 93"),
    ("2013-07-01", "8.50", "Stb. 2013, 244"),
    ("2014-01-01", "8.25", "Stb. 2013, 556"),
    ("2014-07-01", "8.15", "Stb. 2014, 237"),
    ("2015-01-01", "8.05", "Stb. 2014, 516"),
    ("2015-07-01", "8.05", "Stb. 2015, 266"),
    ("2016-01-01", "8.05", "Stb. 2015, 521"),
    ("2016-07-01", "8.00", "Stb. 2016, 250"),
    ("2017-01-01", "8.00", "Stb. 2016, 508"),
    ("2017-07-01", "8.00", "Stb. 2017, 279"),
    ("2018-01-01", "8.00", "Stb. 2017, 488"),
    ("2018-07-01", "8.00", "Stb. 2018, 211"),
    ("2019-01-01", "8.00", "Stb. 2018, 476"),
    ("2019-07-01", "8.00", "Stb. 2019, 210"),
    ("2020-01-01", "8.00", "Stb. 2019, 462"),
    ("2020-07-01", "8.00", "Stb. 2020, 233"),
    ("2021-01-01", "8.00", "Stb. 2020, 520"),
    ("2021-07-01", "8.00", "Stb. 2021, 283"),
    ("2022-01-01", "8.00", "Stb. 2021, 610"),
    ("2023-01-01", "10.50", "Stb. 2022, 517"),
    ("2023-07-01", "12.00", "Stb. 2023, 215"),
    ("2024-01-01", "12.50", "Stb. 2023, 462"),
    ("2024-07-01", "12.25", "Stb. 2024, 216"),
    ("2025-01-01", "11.15", "Stb. 2024, 409"),
    ("2025-07-01", "10.15", "Stb. 2025, 211"),
]

# Art. 6:119b BW — overheidshandelsrente
# Per art. 6:120 lid 2 BW: this rate equals the commercial rate (art. 6:119a)
# We seed it separately for clarity and so queries on rate_type='government' work.
GOVERNMENT_RATES = COMMERCIAL_RATES  # Identical to commercial rates


def upgrade() -> None:
    """Seed all official Dutch interest rates (skip if already seeded)."""
    # Check if data already exists (may have been seeded via script)
    conn = op.get_bind()
    count = conn.execute(sa.text("SELECT COUNT(*) FROM interest_rates")).scalar()
    if count > 0:
        return  # Already seeded — skip

    interest_rates = sa.table(
        "interest_rates",
        sa.column("id", sa.Uuid),
        sa.column("rate_type", sa.String),
        sa.column("effective_from", sa.Date),
        sa.column("rate", sa.Numeric),
        sa.column("source", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    rows = []

    for effective_from_str, rate_str, source in STATUTORY_RATES:
        rows.append({
            "id": str(uuid.uuid4()),
            "rate_type": "statutory",
            "effective_from": date.fromisoformat(effective_from_str),
            "rate": Decimal(rate_str),
            "source": source,
        })

    for effective_from_str, rate_str, source in COMMERCIAL_RATES:
        rows.append({
            "id": str(uuid.uuid4()),
            "rate_type": "commercial",
            "effective_from": date.fromisoformat(effective_from_str),
            "rate": Decimal(rate_str),
            "source": source,
        })

    for effective_from_str, rate_str, source in GOVERNMENT_RATES:
        rows.append({
            "id": str(uuid.uuid4()),
            "rate_type": "government",
            "effective_from": date.fromisoformat(effective_from_str),
            "rate": Decimal(rate_str),
            "source": source,
        })

    op.bulk_insert(interest_rates, rows)


def downgrade() -> None:
    """Remove all seeded interest rates."""
    op.execute(
        sa.text(
            "DELETE FROM interest_rates WHERE rate_type IN "
            "('statutory', 'commercial', 'government')"
        )
    )
