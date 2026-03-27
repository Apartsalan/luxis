# Luxis Operations Runbook

**VPS:** 46.225.115.216 (Hetzner, Ubuntu 24.04)
**SSH:** `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216`
**Domain:** luxis.kestinglegal.nl
**Stack:** Docker Compose (backend, frontend, db, redis, celery, caddy)

---

## Dagelijkse checks

```bash
# Container status
docker compose ps

# Disk usage
df -h /

# Backup status (laatste backup)
ls -lah /backups/luxis/ | tail -3

# fail2ban geblokkeerde IPs
fail2ban-client status sshd
```

---

## Deploy

Automatisch via GitHub Actions (self-hosted runner op VPS). Na push naar main:
1. CI draait (lint, tests, typecheck, build)
2. Bij succes: auto-deploy

### Handmatig deployen

```bash
cd /opt/luxis
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache backend frontend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Alleen backend deployen

```bash
cd /opt/luxis && git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend
```

---

## Backup & Restore

### Backup (automatisch, dagelijks 03:00)

```bash
crontab -l  # Toont backup schedule
cat /var/log/luxis-backup.log  # Backup log
ls -lah /backups/luxis/  # Lokale backups (7 dagen)
```

Off-site: Backblaze B2 bucket `Luxis-backup` (90 dagen retentie).

```bash
rclone ls luxis-backup:Luxis-backup/  # Lijst off-site backups
```

### Restore database

```bash
# Stop backend
docker compose stop backend celery-worker celery-beat

# Restore meest recente backup
LATEST=$(ls -t /backups/luxis/luxis_db_*.sql.gz | head -1)
gunzip -c "$LATEST" | docker exec -i luxis-db psql -U luxis luxis

# Start backend
docker compose up -d backend celery-worker celery-beat
```

### Restore uploads

```bash
LATEST=$(ls -t /backups/luxis/luxis_uploads_*.tar.gz | head -1)
docker cp "$LATEST" luxis-backend:/tmp/uploads.tar.gz
docker exec luxis-backend bash -c "cd /app && tar xzf /tmp/uploads.tar.gz"
```

---

## Disaster Recovery

### VPS volledig kwijt

1. Nieuwe Hetzner VPS aanmaken (Ubuntu 24.04, 4GB RAM)
2. SSH key instellen
3. Docker + Docker Compose installeren
4. `git clone` de repo naar `/opt/luxis`
5. `.env` file aanmaken met productie credentials
6. Restore database van B2:
   ```bash
   rclone copy luxis-backup:Luxis-backup/ /backups/luxis/ --include "luxis_db_*"
   LATEST=$(ls -t /backups/luxis/luxis_db_*.sql.gz | head -1)
   docker compose up -d db
   sleep 10
   gunzip -c "$LATEST" | docker exec -i luxis-db psql -U luxis luxis
   ```
7. Restore uploads van B2
8. `docker compose up -d`
9. DNS bijwerken naar nieuw IP
10. Caddy haalt automatisch nieuw SSL certificaat op

**RTO:** ~30 minuten (mits B2 backup beschikbaar)
**RPO:** maximaal 24 uur (dagelijkse backup)

---

## Database

### Migraties draaien

```bash
docker compose exec backend python -m alembic upgrade head
```

### Database console

```bash
docker compose exec db psql -U luxis luxis
```

### Wachtwoord resetten (als login niet werkt)

```bash
docker compose exec backend python -c "
from app.auth.service import hash_password
print(hash_password('NieuwWachtwoord123'))
"
# Kopieer de hash, dan:
docker compose exec db psql -U luxis luxis -c \
  "UPDATE users SET hashed_password='<hash>' WHERE email='seidony@kestinglegal.nl';"
```

---

## Logs bekijken

```bash
# Alle containers
docker compose logs --tail 50

# Specifieke container
docker compose logs backend --tail 100 -f
docker compose logs frontend --tail 50

# Caddy access log
docker compose logs caddy --tail 50

# Backup log
tail -50 /var/log/luxis-backup.log

# fail2ban
journalctl -u fail2ban --since "1 hour ago"

# GitHub Actions runner
journalctl -u actions.runner.Apartsalan-luxis.luxis-vps.service --since "1 hour ago"
```

---

## Veelvoorkomende problemen

### Backend start niet

```bash
docker compose logs backend --tail 30
# Vaak: missing env var, database niet bereikbaar, migratie nodig
```

### "502 Bad Gateway" in browser

Caddy kan backend/frontend niet bereiken:
```bash
docker compose ps  # Check of containers draaien
docker compose restart backend frontend
```

### Database vol

```bash
docker compose exec db psql -U luxis -c "SELECT pg_size_pretty(pg_database_size('luxis'));"
```

### Disk vol

```bash
df -h /
docker system prune -f  # Verwijder ongebruikte Docker images/containers
```

### SSL certificaat problemen

Caddy regelt dit automatisch. Als het niet werkt:
```bash
docker compose restart caddy
docker compose logs caddy --tail 30
```

---

## Contactgegevens

- **VPS Provider:** Hetzner (hetzner.com)
- **Domain:** TransIP (transip.nl) — luxis.kestinglegal.nl
- **Off-site Backup:** Backblaze B2 (backblaze.com) — bucket `Luxis-backup`
- **CI/CD:** GitHub Actions — github.com/Apartsalan/luxis
- **Monitoring:** geen (TODO)
