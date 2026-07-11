# PLAN — PowerSearch + menu-opschoning (S198-vervolg, frozen spec)

Bevroren spec, ontworpen door Fable op basis van gemeten feiten. Bouwer implementeert
exact dit; onmogelijk-als-geschreven → dichtstbijzijnde trouwe variant + afwijking melden.
NIET herontwerpen.

## Context (gemeten, niet aannemen)

- Stack: FastAPI + SQLAlchemy 2.0 **async** + Alembic; PostgreSQL **16.13**; Next.js 15.
  Multi-tenant: RLS + `tenant_id` op alle domeintabellen. Alembic head: `s198_status_simplify`.
- `synced_emails`: 6.509 rijen met `body_text` al gevuld. De globale zoek
  (`backend/app/search/service.py::global_search`) zoekt nu alléén op onderwerp/afzender
  (ILIKE) — niet op inhoud.
- `case_files`: 2.619 actieve rijen; content_type-verdeling: 2.008 PDF, 394 Excel,
  147 octet-stream, 45 HTML, 2 plain text, rest beeld/zip/audio. Bestanden staan op schijf;
  pad via `backend/app/cases/files_service.py::get_file_path(case_file)`. Steekproef:
  ±75% van de PDF's heeft een echte tekstlaag (pymupdf `page.get_text()`).
- `pymupdf4llm` staat al in `backend/pyproject.toml` → `import fitz` werkt in de container.
- HTML→tekst-helper bestaat al: `backend/app/email/providers/imap_provider.py::_html_to_text`.
- Frontend-zoekbalk: `frontend/src/components/command-palette.tsx` → `GET /api/search?q=`
  → `SearchResultItem{id,type,title,subtitle,href}` (backend `app/search/schemas.py`).
- Tests: `backend/tests/test_search.py` (patroon: seed + `GET /api/search` via httpx).
  Testrunner: `docker compose exec -T backend python -m pytest ...` (async test-DB via conftest).

## Klus A — "Documenten"-pagina uit het menu (sjabloonbeheer zit al in Instellingen)

1. Verwijder het nav-item `{ name: "Documenten", href: "/documenten", ... }` uit
   `frontend/src/components/layout/app-sidebar.tsx` (sectie "Beheer"). Ruim daarna
   ongebruikte imports op (bv. `FileText` als die nergens anders in het bestand voorkomt).
2. Verwijder `frontend/src/app/(dashboard)/documenten/page.tsx` volledig.
3. Grep het hele frontend op `"/documenten"` — elke overgebleven link/verwijzing repareren
   (verwijzen naar Instellingen → Sjablonen of weghalen; geen dode links achterlaten).
   NB: `/zaken/[id]?tab=documenten` is een dossier-tab en heeft hier NIETS mee te maken —
   niet aanraken.
4. Hooks `useDocxTemplates`/`useDocumentTemplates` in `frontend/src/hooks/use-documents.ts`
   NIET verwijderen (dossier-tab en compose gebruiken ze mogelijk); alleen als een hook na
   stap 2 aantoonbaar 0 gebruikers heeft, mag die weg.

## Klus B — PowerSearch (inhoud doorzoekbaar, Nederlands, relevantie + snippet)

### B1. Migratie `s199_powersearch` (down_revision: `s198_status_simplify`)

Raw SQL via `op.execute` (generated columns). GEEN nieuwe tabel → geen RLS-wijziging nodig.

```sql
-- e-mails: inhoud doorzoekbaar (cap 300k tekens; tsvector-limiet is 1MB)
ALTER TABLE synced_emails ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    to_tsvector('dutch',
      coalesce(subject,'') || ' ' || coalesce(left(body_text, 300000),''))
  ) STORED;
CREATE INDEX ix_synced_emails_search ON synced_emails USING GIN (search_vector);

-- dossierstukken: geëxtraheerde tekst + doorzoekbaar
ALTER TABLE case_files ADD COLUMN extracted_text text;
ALTER TABLE case_files ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    to_tsvector('dutch',
      coalesce(original_filename,'') || ' ' || coalesce(description,'') || ' ' ||
      coalesce(left(extracted_text, 300000),''))
  ) STORED;
CREATE INDEX ix_case_files_search ON case_files USING GIN (search_vector);
```

