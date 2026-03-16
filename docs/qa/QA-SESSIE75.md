# QA Sessie 75 — Volledige Walkthrough

**Datum:** 16 maart 2026
**Tester:** Claude (Playwright MCP)
**Omgeving:** https://luxis.kestinglegal.nl (productie)
**Account:** seidony@kestinglegal.nl

## Samenvatting

**Algehele status: GOED — systeem is demo-ready met enkele UX-verbeteringen nodig.**

Alle hoofdfuncties werken:
- Login, dashboard, sidebar navigatie
- Nieuw dossier wizard met AI factuur parsing
- Dossier detail met alle 9 tabs
- Facturatie (aanmaken + PDF generatie)
- Incasso pipeline met batch werkstroom
- Relatiebeheer, urenregistratie, agenda

Gevonden: 0 P0 bugs, 4 P1 bugs, 7 P2 bugs.

---

## Geteste flows

### 1. Login pagina
**Status:** Werkt

- Login form: clean, professioneel design
- Inloggen met credentials: succesvol
- Redirect naar dashboard: correct

**Issues gevonden:**
- [P2-01] `favicon.ico` 404 error in console
- [P1-01] API call naar `/api/cases?page=1&per_page=20` op login pagina voordat gebruiker is ingelogd (401 error in console). Waarschijnlijk een component dat data probeert te laden voordat auth check compleet is.

### 2. Dashboard
**Status:** Werkt goed

- Begroeting: "Goedemiddag, Lisanne" — correct
- KPI-kaarten: Actieve dossiers (16), Relaties (17), Openstaand, Vandaag gewerkt, Open facturen
- Pipeline balk: toont distributie
- Mijn taken: 5 taken zichtbaar met "Verlopen" indicatie
- Uren deze week: correct
- Recente facturen: 3 stuks met bedragen
- Actie nodig: correct
- Dossiers per status: correct
- Recente activiteit: chronologisch

**Geen issues.**

### 3. Sidebar navigatie
**Status:** Werkt

- 14 menu-items met iconen
- Badge counts: Dossiers (3), Follow-up (1), Incasso (1)
- Collapse/expand werkt
- Actieve pagina highlighted

**Issues gevonden:**
- [P2-02] Dashboard toont "16 actieve dossiers" maar sidebar badge toont "3" — onduidelijk wat de badge representeert (mogelijk "3 nieuw deze maand"). Kan verwarrend zijn.

### 4. Nieuw dossier wizard
**Status:** Werkt — AI parsing is indrukwekkend

**Stap 1 — Zaakgegevens:**
- Upload zone: duidelijk, klikbaar
- PDF upload: werkt (factuur_techvision_bv.pdf)
- AI parsing: velden automatisch ingevuld (Beschrijving, Debiteurtype)
- Confidence dots: groen zichtbaar bij ingevulde velden
- Success message: "Factuur geanalyseerd — velden ingevuld"
- Toast notification: "Factuurgegevens ingevuld"

**Stap 2 — Partijen:**
- Cliënt en wederpartij search fields pre-filled met AI-parsed tekst
- Conflict detection: werkt (waarschuwing bij conflicterende partij)

**Stap 3 — Vordering:**
- Optioneel, automatisch overgeslagen met AI-parsed data
- Vordering correct aangemaakt (€ 3.872,00)

**Issues gevonden:**
- [P1-02] Timer floating button (`fixed bottom-4 right-4 z-50`) blokkeert de "Volgende" knop. Gebruikers op normaal scherm kunnen niet op Volgende klikken zonder de Timer eerst weg te klikken. Dit is een BREED probleem dat op meerdere pagina's voorkomt.
- [P2-03] "Vordering(optioneel)" — spatie ontbreekt voor haakje in step indicator. Moet zijn: "Vordering (optioneel)".
- [P1-03] AI-parsed partijnamen worden als zoektekst in het veld gezet maar triggeren geen daadwerkelijke selectie. Gebruiker moet handmatig de tekst wissen en opnieuw zoeken/selecteren. UX verbetering: AI zou moeten proberen te matchen met bestaande contacten, of een "Nieuwe relatie aanmaken met deze gegevens" knop aanbieden.
- [P2-04] "Selecteer een client" validatiefout blijft zichtbaar nadat client WEL is geselecteerd (visueel stale error).

