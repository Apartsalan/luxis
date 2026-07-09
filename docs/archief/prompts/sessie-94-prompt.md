# Sessie 94 — Mega-audit afronden: BUG-50 + defensieve UX

## Terminal A (leiding — commit + push + deploy)

```
Sessie 94A — BUG-50 test failures + UX-19/UX-20
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-audit' en 'BUG-50') en SESSION-NOTES.md (sessie 91). Geef compacte samenvatting."

## Taak
Fix alle openstaande items uit de mega-audit. Dit zijn er 3:

### 1. BUG-50 — 5 pre-existing test failures (PRIORITEIT)
De volgende tests falen al sinds sessie 90+. Fix ze:

- `test_auth.py::test_refresh_token` — IntegrityError (waarschijnlijk fixture/schema mismatch)
- `test_invoice_parser.py::test_validate_and_clean_basic` — AssertionError
- `test_invoice_parser.py::test_validate_and_clean_decimal_precision` — AssertionError
- `test_invoice_parser.py::test_parse_invoice_pdf_success` — AssertionError
- `test_invoices.py::test_status_workflow_happy_path` — assert 400 == 200

Draai eerst: `docker compose exec backend pytest tests/test_auth.py::test_refresh_token tests/test_invoice_parser.py tests/test_invoices.py::test_status_workflow_happy_path -v`
Analyseer elke failure, fix de root cause (niet de test aanpassen tenzij de test echt fout is).

### 2. UX-19 — Error boundaries per tab
JS error in één tab crasht hele case detail pagina. Fix:
- Maak een `ErrorBoundary` component (class component, React error boundaries werken alleen met classes)
- Wrap elke tab in het case detail (`frontend/src/app/(dashboard)/zaken/[id]/page.tsx`) met ErrorBoundary
- Toon een nette foutmelding in Nederlands met "Probeer opnieuw" knop

### 3. UX-20 — formatCurrency NaN
`formatCurrency()` in `frontend/src/lib/utils.ts` toont "NaN" bij null/undefined waarden.
- Fix: return "€ 0,00" of "-" bij null/undefined/NaN input
- Check alle plekken waar formatCurrency wordt aangeroepen met potentieel null waarden

## Verificatie
- `docker compose exec backend pytest tests/ -v` — ALLE tests moeten slagen (0 failures)
- `docker compose exec backend ruff check app/` — 0 warnings
- Frontend build check: `docker compose exec frontend npx tsc --noEmit` (pre-existing errors in confirm-dialog en sanitize zijn OK)

## Constraints
- GEEN nieuwe features bouwen
- GEEN refactors buiten scope
- GEEN worktrees

## Commit + Deploy
- WACHT op terminal B voordat je commit+push doet
- Vraag de gebruiker: "Is terminal B klaar?"
- Commit message: `fix(backend+frontend): sessie 94 — BUG-50 test fixes + UX-19/20 error handling`
- Na push: deploy via SSH (`ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build --no-cache backend frontend && docker compose up -d backend frontend"`)
- Update LUXIS-ROADMAP.md en SESSION-NOTES.md
```

## Terminal B

```
Sessie 94B — UX-14 t/m UX-18 frontend verbeteringen
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-audit', items UX-14 t/m UX-18). Geef compacte samenvatting."

## Taak
Fix 5 MEDIUM UX issues uit de mega-audit. Allemaal frontend-only.

### 1. UX-14 — Responsive tabellen
Data wordt verborgen op mobiel (`hidden sm:table-cell`) zonder alternatief.
- Voeg een card-based mobile view toe voor de belangrijkste tabellen (dossierlijst, facturenlijst, relatielijst)
- Pattern: `<div class="block sm:hidden">` card view + `<table class="hidden sm:table">` tabel view
- Minimaal: naam, status, bedrag zichtbaar op mobiel

### 2. UX-15 — Form validatie
Geen inline foutmeldingen op formulieren.
- Voeg inline validatie toe aan de belangrijkste formulieren: nieuw dossier wizard, nieuwe factuur, nieuwe relatie
- Pattern: rode border + foutmelding onder het veld
- Focus op verplichte velden (client, type, datum)
- Gebruik bestaande form state, geen nieuwe library

### 3. UX-16 — Unsaved changes warning
Geen waarschuwing bij onopgeslagen wijzigingen.
- Voeg `beforeunload` event toe op pagina's met bewerkbare formulieren
- Focus op: DetailsTab (dossier bewerken), relatie bewerken, factuur aanmaken
- Pattern: `useEffect` met `window.addEventListener('beforeunload', handler)` wanneer form dirty is
- GEEN custom modal nodig — browser's native dialog is voldoende

### 4. UX-17 — Empty state guidance
Lege lijsten missen begeleiding/onboarding.
- Voeg empty states toe met icoon + tekst + actie-knop aan: dossierlijst, facturenlijst, relatielijst
- Pattern: icoon (lucide-react) + korte beschrijving + "Eerste [item] aanmaken" knop
- Check of er al empty states zijn en verbeter die (sommige bestaan al maar zijn kaal)

### 5. UX-18 — Breadcrumbs
Ontbreken op detail pagina's.
- Voeg breadcrumbs toe aan: dossier detail, relatie detail, factuur detail
- Pattern: "Dashboard > Dossiers > 2026-00042" met links
- Maak een herbruikbaar `Breadcrumb` component
- Plaats boven de pagina-titel

## Verificatie
- Geen backend wijzigingen, dus geen tests nodig
- Check visueel via de app dat de changes werken (als preview beschikbaar is)

## Constraints
- GEEN backend wijzigingen
- GEEN nieuwe dependencies toevoegen
- GEEN worktrees
- NIET committen of pushen — Terminal A doet dat
```
