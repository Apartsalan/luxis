#!/bin/bash
# Daily backup script for Luxis
# Backs up: PostgreSQL database + uploads directory
#
# Off-site opslag (S207, review): documenten gaan NIET meer elke nacht als een
# volledige verse kopie de deur uit — dat liep bij 90 dagen bewaartijd binnen
# enkele dagen tegen de gratis Backblaze-opslaggrens aan (elke nacht +-1,2 GB,
# 90 dagen = 100+ GB). Nu: één actuele spiegel (rclone sync) + alleen wat
# écht wijzigt/verdwijnt gaat apart de geschiedenis-map in (--backup-dir).
# De database blijft klein genoeg (~tientallen MB) om gewoon elke nacht een
# losse dump te bewaren.
#
# --fast-list (S213): de documenten staan in een diepe mappenboom
# (email_attachments/tenant/mail/bijlage/bestand). Zonder --fast-list doet
# rclone op Backblaze B2 één zoekopdracht (list) PER map → duizenden Class C-
# transacties per nacht, ver boven de gratis dagcap van 2.500. Met --fast-list
# wordt de hele boom in één doorlopende, gepagineerde lijst opgehaald (~tientallen
# calls i.p.v. duizenden). Verplicht op elke list-zware rclone-stap hieronder.
#
# Rotation: lokaal 7 dagen. Off-site: 90 dagen (db-dumps + upload-geschiedenis).
#
# Crontab (use bash explicitly to avoid permission issues after git pull):
#   0 3 * * * /bin/bash /opt/luxis/scripts/backup.sh >> /var/log/luxis-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/luxis}"
# Default = de Europese versleutelde bucket (Amsterdam). De cron zet deze env-vars
# expliciet; de oude Amerikaanse bucket/remote (`luxis-backup`) is per juli 2026
# verwijderd — nooit meer als default naar de VS wijzen.
RCLONE_REMOTE="${RCLONE_REMOTE:-luxis-backup-eu-crypt}"
RCLONE_BUCKET="${RCLONE_BUCKET:-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
OFFSITE_RETENTION_DAYS="${OFFSITE_RETENTION_DAYS:-90}"
DATE=$(date +%Y-%m-%d_%H%M)
CONTAINER_DB="luxis-db"
CONTAINER_BACKEND="luxis-backend"

DB_FILENAME="luxis_db_${DATE}.sql.gz"
UPLOADS_FILENAME="luxis_uploads_${DATE}.tar.gz"
UPLOADS_STAGE="$BACKUP_DIR/uploads-current"

mkdir -p "$BACKUP_DIR" "$UPLOADS_STAGE"

echo "=========================================="
echo "[$(date)] Starting Luxis backup..."

# 1. Database dump
echo "[$(date)] Dumping PostgreSQL..."
docker exec "$CONTAINER_DB" pg_dump -U "${POSTGRES_USER:-luxis}" "${POSTGRES_DB:-luxis}" | gzip > "$BACKUP_DIR/$DB_FILENAME"
DB_SIZE=$(du -h "$BACKUP_DIR/$DB_FILENAME" | cut -f1)
echo "[$(date)] Database backup: $DB_FILENAME ($DB_SIZE)"

# 2. Uploads directory — lokale volledige archiefkopie blijft bestaan (snel
# lokaal herstel, 7-daagse rotatie op de VPS-schijf; die is niet het knelpunt).
echo "[$(date)] Backing up uploads (local archive)..."
docker cp "$CONTAINER_BACKEND":/app/uploads - 2>/dev/null | gzip > "$BACKUP_DIR/$UPLOADS_FILENAME"
UPLOADS_SIZE=$(du -h "$BACKUP_DIR/$UPLOADS_FILENAME" | cut -f1)
echo "[$(date)] Uploads backup: $UPLOADS_FILENAME ($UPLOADS_SIZE)"

# 3. Upload to off-site storage (if rclone is configured)
if command -v rclone &> /dev/null && rclone listremotes 2>/dev/null | grep -q "^${RCLONE_REMOTE}:"; then
    # Database: klein genoeg om gewoon elke nacht een losse dump te bewaren.
    rclone copy "$BACKUP_DIR/$DB_FILENAME" "${RCLONE_REMOTE}:${RCLONE_BUCKET}/db/" --log-level INFO
    rclone delete "${RCLONE_REMOTE}:${RCLONE_BUCKET}/db/" --min-age "${OFFSITE_RETENTION_DAYS}d" --fast-list --log-level INFO 2>/dev/null || true

    # Documenten: spiegel + delta-geschiedenis i.p.v. elke nacht een volledige
    # verse kopie. rclone sync werkt bestand-voor-bestand: ongewijzigde
    # documenten worden niet opnieuw geüpload. Wat verandert of verdwijnt gaat
    # niet verloren maar naar een gedateerde geschiedenis-map (--backup-dir) —
    # dus zowel "huidige staat" als "wat er ooit was" blijven behouden, zonder
    # elke nacht de volledige verzameling opnieuw op te tellen.
    echo "[$(date)] Syncing uploads mirror off-site..."
    rm -rf "${UPLOADS_STAGE:?}"/*
    docker cp "$CONTAINER_BACKEND":/app/uploads/. "$UPLOADS_STAGE"/ 2>/dev/null || true
    rclone sync "$UPLOADS_STAGE" "${RCLONE_REMOTE}:${RCLONE_BUCKET}/uploads-current" \
        --backup-dir "${RCLONE_REMOTE}:${RCLONE_BUCKET}/uploads-history/${DATE}" \
        --fast-list \
        --log-level INFO
    rclone delete "${RCLONE_REMOTE}:${RCLONE_BUCKET}/uploads-history/" --min-age "${OFFSITE_RETENTION_DAYS}d" --fast-list --log-level INFO 2>/dev/null || true

    # Opruiming van vóór S207: losse gedateerde bestanden die ooit rechtstreeks
    # in de bucket-root zijn geland, laten we op hun eigen 90-dagen-klok
    # uitsterven (geen handmatige verwijdering hier).
    rclone delete "${RCLONE_REMOTE}:${RCLONE_BUCKET}/" --min-age "${OFFSITE_RETENTION_DAYS}d" --fast-list --log-level INFO 2>/dev/null || true

    echo "[$(date)] Off-site upload complete"
else
    echo "[$(date)] WARNING: rclone not configured — local-only backup"
fi

# 4. Rotate old local backups
find "$BACKUP_DIR" -maxdepth 1 -name "luxis_*.gz" -mtime "+${RETENTION_DAYS}" -delete
BACKUP_COUNT=$(find "$BACKUP_DIR" -maxdepth 1 -name "luxis_*.gz" | wc -l)
echo "[$(date)] Local backups retained: $BACKUP_COUNT files (${RETENTION_DAYS}-day rotation)"

echo "[$(date)] Backup completed successfully"
echo "=========================================="
