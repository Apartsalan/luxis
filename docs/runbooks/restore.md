# Runbook — Backup & Restore (Luxis productie)

*Laatst geverifieerd: 7 juli 2026 (S182). Off-site is sinds die datum de
VERSLEUTELDE EU-remote `luxis-backup-eu-crypt:` (Backblaze eu-central-003,
Amsterdam). De restore-test in §4 is op 7 juli end-to-end via die remote
uitgevoerd: dump off-site opgehaald (automatisch ontsleuteld), teruggezet in een
wegwerp-DB, tellingen exact gelijk aan live (cases 607, contacts 1168,
payments 255), 0 fouten.*

VPS: `root@46.225.115.216` · SSH-key: `~/.ssh/luxis_deploy` · app in `/opt/luxis`.

> 🔐 **Versleuteling (S182):** off-site staat alles versleuteld (bestandsnamen én
> inhoud, rclone `crypt`). Ontsleutelen kan uitsluitend met de twee
> crypt-wachtwoorden. Die staan (obscured) in `/root/.config/rclone/rclone.conf`
> op de VPS én in Arsalans wachtwoordmanager. **Zonder die wachtwoorden zijn de
> off-site backups definitief onleesbaar** — bewaar ze los van de VPS.

---

## 1. Wat wordt geback-upt

`/opt/luxis/scripts/backup.sh` draait **dagelijks 03:00** (cron) en maakt:

| Bestand | Inhoud | Hoe |
|---|---|---|
| `/backups/luxis/luxis_db_<datum>.sql.gz` | volledige PostgreSQL-dump (schema + data) | `docker exec luxis-db pg_dump -U luxis luxis \| gzip` |
| `/backups/luxis/luxis_uploads_<datum>.tar.gz` | `/app/uploads` (dossierbestanden, ~39 MB) | `docker cp luxis-backend:/app/uploads - \| gzip` |

**Rotatie:** 7 dagen lokaal, 90 dagen off-site. **Off-site (sinds 7 juli 2026):**
rclone-remote `luxis-backup-eu-crypt:` (crypt-laag) → `luxis-b2-eu:luxis-backup-eu`
(**Backblaze B2, eu-central-003 Amsterdam**), pad `backups/`. De cron geeft
`RCLONE_REMOTE=luxis-backup-eu-crypt RCLONE_BUCKET=backups` mee. Log:
`/var/log/luxis-backup.log`. De oude US-remote `luxis-backup:` wordt na 2 dagen
bewezen EU-runs gewist en verwijderd.

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

Altijd via de **crypt-remote** — die ontsleutelt automatisch. (Direct via
`luxis-b2-eu:` zie je alleen versleutelde bestandsnamen; daar kun je niets mee.)

```bash
rclone ls   luxis-backup-eu-crypt:backups/ | sort | tail    # wat staat off-site?
rclone copy luxis-backup-eu-crypt:backups/luxis_db_<datum>.sql.gz      /backups/luxis/
rclone copy luxis-backup-eu-crypt:backups/luxis_uploads_<datum>.tar.gz /backups/luxis/
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

# (zo nodig backup off-site ophalen — EERST de rclone-remotes herstellen, zie §5.7)
rclone copy luxis-backup-eu-crypt:backups/luxis_db_<datum>.sql.gz /backups/luxis/

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
rclone copy luxis-backup-eu-crypt:backups/luxis_uploads_<datum>.tar.gz /backups/luxis/   # zo nodig
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

### 5.7 Na herstel (of vóór §5.3 als je off-site moet ophalen)
- **rclone-remotes opnieuw aanmaken** (nodig vóór elk off-site ophalen op een
  verse server). Benodigd: Backblaze keyID + applicationKey (Backblaze-console →
  Application Keys; nieuwe key aanmaken mag) én de twee crypt-wachtwoorden uit
  Arsalans wachtwoordmanager (NIET vervangbaar!):
  ```bash
  rclone config create luxis-b2-eu b2 account <keyID> key <applicationKey> hard_delete true
  rclone config create luxis-backup-eu-crypt crypt \
    remote 'luxis-b2-eu:luxis-backup-eu' \
    password '<crypt-wachtwoord-1>' password2 '<crypt-wachtwoord-2>' --obscure
  rclone ls luxis-backup-eu-crypt:backups/ | tail   # leesbare namen = goed
  ```
- Outlook-mailkoppeling opnieuw verbinden (Instellingen → e-mail) als
  `TOKEN_ENCRYPTION_KEY`/`SECRET_KEY` veranderd zijn.
- `ufw` opnieuw zetten (22/80/443), fail2ban, backup-cron (`crontab -e` — de
  regel geeft `RCLONE_REMOTE=luxis-backup-eu-crypt RCLONE_BUCKET=backups` mee).

---

## 6. Aandachtspunten / open

- **AVG — off-site locatie: ✅ opgelost 7 juli 2026 (S182).** Off-site staat
  versleuteld in Backblaze **eu-central-003 (Amsterdam)**. De oude US-bucket
  wordt na 2 dagen bewezen EU-runs volledig gewist (wisbewijs in SESSION-NOTES).
- **`.env` zit niet in de backups.** Bewaar `.env` + `.env.bak-s158` apart in een
  kluis — zonder deze is een totaalherstel onvolledig.
- **Crypt-wachtwoorden zijn onvervangbaar.** Kwijt = alle off-site backups
  definitief onleesbaar. Locaties: `/root/.config/rclone/rclone.conf` (VPS) +
  Arsalans wachtwoordmanager.
- Backup-retentie: 7d lokaal / 90d off-site. Voor een herstel ouder dan 90 dagen
  is geen backup beschikbaar.
