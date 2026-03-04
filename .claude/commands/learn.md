Extract lessons learned from the current session and propose additions to project memory files.

## Steps

1. **Review recent git history**: Run `git log --oneline -20` to see what changed this session
2. **Identify patterns**: Look for:
   - Bugs you encountered and how they were fixed
   - Workarounds for unexpected behavior
   - New knowledge about the codebase, frameworks, or tools
   - Corrections from the user
   - Things that took longer than expected (why?)
3. **Categorize each lesson** into the right target file:
   - Backend bug/pattern → `backend/CLAUDE.md`
   - Frontend bug/pattern → `frontend/CLAUDE.md`
   - Playwright/E2E quirk → `frontend/CLAUDE.md` (E2E section)
   - Deploy/infra issue → `.claude/skills/deploy-regels/SKILL.md`
   - Common mistake/pitfall → `.claude/skills/bekende-fouten/SKILL.md`
   - Process/workflow lesson → `CLAUDE.md` (root)
4. **Check for duplicates**: Read the target file and verify the lesson is NOT already documented. Skip duplicates.
5. **Propose additions**: Show the user:
   - What will be added (exact text)
   - Where it will be added (file + section)
   - Why it matters (what it prevents)
6. **Wait for user approval** before writing anything
7. **Write approved additions** to the target files
8. **Commit**: `docs: add learned patterns from session N`

## Quality Gates

- Each lesson must be actionable (not just "be careful with X")
- Each lesson must include the solution, not just the problem
- No duplicates — if it's already documented, skip it
- Maximum 1-2 sentences per lesson — be concise like the existing items in bekende-fouten
