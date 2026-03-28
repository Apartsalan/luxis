Sessie 113 — Lisanne overzetten naar M365 + data-migratie voorbereiding
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Huidige status' + 'Audit 110 Actiepunten' + 'P0') en SESSION-NOTES.md (sessie 112). Geef compacte samenvatting."

## Taak

### Prioriteit 1: Lisanne overzetten naar M365 (AUDIT-04/05 voorbereiding)

Lisanne gebruikt nog BaseNet voor email. Ze moet overgezet worden naar Microsoft 365 zodat de Outlook integratie in Luxis volledig werkt.

Wat gedaan moet worden:
1. Controleer of Lisanne's M365 mailbox al aangemaakt is (seidony@kestinglegal.nl werkt al)
2. Bouw een data-migratie voorbereidingsscript dat BaseNet export-formaten kan analyseren
3. Documenteer stap-voor-stap wat Lisanne moet doen om haar BaseNet data te exporteren
4. Bouw een dry-run import tool die BaseNet CSV/Excel kan parsen en mappen naar Luxis schema's

### Prioriteit 2: Exact Online live brengen

De Exact Online integratie is gebouwd (sessie 112) maar heeft nog geen credentials:
1. Documenteer hoe een Exact Online developer account te registreren
2. Maak een setup-gids voor Lisanne (stap-voor-stap)
3. Test de OAuth flow als de credentials beschikbaar zijn

### Prioriteit 3: Overgebleven a11y verbetering

Er zijn nog form-label associaties (htmlFor/id) die ontbreken op veel formulieren. De belangrijkste:
- relaties/nieuw/page.tsx
- facturen/nieuw/page.tsx
- instellingen tabs (kantoor, profiel, sjablonen)
- agenda/page.tsx

## Verificatie
- pytest voor backend changes
- tsc --noEmit voor frontend changes
- Commit + push na elke afgeronde deeltaak

## Constraints
- Geen wijzigingen aan bestaande facturatie/betalingen/incasso logica
- Geen worktrees
- Deploy automatisch na commit+push
