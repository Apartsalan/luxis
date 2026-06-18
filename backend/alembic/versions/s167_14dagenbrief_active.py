"""S167: garandeer een ACTIEVE 14-dagenbrief (prod-drift fix op s166).

s166 voegde de 14-dagenbrief alleen toe als er nog GEEN stap met die naam bestond.
Op productie bleek echter een oude, gedeactiveerde 14-dagenbrief te bestaan (uit een
legacy pipeline-set), waardoor de NOT EXISTS-guard de insert oversloeg → er was geen
ACTIEVE 14-dagenbrief en B2C-dossiers startten er niet op. Bovendien had prod dubbele
stapnamen (legacy inactieve "Eerste sommatie" naast de actieve), waardoor de
s166-transitie-insert per ongeluk dubbele/kapotte transities vanaf de inactieve
14-dagenbrief aanmaakte.

Deze migratie convergeert elke staat (dev: al schoon → no-op; prod: drift → fix) naar:
exact één ACTIEVE 14-dagenbrief (sort_order 0, b2c, minnelijk) met precies één
timeout-transitie naar de ACTIEVE "Eerste sommatie". De legacy inactieve 14-dagenbrief
blijft ongemoeid (inactief, nergens zichtbaar). Dry-run op prod bevestigd:
INSERT 0 1 / DELETE 2 / INSERT 0 1 → 1 actieve stap + 1 schone transitie.

Idempotent (NOT EXISTS / is_active-guards). Disambigueert dubbele stapnamen via is_active.

Revision ID: s167_14dagenbrief_active
Revises: s166_b2c_14dagenbrief
"""

from alembic import op

revision = "s167_14dagenbrief_active"
down_revision = "s166_b2c_14dagenbrief"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Voeg een schone ACTIEVE 14-dagenbrief toe als er nog geen actieve is.
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
            WHERE s.tenant_id = t.tenant_id
              AND s.name = '14-dagenbrief' AND s.is_active = true
        )
        """
    )

    # 2. Ruim legacy/dubbele timeout-transities vanaf een INACTIEVE 14-dagenbrief op.
    op.execute(
        """
        DELETE FROM step_transitions tr
        USING incasso_pipeline_steps s_from
        WHERE tr.from_step_id = s_from.id
          AND s_from.name = '14-dagenbrief' AND s_from.is_active = false
          AND tr.trigger_type = 'timeout'
        """
    )

    # 3. Precies één timeout-transitie van de ACTIEVE 14-dagenbrief -> ACTIEVE Eerste sommatie.
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
            ON s2.tenant_id = s1.tenant_id
           AND s2.name = 'Eerste sommatie' AND s2.is_active = true
        WHERE s1.name = '14-dagenbrief' AND s1.is_active = true
          AND NOT EXISTS (
            SELECT 1 FROM step_transitions x
            WHERE x.tenant_id = s1.tenant_id AND x.from_step_id = s1.id
              AND x.to_step_id = s2.id AND x.trigger_type = 'timeout'
          )
        """
    )


def downgrade() -> None:
    # Bewust een no-op: dit is een corrigerende normalisatie die niet zinvol naar de
    # eerdere (kapotte/dubbelzinnige) staat terug te draaien is. De 14-dagenbrief zelf
    # wordt verwijderd door de downgrade van s166 (verwijdert alle stappen met die naam).
    pass