Downgrade: indexes + kolommen droppen. Modellen (`SyncedEmail`, `CaseFile`) krijgen
`extracted_text` als gewone kolom; `search_vector` NIET als ORM-attribuut mappen
(of map 'm met `FetchedValue`/deferred) — er mag nooit vanuit Python naar geschreven worden.

### B2. Extractie-module `backend/app/search/extract.py` (nieuw)

```python
def extract_text(content: bytes, content_type: str) -> str | None
```
- `application/pdf` → `fitz.open(stream=content, filetype="pdf")`, alle pagina's
  `page.get_text()`, join met "\n".
- `text/html` → hergebruik `_html_to_text` (import uit
  `app.email.providers.imap_provider`; korte comment waarom).
- `text/plain` → `content.decode("utf-8", errors="replace")`.
- Alles anders (Excel, beeld, zip, audio, octet-stream) → `None` (bewust; NON-GOAL).
- Resultaat: strip; cap op 200.000 tekens; lege string → `None`.
- HELE functie in try/except → bij elke fout `None` + `logger.warning` (extractie mag
  nooit een upload of backfill laten klappen). Sync functie (CPU-werk, geen I/O).

### B3. Upload-hook

In `files_service.upload_case_file`: na het lezen van `content` en vóór `db.add`:
`extracted_text=extract_text(content, content_type)` meegeven aan het `CaseFile`-object.

### B4. Backfill-script `backend/scripts/backfill_extracted_text.py` (nieuw)

- Async script (zelfde patroon als bestaande scripts; gebruikt `app.database.engine`).
- Selecteer `case_files` met `extracted_text IS NULL`, `is_active=true`,
  `content_type IN ('application/pdf','text/html','text/plain')`.
- Per rij: pad via `files_service.get_file_path`; bestand niet op schijf → skip + tel.
- `extract_text(...)`; schrijf resultaat (ook al is het None → laat dan NULL staan maar
  tel als "geen tekst"). Commit per 100 rijen. Eindrapport printen:
  verwerkt / met tekst / zonder tekst / bestand-ontbreekt.
- Idempotent: herdraaien slaat gevulde rijen over. NB: rijen die None opleveren blijven
  NULL en worden bij een herdraai opnieuw geprobeerd — dat is acceptabel en bedoeld.

### B5. Zoekdienst `backend/app/search/service.py` ombouwen

E-mails-blok en documenten-blok worden FTS-hybride; cases/contacts/invoices blijven ILIKE
(nummers/namen → substring is daar correct).

- Querybouw: `func.websearch_to_tsquery(literal("dutch"), bindparam)` — parameter binden,
  NOOIT string-interpolatie (SQL-injectie).
- E-mails: `WHERE tenant_id=... AND (subject ILIKE ... OR from_email ILIKE ... OR
  from_name ILIKE ... OR search_vector @@ websearch_to_tsquery('dutch', :q))`,
  `ORDER BY ts_rank(search_vector, websearch_to_tsquery('dutch', :q)) DESC, email_date DESC`.
- Documenten (case_files): idem — bestaande ILIKE op filename/description behouden +
  `search_vector @@ ...`; zelfde ranking-benadering.
- Snippet: bij FTS-treffers subtitle = `ts_headline('dutch', left(body_text, 5000),
  websearch_to_tsquery('dutch', :q), 'MaxWords=14, MinWords=6')` (e-mails) resp.
  `left(extracted_text, 5000)` (documenten). Bij alleen-ILIKE-treffers: huidige subtitle
  behouden. ts_headline alleen op de al-gelimiteerde resultaatrijen (max ~5 per type).
- Response-schema en frontend NIET wijzigen — subtitle draagt de snippet vanzelf.
- Lege/whitespace-query → `websearch_to_tsquery` geeft lege query; guard: bij lege
  `q.strip()` gedrag houden zoals nu (router valideert al? — check en behoud).

### B6. Tests (uitbreiden `backend/tests/test_search.py` + nieuw unit-bestand)

1. **Inhoud + Nederlandse stemming:** seed een `SyncedEmail` met
   `body_text="Wij betwisten alle betalingen aan Jansen."`, onderwerp zonder dat woord;
   `GET /api/search?q=betaling` → e-mail gevonden (stemming: betaling→betalingen).
2. **Document-inhoud:** seed `CaseFile` met `extracted_text="huurovereenkomst kantoorpand"`;
   zoek `huurovereenkomst` → document gevonden, subtitle bevat snippet-fragment.
3. **Tenant-isolatie FTS:** zelfde seed onder tenant B; zoek als tenant A → 0 van die hits.
4. **Substring blijft:** bestaand gedrag zaaknummer/naam — bestaande tests moeten
   ongewijzigd groen blijven.
5. **Unit `backend/tests/test_extract_text.py`:** PDF in-memory bouwen met fitz
   (`fitz.open()`, `page.insert_text`, `doc.tobytes()`) → `extract_text` geeft de tekst;
   `extract_text(b"x", "application/vnd.ms-excel")` → None; corrupte bytes als PDF → None.

LET OP conftest: de test-DB draait migraties/metadata — controleer dat de generated
columns er in de testomgeving ook zijn (als conftest `Base.metadata.create_all` gebruikt
i.p.v. alembic, moeten de kolommen als DDL in conftest of via het ORM-model bestaan;
kies dan: map `extracted_text` gewoon in het model en voeg de tsvector-kolommen in de
test-setup toe met hetzelfde raw SQL, of — eenvoudiger — geef de modellen een
`search_vector`-kolom met `sa.Computed(<zelfde expressie>, persisted=True)` zodat
create_all én alembic identiek zijn. Verifieer met de proof-run.)

## NON-GOALS (niet bouwen)

OCR/scans; Excel-inhoud; aparte zoekpagina of UI-redesign; wijzigingen aan mailverzending
(mailslot blijft UIT); de 473 wachtende classificaties; alles buiten de genoemde bestanden.

## Verificatie (proof)

1. `docker compose exec -T backend python -m alembic upgrade head` (dev-DB).
2. `docker compose exec -T backend python -m pytest tests/test_search.py tests/test_extract_text.py tests/test_cases.py -q` — alles groen.
3. `cd frontend && npx tsc --noEmit` — exit 0.
4. `uvx ruff check backend/app/ backend/scripts/` — schoon (alleen de eigen bestanden hoeven schoon; bestaande meldingen elders negeren).
