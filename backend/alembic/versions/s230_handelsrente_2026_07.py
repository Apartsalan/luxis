"""S230: wettelijke handelsrente + overheidsrente per 1 juli 2026 (10,40%).

De rentetabel is op 18-02-2026 gevuld (migratie 010) en eindigde bij 10,15%
(1-7-2025). Per 1 juli 2026 geldt 10,4% voor handelstransacties (art. 6:119a BW)
en daarmee ook voor de overheidsrente (art. 6:119b BW).

Bronnen (beide gecontroleerd 20-07-2026):
- Rijksoverheid.nl: "De wettelijke rente voor handelstransacties is sinds
  1 juli 2026 10,4%."
- Rekenregel art. 6:119a lid 2 BW: ECB-basisherfinancieringsrente 2,40%
  (per 17-06-2026) + 8 procentpunt = 10,40%.

De consumentenrente (statutory) is per 1-1-2026 al 4% en ongewijzigd; het
tarief per 1-1-2026 voor handel bleef 10,15% (ECB stond toen nog op 2,15%),
dus daar is geen rij nodig.

Data-only en idempotent: ON CONFLICT op (rate_type, effective_from) doet niets
als de rij al bestaat.

Revision ID: s230_handelsrente_2026_07
Revises: s221_ai_draft_intent_step
"""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from alembic import op

revision: str = "s230_handelsrente_2026_07"
down_revision: str | None = "s221_ai_draft_intent_step"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# asyncpg wil echte date/Decimal-objecten, geen strings (KNOWN-quirk).
EFFECTIVE_FROM = date(2026, 7, 1)
RATE = Decimal("10.40")
SOURCE = "Rijksoverheid.nl / ECB-refi 2,40% + 8pp (art. 6:119a lid 2 BW)"


def upgrade() -> None:
    for rate_type in ("commercial", "government"):
        op.get_bind().execute(
            text("""
                INSERT INTO interest_rates
                    (id, rate_type, effective_from, rate, source, created_at, updated_at)
                VALUES
                    (gen_random_uuid(), :rate_type, :effective_from, :rate, :source,
                     now(), now())
                ON CONFLICT (rate_type, effective_from) DO NOTHING
            """),
            {
                "rate_type": rate_type,
                "effective_from": EFFECTIVE_FROM,
                "rate": RATE,
                "source": SOURCE,
            },
        )


def downgrade() -> None:
    op.get_bind().execute(
        text("""
            DELETE FROM interest_rates
            WHERE effective_from = :effective_from
              AND rate_type IN ('commercial', 'government')
        """),
        {"effective_from": EFFECTIVE_FROM},
    )
