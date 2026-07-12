cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 206 — checklist afvinken + één vervolgspoor kiezen en uitvoeren

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): geen — alle detail staat in
SESSION-NOTES (entry S205) en `LUXIS-ROADMAP.md` §Huidige prioriteit.

## Taak

### 1. Checklist eerst (klein, read-only)
S204/S205 lieten één open verificatie: staan de **5 dagelijkse-job-rijen** nu in
`scheduler_heartbeat` op prod (na 13 juli 06:40 UTC)? Verwacht: `daily_verjaring_check`,
`daily_task_status_update`, `daily_deadline_notifications`, `daily_installment_overdue_check`,
`daily_invoice_overdue_check`. Zo nee → uitzoeken waarom de dagelijkse jobs niet draaien
(de 5 periodieke jobs draaien wél). Check via SSH read-only:
`docker compose exec -T db psql -U luxis -d luxis -c "SELECT job_id, last_run_at, last_error FROM scheduler_heartbeat ORDER BY job_id;"`

### 2. Kies één vervolgspoor (leg de keuze eerst aan Arsalan voor)
Presenteer de drie sporen kort in gewone taal + een aanbeveling; wacht op zijn keuze.
- **S201 facturatie-import** — 439 conflict-vrije facturen; recept + droogloop-poorten klaar in
  `docs/research/S201-facturatie-recept.md`. Naar-buiten-gerichte schrijfactie op prod → **apart
  akkoord vereist**, droogloop eerst.
- **S202 security-fixes (Fase D)** — H1 cross-tenant CaseFile, H2 fail-open "betaald"-guard, H3
  "Geïnd" telt verwijderde betalingen, M1/M2 + mailhardening. Rapport `docs/security/S202-delta-audit.md`.
  Bounded, geen prod-data-mutatie. M3 (DB-superuser/RLS Fase 2) bewust apart.
- **S203-restpunten** — 35-route backend-sloop (eigen per-route-verificatie), #7 document-audittrail,
  #15 regeling-badge, log-persistentie VPS.

Voer daarna het gekozen spoor uit met de 4-stappen-werkwijze (onderzoek → plan → bouw → verificatie),
per taak rood→groen→commit→push→deploy.

## Openstaand uit S205 (meenemen, niet vergeten)
- ⚠️ **Waarschuwingstekst "toch versturen"-noodknop langs Lisanne** vóór er echt een B2C-sommatie
  vanuit Luxis de deur uit gaat (haar beroepsrisico) — concept staat in `zaken/[id]/page.tsx`.

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -k "<relevant>" -v` (relevante modules).
- Lint: `uvx ruff check backend/app/`
- Frontend geraakt? `cd frontend && npx tsc --noEmit && npm run build`.

## Constraints (wat NIET doen)
- Mailslot blijft DICHT; niets versturen.
- Geen prod-instellingen/data wijzigen zonder apart akkoord.
- Nooit `git add -A` — alleen expliciete paden stagen.
- Sporen niet mengen — kies er één.

## Commit
Commit + push naar main per afgeronde taak. Deploy via SSH (deploy-regels). Werk af met /sessie-einde.
