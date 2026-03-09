---
name: deploy-regels
description: Deployment regels en commando's voor de Luxis VPS
---

# Deploy Regels

## SSH Toegang
- **Host:** root@46.225.115.216
- **Key:** `~/.ssh/luxis_deploy` (passphrase-vrij)
- **SSH commando:** `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216`
- **Productie URL:** https://luxis.kestinglegal.nl
- **App pad op VPS:** `/opt/luxis`
- `COMPOSE_FILE` staat in `.env` → gewoon `docker compose` werkt

## Autonome deploy (Claude doet dit zelf)

Na commit + push → deploy automatisch via SSH. Geen commando aan gebruiker geven.

### Alleen frontend:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build --no-cache frontend && docker compose up -d frontend"
```

### Alleen backend:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build --no-cache backend && docker compose up -d backend"
```

### Backend + migraties:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose run --rm backend python -m alembic upgrade head && docker compose build --no-cache backend && docker compose up -d backend"
```

### Alles:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose run --rm backend python -m alembic upgrade head && docker compose build --no-cache backend frontend && docker compose up -d"
```

## Verificatie na deploy
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose ps && docker compose logs backend --tail 5"
```

## Veiligheidsregels
- **Autonoom:** git pull, logs, disk check, ps, deploy (na groene tests)
- **ALTIJD bevestiging vragen:** volumes verwijderen, database wissen, rm -rf, rollback migraties
- Na deploy altijd vermelden: welke service(s), of er migraties gedraaid zijn

## Valkuilen
- **Alembic: `run` niet `exec`** als backend crashed
- **POSTGRES_PASSWORD:** werkt alleen bij eerste volume-init. Later wijzigen via `ALTER USER`
- **Na ELKE commit ALTIJD `git push origin main`** — anders bereikt het de VPS niet
