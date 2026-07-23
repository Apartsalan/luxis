cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 246 — Uitgesteld versturen (demo-punten blok 3)

## Model
Bouwen → **Opus**. Check bij start; verkeerd model → wissel vragen.
Dit raakt ÁLLE verzendroutes → eindreview op Fable verplicht.

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S246). CI van S245 natrekken.

## Hoofdtaak — "verstuur om 15:00" op ELKE verzendmethode
Wens Arsalan: incassomails alleen op nette tijden; Lisanne werkt 's avonds en
wil dan klaarzetten voor de volgende dag. Moet werken op: AI-antwoord,
AI-concept, gewone mail, sjablonen, vanuit dossier — "echt overal".

Gemeten verzenddeuren (S243): gedeeld punt `send_with_attachment`
(`backend/app/email/send_service.py:90`) met callers in followup_service (2×),
ai_agent/service, documents/router, incasso/service (2×), invoices/service;
PLUS `compose_router.py::send_via_provider` (regel 392, eigen provider-call).

1. **Tabel `scheduled_emails`** — TenantBase, **RLS in DEZELFDE migratie**
   (`apply_rls`): volledige verzendpayload, scheduled_at, status
   (pending/sent/cancelled/failed), case_id, aanmaker, poging-teller.
2. **Verzenddeuren**: optionele `scheduled_at` → rij in de wachtrij i.p.v.
   verzenden. Verzending later loopt door EXACT dezelfde functies (doorschuiven,
   logging, afzender — identiek gedrag).
3. **Scheduler-job** (bestaand APScheduler-patroon + pipeline-lock/heartbeat,
   memory `feedback_pipeline_locks`): elke minuut rijpe rijen versturen;
   fout → status failed + melding, geen stille retry-storm.
4. **UI**: "Verstuur later"-knop met presets (Morgen 09:00 / Morgen 15:00 /
   eigen tijdstip) op compose-dialoog, AI-concept-review, follow-up-verzending
   en batch. Geplande mails zichtbaar (dossier + Mail-pagina) + annuleerbaar.

## Verificatie (HARD)
- Kruispunt-check skill `breed-testen`: route×huisregel-matrix over alle 7
  deuren; wachter per foutSOORT.
- pytest breed (send/compose/followup/incasso/invoice); uvx ruff; tsc.
- Migratie: RLS-drift-guard groen (`test_rls_isolation.py`).
- **Playwright, screenshots**: plannen, in de lijst zien, annuleren; klok van
  de server is UTC — tijden in NL-tijd tonen én opslaan-conversie bewijzen.
- Live-bewijs met 1 testmail naar 2026-00006 (eigen gmail), GO per verzending.
- Deploy mét migratie (build → migrate → up), login 200, CI groen.

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S247).
