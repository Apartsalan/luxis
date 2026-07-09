# Goal: Complete test-suite voor Luxis

**Doel:** Bouw complete test-suite (unit + integration + E2E) met sterke nadruk op
frontend Playwright coverage. Alle 28 demo-bugs uit sessies 138-139 als
regressie-tests opgenomen.

Dit bestand wordt gelezen door `/goal` in Claude Code. De `/goal`-conditie zelf
is kort; alle scope, mocking, constraints en werkwijze staan hieronder.

---

## FASE 0 — VERPLICHTE CONTEXT-INNAME (eerste turn)

LEES IN DEZE VOLGORDE voor je 1 test schrijft:

1. `CLAUDE.md` — project-overview, kritieke regels (financial precision, multi-tenant)
2. `backend/CLAUDE.md` — module pattern, financial calc locaties, test patterns
3. `frontend/CLAUDE.md` — Playwright setup, auth flow, force:true conventie
4. `docs/dutch-legal-rules.md` — wettelijke rente, WIK, art. 6:44 BW
5. `.claude/projects/C--Users-arsal-Documents-luxis/memory/MEMORY.md`
6. Memory files waar MEMORY.md naar verwijst, in het bijzonder:
   - `feedback_test_recipient_safety.md` (KRITIEK voor mail tests)
   - `feedback_no_destructive_db.md`
   - `feedback_geen_caveman.md`
   - `feedback_ui_benamingen.md`
   - `feedback_grondig_checken.md`
7. `SESSION-NOTES.md` — laatste 4 sessies (136-139), in het bijzonder alle
   28 demo-bugs gefixt in 138-139 — die zijn de **regressie-test-database**
8. `LUXIS-ROADMAP.md` sectie "Demo Feedback Lisanne sessie 138"
9. `backend/tests/conftest.py` — test-DB fixtures
10. `frontend/playwright.config.ts` + `frontend/e2e/auth.setup.ts` +
    `frontend/e2e/helpers/auth.ts` + `frontend/e2e/helpers/api.ts`
11. `frontend/e2e/` + `backend/tests/` directories listen
12. `git log --oneline -30` voor recente context

Vat in 1 turn samen: codebase, kritieke regels, alle 28 demo-bugs die als
regressie-tests moeten verschijnen.

---

## DEFINITION OF DONE

Alle 6 commands moeten groen:

```bash
docker compose exec backend pytest --cov=app --cov-fail-under=80 --cov-report=term
docker compose exec backend pytest tests/ -v
docker compose exec backend ruff check app/
cd frontend && npx tsc --noEmit
cd frontend && npx playwright test --reporter=list
```

Plus:

- Minimaal 150 backend tests, geen unsanctioned skips
- Minimaal 55 frontend E2E tests
- `backend/tests/COVERAGE.md` + `frontend/e2e/COVERAGE.md` bestaan met
  checklist per workflow + regressie-test per DF138-XX bug

---

## SCOPE PER LAAG

### Laag 1 — Backend unit tests (pytest, ~80 tests)

Financiële kernlogica:

- `app/collections/interest.py` — simple + compound, monthly + yearly basis,
  rente vanaf verzuimdatum (niet 1 jan), capitalisatie, deelbetaling, NULL rate
- `app/collections/wik.py` — alle 5 staffeltrappen (15/10/5/1/0.5%), min €40,
  max €6.775, exact-grenzen (€2.500/€5.000/€10.000/€200.000)
- `app/collections/payment_distribution.py` — art. 6:44 BW kosten→rente→hoofdsom,
  edge cases (betaling < kosten, = totaal, > totaal)
- `app/collections/service.py::get_financial_summary` — BIK-bodem
  (bik_minimum_fee), BTW 21% op BIK bij niet-BTW-plichtig, modes (percentage,
  vast, WIK)
- `app/relations/service.py::select_terms_for_date` — smart-default AV-versie keuze
- `app/incasso/automation_service.py::_resolve_contact_person` — salutation
  tuple return, bedrijf via ContactLink, persoon met last_name fallback
- `app/incasso/automation_service.py::_capitalize_name`, `_last_name_from_full`

