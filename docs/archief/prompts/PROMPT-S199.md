# Sessie-prompt S199 — Veegsessie (stapel 4) + S198-review-voorstellen

Plan gemaakt door Fable in S198 (11 juli), terwijl de PowerSearch-bouw liep. Werkvorm:
zelfde als de PowerSearch-rit als die bevalt — Fable plant/reviewt, Sol (Codex xhigh)
bouwt, Claude deployt en verifieert. Anders: Opus bouwt zelf.

---

Sessie 199 — Veegsessie: opruimen + rechtzetten wat de S198-reviews en de doorlichting
hebben aangewezen. Geen nieuwe features.

## Vooraf — besluiten die al genomen zijn (niet heropenen)
- **12 onverklaarde bankontvangsten (±€21.700, Donker/Dinc): VERVALLEN** (besluit Arsalan
  11 juli). Niet bij de 7 vaste opdrachtgevers → geen incasso → niet boeken, geen open
  punt meer. Er hoeft niets gewist (nooit ingeboekt).
- Verwijderingen van data (testdossier, test-aanvragen): **per stuk akkoord van Arsalan
  ín de sessie** — is hij er niet bij, dan die blokken overslaan en laten staan.
- Mailslot blijft UIT; niets bouwen dat mail verstuurt.

## Taak 1 — 'Betaald' is een eindtoestand, overal (S198-review Fable#5)
Sinds S198 wordt 'betaald' automatisch gezet bij €0 openstaand → het is nu een gewone,
frequente eindstatus. Maar dashboard + rapportages filteren alleen `!= "afgesloten"`,
en de AI-classificatie-sweep sluit alleen 'afgesloten' uit (betaalde zaken blijven
AI-kosten maken).
- Vervang die filters door de bestaande constante `TERMINAL_STATUSES`
  (`backend/app/cases/schemas.py` — staat er al, wordt nergens gebruikt).
- Bekende plekken: `backend/app/dashboard/service.py` (±regels 29/51/70/82),
  `backend/app/dashboard/reports_service.py`, `backend/app/ai_agent/service.py`
  (sweep, ±regel 283). **Grep álle `!= "afgesloten"` / `notin_(["afgesloten"])`-varianten**
  op Case.status vóór je begint; beoordeel per plek (rapportage over gesloten zaken mag
  betaald juist wél tellen als "geïnd" — denk na, niet blind vervangen).

## Taak 2 — Bulk-status-knop repareren (S198-review Codex; pre-existing 404)
`frontend/src/app/(dashboard)/zaken/page.tsx` roept `PUT /api/cases/bulk/status` aan —
dat endpoint bestaat niet → altijd "Statuswijziging mislukt". Bouw het endpoint
(cases/router.py): loop over case_ids via de bestaande `update_case_status`
(4-status-logica, mét de €0-guard voor 'betaald' en de derdengelden-guard voor
'afgesloten'); per zaak die geweigerd wordt: overslaan + reden in de respons, net als
batch_execute. Response: {updated, skipped, errors}. Auth verplicht. Tests: happy path +
guard-skip + tenant-isolatie.

## Taak 3 — Dode status-engine opruimen (S198-voorstel; de tabellen mogen nu wél weg)
Na S198 heeft de oude workflow-status-engine nul productie-callers:
- Backend: `on_status_change` (hooks.py), `execute_transition`/`validate_transition`/
  `get_allowed_transitions` + status/transition/rule-CRUD in `workflow/service.py` en
  `workflow/router.py` (taken-endpoints BLIJVEN — die zijn levend), en de bijbehorende
  tests. `evaluate_rules_for_transition` gaat mee weg (enige caller was on_status_change).
- Frontend: `NEXT_STATUSES` + `PIPELINE_STEPS` (zaken/[id]/types.tsx), de workflow-status/
  transition/rule-hooks in use-workflow.ts (taak-hooks blijven), en het Instellingen-blok
  dat statussen/transities/regels beheert (als dat bestaat — grep).
- **Fase-stepper in DossierHeader** leunt op de lege `workflow_statuses` → toont blanco.
  Vervang de fase-afleiding door de pijplijn-stap-categorie (`step_category` van de
  huidige stap: minnelijk/gerechtelijk/regeling/administratief/afsluiting) of haal de
  stepper weg als dat niet netjes kan. Geen blanco balk laten staan.
- Migratie die `workflow_statuses`/`workflow_transitions`/`workflow_rules` dropt mag —
  ze zijn leeg op prod (0 rijen, S197 gemeten). `workflow_tasks` BLIJFT (levend).
  Verifieer 0 rijen vóór de drop in de migratie zelf (guard).
- Traceer eerst ALLE imports van de te slopen symbolen (grep) — verjaring-monitor
  (`check_verjaring`) gebruikt WorkflowStatus voor terminal-slugs: die query vervangen
  door de vaste `TERMINAL_STATUSES`.

## Taak 4 — C4: rapportages eerlijk maken
- "Geïnd €0" → som van betalingen in de gekozen periode (data is er: 255 betalingen,
  €311.547,70). Definitie vastleggen in een comment.
- Faseverdeling: outer join met "Geen stap"-rij zodat de telling sluit (18=18).

## Taak 5 — kleine vegen (elk heel klein)
- C5: Uren-relatiefilter toont alle 1.169 relaties → alleen cliënten.
- Dashboard: lege uren/facturen-widgets een nette lege-staat geven (modules blijven aan,
  besluit C3).
- A6: "1169 nieuw deze maand" op relaties — import-datum uitsluiten of label aanpassen.
- A12: accountnaam van seidony@ ("Lisanne Kesting") rechtzetten → "Arsalan Seidony".
- 2 verweesde verjaringstaken op afgesloten zaken (IN100015/IN100127) opruimen — akkoord
  is er al (roadmap punt 3).
- Pijplijn-datavervuiling: 16 inactieve reliek-stappen (sort 100-115) + dubbele inactieve
  "Eerste sommatie" + transities die naar inactieve stappen wijzen — hard verwijderen mag
  (inactief + geen verwijzingen; check FK's incl. case_step_history vóór delete; bij
  verwijzingen: laten staan en melden).

## Taak 6 — ALLEEN MET ARSALAN ERBIJ (per stuk akkoord)
- A10: testdossier 2026-00001 verwijderen (vervuilt werkvoorraad/feed/rapportage).
- B10: 6 test-aanvragen in Intake afwijzen + "AI Intake" hernoemen naar "Nieuwe aanvragen".

## Verificatie (per taak, niet pas aan het eind)
- `docker compose exec -T backend python -m pytest tests/ -k "<relevant>" -q`
- Bij taak 3 (brede sloop): volledige suite één keer.
- `uvx ruff check backend/app/` · `npx tsc --noEmit` + `npm run build`
- Deploy via SSH (skill `deploy-regels`); live doorklikken: dashboard-cijfers, rapportages,
  bulk-status op 2 testzaken, dossierkop zonder blanco balk.

## Commit
Per taak committen + pushen (conventional commits); afsluiten met `/sessie-einde`
(notities, roadmap, tag sessie-199).
