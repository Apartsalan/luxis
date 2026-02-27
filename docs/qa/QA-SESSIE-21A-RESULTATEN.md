# QA Sessie 21A — Resultaten

**Datum:** 25 feb 2026
**Geteste secties:** Uren, Facturen, Documenten (standalone)
**Methode:** Playwright MCP op https://luxis.kestinglegal.nl
**Login:** seidony@kestinglegal.nl

---

## Uren (/uren)

| # | Test | Resultaat | Opmerkingen |
|---|------|-----------|-------------|
| T77 | Urenlijst laadt | ✅ PASS | Weekoverzicht, tabel, filters, stopwatch |
| T78 | Uren registreren | ✅ PASS | Dossier-picker, velden, opslaan, toast |
| T79 | Timer start/stop | ✅ PASS | Floating widget, Stop & Opslaan |
| T80 | Bewerken | ✅ PASS | Inline edit, opslaan |
| T81 | Verwijderen | ✅ PASS | Geen bevestigingsdialoog (UX-1) |
| T82 | Filteren | ✅ PASS | Dossier-filter + empty state |

## Facturen (/facturen)

| # | Test | Resultaat | Opmerkingen |
|---|------|-----------|-------------|
| T83 | Facturenlijst laadt | ✅ PASS | Tabel, zoek, filters |
| T84 | Filteren op status | ✅ PASS | Concept/Verzonden + empty state |
| T85 | Debiteuren tab | ✅ PASS | Nette empty state |
| T86 | Nieuwe factuur | ✅ PASS | Relatie-zoek, regels, BTW berekening |
| T87 | Uren importeren | ⏭ SKIP | Geen data beschikbaar |
| T88 | Factuurdetail | ✅ PASS | BUG-22 regressie OK |
| T89 | Goedkeuren | ✅ PASS | Concept → Goedgekeurd, knoppen wijzigen |
| T90 | Verzenden | ✅ PASS | Goedgekeurd → Verzonden, betalingssectie |
| T91 | Betaling registreren | ✅ PASS | Auto "Deels betaald", voortgangsbalk |
| T92 | Credit nota | ✅ PASS | CN-nummering, pre-fill, link naar origineel |

## Documenten (/documenten + dossierdetail)

| # | Test | Resultaat | Opmerkingen |
|---|------|-----------|-------------|
| T93 | Documentenlijst laadt | ✅ PASS | 7 Word templates, status "Beschikbaar" |
| T94 | HTML Sjablonen tab | ✅ PASS | Nette empty state |
| T95 | Document genereren + downloaden | ✅ PASS | Herinnering gegenereerd, .docx download |
| T96 | Document preview | ❌ NIET GETEST | Context window vol |

---

## Gevonden bugs

| # | Beschrijving | Ernst | Locatie |
|---|-------------|-------|---------|
| BUG-25 | Floating timer FAB overlapt knoppen onderin pagina (z-index). Blokkeert klik op "Factuur aanmaken" en filterknoppen. | Midden | Frontend: timer component, z-index te hoog of positie overlapt met page content |
| UX-1 | Geen bevestigingsdialoog bij verwijderen tijdregistratie — direct verwijderd | Laag | Frontend: /uren pagina, delete handler |
| UX-2 | Floating timer widget blokkeert soms klikken op elementen eronder | Midden | Zelfde als BUG-25 — z-index/overlap issue |

---

## Nog te testen (sessie 21B)

### Uit sessie 21A plan (niet afgerond):
- T96: Document preview (👁 knop → PDF modal)

### Sessie 21B plan:
- Agenda (T97-T101) — 5 tests
- Instellingen + Modules (T102-T106) — 5 tests
- Keyboard shortcuts (T107-T110) — 4 tests
- Cross-cutting checks (T111-T116) — 6 tests

### Sessie 21C plan:
- Alle bugs fixen (BUG-25 + eventuele nieuwe)
- Committen + deployen
- Regressie check

---

## Test-data aangemaakt (opruimen indien nodig)

- Factuur F2026-00002 (€363, status: Deels betaald, betaling €200)
- Credit nota CN2026-00001 (€363, concept)
- Gegenereerd document: herinnering_2026-00001_2026-02-25.docx
- Tijdregistraties: opgeruimd tijdens sessie
