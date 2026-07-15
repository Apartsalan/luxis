# PLAN — Dossierpagina 2.0 (van 11 tabbladen naar één rustig geraamte)

**Status:** ontworpen S215 (15 juli 2026, Fable) — onderzoek in code + prod-DB + visueel doorgeklikt
(incasso IN100215 én verse advieszaak, testdossier 2026-00002 daarna verwijderd, staat inactief).
**Bouwen:** Opus, 3 blokken (zie PROMPT-S216). **Review:** Fable + Playwright-doorklik verplicht.

## 0. Harde eisen (Arsalan, 15 juli)

1. **Alles wat nu klikbaar is, blijft klikbaar.** Elke link/knop van de oude pagina bestaat op de
   nieuwe. Verificatie = klik-inventaris oud→nieuw afvinken, geen belofte.
2. **Eén stijl, één geraamte voor beide zaaktypes.** Incasso en normale zaken zijn dezelfde tool;
   afwijken mag alleen waar dat voor dat type aantoonbaar betere UX is. Zelfde kop-opbouw, zelfde
   tabbladvolgorde, zelfde zijbalk-stijl.
3. **Niets wordt onzichtbaar — lege secties zijn ingeklapt, één klik open.** ("Betalingsregeling —
   geen" met chevron.) Soms wil je gewoon even kijken.
4. **Uren blijft een volwaardig tabblad voor élk dossier** (uurtjeszaken komen eraan; timer blijft).

## 1. Diagnose (gemeten 15 juli, prod)

- 608 dossiers, **alles incasso** (1 advies = verwijderde test). Data per tabblad: vorderingen 603,
  bestanden 596, mails 594, betalingen 144, facturen 127, activiteiten 70, taken 3, staphistorie 2,
  uren 0, derdengelden 0, verschotten 0, extra partijen 0.
- **Tabbalk past niet op 1280px**: Facturen/Documenten/Correspondentie/Activiteiten/Partijen vallen
  buiten beeld (screenshotbewijs S215).
- **Kop vult het hele eerste scherm** (fasebalk + 4 statkaarten + 7 knoppen): na elke tab-klik begint
  de inhoud onder de vouw.
- **Dubbelingen:** partijen op 4 plekken, financieel op 3, dossierinfo op 2-3. "Rente"-statkaart toont
  alleen het rentetype. Zijbalk-OHW altijd €0.
- **Notities:** 3 begrippen (notitie / telefoonnotitie / debiteurnotities), 2 invoerplekken, knoppen
  springen naar verschillende tabs. Live bewezen: telefoonnotitie-tekst komt aan maar cursor niet
  (code zoekt een `textarea` die sinds de Tiptap-editor niet meer bestaat; zelfde stale selector in
  de "n"-sneltoets).
- **Advieszaak lekt incasso:** zijbalk toont "Debiteur: B2B" + "Rente: wettelijke rente", kop draagt
  B2B-badge — betekenisloos op advies. Kop heeft daar géén enkele geldinfo (alleen verweesd breed
  Partijen-kaartje).
- **PartijenTab bevat de conflictcontrole-weergave** (useConflictCheck) — nergens anders getoond.
  Bij opheffen tabblad MOET die verhuizen (→ waarschuwingsbanner Overzicht, prominenter).
- **Concurrenten:** Clio = dashboard-kaarten (WIP/openstaand/derdengelden/budget, aan-uit te zetten)
  + agenda-subtab per zaak; Smokeball = widgets (geldstand, "Next Step"-taak, komende 2 afspraken)
  + tijdlijn van alles. Rode draad: één overzicht, één tijdlijn, geld+agenda+volgende-stap bovenaan.

## 2. Doelbeeld

### Tabbladen (zelfde volgorde beide types; incasso heeft er één extra)

| # | Incasso | Normale zaak (dossier/advies) |
|---|---|---|
| 1 | Overzicht | Overzicht |
| 2 | **Financieel** (vorderingen+betalingen+regeling) | — |
| 3 | Facturen | Facturen |
| 4 | Documenten | Documenten |
| 5 | Correspondentie | Correspondentie |
| 6 | Uren | Uren |
| 7 | Tijdlijn | Tijdlijn |

- **Financieel** = VorderingenTab → FinancieelTab (Incassokosten/Specificatie) → BetalingenTab →
  BetalingsregelingSection (ingeklapt indien geen) → DerdengeldenTab (ingeklapt indien leeg/0).
  Anker-subnav bovenin (Vorderingen · Betalingen · Regeling). ProvisieSettingsSection
  ("Facturatie-instellingen") verhuist naar Facturen-tab (hoort bij cliëntfacturatie).
- **Facturen** = Provisie (alleen incasso) + FacturenTab + VerschottenSection (ingeklapt indien leeg).
- **Tijdlijn** = huidige ActiviteitenTab (binnenkop heet al "Tijdlijn"); + filterknop "Stappen"
  (StaphistorieTab-inhoud, alleen incasso).
- **Vervalt als tabblad:** Taken (→ Overzicht-blok, volledige functionaliteit mee: toevoegen/afronden/
  overslaan/herhaling + "Concept openen"-knop), Vorderingen/Betalingen/Staphistorie (→ zie boven),
  Activiteiten (→ Tijdlijn), Partijen (kaarten staan al op Overzicht; conflictcontrole → banner).

### Kop (beide types zelfde opbouw)

1. Titel + status/B2B-badge (B2B/B2C alleen incasso) + verjaring-badge.
2. Sturing: incasso = fasebalk + stapkeuze + afsluiten/heropenen (bestaande kaart, compacter);
   normaal = "Volgende stap"-regel: eerstvolgende open taak + deadline (Smokeball-patroon; taken
   bestaan al — dit is tonen, niet bouwen).
3. **Geldstrook** (smalle band, geen 4 losse kaarten): incasso = Hoofdsom · Betaald · **Openstaand**;
   normaal = OHW · Ongefactureerd · Openstaand (facturen) · Budget (indien gezet). "Rente"-kaart en
   Partijen-kaart vervallen uit de kop (partijen: zijbalk + Overzicht).
4. Actieknoppen: zelfde set, compacter. Renteoverzicht alleen incasso (is al zo).
5. **Doel meetbaar:** op 1280×720 begint tab-inhoud boven de vouw.

### Overzicht-tab

- CaseActionFeed (bestaand) + NIEUW: takenblok + NIEUW: agenda-blok (eerstvolgende 3 afspraken van
  dit dossier, klikbaar → /agenda; endpoint checken, CalendarEvent heeft case-koppeling sinds D5)
  + conflictcontrole-banner (verhuisd uit PartijenTab) + BaseNet-waarschuwingsbanner (amber, als
  debtor_notes "[BaseNet-waarschuwing]" bevat; klik scrollt naar debiteurinstellingen).
- Dossiergegevens/Procesgegevens/Debiteurinstellingen (incasso)/Partijen-sectie: blijven, bewerken
  zoals nu. Notitie-box + recente activiteit rechts blijven.

### Notities

- Eén dialoog (huisstijl-Dialog) voor Notitie én Telefoonnotitie; telefoonnotitie = zelfde dialoog met
  belsjabloon (datum/gesprek-met/onderwerp) + telefoon-icoon. Focus direct in de editor (Tiptap-focus
  via editor-API, niet querySelector) → cursor-bug en stale "n"-sneltoets-selector zijn daarmee gefixt.
- Debiteurnotities blijven dossierveld (incasso).

### Zijbalk (beide types, type-afhankelijke velden)

- Debiteur + Rente alleen bij incasso. OHW alleen bij normale zaken (of >0). Uurtarief/betaaltermijn
  alleen indien gevuld. Rest zoals nu (partijen klikbaar, financieel snapshot, budget-balk).

### Niet stuk laten gaan

- **?tab=-vertaaltabel:** vorderingen→financieel, betalingen→financieel, staphistorie→tijdlijn,
  activiteiten→tijdlijn, partijen→overzicht, taken→overzicht (safeTab-logica uitbreiden; links vanuit
  derdengelden-pagina en CaseActionFeed-onNavigate blijven werken).
- Sneltoetsen (1-9, t/n/d/e/f) bijwerken op de nieuwe tablijst.
- Alle bestaande props/flows (draft-dialoog, compose, batch) ongemoeid.

## 3. Blokken

- **Blok 1 — tabbladen** (beide types): nieuwe tablijst, samenvoegingen, inklap-gedrag, vertaaltabel,
  sneltoetsen, takenblok + conflictbanner op Overzicht. Puur frontend.
- **Blok 2 — kop + notities**: geldstrook per type, compactere sturing, notitie-dialoog,
  BaseNet-waarschuwingsbanner, zijbalk ontdubbelen/type-afhankelijk.
- **Blok 3 — normale zaak**: agenda-blok op Overzicht, "Volgende stap"-regel, geldstrook-bronnen
  (OHW/ongefactureerd bestaan al), incasso-lek dichten (zijbalk/badge + debiteurtype-veld in
  aanmaakformulier verbergen bij niet-incasso).

## 4. Verificatie (per blok, vóór "klaar")

1. `npx tsc --noEmit` + gerichte tests (geen backend-wijzigingen verwacht).
2. Playwright-doorklik op prod: IN100215 (incasso, regeling) + verse advies-testzaak (aanmaken →
   bekijken → verwijderen; kost een dossiernummer, geaccepteerd patroon S210/S215).
3. **Klik-inventaris:** lijst van elke link/knop op de oude pagina → aanwezig + werkend op de nieuwe.
4. Vouw-check: 1280×720, tab-klik → inhoud zichtbaar zonder scrollen.
5. Oude ?tab=-links: alle 6 oude waarden landen goed.

## 5. Pre-mortem

1. *Lisanne raakt dingen kwijt* → niets verdwijnt, verhuist voorspelbaar; demo na blok 1-2.
2. *Financieel-tab te lang* → anker-subnav + inklappen; terugvalbesluit (2 tabs houden) ná het zien.
3. *Type-afhankelijkheid wordt twee ontwerpen* → harde eis 2: zelfde geraamte, afwijking alleen met
   UX-reden; review toetst hierop.
