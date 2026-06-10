# Runbook — Backup & Restore (Luxis productie)

*Laatst geverifieerd: 10 juni 2026 (sessie 159). De restore-test in §4 is op die
datum end-to-end uitgevoerd op de productie-VPS: dump van 10 juni teruggezet in
een wegwerp-DB, record-tellingen exact gelijk aan live (cases 48, contacts 44,
invoices 21, trust_transactions 9), 0 fouten.*

VPS: `root@46.225.115.216` · SSH-key: `~/.ssh/luxis_deploy` · app in `/opt/luxis`.

---

## 1. Wat wordt geback-upt

`/opt/luxis/scripts/backup.sh` draait **dagelijks 03:00** (cron) en maakt:

| Bestand | Inhoud | Hoe |
|---|---|---|
| `/backups/luxis/luxis_db_<datum>.sql.gz` | volledige PostgreSQL-dump (schema + data) | `docker exec luxis-db pg_dump -U luxis luxis \| gzip` |
| `/backups/luxis/luxis_uploads_<datum>.tar.gz` | `/app/uploads` (dossierbestanden, ~39 MB) | `docker cp luxis-backend:/app/uploads - \| gzip` |

**Rotatie:** 7 dagen lokaal, 90 dagen off-site. **Off-site:** rclone-remote
`luxis-backup:` → bucket `Luxis-backup` (provider **Backblaze B2**). Log:
`/var/log/luxis-backup.log`.

> ⚠️ De DB zélf is het wettelijke archief (7 jaar, art. 2:10 BW) — backups
> roteren, dus schoon de productie-DB nooit op. Zie readiness-audit §3.

---

## 2. Snelle sanity-check (mag elk moment)

```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216
ls -lh /backups/luxis/ | tail            # nieuwste db + uploads aanwezig?
gunzip -c /backups/luxis/luxis_db_$(date +%F)_0300.sql.gz | head -15   # geldige pg_dump?
tail -20 /var/log/luxis-backup.log        # laatste run "completed successfully"?
```

---

## 3. Off-site terughalen (lokale backups weg, VPS nog bereikbaar)

```bash
rclone ls   luxis-backup:Luxis-backup/ | sort | tail        # wat staat off-site?
rclone copy luxis-backup:Luxis-backup/luxis_db_<datum>.sql.gz      /backups/luxis/
rclone copy luxis-backup:Luxis-backup/luxis_uploads_<datum>.tar.gz /backups/luxis/
```

---

## 4. Restore-test (vangnet bewijzen — geen impact op productie)

Draai dit periodiek (≥ 1×/kwartaal) om te bewijzen dat een backup écht
herstelbaar is. Het raakt de live-DB niet: alles gebeurt in een wegwerp-DB.

```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216
DB=$(ls -t /backups/luxis/luxis_db_*.sql.gz | head -1)

docker exec luxis-db dropdb -U luxis --if-exists luxis_restore_test
docker exec luxis-db createdb -U luxis luxis_restore_test
gunzip -c "$DB" | docker exec -i luxis-db psql -U luxis -d luxis_restore_test -q

# Tellingen moeten kloppen vs live:
for t in cases contacts invoices trust_transactions; do
  printf "%s: test=" "$t"
  docker exec luxis-db psql -U luxis -d luxis_restore_test -tAc "SELECT count(*) FROM $t" | tr -d '\n'
  printf "  live="
  docker exec luxis-db psql -U luxis -d luxis             -tAc "SELECT count(*) FROM $t"
done

docker exec luxis-db dropdb -U luxis luxis_restore_test   # opruimen — ALTIJD
```

Uploads-tarball leesbaarheid:
```bash
tar -tzf $(ls -t /backups/luxis/luxis_uploads_*.tar.gz | head -1) | head
```

---

## 5. TOTAALVERLIES — herstel op een nieuwe VPS

Uitgangspunt: VPS is weg, je hebt een verse Ubuntu-server + de backups (off-site
via rclone, of een lokale kopie). Voer in volgorde uit.

### 5.1 Server klaarmaken
```bash
# Docker + compose-plugin installeren (Ubuntu)
apt-get update && apt-get install -y docker.io docker-compose-plugin git rclone
systemctl enable --now docker
```