### 5. Dossier detail pagina
**Status:** Alle 9 tabs werken

| Tab | Status | Opmerkingen |
|-----|--------|-------------|
| Overzicht | OK | Pipeline, KPI's, dossiergegevens, procesgegevens, partijen, notitie-editor, activiteiten |
| Taken | OK | Takenlijst met afronding |
| Vorderingen | OK | Vordering tabel, BIK berekening correct (€ 512,20), rente (€ 14,85), specificatie tabel |
| Betalingen | OK | Betalingen, betalingsregeling, derdengelden — alle empty states correct |
| Facturen | OK | Factureer uren, nieuwe factuur, empty state |
| Documenten | OK | Template generatie (aanbevolen), bestandsupload, gegenereerde docs |
| Correspondentie | OK | Sync inbox, nieuwe email, filter tabs |
| Activiteiten | OK | Timeline met notitie-toevoegen |
| Partijen | OK | Partijoverzicht met conflict warning |

**BIK verificatie:** € 3.872 → 15% × € 2.500 + 10% × € 1.372 = € 375 + € 137,20 = **€ 512,20** ✓

### 6. Facturatie flow
**Status:** Werkt

- Nieuwe factuur aanmaken: succesvol (F2026-00003)
- Factuur/Voorschotnota tabs: aanwezig
- Factuurregels: omschrijving, aantal, prijs, totaal — correct berekend
- BTW berekening: € 250 × 21% = € 52,50 ✓
- Totaal: € 302,50 ✓
- PDF generatie: download werkt (F2026-00003.pdf)
- Goedkeuren/Annuleren workflow: knoppen aanwezig
- Dossier linking: correct gekoppeld aan 2026-00017

**Issues gevonden:**
- [P1-04] Navigatie met `case_id` URL parameter vult de Relatie en Dossier velden niet visueel in op het formulier. De data wordt WEL correct opgeslagen (dossier is gelinkt op de detail pagina). UX verbetering nodig: pre-fill de velden.

### 7. Relatiebeheer
**Status:** Werkt

- 17 relaties zichtbaar
- Filter tabs: Alle, Bedrijven, Personen
- Zoekbalk met placeholder
- Type iconen (persoon/bedrijf)

**Issues gevonden:**
- [P2-05] Veel test/rommel data ("dsaas", "poephoofd", "looo", etc.) — opschonen voor demo.

### 8. Incasso pipeline
**Status:** Werkt uitstekend

- Pipeline stappen: Aanmaning, Sommatie, 2e Sommatie, Ingebrekestelling, Executie, Dagvaarding
- Kleur-gecodeerde status dots (groen=normaal, oranje=overdue)
- Filter tabs: Alle dossiers (6), Klaar voor volgende stap, 14d verlopen, Actie vereist
- Batch selectie ("Selecteer alles")
- "Zonder stap" sectie voor nieuwe dossiers
- Werkstroom / Stappen beheren tabs

### 9. Urenregistratie
**Status:** Werkt

- Stopwatch met dossier selector
- Weekoverzicht (Ma-Vr) met per-dag totalen
- Summary: Totaal, Declarabel, Totaal bedrag
- Nieuwe registratie knop

**Issues gevonden:**
- [P2-06] Week range header toont "15 mrt — 19 mrt 2026" maar de daadwerkelijke dagen zijn Ma 16 - Vr 20 mrt. Off-by-one in de week range berekening.

### 10. Agenda
**Status:** Werkt

- Maandoverzicht met kleur-gecodeerde events
- Vandaag (16) highlighted
- View toggles: Vandaag, Maand, Week
- "Nieuw event" knop
- Navigatie vorige/volgende maand

### 11. Zakenlijst (Dossiers)
**Status:** Werkt

