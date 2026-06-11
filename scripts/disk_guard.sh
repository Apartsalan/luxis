#!/bin/bash
# disk_guard.sh — Luxis VPS disk pressure monitor + safe auto-cleanup
#
# Runs hourly via cron. Checks / usage and takes progressively more action
# as pressure builds. Designed to be SAFE: never touches tagged images,
# never touches volumes, never touches the database.
#
# Thresholds:
#   > 85%  WARNING — safe prune: dangling images + build cache > 72h
#   > 95%  CRITICAL — emergency: all build cache + dangling only
#          (still refuses to delete tagged images — rollback stays possible)
#
# Install:
#   chmod +x /opt/luxis/scripts/disk_guard.sh
#   (crontab -l 2>/dev/null; echo '0 * * * * /opt/luxis/scripts/disk_guard.sh') | crontab -
#
# Tail the log:
#   tail -f /var/log/luxis-disk.log

LOG=/var/log/luxis-disk.log
USED=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] disk used: ${USED}%" >> "$LOG"

if [ "$USED" -gt 95 ]; then
    echo "[$TS] CRITICAL — emergency cleanup" >> "$LOG"
    docker builder prune -a -f >> "$LOG" 2>&1
    docker image prune -f >> "$LOG" 2>&1
    NEW=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    echo "[$TS] post-cleanup: ${NEW}%" >> "$LOG"
    if [ "$NEW" -gt 90 ]; then
        echo "[$TS] ALERT: still at ${NEW}% after cleanup — human intervention needed" >> "$LOG"
    fi
elif [ "$USED" -gt 85 ]; then
    echo "[$TS] WARNING — safe prune" >> "$LOG"
    docker image prune -f >> "$LOG" 2>&1
    docker builder prune -f --filter "until=72h" >> "$LOG" 2>&1
    NEW=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    echo "[$TS] post-cleanup: ${NEW}%" >> "$LOG"
fi

exit 0
