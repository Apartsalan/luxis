# Goal: Test-suite cleanup + coverage doorpushen

**Doel:** Werk de 5 KNOWN-bugs categorieën weg, herschrijf 35 stale E2E specs
tegen de huidige UI, en duw backend coverage van 57.75% naar 70%.

Dit bestand wordt gelezen door `/goal`. De `/goal`-conditie zelf is kort; alle
scope, mocking, constraints en werkwijze staan hieronder.

---

## FASE 0 — VERPLICHTE CONTEXT (eerste turn)

LEES IN DEZE VOLGORDE voor je 1 wijziging maakt:

1. `CLAUDE.md` + `backend/CLAUDE.md` + `frontend/CLAUDE.md`
2. `docs/dutch-legal-rules.md`
3. `.claude/projects/C--Users-arsal-Documents-luxis/memory/MEMORY.md` + alle
   feedback-files waar het naar verwijst (i.h.b. `feedback_test_recipient_safety.md`,
   `feedback_no_destructive_db.md`, `feedback_geen_caveman.md`)
4. `SESSION-NOTES.md` (laatste 4 sessies — context van demo-bugs en wat sinds
   sessie 139 is gewijzigd)
5. **`backend/tests/KNOWN_BUGS.md`** — KRITIEK: dit is de werklijst, alle 5
   categorieën zijn hier gedocumenteerd
6. `backend/tests/COVERAGE.md` + `frontend/e2e/COVERAGE.md` — wat bestaat al
7. `docs/GOAL-TEST-SUITE.md` — vorige scope-document (voor patronen)
8. `backend/tests/conftest.py` + `frontend/playwright.config.ts`
9. `git log --oneline -40`

---

## DEFINITION OF DONE (3 sub-doelen, ALLE 3 moeten waar zijn)

### Sub-doel 1: KNOWN-bugs weggewerkt of bevestigd-onhaalbaar

Voor elke KNOWN-XXX entry in `backend/tests/KNOWN_BUGS.md`:
- Óf de skip-marker verwijderen + test laten slagen (gefixt)
- Óf de entry markeren als `STATUS: BEVESTIGD ONHAALBAAR` met technische reden

**Concreet per categorie:**

- **KNOWN-001 (derdengelden endpoints verplaatst)**: oude tests in
  `test_collections_router.py` en `test_integration_api.py` herschrijven om
  de nieuwe `/api/trust-funds/...` endpoints aan te roepen. Skip-markers weg.
- **KNOWN-002 (SEPA test-client lifecycle)**: helpers `_setup_approved_disbursement`
  en `_set_trust_account` splitsen zodat httpx-client open blijft. Skip-markers
  in `test_trust_funds.py` en `test_trust_funds_offset.py` weg.
- **KNOWN-003 (DOCX-render zonder seeded templates)**: conftest fixture toevoegen
  die `templates/*.docx` kopieert naar test-templates-pad zodat assertions
  realistische counts krijgen. Skip-markers in `test_documents.py` weg.
- **KNOWN-004 (greeting-tests t.o.v. nieuwe aanhef-logica)**: `test_html_renderer.py`
  twee tests updaten zodat ze de nieuwe salutation+achternaam format checken.
- **KNOWN-005 (12+ stale E2E specs)**: zie sub-doel 3.

### Sub-doel 2: Backend coverage minstens 70%

```
docker compose exec backend pytest --cov=app --cov-fail-under=70 --cov-report=term
```

Exit 0. Coverage rapport in `backend/coverage.xml` aanwezig.

**Strategie**: focus op modules met laagste coverage uit het rapport. Schrijf
unit-tests voor specifieke functies, niet meer integration tests (die zijn
al groot).

### Sub-doel 3: Alle stale E2E specs herschreven of bevestigd-onhaalbaar

Voor elke spec in KNOWN-005 lijst:
- Óf herschrijven tegen huidige UI zodat test slaagt
- Óf vervangen door equivalente test in `regression.spec.ts` / `edge-cases.spec.ts`
- Óf gemarkeerd `STATUS: NIET MEER RELEVANT` in `KNOWN_BUGS.md` met reden

