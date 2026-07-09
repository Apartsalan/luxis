```
cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 146 — CaseActionFeed widget (deel 1: onderzoek + ontwerp + notification-types)

## Context laden bij start

Gebruik de luxis-researcher subagent:
"Lees `docs/onderzoek-ai-overlap-S141.md` (architectuur-voorstel sectie),
SESSION-NOTES.md (sessie 145 — Volgende sessie + Bekende issues),
en LUXIS-ROADMAP.md (zoek FEAT-AI-04, BUG-83, BUG-84).
Geef compacte samenvatting in max 350 woorden:
1. Wat is CaseActionFeed (visie uit S141 onderzoek)
2. Welke 3 plekken vervangt het (DossierHeader banner / TijdregistratieTab / CorrespondentieTab smart-reply)
3. Status BUG-83 (bel-icon) + BUG-84 (notification-types) — open issues
4. Beslissingen Lisanne S141 (concept-knop weg, één centrale plek)
5. UnifiedDraftService endpoint POST /api/ai/draft staat klaar voor frontend integratie (S145)"

## Taak

**Hoofddoel:** CaseActionFeed widget op Overzicht-tab dossier ontwerpen + bouwen
(deel 1: onderzoek + notification-types backend + widget skeleton). Vervolg in S147.

### Subtaak 1 — Onderzoek (max 30 min)
Bestudeer hoe HubSpot Activity Feed, Notion Inbox, Clio Manage Activity Feed werken.
Doel: één chronologische stream van acties op dossier. Vragen om te beantwoorden:
- Kaart-types (concept-klaar / inbound-mail / classification / deadline / pipeline-stap)?
- Filters (alles / wachtend op actie / afgehandeld)?
- Acties per kaart (preview/openen/dismissen/snooze)?
- Real-time refresh of pull-to-refresh?

Pre-mortem (memory bekende-fouten): 3 faalredenen + waarom toch juiste aanpak.

### Subtaak 2 — Notification-types backend uitbreiden (BUG-84)
- `email_received`: bij elke inbound mail die aan dossier wordt gekoppeld
- `draft_ready`: bij elke AIDraft.status='generated' (via UnifiedDraftService)
- `classification_done`: bij EmailClassification create
- `deadline_overdue`: bestaand, behouden

Plekken:
- `app/notifications/service.py` — nieuwe `create_*` functies
- Hooks in `app/email/sync_service.py` (email_received), `app/ai_agent/unified_draft_service.py` (draft_ready), `app/ai_agent/service.py` (classification_done)

### Subtaak 3 — CaseActionFeed component skeleton
- `frontend/src/components/case-action-feed/CaseActionFeed.tsx` — container, query, list
- `frontend/src/hooks/use-case-action-feed.ts` — fetch notifications gefilterd op case_id
- 4 card-componenten: DraftReadyCard, EmailReceivedCard, ClassificationCard, DeadlineCard
- Mount op `zaken/[id]/page.tsx` Overzicht-tab BOVENAAN

### Subtaak 4 — BUG-83 bel-icon onderzoek
- Open productie via Playwright, login via token (zie S145 SESSION-NOTES voor token-generatie script)
- Check `useUnreadCount` hook + bel-component
- Diagnose: rendering of polling-bug? Document in BUG-83.

### Subtaak 5 — Tests
- `tests/test_notifications_service.py` — nieuwe create_* functies
- Frontend tsc clean

## Verificatie

- Backend: `docker compose exec backend pytest tests/ -v`
- Lint: `docker compose exec backend ruff check app/`
- Frontend: `cd frontend && npx tsc --noEmit`
- Visueel: open dossier 2026-00062, check CaseActionFeed widget toont kaarten

## Constraints (wat NIET doen)

- GEEN frontend cleanup van oude AI-banners — S147 scope. Eerst skeleton + notification-types
- GEEN deprecatie `/api/ai-agent/draft` endpoint — blijft tot S147 frontend migratie klaar is
- GEEN refactor van bestaande `draft_service.py` of `smart_reply_service.py`
- GEEN polling-interval optimalisatie — eerst zien hoe vaak data daadwerkelijk wijzigt

## Commit

Conventional commits per subtaak. Push automatisch + auto-deploy via GitHub Actions.

## Memory-aandacht

- `feedback_s141_afspraken` — concept-knop op Correspondentie BLIJFT weg
- `feedback_kritisch_zijn` — als CaseActionFeed te complex wordt, deel op in 3 sessies
- `feedback_grondig_checken` — niet alleen tests, ook visueel checken op productie
- `feedback_test_recipient_safety` — bij elke email-test recipient ALTIJD arsalanir@hotmail.com
- `reference_auto_deploy` — push triggert CI → auto-deploy. Niet handmatig SSH'en.
```
