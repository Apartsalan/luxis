Run all backend tests and report results. If any test fails, analyze the failure and fix it.

Steps:
1. Run `MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -v`
2. If tests fail: read the failing test, understand the error, fix the code (not the test unless the test is wrong)
3. Re-run until all tests pass
4. Report: total tests, passed, failed, and what was fixed
