"""AUDIT-H2: complete Row-Level Security — luxis_app role + FORCE RLS on every tenant table

Closes the multi-tenant isolation gap found in the 2026-06-01 system audit.

Diagnosis (dev DB): the ``luxis_app`` role was missing, so the tenant middleware
never switched roles and the app ran as the bypassrls superuser — every RLS
policy was silently ignored. Only 2 of 46 tenant tables had FORCE RLS, and
``ai_drafts`` / ``contact_terms`` had no RLS at all.

This migration is the single, idempotent fix:
  1. Create the non-superuser ``luxis_app`` role (if missing) and grant it to the
     connecting (super)user so ``SET ROLE`` works. GRANT targets ``current_user``
     dynamically so it is correct in both dev and prod.
  2. Grant luxis_app the DML it needs on all tables/sequences (+ default privileges
     for future tables).
  3. ENABLE + FORCE RLS and (re)create the ``tenant_isolation`` policy on every
     table carrying a ``tenant_id`` column (except ``users`` — see app.security.rls).

Idempotent and safe to re-run on databases where earlier RLS migrations
(sec9 / sec9b / sec13 / aud124_08) ran fully, partially, or were stamped.

Revision ID: h2_rls_complete
Revises: s147a_notification_snooze
Create Date: 2026-06-02
"""

from collections.abc import Sequence

from alembic import op
from app.security.rls import (
    apply_rls,
    disable_rls,
)

# revision identifiers, used by Alembic.
revision: str = "h2_rls_complete"
down_revision: str | None = "s147a_notification_snooze"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # apply_rls handles role creation, grants, and per-table ENABLE/FORCE/policy.
    apply_rls(op.get_bind())


def downgrade() -> None:
    # Drop policies + disable RLS on all tenant tables. The luxis_app role and its
    # grants are intentionally left in place: earlier migrations and the running
    # app depend on the role existing. After this the DB falls back to app-layer
    # tenant filtering (the pre-S150 reality).
    disable_rls(op.get_bind())
