cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 204 — Fable-review van de S203-voorkant-fixes (read-only)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/sessions/S200-BEVINDINGEN.md` — de bevindingenlijst met ✅-statuskolom (wat S203 fixte).
- De S203-diff: `git log --oneline sessie-203..sessie-203-fixes` en `git diff sessie-203 sessie-203-fixes`.

## Taak
Review ALLE S203-voorkant-fixes (Opus bouwde ze, 11 van 12 bevindingen; migraties `s203`+`s203b`
staan op prod). Dit is een **read-only** controlesessie: geen productcode of prod-data wijzigen,
geen mail. Alleen als je een echte fout vindt, presenteer die + voorgestelde fix vóór je iets aanraakt
(Plan Mode) — de bouw is dan een aparte vervolgstap.

Werk de fable-discipline toe: **fable-diepte** (meet in de bron/prod, niet in de commit-tekst),
**fable-tegenspreker** (probeer elke fix te weerleggen). Per fix: klopt de root cause, is de test
echt dekkend, zijn er zij-ingangen/sibling-callers gemist, en klopt het gedrag op prod?

Loop minimaal deze fixes na (bron + waar mogelijk read-only prod-SQL/API):
1. **Tijdlijn-crash** (#13): `cases/timeline_service.py` leest nu `duration_minutes`/`date`.
   Check of er nog andere plekken `duration_seconds`/`entry_date` op TimeEntry lezen.
2. **Hernoem-knop** (#4): nieuwe PATCH `/api/cases/{id}/files/{id}` — tenant-scoping + 404 buiten tenant.
3. **AI-concept €0-markering** (#3): `incasso/automation_service.py` — vuurt de marker alleen bij
   een €-sjabloon, en lekt de `_amounts_fallback`-sleutel echt niet meer in `build_user_prompt`?
4. **"1169→1 deze maand"** (#6): `dashboard/service.py` sluit de `[BaseNet-import]`-marker uit.
   Prod-SQL: telt `contacts_this_month` nu de echte nieuwe relaties?
5. **Batch-foutmelding** (#9) + **cijfer-definities** (#10/#14): ratio zelfde populatie + gecapt;
   negatief "Openstaand" → "teveel betaald". Prod: `collection_rate` plausibel (≤100)?
6. **Mailsync-gezondheid** (#1): `last_sync_error` — de scheduler-except doet rollback→commit per
   account; kan een geslaagde sync van een ánder account daardoor verloren gaan? Controleer de flow.
7. **Scheduler-heartbeat** (#2): de APScheduler-listener schrijft async vanuit een sync-callback
   (`asyncio.ensure_future`). Draait dat betrouwbaar in prod (AsyncIOScheduler-loop)? Prod: staan er
   `scheduler_heartbeat`-rijen ná ~een dag draaien, en is `scheduler_alerts` leeg terwijl jobs lopen?
8. **Intake-startstap** (#8): een via intake goedgekeurd incassodossier krijgt nu stap + historie.
   Klopt de status-overgang (werk-stap → in_behandeling) met de rest van de app?
9. **14-dagenbrief harde blokkade** (#5, JURIDISCH — extra streng nalezen): de batch blokkeert een
   B2C-sommatie als de 14-dagenbrief niet verstuurd is óf < 15 dagen geleden (`DAGENBRIEF_MIN_DAYS`).
   Is `entered_at` van de 14-dagenbrief-stap de juiste "verstuurd"-proxy? Zijn er ándere verzendpaden
   (follow-up "Uitvoeren", losse compose) die B2C-sommaties versturen en deze gate NIET raken? Dat is
   het grootste risico: een tweede deur waardoor een te-vroege sommatie alsnog kan.
10. **Logout server-side intrekken** (#16) + **Gmail-knop verborgen** (#17): geen regressie in de
    inlog/uitlog-flow.

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -v` (of gericht per module; de S203-tests:
  `test_time_entries`, `test_case_files_rename`, `test_draft_amounts_fallback`, `test_dashboard`,
  `test_intake`, `test_email_sync`, `test_incasso_pipeline`, `test_compliance_14dagenbrief`).
- Lint: `uvx ruff check backend/app/`
- Prod read-only: login als seidony@ (creds in memory), GET-only + read-only SQL via SSH.

## Constraints (wat NIET doen)
- 100% read-only: geen prod-mutatie, geen deploy, geen mail (mailslot blijft dicht).
- Niet zelf bouwen zonder eerst de bevinding + fix te presenteren (Plan Mode).
- 35-route backend-sloop, #7 en #15 zijn GEEN onderdeel van deze review (apart spoor).

## Uitkomst
Een kort reviewrapport (`docs/sessions/S204-review.md`): per fix ✅ bevestigd / ⚠️ punt gevonden,
met bewijs. Bevestigde fouten → beslislijst voor een vervolg-bouwsessie. Werk af met /sessie-einde.
