# Frontend E2E Coverage — Luxis

Dit document beschrijft welke workflows worden gedekt door de Playwright E2E
test-suite. Voor backend-coverage zie `backend/tests/COVERAGE.md`.

## Setup

- Config: `playwright.config.ts` — 3-project setup (setup → auth → chromium)
- Auth: storageState pattern via `auth.setup.ts` → `e2e/.auth/user.json`
- Helpers: `helpers/auth.ts`, `helpers/api.ts`
- Workers: 1, fullyParallel: false (volgordeafhankelijkheid tussen tests)
- Doel: `http://localhost:3000` — NOOIT productie

---

## Groep A — Kern workflows

| # | Test | Bestand | Dekt |
|---|------|---------|------|
| A1 | Login happy path | `auth.spec.ts` | /login → dashboard |
| A2 | Login foutpad: verkeerd wachtwoord | `auth.spec.ts` | 401 + foutmelding |
| A3 | Login foutpad: ontbrekend veld | `auth.spec.ts` | Validatie |
| A4 | Logout | `auth.spec.ts` | Token clear + redirect |
| A5 | Relaties: lijst + zoeken + filter | `relaties.spec.ts` R1 | /relaties |
| A6 | Relatie aanmaken bedrijf | `relaties.spec.ts` R2 | /relaties/nieuw |
| A7 | Relatie aanmaken persoon | `relaties.spec.ts` R3 | /relaties/nieuw |
| A8 | Relatie bewerken | `relaties.spec.ts` R4 | /relaties/[id] |
| A9 | Relatie verwijderen | `relaties.spec.ts` R5 | /relaties/[id] |
| A10 | Dossier-wizard | `zaken.spec.ts` Z3 | /zaken/nieuw |
| A11 | Dossier-detail tabs | `zaken.spec.ts` Z4, Z5 | /zaken/[id] |
| A12 | Dossier status wijzigen | `zaken.spec.ts` Z7 | Workflow API |
| A13 | Dossier bewerken | `zaken.spec.ts` Z6 | /zaken/[id] |
| A14 | Dossier verwijderen | `zaken.spec.ts` Z8 | /zaken/[id] |
| A15 | Incasso pipeline | `incasso-pipeline.spec.ts` E1-E9 | /incasso |

## Groep B — Edge cases

| # | Test | Bestand | Dekt |
|---|------|---------|------|
| B1 | Zoek zonder resultaat | `edge-cases.spec.ts` | Lege staat met juiste boodschap |
| B2 | Filter combinatie relaties | `edge-cases.spec.ts` | contactType + zoekterm |
| B3 | Filter combinatie dossiers | `edge-cases.spec.ts` | status + type |
| B4 | Paginering relaties | `edge-cases.spec.ts` | >25 items toont pagina-control |
| B5 | Paginering dossiers | `edge-cases.spec.ts` | >25 items toont pagina-control |
| B6 | Mobile rendering sidebar | `edge-cases.spec.ts` | sm breakpoint collapse |
| B7 | Mobile rendering relaties | `edge-cases.spec.ts` | Card-view op mobile |
| B8 | Mobile rendering dossiers | `edge-cases.spec.ts` | Card-view op mobile |
| B9 | Foutmelding 422 email-format | `edge-cases.spec.ts` | Validatie bij aanmaken |
| B10 | Foutmelding 409 delete-met-dossier | `edge-cases.spec.ts` | Server error toon |
| B11 | Foutmelding wizard-velden | `edge-cases.spec.ts` | Required validatie |
| B12 | Lege staat dossiers | `edge-cases.spec.ts` | Geen content fallback |
| B13 | Lege staat relaties zoekterm | `edge-cases.spec.ts` | Geen resultaten + reset |
| B14 | Sidebar links toonbaar | `edge-cases.spec.ts` | Alle nav items zichtbaar |
| B15 | Dashboard skeleton | `edge-cases.spec.ts` | Loader bij data fetch |

## Groep C — Regressie alle 28 demo-bugs (sessie 138 + 139)

Elke bug uit demo-feedback Lisanne is als regressie-test opgenomen om
herhaling te voorkomen. Zie `regression.spec.ts`.

