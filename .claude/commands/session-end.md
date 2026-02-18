End-of-session quality check. Run this before ending every work session.

Steps:
1. **Lint**: `MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/`
2. **Tests**: `MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -v`
3. **Duplicate check**: Search for duplicated code patterns or functions that do the same thing
4. **Consistency check**: Verify naming conventions, import patterns, and module structure are consistent
5. **Uncommitted changes**: `git status` — commit everything that should be committed
6. **Push**: Push all commits to origin
7. **Report**: Summary of session work, any issues found, and state of the codebase
