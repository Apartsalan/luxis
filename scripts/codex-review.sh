#!/bin/sh
# codex-review.sh — Codex read-only review met HARTSLAG-BEWAKER (geen tijdslimiet).
#
# Waarom: Codex mag op 'ultra' zo lang nadenken als nodig. Een botte wall-clock
# timeout kapt echt-nadenken af (zie S194/S196). In plaats daarvan bewaken we de
# HARTSLAG: zolang Codex zijn --json-uitvoer laat groeien, denkt hij. Valt die
# groei IDLE_LIMIT seconden stil, dan (en alleen dan) is hij vastgelopen -> stop.
# Codex heeft zelf al een 5-min stream-retry (openai/codex#23807); IDLE_LIMIT=360
# ligt daar bewust ruim boven zodat een normale retry niet als hang telt.
#
# Gebruik: scripts/codex-review.sh <prompt-file> <output-file> [effort] [idle_sec]
# Draai 'm op de ACHTERGROND (Bash run_in_background) — geen ceiling nodig.
# Exit 0 = Codex normaal klaar. Exit 42 = als vastgelopen gestopt.
set -u

PROMPT_FILE="$1"
OUT="$2"
EFFORT="${3:-ultra}"
IDLE_LIMIT="${4:-360}"

: > "$OUT"

# ponytail: read-only sandbox is de hele veiligheid hier — Codex schrijft nooit.
codex exec -s read-only -c model_reasoning_effort="$EFFORT" --json \
    "$(cat "$PROMPT_FILE")" < /dev/null >> "$OUT" 2>&1 &
PID=$!

while kill -0 "$PID" 2>/dev/null; do
    sleep 20
    now=$(date +%s)
    mtime=$(stat -c %Y "$OUT" 2>/dev/null || echo "$now")
    idle=$(( now - mtime ))
    if [ "$idle" -ge "$IDLE_LIMIT" ]; then
        # ponytail: best-effort kill; hoofddoel is MELDEN, niet perfect opruimen.
        kill "$PID" 2>/dev/null
        sleep 2
        kill -9 "$PID" 2>/dev/null
        printf '\n[WATCHDOG] geen uitvoer voor %ss — als vastgelopen beschouwd en gestopt.\n' "$idle" >> "$OUT"
        exit 42
    fi
done

wait "$PID"
printf '\n[WATCHDOG] Codex normaal afgerond.\n' >> "$OUT"
exit 0
