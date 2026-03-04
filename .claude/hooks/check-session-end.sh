#!/bin/bash
# Session-end check hook — verifies SESSION-NOTES.md and LUXIS-ROADMAP.md were updated
# Called by Claude Code Stop hook via settings.json

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "C:/Users/arsal/Documents/luxis")"

# Check if SESSION-NOTES.md was modified (staged or unstaged)
NOTES_MODIFIED=$(git -C "$REPO_ROOT" diff --name-only HEAD 2>/dev/null | grep -c "SESSION-NOTES.md")
NOTES_STAGED=$(git -C "$REPO_ROOT" diff --cached --name-only 2>/dev/null | grep -c "SESSION-NOTES.md")

# Check if LUXIS-ROADMAP.md was modified
ROADMAP_MODIFIED=$(git -C "$REPO_ROOT" diff --name-only HEAD 2>/dev/null | grep -c "LUXIS-ROADMAP.md")
ROADMAP_STAGED=$(git -C "$REPO_ROOT" diff --cached --name-only 2>/dev/null | grep -c "LUXIS-ROADMAP.md")

# Check for uncommitted changes
UNCOMMITTED=$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

# Check for unpushed commits
UNPUSHED=$(git -C "$REPO_ROOT" log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "=== SESSION END CHECK ==="

if [ "$NOTES_MODIFIED" -gt 0 ] || [ "$NOTES_STAGED" -gt 0 ]; then
  echo "[OK] SESSION-NOTES.md was updated"
else
  echo "[WARNING] SESSION-NOTES.md was NOT updated this session!"
fi

if [ "$ROADMAP_MODIFIED" -gt 0 ] || [ "$ROADMAP_STAGED" -gt 0 ]; then
  echo "[OK] LUXIS-ROADMAP.md was updated"
else
  echo "[WARNING] LUXIS-ROADMAP.md was NOT updated this session!"
fi

if [ "$UNCOMMITTED" -gt 0 ]; then
  echo "[WARNING] $UNCOMMITTED uncommitted file(s) — run /commit"
else
  echo "[OK] No uncommitted changes"
fi

if [ "$UNPUSHED" -gt 0 ]; then
  echo "[WARNING] $UNPUSHED unpushed commit(s) — run git push origin main"
else
  echo "[OK] All commits pushed"
fi

echo "========================="
