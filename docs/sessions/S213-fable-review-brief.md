# S213 — Fable-review-brief + UITKOMST (afgerond 14 juli, model=Fable)

Opgesteld door Opus aan het eind van de bouw; daarna heeft Fable (zelfde sessie,
model omgezet op verzoek Arsalan) de review gedaan én de koppeling uitgevoerd.

## FABLE-UITKOMST (samenvatting)

**Klus 3 UITGEVOERD (na "go" Arsalan): 1.357/1.563 vorderingen gekoppeld.**
- Bron eerst gelezen (S180-les): `IncassoLine`-XML heeft GEEN document-verwijzing
  (alleen systemid/invnr/datums/bedrag) → naam-matching is echt de enige sleutel;
  geen verborgen koppelkolom.
- Script uitgebreid naar 3 treden (commit `ce54eb4`):
  1. exacte naam uniek → **1.306**
  2. meerdere naam-matches, ALLE byte-identiek (sha256 op de echte bestanden;
     prod-meting vooraf: 35/35 identiek) → oudste gekozen → **35**
  3. kopie-achtervoegsel (`Factuur_140005__1_.pdf` = "(1)"; kale `_1` bewust niet)
     → **16** (waarvan 1 .rtf — verzendpad is type-agnostisch; paperclip-preview
     geeft daar een nette fout, 1 record, geaccepteerd)
- Dry-run == commit == onafhankelijke DB-natelling: 1.357 gevuld, som hoofdsom
  onveranderd €3.142.934,72, 0 kruis-dossier, 0 kruis-tenant, 0 dode verwijzing.
- End-to-end: `has_file=true` telt 1.357; preview van gekoppelde vordering
  levert échte PDF (http 200, application/pdf, %PDF-header).
- **206 rest, terecht niet gekoppeld:** 8 kostenpost-regels (Griffierecht,
  Nakosten, …, geen facturen), ±92 dossiers zonder factuurbestand, ±96 met ander
  nummerschema. Tekst-inhoud-matching (extracted_text) is gemeten (20 uniek,
  waarvan 13 al door trede 3 gedekt) maar bewust NIET gebruikt: een sommatie/vonnis
  dat het nummer citeert zou vals matchen. Restant = handwerk als Lisanne het wil.

**Klus 2 (live sinds `2a9caa3`): alle open klik-verificaties alsnog met ÉCHTE
kliks op prod bewezen (Playwright, na opruimen stale lockfile):** tab-wissel ✓,
sorteerkop → URL `sort_by=principal_amount&sort_dir=desc` en top = €142.961,50
(grootste eerst) ✓, tweede klik → asc ✓, Per-klant-schakelaar → `view=per_klant`
+ per-klant-weergave (lege staat klopt: geen openstaande kantoorfacturen) ✓,
paperclip-klik → popup `application/pdf` ✓, terug naar Kantoorfacturen wist de
tab-parameter ✓. De eerdere klik-problemen waren het automatiseringstool, niet de code.

Bekend & geaccepteerd: browser-terug binnen een open Vorderingen-tab synct de
filter-VELDEN niet live mee (sortering wél) — zelfde gedrag als `zaken/page.tsx`
(huispatroon CONN-8/DF139), lijst en zichtbare filters blijven onderling consistent.

**Afsluitende code-tegenspreker-ronde klus 2 (Fable, zelfde dag, na vraag Arsalan):**
- Backend: sort-whitelist server-side (kolomobjecten, geen injectie); count/sum-queries met
  outer-join kunnen niet dubbeltellen (debiteur = enkelvoudige FK); alle filters AND-gecombineerd;
  beide routes 401 zonder token (live geverifieerd).
- Kruisproef prod: `has_file=true` (1.357 / €2.788.733,32) + `has_file=false` (206 / €354.201,40)
  = exact het totaal (1.563 / €3.142.934,72). Dropdown-endpoint levert 13 opdrachtgevers,
  alfabetisch, allemaal bekende namen.
- Cosmetische randgevallen, geaccepteerd (geen fix): "Wis filters" in Kantoorfacturen wist ook
  bewaarde Vorderingen-parameters uit de URL; drill-down met `contact_id` terwijl `tab=vorderingen`
  nog in de URL staat → UI wint, URL loopt één stap achter; PDF-popup is in Chrome bewezen
  (Playwright), andere browsers met strenge popup-blokkering niet getest.
