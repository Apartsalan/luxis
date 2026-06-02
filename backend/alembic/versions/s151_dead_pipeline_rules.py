"""S151: deactivate dead pipeline automation rules (AUDIT-H12).

The pipeline rule-evaluator (automation_service.evaluate_timeout_rules) only ever
reads StepTransition rows with trigger_type='timeout'. The seeded 'payment' and
'debtor_response' rules were never evaluated:

* debtor_response is handled independently by the email-classification hook
  (trigger_defense_response_for_email) — the rule rows were dead duplicate config.
* payment was read nowhere, so a payment never moved a case.

Both surfaced as non-functioning "Automatische regels" in the UI. Deactivate the
existing rows (soft, reversible — mirrors delete_transition's is_active=False
pattern) so they stop showing. The seed no longer creates them (see
incasso/service.seed_default_transitions).

Revision ID: s151_dead_pipeline_rules
Revises: s151_heal_email_logs
"""

from alembic import op

revision = "s151_dead_pipeline_rules"
down_revision = "s151_heal_email_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE step_transitions
        SET is_active = false
        WHERE trigger_type IN ('payment', 'debtor_response')
          AND is_active = true
        """
    )


def downgrade() -> None:
    # Restore the previous state (re-activate the dead rules).
    op.execute(
        """
        UPDATE step_transitions
        SET is_active = true
        WHERE trigger_type IN ('payment', 'debtor_response')
        """
    )
