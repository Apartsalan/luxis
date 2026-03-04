Run a structured post-implementation verification checklist. Use this after implementing a feature to ensure quality before committing.

## Steps

### 1. Backend tests
```bash
MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -v
```
Report: PASS (all green) / FAIL (list failures)

### 2. Backend lint
```bash
MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/
```
Report: PASS (no issues) / FAIL (list issues, auto-fix with `ruff check --fix app/`)

### 3. Frontend build
```bash
cd frontend && npm run build
```
Report: PASS (build successful) / FAIL (list errors)

### 4. Common mistake scan (grep-based)

Run these checks on the codebase:

a. **localhost:8000 in frontend** (should use relative URLs):
Search `frontend/src/` for `localhost:8000` in `.ts` and `.tsx` files

b. **float for money in backend** (should use Decimal):
Search `backend/app/` for `float(` in `.py` files, excluding tests and comments

c. **Missing /api/ prefix in tests**:
Search `backend/tests/` for `"/auth/` or `"/relations/` (missing `/api/` prefix)

d. **undefined vs null in frontend forms**:
Search `frontend/src/` for `|| undefined` in `.ts` and `.tsx` files

e. **Hardcoded dates in tests**:
Search `backend/tests/` for date patterns like `"2026-` or `"2025-` that aren't in comments

Report: PASS (no matches) / WARN (list matches for manual review)

### 5. Code review (on changed files only)

Get changed files: `git diff --name-only HEAD`

If there are changed files, spawn the `code-reviewer` agent on those files. Report the agent's findings.

### 6. Git status

Check:
- Uncommitted changes: `git status --porcelain`
- Unpushed commits: `git log origin/main..HEAD --oneline`

Report: CLEAN / HAS_UNCOMMITTED / HAS_UNPUSHED

### 7. Summary table

Print results:
```
| Check              | Status    |
|--------------------|-----------|
| Backend tests      | PASS/FAIL |
| Backend lint       | PASS/FAIL |
| Frontend build     | PASS/FAIL |
| Common mistakes    | PASS/WARN |
| Code review        | N issues  |
| Git status         | CLEAN/... |
|                    |           |
| Overall            | READY / NEEDS ATTENTION |
```

## Notes

- Skip steps that aren't relevant (e.g., skip frontend build if no frontend files changed)
- For step 4, false positives are possible — review matches before flagging as issues
- If Docker is not running, skip steps 1-2 and note it in the summary
