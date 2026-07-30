#!/usr/bin/env python3
"""PreToolUse-wachter op Bash: zet twee tekstregels om in echte sloten.

1. `git add -A` / `git add .` wordt geblokkeerd (S203: veegde bank-CSV de historie in).
2. `git push` draait eerst ruff over backend/app — alleen als er Python is gewijzigd
   t.o.v. origin/main. Rood = push geblokkeerd.

Exit 2 = tool-aanroep blokkeren, stderr gaat naar Claude.
"""

import json
import re
import subprocess
import sys

REPO = "C:/Users/arsal/Documents/luxis"

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # geen leesbare invoer → nooit blokkeren

command = (payload.get("tool_input") or {}).get("command") or ""

# ---- Slot 1: git add -A / git add . -------------------------------------
# Woordgrens zodat `git add -Applesauce` of een pad als `./app` niet meetelt.
if re.search(r"\bgit\s+add\s+(-A\b|--all\b|\.(?:\s|$))", command):
    print(
        "GEBLOKKEERD: `git add -A` / `git add .` mag niet in deze repo.\n"
        "De repo bevat bewust-untracked bestanden (bank-CSV, AV-PDF's, tmp-SQL).\n"
        "In S203 belandde het bankafschrift zo in de historie (history-rewrite nodig).\n"
        "Stage expliciete paden: git add backend/app/x.py frontend/src/y.tsx",
        file=sys.stderr,
    )
    sys.exit(2)

# ---- Slot 2: lint vóór push --------------------------------------------
if re.search(r"\bgit\s+push\b", command):
    try:
        changed = subprocess.run(
            ["git", "-C", REPO, "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True, text=True, timeout=20,
        ).stdout
    except Exception:
        sys.exit(0)  # geen git-info → doorlaten, nooit de push gijzelen

    py_touched = [
        f for f in changed.splitlines()
        if f.startswith("backend/app/") and f.endswith(".py")
    ]
    if not py_touched:
        sys.exit(0)

    try:
        ruff = subprocess.run(
            ["uvx", "ruff", "check", "backend/app/"],
            cwd=REPO, capture_output=True, text=True, timeout=120,
        )
    except Exception:
        sys.exit(0)  # uvx ontbreekt of hangt → push niet blokkeren

    if ruff.returncode != 0:
        print(
            "GEBLOKKEERD: ruff is rood — CI zou hierop falen.\n"
            f"{ruff.stdout.strip()[:2000]}\n"
            "Fix eerst, of draai `uvx ruff check --fix backend/app/`.",
            file=sys.stderr,
        )
        sys.exit(2)

sys.exit(0)
