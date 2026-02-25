# Sessie 21 — Deploy Verificatie + QA Afronding

## Lees eerst deze bestanden (in volgorde):

1. `LUXIS-ROADMAP.md` — Volledige projectstatus, tech stack, features, bugs
2. `SESSION-NOTES.md` — Sessie 20 details (bovenaan), gewijzigde bestanden
3. `QA-CHECKLIST.md` — 14 secties om te testen
4. `CLAUDE.md` — Ontwikkelregels en conventies
5. `backend/CLAUDE.md` — Backend-specifieke conventies

## Context sessie 20

### Wat er gedaan is
- QA testing via Playwright MCP browser automation (14 secties)
- 3 bugs gevonden en gefixt: BUG-22 (invoice 500), BUG-23 (notifications 404), BUG-24 (users 404)
- Deploy issues opgelost: `.env` ontbrak op VPS, import path fout in notifications router

### Wat er gedeployed is
- **Backend:** gedeployed (commit `941aaad` — notifications import fix)
- **Frontend:** gedeployed (commit `08142dc` — `/api/` prefix fix in notification hooks)

### Productie-omgeving
- **URL:** https://luxis.kestinglegal.nl
- **Login:** `seidony@kestinglegal.nl` / `Hetbaken-KL-5`
- **VPS:** Hetzner, SSH als root, project in `/opt/luxis`
- **`.env`**: moet bestaan in `/opt/luxis/` (kopie van `.env.production`)

### Deploy commando
```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend backend
```

## Taken voor sessie 21

### 1. Deploy verificatie (PRIORITEIT)
Verifieer dat alle 3 bugs gefixt zijn op productie:
- **BUG-22:** Open een factuur detail pagina → geen 500 error meer
- **BUG-23:** Console errors voor `/notifications` en `/notifications/unread-count` zijn weg (of geven 200/leeg terug)
- **BUG-24:** Console errors voor `/api/users` zijn weg

### 2. Volledige QA via Playwright MCP
Loop de hele QA-CHECKLIST.md door op productie. Gebruik Playwright MCP tools om:
- In te loggen
- Elke sectie (1-14) systematisch te testen
- Bugs te documenteren
- Fixes direct toe te passen

### 3. Bugs fixen die je vindt
Fix gevonden bugs direct:
- Backend fixes in `C:\Users\arsal\Documents\luxis\backend\`
- Frontend fixes in `C:\Users\arsal\Documents\luxis\frontend\`
- Commit + push na elke fix
- Laat gebruiker deployen

### 4. Documentatie bijwerken
Na alle fixes:
- LUXIS-ROADMAP.md bijwerken met nieuwe bugs/fixes
- SESSION-NOTES.md bijwerken met sessie 21 details
- QA-CHECKLIST.md afvinken

## Volgende prioriteiten (na QA)
1. Document template editing UI + merge fields uitbreiden
2. Incasso Workflow Automatisering (P1) — zie roadmap
3. BaseNet data migratie — wacht op Lisanne's export
