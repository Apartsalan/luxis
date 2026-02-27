---
name: deploy-regels
description: Deployment regels en commando's voor de Luxis VPS
---

# Deploy Regels

## KRITISCH
- Claude heeft GEEN SSH-toegang. Geef het commando aan de gebruiker.
- Productie: https://luxis.kestinglegal.nl — VPS op `/opt/luxis`
- `COMPOSE_FILE` staat in `.env` → gewoon `docker compose` werkt

## Deploy commando's

### Alleen frontend:
```bash
cd /opt/luxis && git pull && docker compose build --no-cache frontend && docker compose up -d frontend
```

### Alleen backend:
```bash
cd /opt/luxis && git pull && docker compose build --no-cache backend && docker compose up -d backend
```

### Backend + migraties:
```bash
cd /opt/luxis && git pull
docker compose run --rm backend python -m alembic upgrade head
docker compose build --no-cache backend && docker compose up -d backend
```

### Alles:
```bash
cd /opt/luxis && git pull
docker compose run --rm backend python -m alembic upgrade head
docker compose build --no-cache backend frontend && docker compose up -d
```

## Valkuilen
- **Alembic: `run` niet `exec`** als backend crashed
- **POSTGRES_PASSWORD:** werkt alleen bij eerste volume-init. Later wijzigen via `ALTER USER`
- **Na ELKE commit ALTIJD `git push origin main`** — anders bereikt het de VPS niet