- 17 dossiers in tabel
- Zoekbalk
- Filters: type, status, meer filters
- CSV export
- Batch selectie
- Sorteerbare kolommen

---

## Issue overzicht

### P0 — Broken functionaliteit (directe fix nodig)
*Geen P0 issues gevonden.*

### P1 — Belangrijke UX problemen (fix voor demo)

| # | Beschrijving | Locatie | Impact |
|---|-------------|---------|--------|
| P1-01 | API call op login pagina voor auth check (401 in console) | Login pagina | Console errors, mogelijke race condition |
| P1-02 | Timer floating button blokkeert "Volgende" en andere knoppen | Breed (alle pagina's) | Gebruiker kan knoppen onderin niet klikken |
| P1-03 | AI-parsed partijnamen worden niet gematcht met bestaande contacten | Nieuw dossier wizard stap 2 | Extra handmatig werk voor gebruiker na AI parsing |
| P1-04 | case_id URL parameter vult formuliervelden niet visueel in | Nieuwe factuur pagina | Verwarrend — dossier IS gelinkt maar velden lijken leeg |

### P2 — Visuele/UX verbeteringen (fix na demo)

| # | Beschrijving | Locatie |
|---|-------------|---------|
| P2-01 | favicon.ico 404 | Alle pagina's |
| P2-02 | Sidebar badge "3" onduidelijk vs dashboard "16 actieve dossiers" | Dashboard/sidebar |
| P2-03 | "Vordering(optioneel)" spatie ontbreekt | Nieuw dossier wizard |
| P2-04 | Stale validatiefout na succesvolle client selectie | Nieuw dossier wizard stap 2 |
| P2-05 | Test/rommel data opschonen voor demo | Relaties + dossiers |
| P2-06 | Week range off-by-one (15-19 mrt i.p.v. 16-20 mrt) | Urenregistratie |
| P2-07 | Sticky header rendering in full-page screenshots (geen impact op gebruiker) | Meerdere pagina's |

---

## Screenshots

Alle screenshots opgeslagen in `.playwright-mcp/`:
- `qa-01-login-page.png` — Login pagina
- `qa-02-dashboard.png` — Dashboard (full page)
- `qa-03-sidebar.png` — Sidebar navigatie
- `qa-04-nieuw-dossier-step1.png` — Wizard stap 1
- `qa-05-ai-parsed.png` — AI parsing resultaat met confidence dots
- `qa-06-wizard-step2.png` — Wizard stap 2 (Partijen)
- `qa-09-conflict-detection.png` — Conflict detectie
- `qa-10-case-detail-overview.png` — Dossier overzicht
- `qa-11-vorderingen-tab.png` — Vorderingen tab
- `qa-12-betalingen-tab.png` — Betalingen tab
- `qa-13-documenten-tab.png` — Documenten tab
- `qa-14-factuur-nieuw.png` — Nieuwe factuur form
- `qa-15-factuur-filled.png` — Factuur ingevuld
- `qa-16-factuur-detail.png` — Factuur detail + PDF
- `qa-17-relaties.png` — Relatiebeheer
- `qa-18-incasso-pipeline.png` — Incasso pipeline
- `qa-19-uren.png` — Urenregistratie
- `qa-20-agenda.png` — Agenda

---

## Conclusie

**Luxis is demo-ready.** De kernfunctionaliteit werkt goed en het systeem ziet er professioneel uit. De AI factuur parsing is een sterke feature die goed indruk zal maken.

**Aanbevelingen voor demo:**
1. Fix P1-02 (Timer overlay) — dit is het meest zichtbare probleem
2. Schoon test data op (P2-05) — relaties en dossiers met rommel-namen verwijderen
3. De overige P1/P2 items kunnen na de demo opgepakt worden

**Sterke punten:**
- AI factuur parsing met confidence dots
- Professioneel en data-dense dashboard
- Complete incasso pipeline met batch werkstroom
- BIK berekening 100% correct
- PDF generatie werkt
- Conflict detection bij partij selectie
- Document templates met "aanbevolen voor huidige status"