- Oordeel: **0 must-fixes**; klus 2 + klus 3 volledig gereviewd.

**Naslag rest-206:** `docs/research/S213-rest-vorderingen-zonder-pdf.md` — 199/206 op gesloten
dossiers; op open dossiers 6 creditfacturen + **1 echte** (IN100002, Total Flex, €11.585,12 —
PDF ontbreekt in het dossier, handmatig uploaden als gewenst).

---

## Oorspronkelijke brief (Opus, vóór de Fable-pass)

---

## Wat LIVE staat (gedeployd, prod HEAD `9aea91c`)

**Klus 2 — Facturen-menu 3→2 tabs + rijke Vorderingen-filters.** Twee commits:
- `2a9caa3` feat(facturen): 2-tab menu + rijke vorderingen-filters + directe factuur-PDF
- `9aea91c` feat(scripts): koppel-script (staat klaar, NIET gedraaid)

Backend + frontend gebouwd en gestart via SSH; beide containers healthy; nieuwe endpoints
`/api/claims/clients` + uitgebreide `/api/claims` geven 200 op prod.

### Gewijzigde bestanden (klus 2)
- Backend: `collections/schemas.py` (ClaimOverviewItem +`invoice_file_id`, nieuw `ClaimClient`),
  `collections/service.py` (`list_all_claims` + filters/sort, nieuw `list_claim_clients`,
  const `CLAIM_SORT_FIELDS`), `collections/router.py` (query-params + `/clients`-route).
- Backend tests: `tests/test_claims_overview.py` (6 groen: client-filter, datumbereik, has_file
  beide kanten, sort principal asc/desc, clients-endpoint, `invoice_file_id` in payload).
- Frontend: `hooks/use-invoices.ts` (useClaims params + `useClaimClients` + `invoice_file_id`),
  `app/(dashboard)/facturen/page.tsx` (2 tabs, Lijst/Per-klant-schakelaar binnen Kantoorfacturen,
  Vorderingen-filters + sorteerkoppen + paperclip opent PDF via preview-route + URL-persistentie).

### Verificatie klus 2 (bewijs)
- 6 backend-tests groen (dev-container). `uvx ruff` schoon. `tsc --noEmit` schoon. `npm run build` groen.
- Live dev-backend (na herstart, want container was 8 dagen stale): alle nieuwe endpoints 200,
  payload bevat `invoice_file_id`, clients-dropdown gevuld.