**Concreet per file (zie KNOWN-005 in KNOWN_BUGS.md voor details):**
- `auth.spec.ts::A4` — logout-button heeft aria-label, geen title
- `agenda.spec.ts::A2` — dialog-flow veranderd
- `correspondentie.spec.ts` — empty-state tekst veranderd
- `dashboard.spec.ts` — greeting heading veranderd
- `documenten.spec.ts` — page structure veranderd
- `facturen.spec.ts::F2, ::F7` — wizard flow + delete-confirm dialog veranderd
- `incasso-pipeline.spec.ts` — pipeline steps hernoemd
- `instellingen.spec.ts` — tab-structure veranderd
- `sidebar.spec.ts` — dashboard greeting check faalt voor beforeEach
- `relaties.spec.ts::R5` — delete-confirm dialog nu custom React component
- `tijdregistratie.spec.ts::T5` — zelfde delete-confirm issue
- `zaken.spec.ts::Z3` — client-search input verplaatst naar latere wizard-stap

Voor R5/T5/F7/... delete-confirm dialog: gebruik `page.click('text=Verwijderen')`
+ wacht op AlertDialogContent component + bevestig-klik. Geen `page.on('dialog')`
meer.

### Verificatie-commando's (alle 6 groen)

```bash
docker compose exec backend pytest --cov=app --cov-fail-under=70 --cov-report=term
docker compose exec backend pytest tests/ -v
docker compose exec backend ruff check app/
cd frontend && npx tsc --noEmit
cd frontend && npx playwright test --reporter=list
grep -c "STATUS:" backend/tests/KNOWN_BUGS.md  # elke KNOWN-XXX moet STATUS hebben
```

Alle 6 exit 0 + grep telt minstens 5 STATUS-regels.

---

## MOCKING — niet onderhandelbaar

- `app/ai_agent/kimi_client.call_draft_ai` → fixed JSON stub
- `app/email/providers/outlook.py::OutlookProvider.send_message` → noop + log
- Recipient bij mail-tests ALTIJD `arsalanir@hotmail.com`
- KVK API + externe providers → mock
- SMTP → endpoint `?skip_email=true` of mock

## CONSTRAINTS — WAT NIET DOEN

- GEEN productie-DB acties
- GEEN echte emails, AI-calls, externe API-calls
- GEEN nieuwe productie-features bouwen — alleen tests + minimaal nodige
  bugfixes om tests te laten passeren
- GEEN Alembic-migraties wijzigen
- GEEN dependencies toevoegen tenzij hard nodig
- GEEN docker-compose wijzigingen
- GEEN tests tegen productie URL — alleen `http://localhost:3000`
- GEEN caveman-stijl in commits — normale taal
- Bij bug in productie-code die tests onthullen: fix de bug + commit apart
  met `fix(module): beschrijving (gevonden door /goal cleanup)`. Test daarna
  toevoegen.

## WERKWIJZE PER ITERATIE

1. Pak één KNOWN-XXX of één laag-coverage module
2. Schrijf/update tests met realistische data (geen hardcoded dates, geen
   exact counts op seeded data)
3. Lokaal runnen, check groen
4. Bij fail: óf code fixen (bug) óf test fixen (verkeerde verwachting) óf
   STATUS-regel in KNOWN_BUGS.md
5. Lint + TS check
6. Commit per logisch groepje, conventional message + Co-Authored-By trailer
7. `git push origin main` na elke commit
8. Update `COVERAGE.md` indien relevant
9. Volgende iteratie

Volgorde:
1. Eerst KNOWN-001 t/m KNOWN-004 (klein per stuk, snel resultaat)
2. Dan KNOWN-005 stale E2E specs (groter werk, 12 files)
3. Dan coverage doorpushen naar 70% door specifiek-modules-targeten

## CONTEXT

- Werkmap: `C:\Users\arsal\Documents\luxis`
- Dev stack: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
- Test DB: zelfde container, `conftest.py` regelt
- E2E target: `http://localhost:3000` — NIET productie
