cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 205 — S204-beslislijst bouwen: 14-dagenbrief-zijdeuren dicht + mailsync-foutpad

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/sessions/S204-review.md` — het reviewrapport met per punt bewijs + regelnummers
  (§Beslislijst = jouw takenlijst; lees per taak eerst de bijbehorende ⚠-sectie).

## Taak (in deze volgorde — juridisch eerst)
1. **Gate in follow-up "Uitvoeren"** (🔴): dezelfde 14-dagenbrief-check als in `batch_execute`
   (incasso/service.py:1255) óók in `execute_recommendation` (ai_agent/followup_service.py:359),
   vóór het versturen. Hergebruik één gedeelde helper (bv. in collections/compliance.py) i.p.v.
   de check te dupliceren; ook `approve_and_execute_recommendation` dekt dan mee. Fout = skip
   mét reden richting de gebruiker, nooit stil.
2. **Gate in het AI-concept-verzendpad** (🔴): een B2C-sommatie-concept mag niet verstuurd worden
   zonder dagenbrief-spoor. Kies de plek bewust (advies uit S204: in `advance-after-send`
   (incasso/router.py:359) is te laat — de mail is dan al weg; de check hoort vóór verzending,
   dus in het compose/send-pad wanneer een draft_id/case-context meegaat, of als aparte
   pre-send-check die de frontend afdwingt). Presenteer je keuze kort vóór je bouwt (Plan Mode).
3. **Verstuurd-proxy verstevigen** (🟠): `get_dagenbrief_entered_at` rekent nu vanaf
   stap-BINNENKOMST. Sterker anker: bewijs van echte verzending — de `email_sent`-vlag op de
   historierij (advance-after-send zet die al) en/of EmailLog/GeneratedDocument. Het batchpad
   moet dan óók `mark_current_step_communication_sent` aanroepen na een geslaagde send
   (ontbreekt nu).

   **HARDE EIS Arsalan (13 juli, S204-nagesprek) — flexibiliteit voor laat-binnengekomen zaken:**
   een opdrachtgever kan een consumentenzaak aanleveren waarbij de 14-dagenbrief al eerder is
   verstuurd (door de opdrachtgever zelf of vóór de overdracht), of waarbij de zaak hals-over-kop
   instroomt. De gate mag zo'n zaak niet muurvast zetten:
   a. Er moet een expliciete registratie zijn: "14-dagenbrief al verstuurd buiten Luxis, op datum
      X" (bewuste handeling mét datum, door een mens). De gate rekent dan vanaf die datum.
   b. Het versturen van de 14-dagenbrief ZELF mag nooit geblokkeerd worden — een zaak die laat
      binnenkomt zonder eerdere brief moet direct de brief kunnen sturen (dat kan nu al: de gate
      zondert de dagenbrief-stap uit — bewaken dat dat zo blijft in alle paden).
   c. Wat NIET komt: een "toch versturen"-knop die de wachttijd van een sommatie-mét-kosten
      overslaat — de 14 dagen zijn wet (art. 6:96 lid 6 BW), geen systeemkeuze. Flexibiliteit =
      registreren wat buiten het systeem al gebeurd is, niet de wettelijke termijn omzeilen.
   Bouw a. als eerste-klas flow (geen "sleep de zaak stiekem door de stap"-truc) en zorg dat de
   proxy-verharding deze registratie als geldig bewijs blijft zien.
4. **Mailsync-foutpad** (🟠, bewezen defect): in `email_auto_sync` (workflow/scheduler.py:234-266)
   expireert de `rollback()` álle accounts → volgend account crasht met MissingGreenlet en de hele
   run stopt. Fix: e-mailadres per account in een lokale variabele vóór de try + na een rollback de
   resterende accounts opnieuw laden (of per account een eigen sessie). Schrijf een test die het
   scenario "account 1 faalt, account 2 synct alsnog" afdwingt.
5. **Heartbeat-`last_error` bij interne jobfouten** (🟡): jobs slikken hun eigen excepties, dus
   "draait maar faalt elke dag" blijft onzichtbaar. Kleinste ingreep kiezen (decorator of
   per-job except die de heartbeat-fout zet).
6. **Checklist:** staan er inmiddels dagelijkse-job-rijen in `scheduler_heartbeat` op prod
   (daily_verjaring_check e.a.)? Zo nee → uitzoeken waarom (S204 ⚠a).

**Beslispunt voor Arsalan (vragen, niet zelf doen):** wil hij dat Luxis de 14-dagenbrief zelf kan
versturen? Zo ja: `template_type='14_dagenbrief'` op de pijplijn-stap zetten (het e-mailsjabloon
bestaat al in code, email/incasso_templates.py:631) — dat is een prod-instelling, dus apart akkoord.

## Verificatie
- Per fix eerst een rode test, dan groen: `docker compose exec backend python -m pytest tests/ -k "compliance or followup or email_sync or scheduler" -v` + de suites die je raakt.
- Lint: `uvx ruff check backend/app/`
- Frontend geraakt? `cd frontend && npx tsc --noEmit && npm run build`.

## Constraints (wat NIET doen)
- Mailslot blijft DICHT; niets versturen.
- Geen prod-instellingen/data wijzigen zonder apart akkoord (het dagenbrief-sjabloon-besluit hierboven).
- De 35-route-sloop, #7 audittrail, #15 regeling-badge, S201-import en S202-securityfixes zijn
  aparte sporen — niet meenemen.
- Nooit `git add -A` — alleen expliciete paden stagen.

## Commit
Commit + push naar main per afgeronde taak met conventional commit message. Deploy automatisch via
SSH (deploy-regels-skill); migraties zijn niet voorzien. Werk af met /sessie-einde.