- Prod na deploy: `/api/claims/clients` 200, `/api/claims?has_file=false&sort_by=principal_amount` 200.
- Frontend doorgeklikt (claude-in-chrome) via token-injectie: 2 tabs (geen 3e), Lijst/Per-klant-toggle,
  Vorderingen-filters (opdrachtgever-dropdown, lopende-toggle, meer-filters→datum+PDF), sorteerkoppen,
  PDF-kolom. **Kanttekening (eerlijk):** de klik-robot kon de in-page React-onClick-handlers niet
  triggeren (login-form, tab-switch, sort-toggle, PDF-open negeerden gesimuleerde clicks). Die paden
  zijn geverifieerd via de URL-equivalenten (tab/filters/sort initialiseren correct uit de URL) +
  tsc/build. **Nog niet met een echte muisklik bewezen:** tab-wissel-knop, sorteer-toggle-schrijf naar
  URL, en het openen van een PDF (kon sowieso niet — dev heeft 0 factuur-PDF's). PDF-open spiegelt
  exact het bewezen `DocumentenTab.handlePreviewFile`-patroon.

---

## Klus 3 — PDF-koppeling: KLAAR, NIET GEDRAAID (wacht op Fable-oordeel + akkoord)

Script: `backend/scripts/link_invoice_files.py` (op prod in image op `/app/scripts/`).
Draaien op de VPS:
```
docker compose exec -T backend python scripts/link_invoice_files.py --self-test   # matching-logica
docker compose exec -T backend python scripts/link_invoice_files.py --dry-run      # rapport, schrijft niks
docker compose exec -T backend python scripts/link_invoice_files.py --commit       # zet invoice_file_id
```

### Matching-recept (conservatief, exact + uniek)
Per vordering zonder PDF (`invoice_file_id` NULL) mét factuurnummer: zoek in HETZELFDE dossier het
actieve bestand waarvan `filename_invoice_key(original_filename)` exact gelijk is aan
`_norm(invoice_number)`. `filename_invoice_key` = stem zonder extensie, spaties/underscores weg,
leidend `factuur`-prefix eraf, hyphens behouden. **Alleen koppelen bij precies één kandidaat**
(anders overslaan). Alleen `invoice_file_id` wordt gemuteerd.

### Dry-run op PROD (14 juli, read-only, niets geschreven)
```
Vorderingen zonder PDF, mét factuurnummer : 1563
  -> uniek koppelbaar (zou gekoppeld)     : 1306
  -> meerdere kandidaten (overgeslagen)   : 35
  -> geen match (overgeslagen)            : 222
Vorderingen zonder factuurnummer          : 0
```
Steekproef schoon: `132391 -> Factuur_132391.pdf`, `LW100719 -> Factuur_LW100719.pdf`.

Diagnose van de 222 "geen match" (read-only):
- **92** hebben helemaal geen PDF op het dossier → niet koppelbaar.
- **130** hebben wél PDFs maar geen naam-match. Steekproef:
  - `25130123 -> Factuur_LW103621.pdf …` (ander nummerschema, geen match)
  - `F2024-00102 -> Offerte-…pdf, Alle_facturen_Bigvand_Gallery_R.pdf` (alleen offerte + bundel)
  - `Hoofdsom / Dagvaarding / Griffierecht / Salaris gemachtigde / Nakosten -> paspoort/vonnis`
    → dit zijn **kostenposten als "vordering", geen facturen** — terecht geen PDF.
  - `18910670 -> Factuur_078913421.pdf …` (ander nummer, geen match)

**Waarom 1306 i.p.v. de ±1.368-schatting (S212):** het script koppelt alléén 100%-zekere unieke
matches. De 35 ambigue (dubbele upload, zelfde nummer) worden bewust NIET gegokt.

### Reviewpunten voor Fable (klus 3) — actief weerleggen vóór `--commit`
1. **Is de matching veilig?** Kan `filename_invoice_key` ooit twee verschillende facturen op één
   nummer laten vallen, of een niet-factuur (kostenpost) toch matchen? (steekproef zegt nee.)
2. **De 35 ambigue** — zijn dat echt dubbele uploads (zelfde bestand) of twee verschillende? Wil
   Lisanne die met de hand? (nu: overgeslagen.)
3. **Tenant/RLS:** script zet `SET LOCAL app.current_tenant` per tenant (zoals kvk-script). Correct?
4. **Alleen `invoice_file_id` gemuteerd?** Geen andere velden, geen kosten/rente geraakt. (Verifieer.)
5. **Natelling-plan:** na `--commit` moet "uniek koppelbaar" (1306) == werkelijk gezet, en de
   totale set vorderingen ongewijzigd op 1563; steekproef van 5 in de UI (paperclip opent de juiste PDF).
6. **`--self-test` groen** (pure matcher) — al bevestigd op prod.

---

## Totale sessie-review (wens Arsalan) — aandachtspunten
- **Backend `/api/claims`:** filters (client_id/date_from/date_to/has_file) + sort — SQL correct,
  NULL-`invoice_date` valt bewust buiten een datumbereik (gedocumenteerd + getest). Geen N+1?
- **`/api/claims/clients`:** distinct-join Contact↔Case↔Claim — geen dubbelen, tenant-scoped.
- **Frontend URL-persistentie:** vorderingen-filters + tab + view in de URL; botst niet met de
  Kantoorfacturen-params (`contact_id`/`status`). Parent-`useEffect` op `[searchParams]` reset
  geen tab bij een filter-schrijf. (Controleer de wissel Kantoorfacturen↔Vorderingen met echte klik.)
- **Paperclip PDF-open:** preview-route + token→blob→`window.open`. Foutafhandeling (toast) ok?

## Losse eindjes / omgeving
- **Dev-DB:** wachtwoord van `seidony@kestinglegal.nl` is in dev gewijzigd naar `Devpass-123`
  (om lokaal te kunnen inloggen; oorspronkelijke dev-hash was onbekend). **Alleen dev**, prod
  ongemoeid. E2E gebruikt `e2e-test@` (los account), dus geen impact.
- **KvK-backfill (hoofdtaak S213):** nog niet gestart — wacht op de echte KvK-sleutel (~16 juli).
- Geen migraties in deze sessie (klus 2 is puur additief in code, geen schema-wijziging).
