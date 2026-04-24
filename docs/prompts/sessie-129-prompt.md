Sessie 129 — Visueel testen AI banner + volgende taak
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie AI-UX) en SESSION-NOTES.md (sessie 128). Geef compacte samenvatting."

## Taak 1: Visueel testen AI banner (sessie 128 wijziging)

In sessie 128 is de AI-suggestie banner op de zaakdetailpagina uitgebreid met:
1. **Uitklapbaar emailbericht** — "Toon volledige e-mail" toggle met sanitized HTML body
2. **Klikbare bronnen** — pill-badges (dossier, stap, openstaand bedrag, debiteur, email)

Dit is gecommit (`74605cf`) en deployed naar productie, maar nog NIET visueel getest.

### Teststappen:
1. Open https://luxis.kestinglegal.nl en log in als seidony@kestinglegal.nl
2. Ga naar een incasso-dossier met een pending AI classificatie (bijv. case-2026-00048)
3. Controleer de AI-suggestie banner:
   - Verschijnt de banner met email context (van, datum, onderwerp)?
   - Klik "Toon volledige e-mail" — verschijnt de emailbody? Scrollbaar bij lange emails?
   - Zijn de bronnen-pills zichtbaar (Dossier, Stap, Openstaand, Debiteur, Inkomende e-mail)?
   - Klik "Openstaand: €X" — navigeert naar vorderingen tab?
   - Klik "Inkomende e-mail" — navigeert naar correspondentie tab?
4. Als er GEEN pending classificaties zijn: classificeer handmatig een email via de correspondentie tab

### Als er bugs zijn:
Fix ze direct, commit, push, deploy.

## Taak 2: Volgende feature (als taak 1 groen is)
Check de roadmap voor de volgende prioriteit. Kandidaten:
- DF122-04: mailsjablonen-editor
- BIK-BTW voor niet-BTW-plichtige clienten (AUD124-01)

## Verificatie
- `npx tsc --noEmit` (frontend)
- Visueel + functioneel in browser via Playwright
- Commit + push + deploy na elke fix

## Constraints (wat NIET doen)
- Geen worktrees
- Geen refactors buiten scope
- Geen nieuwe features starten voordat taak 1 visueel groen is
- Draai GEEN lint/tests/build tenzij expliciet nodig

## Commit
Commit + push na elke afgeronde taak. Deploy automatisch via SSH.