| # | Bug | Test | Wat verifiëren |
|---|-----|------|----------------|
| C1 | DF138-01 | regression.spec.ts | Partij-pills openen relatie-detail in nieuw tab |
| C2 | DF138-02 | regression.spec.ts | Wizard heeft advocatenkantoor selector + contactpersoon-veld |
| C3 | DF138-03 | regression.spec.ts | Label "Minimum provisie" (niet "Minimumkosten") |
| C4 | DF138-04 | regression.spec.ts | Salutation dropdown bij person-aanmaken |
| C5 | DF138-05 | regression.spec.ts | Concept-mail Betreft toont alleen dossiernummer |
| C6 | DF138-06 | regression.spec.ts | Concept-mail toont rente + BIK + BTW velden |
| C7 | DF138-07 | regression.spec.ts | Datums in concept-mail in NL-format DD-MM-JJJJ |
| C8 | DF138-08 | regression.spec.ts | Relatielijst toont realistic created_at, niet "Vandaag" voor allen |
| C9 | DF138-09 | regression.spec.ts | Relatie-delete met dossier toont duidelijke 409-melding |
| C10 | DF138-10 | regression.spec.ts | Sorteer-headers met chevron-indicator op relaties |
| C11 | DF138-11 | regression.spec.ts | Inline contactpersoon-velden in wizard bij bedrijf |
| C12 | DF138-12 | regression.spec.ts | Info-box rente in wizard zonder klant-default |
| C13 | DF138-13 | regression.spec.ts | rate_basis cascade van klant naar dossier in wizard |
| C14 | DF138-14 | regression.spec.ts | BIK-bodem zichtbaar in Vorderingen-tab |
| C15 | DF138-15 | regression.spec.ts | Voetnoot in concept-mail bevat "kestinglegal.nl/debiteuren" |
| C16 | DF138-16 | regression.spec.ts | Klant-detail toont apart "Minimum BIK" veld |
| C17 | DF138-17 | regression.spec.ts | bik_source zonder "minimumtarief van € X" suffix |
| C18 | DF138-18 | regression.spec.ts | default_bik_minimum_fee opslaan en herladen |
| C19 | DF138-19 | regression.spec.ts | BIK-bodem in Vorderingen-tab (frontend rekening) |
| C20 | DF138-20 | regression.spec.ts | Pipeline-mail body bevat nieuwe voetnoot |
| C21 | DF138-21 | regression.spec.ts | Rente-cel toont berekende waarde, niet € 0,00 |
| C22 | DF138-22 | regression.spec.ts | Aanhef toont alleen achternaam (geen voornaam) |
| C23 | DF138-23 | regression.spec.ts | Geen lege factuur-placeholder-rijen in mail |
| C24 | S139-bulk-dossiers | regression.spec.ts | Bulk-toolbar verschijnt bij selectie van dossier-checkboxes |
| C25 | S139-bulk-relaties | regression.spec.ts | Bulk-toolbar verschijnt bij selectie van relatie-checkboxes |
| C26 | S139-sort-persist relaties | regression.spec.ts | URL bevat sort_by/sort_dir na klik header |
| C27 | S139-sort-persist dossiers | regression.spec.ts | URL bevat sort_by/sort_dir + browser-back behoudt |
| C28 | S139-av-versies | regression.spec.ts | Cliënt-detail toont AV-versie-sectie |

## Groep D — UI rendering checks

| # | Test | Bestand | Dekt |
|---|------|---------|------|
| D1 | Status-badges kleur | `ui-rendering.spec.ts` | Badge classes per case status |
| D2 | Bedrag-format | `ui-rendering.spec.ts` | € 1.234,56 NL-locale |
| D3 | Datum-format | `ui-rendering.spec.ts` | DD-MM-JJJJ NL-format |
| D4 | Mailto-link | `ui-rendering.spec.ts` | Email-velden zijn mailto-anchors |
| D5 | Tel-link | `ui-rendering.spec.ts` | Telefoon-velden zijn tel-anchors |
| D6 | Sidebar items zichtbaar | `ui-rendering.spec.ts` | Alle nav items na auth |
| D7 | Skeleton loader | `ui-rendering.spec.ts` | Loader bij eerste paint |
| D8 | Toast notification | `ui-rendering.spec.ts` | Sonner toast na success |

---

## Bestanden

- `auth.spec.ts` — login/logout
- `auth.setup.ts` — storageState voor authenticated tests
- `relaties.spec.ts` — relaties CRUD
- `zaken.spec.ts` — dossiers CRUD
- `incasso-pipeline.spec.ts` — incasso pipeline
- `facturen.spec.ts` — facturen CRUD
- `tijdregistratie.spec.ts` — uren CRUD
- `agenda.spec.ts` — agenda CRUD
- `taken.spec.ts` — taken CRUD
- `correspondentie.spec.ts` — correspondentie
- `documenten.spec.ts` — documenten
- `dashboard.spec.ts` — dashboard
- `sidebar.spec.ts` — sidebar navigatie
- `instellingen.spec.ts` — instellingen
- `regression.spec.ts` — Groep C: 28 demo-bug regressies
- `edge-cases.spec.ts` — Groep B: 15 edge cases
- `ui-rendering.spec.ts` — Groep D: 8 UI rendering checks
