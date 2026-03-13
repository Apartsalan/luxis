Sessie 67 — Fix 196 test errors + 1 failure (BUG-42)
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees SESSION-NOTES.md (sessie 66 en 65) en LUXIS-ROADMAP.md (BUG-42). Geef compacte samenvatting."

## Taak
De test suite geeft 196 errors en 1 failure. Dit moet 0 errors en 0 failures worden.

**Symptomen:**
- `pytest tests/ -q` → 376 passed, 196 errors, 1 failed
- Alle errors zijn `relation "X" does not exist` (tabellen niet aangemaakt)
- Getroffen test-modules: test_ai_agent, test_auth, test_cases, test_dashboard, test_documents, test_email_sync, test_followup, test_incasso_pipeline, test_intake, test_integration_api, test_invoice_payments, test_invoice_pdf, test_invoices, test_payment_matching, test_relations
- 1 failure: `test_derdengelden_flow` in test_integration_api.py

**Belangrijk context:**
- Sessie 65 rapporteerde 573 passed / 0 errors met `pytest tests/ -v`
- Sessie 66 draaide `pytest tests/ -q` en kreeg 376 passed / 196 errors
- Dit verschil kan liggen aan: test ordering, fixture scoping, of hoe `-q` vs `-v` pytest configuratie beïnvloedt
- De conftest.py fix uit sessie 65 gebruikte `DROP SCHEMA public CASCADE` + `CREATE SCHEMA public` + `metadata.create_all()` + `NullPool`

**Aanpak:**
1. Lees `backend/tests/conftest.py` en begrijp de huidige setup
2. Draai `pytest tests/ -q` en bevestig de errors
3. Draai `pytest tests/ -v` en vergelijk — zijn er dan WEL 0 errors?
4. Analyseer het verschil — welke fixture scope/ordering veroorzaakt het probleem
5. Fix de conftest.py zodat BEIDE runs 0 errors geven
6. Specifiek voor `test_derdengelden_flow`: lees de test en analyseer waarom die faalt

## Verificatie
```bash
docker compose exec -T backend pytest tests/ -q    # Moet 0 errors, 0 failures geven
docker compose exec -T backend pytest tests/ -v    # Moet ook 0 errors, 0 failures geven
docker compose exec -T backend ruff check app/     # Moet 0 warnings geven
```

## Constraints (wat NIET doen)
- Geen nieuwe features bouwen
- Geen refactors buiten conftest.py en test files
- Geen worktrees
- Geen `# noqa` of test-skips — alle tests moeten echt passen

## Commit
`fix(tests): resolve 196 test errors and 1 failure (BUG-42)` + push + deploy
