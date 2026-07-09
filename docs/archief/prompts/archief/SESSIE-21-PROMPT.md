# Sessie 21 — Deploy Verificatie + QA

## Stap 1: Lees ALLEEN dit bestand eerst. Lees andere bestanden pas als je ze nodig hebt.

## Wat er vorige sessie (20) gedaan is

3 bugs gefixt + deploy issues opgelost:

- **BUG-22:** Invoice detail 500 → circulaire `lazy="selectin"` → gefixt met `lazy="noload"` + explicit selectinload
- **BUG-23:** Notifications 404 → stub router aangemaakt + import path fix + frontend `/api/` prefix fix
- **BUG-24:** /api/users 404 → users_router toegevoegd

Deploy issues: `.env` ontbrak op VPS (fix: `cp .env.production .env`), import crash gefixt.

**Alles is gecommit, gepusht, en gedeployed (backend + frontend).**

## Stap 2: Verifieer de deploy

Login op https://luxis.kestinglegal.nl met `seidony@kestinglegal.nl` / `Hetbaken-KL-5`

Check:
1. Login werkt (geen 502)
2. Dashboard laadt zonder console errors voor `/notifications` of `/api/users`
3. Ga naar een factuur detail → geen 500 error

## Stap 3: QA doorlopen

Lees `QA-CHECKLIST.md` en loop alle 14 secties door via Playwright MCP. Fix bugs direct.

## Referentie-bestanden (lees alleen als nodig)

- `LUXIS-ROADMAP.md` — Volledige projectstatus (LANG, ~500 regels, lees alleen relevante secties)
- `SESSION-NOTES.md` — Details sessie 20 staat bovenaan
- `CLAUDE.md` + `backend/CLAUDE.md` — Conventies

## Deploy commando (voor gebruiker op VPS)

```bash
cd /opt/luxis && git pull && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend backend && \
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend backend
```

## Na QA: volgende prioriteiten

1. Document template editing UI + merge fields uitbreiden
2. Incasso Workflow Automatisering (P1)
