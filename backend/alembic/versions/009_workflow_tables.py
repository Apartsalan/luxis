"""Add workflow tables: WorkflowStatus, WorkflowTransition, WorkflowTask, WorkflowRule
with default seed data for incasso workflow.

Revision ID: 009
Revises: 008
Create Date: 2026-02-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── WorkflowStatus ──────────────────────────────────────────────────────
    op.create_table(
        "workflow_statuses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color", sa.String(20), nullable=False, server_default="gray"),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_initial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index(
        "ix_workflow_statuses_tenant_id", "workflow_statuses", ["tenant_id"]
    )
    op.create_index(
        "ix_workflow_statuses_tenant_slug",
        "workflow_statuses",
        ["tenant_id", "slug"],
        unique=True,
    )

    # ── WorkflowTransition ──────────────────────────────────────────────────
    op.create_table(
        "workflow_transitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("from_status_id", sa.Uuid(), nullable=False),
        sa.Column("to_status_id", sa.Uuid(), nullable=False),
        sa.Column(
            "debtor_type", sa.String(10), nullable=False, server_default="both"
        ),
        sa.Column("requires_note", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["from_status_id"], ["workflow_statuses.id"]),
        sa.ForeignKeyConstraint(["to_status_id"], ["workflow_statuses.id"]),
    )
    op.create_index(
        "ix_workflow_transitions_tenant_id", "workflow_transitions", ["tenant_id"]
    )

    # ── WorkflowRule (must come before WorkflowTask due to FK) ──────────────
    op.create_table(
        "workflow_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_status_id", sa.Uuid(), nullable=False),
        sa.Column(
            "debtor_type", sa.String(10), nullable=False, server_default="both"
        ),
        sa.Column("days_delay", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("action_config", JSONB(), nullable=True),
        sa.Column("auto_execute", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "assign_to_case_owner",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["trigger_status_id"], ["workflow_statuses.id"]),
    )
    op.create_index("ix_workflow_rules_tenant_id", "workflow_rules", ["tenant_id"])

    # ── WorkflowTask ────────────────────────────────────────────────────────
    op.create_table(
        "workflow_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_to_id", sa.Uuid(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("auto_execute", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("action_config", JSONB(), nullable=True),
        sa.Column("created_by_rule_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_rule_id"], ["workflow_rules.id"]),
    )
    op.create_index("ix_workflow_tasks_tenant_id", "workflow_tasks", ["tenant_id"])
    op.create_index("ix_workflow_tasks_case_id", "workflow_tasks", ["case_id"])
    op.create_index(
        "ix_workflow_tasks_status_due", "workflow_tasks", ["status", "due_date"]
    )

    # ── Seed default statuses + transitions for ALL existing tenants ────────
    _seed_workflow_data()


def _seed_workflow_data() -> None:
    """Insert default workflow statuses, transitions, and rules for every tenant."""
    conn = op.get_bind()

    tenant_rows = conn.execute(sa.text("SELECT id FROM tenants")).fetchall()
    if not tenant_rows:
        return

    for (tenant_id,) in tenant_rows:
        _seed_for_tenant(conn, str(tenant_id))


def _seed_for_tenant(conn, tenant_id: str) -> None:
    """Seed workflow data for a single tenant."""
    import uuid

    # ── Statuses ────────────────────────────────────────────────────────────
    statuses = [
        ("nieuw", "Nieuw", "minnelijk", 10, "blue", False, True),
        ("herinnering", "Herinnering", "minnelijk", 20, "sky", False, False),
        ("aanmaning", "Aanmaning", "minnelijk", 30, "amber", False, False),
        ("14_dagenbrief", "14-dagenbrief", "minnelijk", 40, "orange", False, False),
        ("sommatie", "Sommatie", "minnelijk", 50, "orange", False, False),
        ("tweede_sommatie", "Tweede sommatie", "minnelijk", 60, "red", False, False),
        ("betalingsregeling", "Betalingsregeling", "regeling", 70, "purple", False, False),
        ("conservatoir_beslag", "Conservatoir beslag", "gerechtelijk", 80, "red", False, False),
        ("dagvaarding", "Dagvaarding", "gerechtelijk", 90, "red", False, False),
        ("vonnis", "Vonnis", "gerechtelijk", 100, "red", False, False),
        ("executie", "Executie", "executie", 110, "red", False, False),
        ("faillissementsaanvraag", "Faillissementsaanvraag", "executie", 120, "red", False, False),
        ("betaald", "Betaald", "afgerond", 130, "green", True, False),
        ("schikking", "Schikking", "afgerond", 140, "green", True, False),
        ("oninbaar", "Oninbaar", "afgerond", 150, "gray", True, False),
    ]

    slug_to_id = {}
    for slug, label, phase, sort_order, color, is_terminal, is_initial in statuses:
        status_id = str(uuid.uuid4())
        slug_to_id[slug] = status_id
        conn.execute(
            sa.text(
                """INSERT INTO workflow_statuses
                (id, tenant_id, slug, label, phase, sort_order, color, is_terminal, is_initial)
                VALUES (:id, :tenant_id, :slug, :label, :phase, :sort_order, :color, :is_terminal, :is_initial)"""
            ),
            {
                "id": status_id,
                "tenant_id": tenant_id,
                "slug": slug,
                "label": label,
                "phase": phase,
                "sort_order": sort_order,
                "color": color,
                "is_terminal": is_terminal,
                "is_initial": is_initial,
            },
        )

    # ── Transitions ─────────────────────────────────────────────────────────
    # (from_slug, to_slug, debtor_type)
    transitions = [
        # From nieuw
        ("nieuw", "herinnering", "both"),
        ("nieuw", "aanmaning", "both"),
        ("nieuw", "14_dagenbrief", "b2c"),
        ("nieuw", "sommatie", "b2b"),
        ("nieuw", "betaald", "both"),
        ("nieuw", "oninbaar", "both"),
        # From herinnering
        ("herinnering", "aanmaning", "both"),
        ("herinnering", "14_dagenbrief", "b2c"),
        ("herinnering", "sommatie", "b2b"),
        ("herinnering", "betaald", "both"),
        ("herinnering", "oninbaar", "both"),
        # From aanmaning
        ("aanmaning", "14_dagenbrief", "b2c"),
        ("aanmaning", "sommatie", "b2b"),
        ("aanmaning", "betaald", "both"),
        ("aanmaning", "oninbaar", "both"),
        # From 14_dagenbrief
        ("14_dagenbrief", "sommatie", "both"),
        ("14_dagenbrief", "tweede_sommatie", "both"),
        ("14_dagenbrief", "betaald", "both"),
        ("14_dagenbrief", "betalingsregeling", "both"),
        ("14_dagenbrief", "oninbaar", "both"),
        # From sommatie
        ("sommatie", "tweede_sommatie", "both"),
        ("sommatie", "dagvaarding", "both"),
        ("sommatie", "betaald", "both"),
        ("sommatie", "betalingsregeling", "both"),
        ("sommatie", "oninbaar", "both"),
        # From tweede_sommatie
        ("tweede_sommatie", "dagvaarding", "both"),
        ("tweede_sommatie", "betaald", "both"),
        ("tweede_sommatie", "betalingsregeling", "both"),
        ("tweede_sommatie", "oninbaar", "both"),
        # From betalingsregeling
        ("betalingsregeling", "sommatie", "both"),
        ("betalingsregeling", "dagvaarding", "both"),
        ("betalingsregeling", "betaald", "both"),
        ("betalingsregeling", "oninbaar", "both"),
        # From conservatoir_beslag
        ("conservatoir_beslag", "dagvaarding", "both"),
        ("conservatoir_beslag", "betaald", "both"),
        ("conservatoir_beslag", "schikking", "both"),
        # From dagvaarding
        ("dagvaarding", "vonnis", "both"),
        ("dagvaarding", "betaald", "both"),
        ("dagvaarding", "schikking", "both"),
        # From vonnis
        ("vonnis", "executie", "both"),
        ("vonnis", "faillissementsaanvraag", "both"),
        ("vonnis", "betaald", "both"),
        ("vonnis", "schikking", "both"),
        # From executie
        ("executie", "faillissementsaanvraag", "both"),
        ("executie", "betaald", "both"),
        ("executie", "oninbaar", "both"),
        # From faillissementsaanvraag
        ("faillissementsaanvraag", "betaald", "both"),
        ("faillissementsaanvraag", "oninbaar", "both"),
        # Schikking can also lead to betaald
        ("schikking", "betaald", "both"),
    ]

    for from_slug, to_slug, debtor_type in transitions:
        conn.execute(
            sa.text(
                """INSERT INTO workflow_transitions
                (id, tenant_id, from_status_id, to_status_id, debtor_type)
                VALUES (:id, :tenant_id, :from_status_id, :to_status_id, :debtor_type)"""
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "from_status_id": slug_to_id[from_slug],
                "to_status_id": slug_to_id[to_slug],
                "debtor_type": debtor_type,
            },
        )

    # ── Default Workflow Rules ──────────────────────────────────────────────
    rules = [
        # (trigger_slug, delay_days, action_type, name, debtor_type, action_config)
        ("nieuw", 0, "manual_review", "Beoordeel nieuwe zaak", "both", None),
        ("herinnering", 14, "check_payment", "Check betaling na herinnering", "both", None),
        ("aanmaning", 14, "send_letter", "Stuur 14-dagenbrief", "b2c", {"template_type": "14_dagenbrief"}),
        ("aanmaning", 14, "send_letter", "Stuur sommatie", "b2b", {"template_type": "sommatie"}),
        ("14_dagenbrief", 15, "check_payment", "Check betaling na 14-dagenbrief", "b2c", None),
        ("sommatie", 14, "check_payment", "Check betaling na sommatie", "both", None),
        ("vonnis", 0, "manual_review", "Plan executie", "both", None),
        ("betalingsregeling", 30, "check_payment", "Controleer termijnbetaling", "both", None),
    ]

    import json

    for trigger_slug, days_delay, action_type, name, debtor_type, action_config in rules:
        config_json = json.dumps(action_config) if action_config else None
        conn.execute(
            sa.text(
                """INSERT INTO workflow_rules
                (id, tenant_id, name, trigger_status_id, debtor_type, days_delay,
                 action_type, action_config, auto_execute, assign_to_case_owner, sort_order)
                VALUES (:id, :tenant_id, :name, :trigger_status_id, :debtor_type, :days_delay,
                        :action_type, CAST(:action_config AS jsonb), false, true, :sort_order)"""
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "name": name,
                "trigger_status_id": slug_to_id[trigger_slug],
                "debtor_type": debtor_type,
                "days_delay": days_delay,
                "action_type": action_type,
                "action_config": config_json,
                "sort_order": 0,
            },
        )

    # ── Map existing cases with old statuses ────────────────────────────────
    # Existing cases may have statuses like 'afgesloten' that are now mapped to
    # terminal statuses. We don't change Case.status (still a slug string).
    # The mapping is: 'afgesloten' no longer exists, map to 'oninbaar' or keep as-is.
    # For safety, we only ensure old slugs that don't exist get mapped.
    conn.execute(
        sa.text(
            """UPDATE cases SET status = 'oninbaar'
            WHERE status = 'afgesloten' AND tenant_id = :tenant_id"""
        ),
        {"tenant_id": tenant_id},
    )


def downgrade() -> None:
    # Restore 'afgesloten' for cases that were mapped to 'oninbaar'
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE cases SET status = 'afgesloten' WHERE status = 'oninbaar'"
        )
    )

    op.drop_table("workflow_tasks")
    op.drop_table("workflow_rules")
    op.drop_table("workflow_transitions")
    op.drop_table("workflow_statuses")
