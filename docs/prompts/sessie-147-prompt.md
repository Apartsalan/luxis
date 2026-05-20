```
cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 147 — Deprecatie oude AI-endpoints + smart-replies UI cleanup (CLEAN-AI-01)

## Context laden bij start

Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (FEAT-AI-04, FEAT-AI-05, CLEAN-AI-01) en SESSION-NOTES.md (sessie 146).
Geef compacte samenvatting (max 350 woorden):
1. Wat is CaseActionFeed precies (5 kaart-types, filters, mounts)
2. Welke OUDE AI-endpoints + UI-componenten draaien nog parallel
3. Welke `useGenerateDraft` / `useSmartReplies` / classification UI bestaat nog
4. Hoeveel productie-records hangen aan oude endpoints (AIDraft / SmartReply / EmailClassification)
5. Memory `feedback_s141_afspraken` — wat blijft definitief weg"

## Taak

**Hoofddoel:** CLEAN-AI-01 — deprecatie oude AI-endpoints + verwijdering smart-replies UI. Eén entry-point (CaseActionFeed), geen parallelle UI.

### Subtaak 1 — Inventarisatie (max 20 min)
- Zoek alle frontend imports van `useGenerateDraft` (oude `/api/ai-agent/draft`)
- Zoek alle frontend imports van `useSmartReplies` / smart-reply componenten
- Zoek backend routes onder `/api/ai-agent/` die NIET via UnifiedDraftService gaan
- Documenteer in tabel: bestand → import → verwijderen of migreren

### Subtaak 2 — Migratie waar nodig
- Vervang resterende `useGenerateDraft` calls door `useDraft({intent: "next_step"})` van `use-ai-draft.ts`
- Smart-reply functionaliteit: óf migreer naar CaseActionFeed.ClassificationDoneCard CTA, óf verwijder volledig (Lisanne keuze nodig — flag)

### Subtaak 3 — Backend cleanup
- Markeer `/api/ai-agent/draft` als deprecated in OpenAPI (Pydantic schema description)
- Plan voor verwijdering in S148 als geen frontend gebruikt
- Smart-reply backend logica: zelfde aanpak

### Subtaak 4 — Tests + verificatie
- `cd frontend && npx tsc --noEmit`
- `docker compose exec backend pytest tests/ -v -k "ai or draft or smart"`
- Playwright op productie: dossier openen, CaseActionFeed werkt zonder oude UI, geen console errors
- Visueel: dossier 2026-00062, dossier 2026-00049 (heeft veel drafts)

### Subtaak 5 — Snooze-feature plannen (S148)
- Alleen ONDERZOEK + ontwerp, geen code
- DB-schema: `notifications.snoozed_until` (timestamp, nullable)
- UI: dropdown per kaart "Snooze 24u / 3 dagen / 1 week"
- Hook update: filter items waar snoozed_until > now
- Pre-mortem 3 faalredenen

## Verificatie

- Backend: `docker compose exec backend pytest tests/ -v`
- Lint: `docker compose exec backend ruff check app/`
- Frontend: `cd frontend && npx tsc --noEmit`
- Visueel: dossier op productie via Playwright, login als seidony@kestinglegal.nl

## Constraints (wat NIET doen)

- GEEN backend-endpoint hard verwijderen (alleen deprecate + plan voor S148)
- GEEN snooze code schrijven (S148 scope, alleen onderzoek + ontwerp)
- GEEN nieuwe kaart-types toevoegen (S148+)
- GEEN cleanup van AIDraft DB-records (audit-trail behoud)

## Commit

Conventional commits per subtaak. Push automatisch + auto-deploy via GitHub Actions.

## Memory-aandacht

- `feedback_s141_afspraken` — concept-knop Correspondentie BLIJFT weg, smart-reply ALLEEN via CaseActionFeed
- `feedback_kritisch_zijn` — als migratie complexer dan ingeschat, deel op in 2 sessies
- `feedback_grondig_checken` — niet alleen tsc, ook visueel productie
- `feedback_test_recipient_safety` — bij elke email-test recipient ALTIJD arsalanir@hotmail.com
- `reference_auto_deploy` — push triggert CI → auto-deploy. Niet handmatig SSH'en tenzij CI faalt.
```
