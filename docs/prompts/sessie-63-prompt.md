Sessie 63 — Pre-launch Sprint: Planning & Eerste Batch
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Pre-Launch Sprint') en SESSION-NOTES.md (sessie 62). Geef compacte samenvatting van de 6 taken en hun status."

## Situatie
Sessie 62 was een productie-readiness audit. Conclusie: Luxis is 90%+ klaar maar heeft 6 concrete gaps die gedicht moeten worden voordat Lisanne ermee kan werken. Dit zijn quick wins — geen grote features.

De 6 taken (PL-1 t/m PL-6):
1. **PL-1: Backups activeren** (~15 min) — crontab op VPS, backup dir, eerste test
2. **PL-2: Factuur-PDF generatie** (~4-6 uur) — endpoint, template, download knop
3. **PL-3: E2E auth test fix** (~30 min) — "Welkom terug" i.p.v. "Goedemorgen"
4. **PL-4: Timer persistent** (~1 uur) — localStorage zodat reload timer niet kwijtraakt
5. **PL-5: Default uurtarief** (~1-2 uur) — user settings + auto-fill
6. **PL-6: CSV payment import UI** (~2-3 uur) — frontend voor bestaand backend

## Taak voor deze sessie

### Fase 1: Planning (5 min)
Beoordeel of alle 6 taken in DEZE sessie passen, of dat we moeten splitsen.
Geef een concreet plan: wat doen we nu, wat schuift naar sessie 64?
Regel: liever 4 taken GOED dan 6 taken half.

### Fase 2: PL-1 — Backups activeren (EERST, altijd)
Dit is de belangrijkste taak. Zonder backup geen productie.
- SSH naar VPS: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216`
- Backup dir aanmaken: `/backups/luxis/`
- Crontab instellen: `0 3 * * * /opt/luxis/scripts/backup.sh`
- EERSTE backup handmatig draaien en verifieer dat het .sql.gz bestand er is
- Eventueel: off-site backup overwegen (S3/Backblaze)

### Fase 3: PL-3 — E2E auth test fix (quick win)
- `frontend/e2e/auth.setup.ts` en `frontend/e2e/auth.spec.ts`
- Zoek "Goedemorgen|middag|avond" en vervang door "Welkom terug" (of flexibelere regex)
- Draai `cd frontend && npx playwright test` om te verifiëren

### Fase 4: PL-4 — Timer persistent (quick win)
- Frontend timer state naar localStorage
- Bij page load: check localStorage voor actieve timer
- Bij timer start/stop: update localStorage
- Test: start timer, refresh pagina, timer loopt door

### Fase 5: PL-5 — Default uurtarief per gebruiker
- Backend: veld `default_hourly_rate` op User of TenantSettings model
- Endpoint: ophalen via settings
- Frontend: auto-fill bij nieuwe tijdregistratie als geen override

### Fase 6: PL-2 — Factuur-PDF generatie (grootste taak)
Dit is de grootste. Als de tijd op is, schuift dit naar sessie 64.
- Backend endpoint: `GET /api/invoices/{id}/pdf`
- DOCX template voor factuur (Kesting Legal huisstijl)
- PDF conversie via LibreOffice (zelfde als documenten)
- Frontend: "Download PDF" knop op factuur detailpagina
- Test: maak factuur, download PDF, check inhoud

### Fase 7: PL-6 — CSV payment import UI (als er tijd is)
- Backend endpoint bestaat al (`/api/payment-matching/import`)
- Frontend: pagina of modal met drag-and-drop CSV upload
- Match review UI (confidence badges, approve/reject)
- Als dit niet past: sessie 64

## Verificatie per taak
Na ELKE taak:
- Relevante tests draaien (`pytest` of `playwright`)
- `npm run build` na frontend changes
- Commit + push
- LUXIS-ROADMAP.md updaten (PL-X status → ✅)
- Deploy naar productie als relevant

## Constraints
- Commit + push na ELKE afgeronde taak (niet batchen)
- Deploy automatisch na elke commit+push
- Geen nieuwe features buiten de PL-1 t/m PL-6 lijst
- Als iets langer duurt dan verwacht: STOP en herplan
- Bij twijfel: vraag de gebruiker

## Commit format
`fix(module): PL-X beschrijving` of `feat(module): PL-X beschrijving`
