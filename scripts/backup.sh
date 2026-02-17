#!/bin/bash
# Daily database backup script for Luxis
# Add to crontab: 0 3 * * * /path/to/luxis/scripts/backup.sh

BACKUP_DIR="/backups/luxis"
DATE=$(date +%Y-%m-%d_%H%M)
CONTAINER="luxis-db"

mkdir -p "$BACKUP_DIR"

# Dump database
docker exec "$CONTAINER" pg_dump -U luxis luxis | gzip > "$BACKUP_DIR/luxis_$DATE.sql.gz"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: luxis_$DATE.sql.gz"
