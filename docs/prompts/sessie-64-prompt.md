Sessie 64 — Factuur-PDF generatie + CSV Payment Import UI
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Pre-Launch Sprint') en SESSION-NOTES.md (sessie 63). Geef compacte samenvatting."

## Situatie
Sessie 63 heeft PL-1 (backups), PL-3 (E2E fix), PL-4 (was al klaar), PL-5 (default uurtarief) afgerond. Er zijn nog 2 taken over: PL-2 en PL-6. PL-2 is de laatste BLOKKER voor productie.

## Taak 1: PL-2 — Factuur-PDF generatie (HOOFDTAAK, ~4-6 uur)

Dit is de grootste en belangrijkste taak. Zonder factuur-PDF kan Lisanne geen facturen versturen.

### Wat er moet komen:
1. **Backend endpoint:** `GET /api/invoices/{id}/pdf` — genereert PDF en retourneert als download
2. **DOCX template:** `backend/templates/factuur.docx` — professioneel Kesting Legal design
3. **PDF conversie:** via LibreOffice (zelfde als bestaande documentgeneratie)
4. **Frontend:** "Download PDF" knop op factuur detailpagina

### Onderzoek EERST (CLAUDE.md werkwijze):
- Hoe doen Clio, Basenet, Xero, Exact Online factuur-PDF's?
- Welke velden zijn standaard op een Nederlandse factuur?
- Check bestaande document generatie flow (docxtpl → LibreOffice → PDF) in `backend/app/documents/`

### Vereiste factuurvelden:
- Kantoorgegevens (uit Tenant: naam, adres, KvK, BTW, IBAN)
- Klantgegevens (uit Contact via billing_contact of case.client)
- Factuurnummer, datum, vervaldatum
- Regelitems (description, quantity, unit_price, total)
- Subtotaal, BTW (21%), Totaal
- Betalingsinstructies (IBAN + tenaamstelling)

### Bekende valkuilen:
- Alle bedragen via `Decimal` — NOOIT float
- Nested relaties: `selectinload().selectinload()` expliciet chainen
- LibreOffice is al geïnstalleerd in de backend container

## Taak 2: PL-6 — CSV Payment Import UI (~2-3 uur, als tijd over is)

Backend endpoint bestaat al: `POST /api/payment-matching/import`. Frontend moet nog gebouwd.

### Wat er moet komen:
1. **Pagina of modal** met CSV upload (drag-and-drop of file picker)
2. **Import resultaat tonen** — hoeveel transacties, hoeveel matches
3. **Match review UI** — lijst van matches met confidence badges, approve/reject knoppen

### Check eerst:
- `backend/app/payment_matching/` — welke endpoints bestaan, wat retourneren ze
- Bestaande frontend patronen voor file upload (zijn er al?)

## Verificatie per taak
- `docker compose exec backend pytest tests/ -v` (alle tests groen)
- `cd frontend && npx next build` (geen errors)
- Commit + push na ELKE afgeronde taak
- LUXIS-ROADMAP.md updaten (PL-X status → ✅)
- Deploy naar productie via SSH

## Constraints
- Geen nieuwe features buiten PL-2 en PL-6
- Als PL-2 langer duurt dan verwacht: PL-6 schuift naar sessie 65
- Commit format: `feat(module): PL-X beschrijving`
- Plan Mode gebruiken voor PL-2 (niet-triviale implementatie)