### 5.2 Code + config terugzetten
```bash
git clone https://github.com/Apartsalan/luxis.git /opt/luxis
cd /opt/luxis
```
Zet **`/opt/luxis/.env`** terug. Dit bestand staat NIET in git. Referentie van de
laatst bekende variabelen-set: **`.env.bak-s158`** (in `/opt/luxis`, mee te nemen
in je eigen veilige opslag — staat niet in de backup-tarballs!). Vereiste keys
(zie `docker-compose.prod.yml`): `POSTGRES_USER/PASSWORD/DB`, `DATABASE_URL`,
`REDIS_URL`, `REDIS_PASSWORD`, `SECRET_KEY`, `TOKEN_ENCRYPTION_KEY`, `CORS_ORIGINS`,
`SMTP_*`, `MICROSOFT_*`, `ANTHROPIC_API_KEY`, `SENTRY_DSN`.

> Bewaar `.env` + `.env.bak-s158` los van de VPS (password manager / kluis).
> Zonder de oorspronkelijke `SECRET_KEY`/`TOKEN_ENCRYPTION_KEY` zijn bestaande
> OAuth-mailtokens onleesbaar → Outlook éénmalig opnieuw koppelen.

### 5.3 Database EERST terugzetten, dan pas de backend starten
De dump bevat het volledige schema. Start daarom NIET eerst de backend (die zou
via `alembic upgrade` een leeg schema aanmaken en botsen met de restore).

```bash
# Alleen db (+ redis) starten:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d db redis
sleep 10

# (zo nodig backup off-site ophalen)
rclone copy luxis-backup:Luxis-backup/luxis_db_<datum>.sql.gz /backups/luxis/

# Dump in een verse, lege luxis-DB laden:
docker exec luxis-db dropdb   -U luxis --if-exists luxis
docker exec luxis-db createdb -U luxis luxis
gunzip -c /backups/luxis/luxis_db_<datum>.sql.gz | docker exec -i luxis-db psql -U luxis -d luxis -q
```

### 5.4 Uploads terugzetten in het volume
De tarball heeft `uploads/` als root, dus `docker cp` naar `/app` landt op
`/app/uploads`. De backend-container moet bestaan (al gebouwd) maar hoeft niet
gezond te zijn:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-start backend
rclone copy luxis-backup:Luxis-backup/luxis_uploads_<datum>.tar.gz /backups/luxis/   # zo nodig
gunzip -c /backups/luxis/luxis_uploads_<datum>.tar.gz | docker cp - luxis-backend:/app/
```

### 5.5 Alles starten + verifiëren
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head   # no-op als dump op head stond
docker exec luxis-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" && echo OK
```

### 5.6 DNS + TLS
- Zet de A-records van `luxis.kestinglegal.nl` (en eventuele alias) naar het
  nieuwe VPS-IP bij de domeinregistrar.
- Caddy regelt automatisch een nieuw Let's Encrypt-certificaat zodra DNS wijst.
- Controleer extern: `curl -sf https://luxis.kestinglegal.nl/health`.

### 5.7 Na herstel
- Outlook-mailkoppeling opnieuw verbinden (Instellingen → e-mail) als
  `TOKEN_ENCRYPTION_KEY`/`SECRET_KEY` veranderd zijn.
- `ufw` opnieuw zetten (22/80/443), fail2ban, backup-cron (`crontab -e`),
  rclone-config (`rclone config` → remote `luxis-backup` type b2).

---

## 6. Aandachtspunten / open

- **AVG — off-site locatie:** `luxis-backup:` is Backblaze B2. Controleer dat de
  bucket `Luxis-backup` in een **EU-regio** staat; zo niet, migreer of leg een
  verwerkersovereenkomst vast (readiness-audit §3).
- **`.env` zit niet in de backups.** Bewaar `.env` + `.env.bak-s158` apart in een
  kluis — zonder deze is een totaalherstel onvolledig.
- Backup-retentie: 7d lokaal / 90d off-site. Voor een herstel ouder dan 90 dagen
  is geen backup beschikbaar.
