cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 185 — S184 uitrollen + nazorg (Opus)

## Model + rol
Opus, `/effort max`. Dit is een **uitrol- + nazorgsessie**: de S184-fixes staan klaar op
branch `s184-fixes` (Fable-gereviewd, 1147 tests groen) maar zijn NOG NIET live. Deze sessie
zet ze live en handelt de post-deploy-taken af. Prod-mutaties met geld: eerst vóór/na tonen,
pas aanpassen met expliciet akkoord van Arsalan.

## Context laden bij start
Gebruik de `general-purpose` subagent (of lees zelf):
"Lees `docs/sessions/S184-MORGEN-CHECKLIST.md` + de S184-entry in SESSION-NOTES.md. Geef de
6 fixes, de deploy-stappen en de open post-deploy-taken."

## Taak 1 — S184 live zetten (na go van Arsalan)
De branch mergen naar main triggert de automatische deploy (build → up → migratie →
healthcheck):
```
git checkout main && git merge s184-fixes && git push origin main
```
Daarna tag zetten: `git tag sessie-184 && git push origin sessie-184`.

**Verifieer na de deploy (read-only):**
- `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose ps && docker compose logs backend --tail 20"`
  → backend gezond, geen RuntimeError van de opstartcontrole.
- Migratie gedraaid: `docker compose exec -T backend python -m alembic current` → head =
  `s184_rls_learned_answers`.
- RLS-gat dicht: prod-query `SELECT relforcerowsecurity FROM pg_class WHERE relname='learned_answers'`
  → `t` (was `f`).

> **Nieuw opstartgedrag:** de app weigert in productie te starten als een tenant-tabel RLS
> mist (fail-closed, bedoeld). Bij een boot-fout: lees de backend-logs — de RuntimeError
> noemt de tabel. Normaal draait de migratie eerst, dus dit hoort niet te gebeuren.

## Taak 2 — 4 heropeningszaken herrekenen (de creditfactuur-fix raakt hun rente)
IN100334, IN100469, IN100505, IN100553. **Eerst read-only een vóór/na-vergelijking tonen**
(oude vs nieuwe rente/saldo na de fix). Bedragen op prod pas aanpassen ná akkoord Arsalan.

## Taak 3 — 7 dossiers sluiten (Lisanne akkoord, zie `LISANNE-A4-heropening.md`)
Sluiten: IN100547, IN100210, IN100456, IN100457, IN100256, IN100197, IN100334.
**NIET sluiten: IN100166** (blijft open om te innen). Kleine, omkeerbare actie; de
workflow-guard controleert het saldo. IN100334 pas sluiten ná taak 2 (herrekening).

## Openstaand (niet deze sessie, wel bewaken)
- **IN100334 ±€215 te veel betaald** — terugstorten? Vraag aan Lisanne (staat in het A4).
- **~10 juli:** Backblaze US-bucket wissen als `/var/log/luxis-backup.log` twee geslaagde
  EU-runs (8+9 juli) toont — dan bucket `Luxis-backup` wissen + oude key intrekken + remote
  `luxis-backup` verwijderen, wisbewijs in SESSION-NOTES.
- Daarna: **heropening werkvoorraad** = aparte sessie (S186), draaiboek
  `docs/plans/PLAN-heropening-werkvoorraad.md`, start met LegalWork B.V.

## Constraints (wat NIET doen)
- Geen bedragen op prod aanpassen zonder expliciet akkoord (taak 2: eerst vóór/na tonen).
- D-Break (IN100555) blijft dicht.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, PROMPT-S186 (heropening).