Test-bestanden in `backend/tests/unit/`. Bestaande tests uitbreiden, niet
vervangen.

### Laag 2 — Backend integration tests (pytest, ~50 tests)

Async test-DB via `conftest.py`. Per resource: CRUD + 1 negative test
(404/409/422) + MULTI-TENANT-ISOLATIE (tenant A mag tenant B niet zien).

Modules: relations, cases, collections, invoices, incasso, workflow, auth.

Test-bestanden in `backend/tests/integration/`. Multi-tenant in eigen file
`test_multi_tenant_isolation.py`.

### Laag 3 — Frontend E2E tests (Playwright, MINIMAAL 55 tests)

Tests als `.spec.ts` files in `frontend/e2e/`.

#### Groep A — Kern workflows (15 tests)

1. Login happy path + 2 foutpaden
2. Logout
3. Relaties: lijst, zoeken, filter Bedrijven/Personen
4. Relatie aanmaken bedrijf
5. Relatie aanmaken persoon (incl. salutation dropdown)
6. Relatie bewerken
7. Relatie soft-delete
8. Relatie bulk-delete met confirm-dialog
9. Dossier-wizard: cliënt + wederpartij + factuur + rente-cascade
10. Dossier-detail tabs: financieel, vorderingen, betalingen, correspondentie
11. Dossier sorteren (case_number/status/hoofdsom/geopend)
12. Dossier bulk-delete
13. Dossier status wijzigen
14. Incasso pipeline step wisselen
15. Concept-mail genereren via "Concept genereren"

#### Groep B — Edge cases per scherm (15 tests)

16. Lege staat: relaties zonder content
17. Lege staat: dossiers zonder content
18. Lege staat: dossier zonder factuur
19. Lege staat: incasso zonder pipeline-stap
20. Lange lijst paginering: relaties (50+ items)
21. Lange lijst paginering: dossiers (50+ items)
22. Filter-combinatie: contactType + zoekterm op relaties
23. Filter-combinatie: status + type + datum op dossiers
24. Foutmelding 422: verkeerd email-format bij relatie aanmaken
25. Foutmelding 409: gekoppelde relatie verwijderen
26. Foutmelding ontbrekende velden in dossier-wizard
27. Mobile rendering: sidebar collapse op sm breakpoint
28. Mobile rendering: relaties card-view op mobile
29. Mobile rendering: dossier card-view op mobile
30. Zoek zonder resultaat: lege staat met juiste boodschap

#### Groep C — Regressie-tests alle 28 demo-bugs (28 tests)

31. DF138-01: partij-pills klikbaar in wizard, openen relatie-detail in nieuw tab
32. DF138-02: advocatenkantoor selector + contactpersoon-veld in wizard
33. DF138-03: label "Minimum provisie" (niet "Minimumkosten")
34. DF138-04: salutation dropdown bij person, aanhef in mail klopt
35. DF138-05: mail-Betreft alleen dossiernummer (niet klant-referentie)
36. DF138-06: concept-mail toont rente + BIK + BTW (niet alleen hoofdsom)
37. DF138-07: datums in mail NL-format DD-MM-JJJJ
38. DF138-08: relaties tonen correct aanmaakdatum (niet vandaag voor iedereen)
39. DF138-09: relatie-delete met gekoppeld dossier toont 409 met melding
40. DF138-10: sorteer-headers op relaties met chevron-indicator
41. DF138-11: inline contactpersoon bij bedrijf-aanmaak in wizard
42. DF138-12: info-box rente "Geen rente-default — wettelijke rente toegepast"
43. DF138-13: rate_basis (per maand/jaar) cascadet van klant naar dossier
44. DF138-14: BIK-minimum bodem toegepast bij percentage-mode
45. DF138-15: voetnoot in mails bevat "kestinglegal.nl/debiteuren" + disclaimer
46. DF138-16: dossier toont apart `bik_minimum_fee` veld los van provisie
47. DF138-17: BIK-bedrag zonder "minimumtarief van € X" suffix
48. DF138-18: `default_bik_minimum_fee` opgeslagen na klant-detail save
49. DF138-19: BIK-bodem zichtbaar in Vorderingen-tab (frontend)
50. DF138-20: pipeline-mail body bevat nieuwe voetnoot
51. DF138-21: Rente-cel in HTML-mail toont berekende waarde (niet € 0,00)
52. DF138-22: aanhef toont alleen achternaam (niet voornaam+achternaam)
53. DF138-23: geen lege factuur-placeholder-rijen tussen factuur en bedragen-tabel
54. S139-bulk-delete dossiers: bulk-toolbar verschijnt bij selectie
55. S139-bulk-delete relaties: bulk-toolbar + 409 in mixed toast
56. S139-sort-persist relaties: URL bevat sort_by/sort_dir na klik header
57. S139-sort-persist dossiers: URL bevat sort_by/sort_dir + browser-back behoudt
58. S139-av-versies: cliënt-detail toont versie-lijst + upload-form werkt

