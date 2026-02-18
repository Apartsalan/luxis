Run linting on the backend code and fix any issues found.

Steps:
1. Run `MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/ --fix`
2. If there are unfixable issues, analyze and fix them manually
3. Run again to verify clean
4. Report what was found and fixed
