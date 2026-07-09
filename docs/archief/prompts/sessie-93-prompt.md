Sessie 93 — Mega-audit Sprint 4: UX polish (pure frontend componenten/pages)
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Mega-Audit Sprint') en SESSION-NOTES.md (sessie 90). Geef compacte samenvatting."

## Taak
Fix ALLE UX issues (ALLEEN frontend componenten en pages, GEEN hooks):

**UX (7 items):**
- UX-14: Responsive tabellen — data verborgen op mobiel. Fix: card layout of horizontaal scrollen op kleine schermen
- UX-15: Form validatie — geen inline foutmeldingen. Fix: voeg field-level validation toe met react-hook-form errors
- UX-16: Unsaved changes warning — geen waarschuwing bij navigeren met onopgeslagen wijzigingen. Fix: beforeunload + router guard
- UX-17: Empty state guidance — lege lijsten missen begeleiding. Fix: voeg illustraties + "Maak je eerste..." CTA toe
- UX-18: Breadcrumbs — ontbreken op detail pagina's. Fix: breadcrumb component op case/contact/invoice detail
- UX-19: Error boundaries per tab — JS error in één tab crasht hele case detail. Fix: ErrorBoundary wrapper per tab
- UX-20: formatCurrency NaN — toont "NaN" bij null waarden. Fix: null check in formatCurrency helper

**LET OP:** UX-21 (isError handling) is verplaatst naar sessie 91 omdat het dezelfde hooks raakt als CQ-12.

## Verificatie
- npx tsc --noEmit (in frontend/)
- Visuele check via Playwright/preview van de gewijzigde pagina's
- Test responsiveness op 375px breed

## Constraints (wat NIET doen)
- Geen backend wijzigingen
- Geen frontend hooks wijzigen (use-invoices.ts, use-collections.ts etc. — dat doet sessie 91)
- Geen Docker/infra wijzigingen (dat doet sessie 92)
- Geen nieuwe features
- NIET committen of pushen — meld dat je klaar bent (andere terminals draaien parallel)

## Commit
NIET zelf committen. Terminal A regelt commit + push voor alle terminals.
