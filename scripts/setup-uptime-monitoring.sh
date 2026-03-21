#!/bin/bash
# Uptime monitoring setup for Luxis
#
# Option 1: UptimeRobot (recommended — free tier: 50 monitors, 5-min interval)
#   1. Sign up at https://uptimerobot.com
#   2. Add monitors:
#      - HTTPS monitor: https://luxis.kestinglegal.nl (keyword: "luxis")
#      - HTTPS monitor: https://luxis.kestinglegal.nl/health (keyword: "ok")
#   3. Configure alert contacts (email, Telegram, Slack, etc.)
#   4. Set check interval to 5 minutes
#
# Option 2: Self-hosted healthcheck (runs on VPS as fallback)
#   Add to crontab: */5 * * * * /opt/luxis/scripts/setup-uptime-monitoring.sh --check
#
# This script can also be used as a self-hosted health checker:

set -euo pipefail

DOMAIN="https://luxis.kestinglegal.nl"
HEALTH_ENDPOINT="${DOMAIN}/health"
ALERT_EMAIL="${ALERT_EMAIL:-seidony@kestinglegal.nl}"
LOGFILE="/var/log/luxis-uptime.log"

if [[ "${1:-}" == "--check" ]]; then
    # Self-hosted health check mode
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" != "200" ]]; then
        MSG="[$(date)] ALERT: luxis.kestinglegal.nl is DOWN (HTTP $HTTP_CODE)"
        echo "$MSG" >> "$LOGFILE"

        # Send alert email (requires mailutils/sendmail)
        if command -v mail &> /dev/null; then
            echo "$MSG" | mail -s "LUXIS DOWN — HTTP $HTTP_CODE" "$ALERT_EMAIL"
        fi

        # Try to auto-recover by restarting containers
        cd /opt/luxis
        docker compose -f docker-compose.yml -f docker-compose.prod.yml restart backend frontend caddy
        echo "[$(date)] Auto-restart triggered" >> "$LOGFILE"
    else
        # Log healthy status every hour (not every 5 min to avoid log spam)
        MINUTE=$(date +%M)
        if [[ "$MINUTE" == "00" ]]; then
            echo "[$(date)] OK — HTTP $HTTP_CODE" >> "$LOGFILE"
        fi
    fi
    exit 0
fi

echo "Uptime monitoring for Luxis"
echo "==========================="
echo ""
echo "Recommended: UptimeRobot (free)"
echo "  1. Go to https://uptimerobot.com and create account"
echo "  2. Add monitor: $DOMAIN"
echo "  3. Add monitor: $HEALTH_ENDPOINT"
echo "  4. Set alerts to: $ALERT_EMAIL"
echo ""
echo "Self-hosted fallback:"
echo "  Add to crontab:"
echo "  */5 * * * * /opt/luxis/scripts/setup-uptime-monitoring.sh --check"
