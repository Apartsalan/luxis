#!/bin/bash
# Daily database backup script for Luxis
# Runs locally + uploads to off-site storage via rclone
#
# Setup:
#   1. Install rclone: curl https://rclone.org/install.sh | sudo bash
#   2. Configure remote: rclone config (create "luxis-backup" remote)
#      - Backblaze B2, S3, or any rclone-supported provider
#   3. Set RCLONE_REMOTE below to your configured remote name
#   4. Add to crontab: 0 3 * * * /opt/luxis/scripts/backup.sh >> /var/log/luxis-backup.log 2>&1
#
# Environment variables (optional):
#   BACKUP_DIR      — local backup directory (default: /backups/luxis)
#   RCLONE_REMOTE   — rclone remote name (default: luxis-backup)
#   RETENTION_DAYS  — local retention in days (default: 30)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/luxis}"
RCLONE_REMOTE="${RCLONE_REMOTE:-luxis-backup}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y-%m-%d_%H%M)
CONTAINER="luxis-db"
FILENAME="luxis_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Dump database
docker exec "$CONTAINER" pg_dump -U "${POSTGRES_USER:-luxis}" "${POSTGRES_DB:-luxis}" | gzip > "$BACKUP_DIR/$FILENAME"

FILESIZE=$(du -h "$BACKUP_DIR/$FILENAME" | cut -f1)
echo "[$(date)] Local backup created: $FILENAME ($FILESIZE)"

# Upload to off-site storage (if rclone is configured)
if command -v rclone &> /dev/null && rclone listremotes 2>/dev/null | grep -q "^${RCLONE_REMOTE}:"; then
    rclone copy "$BACKUP_DIR/$FILENAME" "${RCLONE_REMOTE}:luxis-backups/" --log-level INFO
    echo "[$(date)] Off-site upload complete: ${RCLONE_REMOTE}:luxis-backups/$FILENAME"

    # Clean up old off-site backups (keep 90 days remotely)
    rclone delete "${RCLONE_REMOTE}:luxis-backups/" --min-age 90d --log-level INFO 2>/dev/null || true
else
    echo "[$(date)] WARNING: rclone not configured — skipping off-site upload"
    echo "  Run 'rclone config' to set up remote '${RCLONE_REMOTE}'"
fi

# Clean up old local backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

echo "[$(date)] Backup completed successfully"