#### Groep D — UI rendering checks (8 tests)

59. Status-badges juiste kleur per case-status (nieuw, in_behandeling, betaald, etc.)
60. Bedrag-format consistent € 1.234,56 in alle schermen
61. Datum-format consistent DD-MM-JJJJ in alle schermen
62. Mailto-link werkt op email-velden in relatie-detail
63. Tel-link werkt op telefoon-velden in relatie-detail
64. Externe link "openen in nieuw tab" op partij-pills in wizard
65. Skeleton loader verschijnt tijdens laden lange lijsten
66. Toast notification verschijnt bij success/error acties

---

## MOCKING — niet-onderhandelbaar

- `app/ai_agent/kimi_client.call_draft_ai` → fixed JSON response stub
- `app/email/providers/outlook.py::OutlookProvider.send_message` → noop +
  log; NOOIT echte mails versturen
- Recipient bij mail-tests ALTIJD overrulen naar `arsalanir@hotmail.com`
- KVK API → mock fixture
- Externe betalings-providers (Mollie) → mock

---

## CONSTRAINTS — WAT NIET DOEN

- GEEN productie-DB acties — alleen lokale async test-DB
- GEEN echte emails — recipient overrulen naar `arsalanir@hotmail.com`
- GEEN echte AI-calls — mock alle providers
- GEEN bestaande tests deleten (fixen of skippen met `@pytest.mark.skip(reason=...)`)
- GEEN nieuwe productie-features bouwen — alleen tests
- GEEN Alembic-migraties wijzigen of toevoegen
- GEEN dependencies toevoegen tenzij hard nodig
- GEEN docker-compose wijzigingen
- GEEN tests tegen productie URL (`luxis.kestinglegal.nl`) — alleen `http://localhost:3000`
- GEEN caveman-stijl in commits/comments — normale taal

---

## WERKWIJZE PER ITERATIE

1. Pak één test-file uit scope
2. Schrijf tests met realistische data:
   - GEEN hardcoded dates — `date.today()` of relatief
   - GEEN exact counts op seeded data — `>=` en subset-checks
   - Alle API paths met `/api/` prefix (`/api/auth/login` niet `/auth/login`)
   - Voor Playwright: `force:true` op clicks (Next.js dev overlay blokkeert),
     `getByPlaceholder()` als geen htmlFor/id, regex voor `waitForURL`
3. Run lokaal en check groen
4. Bij fail: óf test corrigeren, óf bug loggen in `tests/KNOWN_BUGS.md` + skip
5. Lint check (`ruff check app/` of `tsc --noEmit`)
6. Commit per logisch groepje (~200 regels): `test(module): beschrijving` +
   Co-Authored-By Claude trailer
7. `git push origin main` na elke commit. Deploy automatisch.
8. Update `backend/tests/COVERAGE.md` of `frontend/e2e/COVERAGE.md`
9. Volgende iteratie

---

## CONTEXT

- Werkmap: `C:\Users\arsal\Documents\luxis`
- Dev stack starten: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
- Test DB: zelfde container, andere database — `conftest.py` regelt setup
- E2E target: `http://localhost:3000` — NIET productie

Volgorde: laag 1 → laag 2 → laag 3 (groep A → B → C → D). Begin met FASE 0.
