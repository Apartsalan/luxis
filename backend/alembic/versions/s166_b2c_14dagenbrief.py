"""S166: voeg de 14-dagenbrief toe als eerste B2C-pipelinestap.

Punt 3 uit de S165-backlog: bij een particulier (B2C) is de 14-dagenbrief
(WIK art. 6:96 lid 6 BW) wettelijk verplicht en moet die vóór de sommaties komen,
maar de incasso-pipeline kende de stap niet. Deze migratie voegt voor elke tenant
die al pipeline-stappen heeft (dus is geseed) de stap "14-dagenbrief" toe als die
ontbreekt — debtor_type 'b2c', categorie 'minnelijk', sort_order 0 zodat hij vóór
"Eerste sommatie" (sort_order 1) staat en de eerste stap is voor een B2C-dossier
(zie cases.service.create_case: eerste geldige stap per debiteurtype).

Plus de bijbehorende default-transitie 14-dagenbrief → Eerste sommatie (timeout,
15 dagen) zodat het B2C-pad na de wettelijke 14-dagentermijn doorloopt op de
sommatie-keten.

Idempotent: voegt alleen toe wat ontbreekt (NOT EXISTS-guards), zodat re-runs en
samenloop met seed_default_steps elkaar niet bijten.

Revision ID: s166_b2c_14dagenbrief
Revises: d4a9c3e87f10
"""

from alembic import op

revision = "s166_b2c_14dagenbrief"
down_revision = "d4a9c3e87f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Voeg de 14-dagenbrief-stap toe voor elke geseede tenant die hem mist.
    op.execute(
        """
        INSERT INTO incasso_pipeline_steps
            (id, tenant_id, name, sort_order, min_wait_days, max_wait_days,
             step_category, debtor_type, is_active, is_terminal, is_hold_step)
        SELECT gen_random_uuid(), t.tenant_id, '14-dagenbrief', 0, 0, 15,
               'minnelijk', 'b2c', true, false, false
        FROM (SELECT DISTINCT tenant_id FROM incasso_pipeline_steps) AS t
        WHERE NOT EXISTS (
            SELECT 1 FROM incasso_pipeline_steps s
            WHERE s.tenant_id = t.tenant_id AND s.name = '14-dagenbrief'
        )
        """
    )

    # 2. Default-transitie 14-dagenbrief → Eerste sommatie (timeout 15 dagen) per tenant,
    #    alleen waar beide stappen bestaan en de transitie nog niet bestaat.
    op.execute(
        """
        INSERT INTO step_transitions
            (id, tenant_id, from_step_id, to_step_id, trigger_type, action,
             condition, priority, is_default, label, is_active)
        SELECT gen_random_uuid(), s1.tenant_id, s1.id, s2.id, 'timeout',
               'advance_to_step', '{"days": 15}', 0, true,
               'Geen betaling na 14-dagentermijn', true
        FROM incasso_pipeline_steps s1
        JOIN incasso_pipeline_steps s2
            ON s2.tenant_id = s1.tenant_id AND s2.name = 'Eerste sommatie'
        WHERE s1.name = '14-dagenbrief'
          AND NOT EXISTS (
            SELECT 1 FROM step_transitions tr
            WHERE tr.tenant_id = s1.tenant_id
              AND tr.from_step_id = s1.id
              AND tr.to_step_id = s2.id
              AND tr.trigger_type = 'timeout'
          )
        """
    )


def downgrade() -> None:
    # FK-veilig terugdraaien: ontkoppel verwijzingen, verwijder transitie + stap.
    op.execute(
        """
        UPDATE cases SET incasso_step_id = NULL
        WHERE incasso_step_id IN (
            SELECT id FROM incasso_pipeline_steps WHERE name = '14-dagenbrief'
        )
        """
    )
    op.execute(
        """
        DELETE FROM case_step_history
        WHERE step_id IN (
            SELECT id FROM incasso_pipeline_steps WHERE name = '14-dagenbrief'
        )
        """
    )
    op.execute(
        """
        DELETE FROM step_transitions
        WHERE from_step_id IN (
            SELECT id FROM incasso_pipeline_steps WHERE name = '14-dagenbrief'
        )
        OR to_step_id IN (
            SELECT id FROM incasso_pipeline_steps WHERE name = '14-dagenbrief'
        )
        """
    )
    op.execute(
        "DELETE FROM incasso_pipeline_steps WHERE name = '14-dagenbrief'"
    )
