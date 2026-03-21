Sessie 93 — Mega-audit Sprint 4: MEDIUM UX polish
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 92). Geef compacte samenvatting."

## Taak
Fix ALLE MEDIUM UX issues:

**UX (8 items):**
- UX-14: Responsive tabellen — data verborgen op mobiel. Fix: card layout of horizontaal scrollen op kleine schermen
- UX-15: Form validatie — geen inline foutmeldingen. Fix: voeg field-level validation toe met react-hook-form errors
- UX-16: Unsaved changes warning — geen waarschuwing bij navigeren met onopgeslagen wijzigingen. Fix: beforeunload + router guard
- UX-17: Empty state guidance — lege lijsten missen begeleiding. Fix: voeg illustraties + "Maak je eerste..." CTA toe
- UX-18: Breadcrumbs — ontbreken op detail pagina's. Fix: breadcrumb component op case/contact/invoice detail
- UX-19: Error boundaries per tab — JS error in één tab crasht hele case detail. Fix: ErrorBoundary wrapper per tab
- UX-20: formatCurrency NaN — toont "NaN" bij null waarden. Fix: null check in formatCurrency helper
- UX-21: isError niet afgevangen — financiële queries tonen lege lijst i.p.v. error state. Fix: error state component

## Verificatie
- npx tsc --noEmit (in frontend/)
- Visuele check via Playwright/preview van de gewijzigde pagina's
- Test responsiveness op 375px breed

## Constraints (wat NIET doen)
- Geen backend wijzigingen
- Geen security/infra wijzigingen
- Geen nieuwe features

## Commit
Commit + push na ALLE fixes. Deploy via SSH automatisch.
