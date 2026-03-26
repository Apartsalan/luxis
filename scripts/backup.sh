#!/bin/bash
# Daily backup script for Luxis
# Backs up: PostgreSQL database + uploads directory
# Rotation: 7 days local, 90 days off-site (if rclone configured)
#
# Crontab (use bash explicitly to avoid permission issues after git pull):
#   0 3 * * * /bin/bash /opt/luxis/scripts/backup.sh >> /var/log/luxis-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/luxis}"
RCLONE_REMOTE="${RCLONE_REMOTE:-luxis-backup}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y-%m-%d_%H%M)
CONTAINER_DB="luxis-db"
CONTAINER_BACKEND="luxis-backend"

DB_FILENAME="luxis_db_${DATE}.sql.gz"
UPLOADS_FILENAME="luxis_uploads_${DATE}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "[$(date)] Starting Luxis backup..."

# 1. Database dump
echo "[$(date)] Dumping PostgreSQL..."
docker exec "$CONTAINER_DB" pg_dump -U "${POSTGRES_USER:-luxis}" "${POSTGRES_DB:-luxis}" | gzip > "$BACKUP_DIR/$DB_FILENAME"
DB_SIZE=$(du -h "$BACKUP_DIR/$DB_FILENAME" | cut -f1)
echo "[$(date)] Database backup: $DB_FILENAME ($DB_SIZE)"

# 2. Uploads directory (from backend container volume)
echo "[$(date)] Backing up uploads..."
docker cp "$CONTAINER_BACKEND":/app/uploads - 2>/dev/null | gzip > "$BACKUP_DIR/$UPLOADS_FILENAME"
UPLOADS_SIZE=$(du -h "$BACKUP_DIR/$UPLOADS_FILENAME" | cut -f1)
echo "[$(date)] Uploads backup: $UPLOADS_FILENAME ($UPLOADS_SIZE)"

# 3. Upload to off-site storage (if rclone is configured)
if command -v rclone &> /dev/null && rclone listremotes 2>/dev/null | grep -q "^${RCLONE_REMOTE}:"; then
    rclone copy "$BACKUP_DIR/$DB_FILENAME" "${RCLONE_REMOTE}:luxis-backups/" --log-level INFO
    rclone copy "$BACKUP_DIR/$UPLOADS_FILENAME" "${RCLONE_REMOTE}:luxis-backups/" --log-level INFO
    echo "[$(date)] Off-site upload complete"
    rclone delete "${RCLONE_REMOTE}:luxis-backups/" --min-age 90d --log-level INFO 2>/dev/null || true
else
    echo "[$(date)] WARNING: rclone not configured — local-only backup"
fi

# 4. Rotate old local backups
find "$BACKUP_DIR" -name "luxis_*.gz" -mtime "+${RETENTION_DAYS}" -delete
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "luxis_*.gz" | wc -l)
echo "[$(date)] Local backups retained: $BACKUP_COUNT files (${RETENTION_DAYS}-day rotation)"

echo "[$(date)] Backup completed successfully"
echo "=========================================="
