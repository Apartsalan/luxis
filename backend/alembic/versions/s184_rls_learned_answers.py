"""S183-1: RLS-gat op learned_answers dichten + drift opruimen.

De RLS-migratie ``h2_rls_complete`` (2 juni) ontdekte tenant-tabellen dynamisch —
maar eenmalig. ``learned_answers`` is daarná aangemaakt (S168, 18 juni) en bleef
zo de enige van 48 tenant-tabellen ZONDER RLS op productie (audit S183-1).

``apply_rls`` is idempotent en her-ontdekt álle tabellen met een ``tenant_id``-kolom,
dus dit her-toepassen dicht ``learned_answers`` én elke andere latere drift, zonder
de al-beveiligde tabellen te raken. Voortaan voorkomt de drift-guard-test
(``tests/test_rls_isolation.py::test_every_tenant_table_has_forced_rls``) dat een
nieuwe tabel ongemerkt zonder RLS blijft.

Revision ID: s184_rls_learned_answers
Revises: s177_terms_interest
Create Date: 2026-07-08
"""

from collections.abc import Sequence

from alembic import op
from app.security.rls import apply_rls

revision: str = "s184_rls_learned_answers"
down_revision: str | None = "s177_terms_interest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent: her-ontdekt alle tenant-tabellen en (her)zet role/grants +
    # ENABLE/FORCE/policy. Vangt learned_answers en eventuele andere drift.
    apply_rls(op.get_bind())


def downgrade() -> None:
    # Geen downgrade: RLS uitzetten op alle tabellen zou de isolatie breken en er
    # is geen reden dit selectief terug te draaien. apply_rls blijft idempotent.
    pass
