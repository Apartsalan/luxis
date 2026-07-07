"""Shared Row-Level Security (RLS) definitions for multi-tenant isolation.

Single source of truth for the tenant-isolation policy. Used by BOTH the Alembic
migration (``h2_rls_complete``) and the adversarial test
(``tests/test_rls_isolation.py``) so the test proves exactly the policy that
production runs — no drift between "what we ship" and "what we verify".

The enforcement model (chosen in S150, AUDIT-H2 phase 1):

* The application connects as the superuser/owner role, but the tenant
  middleware runs ``SET LOCAL ROLE luxis_app`` per authenticated request. After
  that switch ``current_user`` is a non-superuser, non-owner role, so RLS
  policies are enforced. ``current_setting('app.current_tenant')`` is set in the
  same middleware step, before any query runs.
* Migrations and background jobs keep running as the superuser (RLS bypassed) —
  that is why this phase does not break the scheduler or the login/refresh flow.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

# Non-superuser role the app assumes (SET ROLE) so RLS is enforced.
APP_ROLE = "luxis_app"

# Standard policy name applied to every tenant-scoped table.
POLICY_NAME = "tenant_isolation"

# Tables that DO carry a tenant_id column but must stay outside RLS by design.
# `users` is looked up cross-tenant during authentication (login by e-mail
# happens before any tenant context exists), so isolating it would break login.
TENANT_RLS_EXCLUDE = frozenset({"users"})

# The row predicate: a row belongs to the current request's tenant. The strict
# (non-missing_ok) current_setting is intentional — if a luxis_app connection
# ever queries without a tenant set, it fails closed instead of leaking.
_TENANT_PREDICATE = "tenant_id = current_setting('app.current_tenant')::uuid"

# Every public BASE TABLE that has a tenant_id column.
_DISCOVER_SQL = text(
    """
    SELECT c.table_name
    FROM information_schema.columns c
    JOIN information_schema.tables t
      ON t.table_schema = c.table_schema
     AND t.table_name = c.table_name
    WHERE c.table_schema = 'public'
      AND c.column_name = 'tenant_id'
      AND t.table_type = 'BASE TABLE'
    ORDER BY c.table_name
    """
)


def _quote_ident(identifier: str) -> str:
    """Double-quote a SQL identifier safely."""
    return '"' + identifier.replace('"', '""') + '"'


def discover_tenant_tables(conn: Connection) -> list[str]:
    """Return all tenant-scoped tables (those with a tenant_id column), minus
    the deliberate excludes. Dynamic discovery guarantees coverage of current
    tables and any future ones — no hand-maintained list to drift out of sync.
    """
    rows = conn.execute(_DISCOVER_SQL).scalars().all()
    return [t for t in rows if t not in TENANT_RLS_EXCLUDE]


def role_statements(current_user: str) -> list[str]:
    """SQL to create the non-superuser app role (idempotent) and let the
    connecting (super)user assume it via SET ROLE.

    ``current_user`` is resolved at runtime by the caller so the GRANT works
    regardless of the actual DB login name (dev = ``luxis``; prod may differ).
    """
    return [
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} NOLOGIN;
            END IF;
        END
        $$;
        """,
        f"GRANT {APP_ROLE} TO {_quote_ident(current_user)}",
    ]


def grant_statements() -> list[str]:
    """SQL granting luxis_app the DML it needs on all current and future objects."""
    return [
        f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT USAGE, SELECT ON SEQUENCES TO {APP_ROLE}",
    ]


def rls_statements(table: str) -> list[str]:
    """SQL to enable + FORCE RLS and (re)create the tenant_isolation policy on
    one table. Idempotent: the policy is dropped first, FORCE/ENABLE are no-ops
    if already set. WITH CHECK mirrors USING so cross-tenant INSERT/UPDATE are
    rejected, not just hidden.
    """
    q = _quote_ident(table)
    return [
        f"ALTER TABLE {q} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {q} FORCE ROW LEVEL SECURITY",
        f"DROP POLICY IF EXISTS {POLICY_NAME} ON {q}",
        f"CREATE POLICY {POLICY_NAME} ON {q} "
        f"USING ({_TENANT_PREDICATE}) WITH CHECK ({_TENANT_PREDICATE})",
    ]


def disable_rls(conn: Connection) -> list[str]:
    """Drop the tenant_isolation policy and DISABLE RLS on every tenant table,
    returning to the no-RLS baseline. Returns the tables touched.

    Used by the migration downgrade and by the test teardown. The role and grants
    are intentionally left in place (other migrations and the running app depend
    on luxis_app existing). DISABLE — not just NO FORCE — because an enabled table
    with no policy denies all rows to the non-owner luxis_app role.
    """
    tables = discover_tenant_tables(conn)
    for table in tables:
        q = _quote_ident(table)
        conn.execute(text(f"DROP POLICY IF EXISTS {POLICY_NAME} ON {q}"))
        conn.execute(text(f"ALTER TABLE {q} DISABLE ROW LEVEL SECURITY"))
    return tables


def find_unprotected_tenant_tables(conn: Connection) -> list[str]:
    """Return tenant tables that SHOULD have RLS but lack FORCE RLS or the policy.

    Drift-guard for S183-1: ``learned_answers`` (S168) shipped without RLS because
    the one-time RLS migration ran before that table existed and nothing re-applied
    it. This detects exactly that class of drift — a table with a ``tenant_id``
    column that a migration created without also securing it. Empty list == every
    tenant table is protected. Uses ``discover_tenant_tables`` as the source of
    truth so new tables are covered automatically.
    """
    unprotected: list[str] = []
    for table in discover_tenant_tables(conn):
        forced = conn.execute(
            text(
                "SELECT relforcerowsecurity FROM pg_class "
                "WHERE relname = :t AND relnamespace = 'public'::regnamespace"
            ),
            {"t": table},
        ).scalar()
        has_policy = conn.execute(
            text(
                "SELECT 1 FROM pg_policies WHERE schemaname = 'public' "
                "AND tablename = :t AND policyname = :p"
            ),
            {"t": table, "p": POLICY_NAME},
        ).scalar()
        if not forced or not has_policy:
            unprotected.append(table)
    return unprotected


def apply_rls(conn: Connection) -> list[str]:
    """Apply the full RLS setup (role + grants + per-table policies) on a sync
    connection and return the list of tenant tables that were secured.

    Used by the migration (via ``op.get_bind()``) and by the test (via
    ``run_sync``) so both exercise the identical setup path.
    """
    current_user = conn.execute(text("SELECT current_user")).scalar()
    for stmt in role_statements(current_user):
        conn.execute(text(stmt))
    for stmt in grant_statements():
        conn.execute(text(stmt))
    tables = discover_tenant_tables(conn)
    for table in tables:
        for stmt in rls_statements(table):
            conn.execute(text(stmt))
    return tables
