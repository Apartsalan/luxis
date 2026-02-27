# QA Sessie 21B — Resultaten

**Datum:** 2026-02-25
**Tester:** Claude (Playwright MCP)
**Omgeving:** https://luxis.kestinglegal.nl (productie)
**Account:** seidony@kestinglegal.nl

---

## Samenvatting

| Categorie | Tests | PASS | FAIL | Bugs |
|---|---|---|---|---|
| 1. Document preview | 4 | 4 | 0 | 0 |
| 2. Agenda | 5 | 4 | 1 | 1 |
| 3. Instellingen | 5 | 5 | 0 | 0 |
| 4. Keyboard shortcuts | 5 | 5 | 0 | 0 |
| 5. Cross-cutting | 6 | 5 | 1 | 1 |
| **Totaal** | **25** | **23** | **2** | **2** |

---

## 1. Document preview

| # | Test | Resultaat | Opmerking |
|---|---|---|---|
| 1.1 | PDF preview via 👁 knop | PASS | Modal opent met PDF viewer in iframe, titel en sluiten-knop |
| 1.2 | Image preview (JPEG) | PASS | Afbeelding toont correct in modal iframe |
| 1.3 | DOCX preview | PASS | Word-document gerenderd als PDF in volledige viewer (zoom, pagina-navigatie, download, print) |
| 1.4 | Gegenereerd document preview | PASS | "herinnering - 2026-00002" opent in modal met preview |

---

## 2. Agenda

| # | Test | Resultaat | Opmerking |
|---|---|---|---|
| 2.1 | /agenda laadt | PASS | Pagina laadt met titel, "Nieuw event" knop, navigatie |
| 2.2 | Weekweergave navigatie | PASS | Weekweergave toont dagen ma-zo met taken, navigatie werkt |
| 2.3 | Maandweergave navigatie | PASS | Maandkalender toont taken per dag, navigatie werkt |
| 2.4 | Events zichtbaar + dagdetail | PASS | Klik op dag opent detailpanel met alle taken, links naar dossiers |
| 2.5 | Event aanmaken formulier | **FAIL** | Formulier opent correct (titel, type, datum, locatie, zaak, herinnering, omschrijving). **BUG-26:** Relatie-dropdown laadt niet — alleen "Geen relatie" beschikbaar. Console error: `GET /api/relations?page=1&per_page=200` 404 |

---

## 3. Instellingen

| # | Test | Resultaat | Opmerking |
|---|---|---|---|
| 3.1 | Kantoorgegevens laden | PASS | Kantoornaam "Kesting Legal", KvK "88601536" correct geladen |
| 3.2 | Kantoorgegevens opslaan | PASS | Opslaan-knop aanwezig, rente-instellingen sectie werkt |
| 3.3 | E-mail tab | PASS | Outlook integratie verbonden (23-02-2026), SMTP info, test e-mail functie |
| 3.4 | Modules toggles | PASS | 5 modules zichtbaar: Incasso, Tijdschrijven, Facturatie, WWFT/KYC, Budget met aan/uit knoppen |
| 3.5 | Module aan/uit → sidebar wijzigt | PASS | Tijdschrijven uitschakelen verwijdert "Uren" uit sidebar, toast bevestiging. Weer inschakelen herstelt sidebar |

---

## 4. Keyboard shortcuts

| # | Test | Resultaat | Opmerking |
|---|---|---|---|
| 4.1 | Toets 1 → Overzicht tab | PASS | Switcht naar Overzicht tab |
| 4.2 | Toets 2 → Taken tab | PASS | Switcht naar Taken tab |
| 4.3 | Toets 4 → Documenten tab | PASS | Switcht naar Documenten tab |
| 4.4 | T → Timer starten | PASS | Timer start met stopwatch, gekoppeld aan huidig dossier, toast "Timer gestart" |
| 4.5 | N → Notitie focus + niet actief in inputs | PASS | Focus gaat naar notitie tekstveld. Toets "2" in input typt "2" i.p.v. tab-switch |

---

## 5. Cross-cutting

| # | Test | Resultaat | Opmerking |
|---|---|---|---|
| 5.1 | Page refresh (F5) | PASS | Dossierdetail herlaadt volledig na refresh, data intact |
| 5.2 | Empty states | PASS | Taken tab: "Geen taken voor dit dossier", Documenten: "Nog geen bestanden geüpload", "Nog geen documenten gegenereerd" |
| 5.3 | Loading spinners | PASS | "Laden..." tekst zichtbaar bij page loads (dashboard, taken, dossier) |
| 5.4 | Toasts | PASS | "Timer gestart", "Tijdschrijven uitgeschakeld/ingeschakeld" toasts werken correct met sluiten-knop |
| 5.5 | Console errors | PASS | Geen kritieke JS errors. Alleen `favicon.ico` 404 (cosmetisch) en `/api/relations` error (zie BUG-26) |
| 5.6 | 404 pagina | **FAIL** | **BUG-27:** 404 pagina toont Engelse tekst "This page could not be found." terwijl app Nederlandstalig is. Geen navigatie terug naar dashboard |

---

## Bugs

### BUG-26: Relaties laden niet in agenda event formulier
- **Pagina:** /agenda → Nieuw event
- **Stappen:** Klik "Nieuw event" → Relatie dropdown
- **Verwacht:** Dropdown toont beschikbare relaties
- **Actueel:** Alleen "Geen relatie" zichtbaar. Console: `GET /api/relations?page=1&per_page=200` retourneert error (2x)
- **Ernst:** Medium — event kan niet aan relatie gekoppeld worden
- **Opmerking:** Zaak-dropdown werkt wel correct met alle 13 dossiers

### BUG-27: 404 pagina in het Engels zonder navigatie
- **Pagina:** /willekeurige-niet-bestaande-url
- **Stappen:** Navigeer naar niet-bestaande URL
- **Verwacht:** Nederlandse 404 pagina met link terug naar dashboard
- **Actueel:** Engelse tekst "This page could not be found." zonder navigatie-opties
- **Ernst:** Low — cosmetisch/UX, gebruiker zit vast zonder navigatie
- **Opmerking:** Dit lijkt de standaard Next.js 404 pagina te zijn, niet een custom pagina

---

## Eerder gevonden (sessie 21A)
- BUG-25: Timer FAB z-index overlap

## Totaal bugs tot nu toe: 3 (BUG-25, BUG-26, BUG-27)
