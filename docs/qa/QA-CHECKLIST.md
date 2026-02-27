# Luxis QA Testlijst

**Doel:** Systematisch alle features testen. Loop elke sectie af, vink af wat werkt, noteer bugs.
**Legenda:** `[ ]` = nog testen, `[x]` = werkt, `[BUG]` = bug gevonden (noteer beschrijving)

---

## 1. Login & Authenticatie

- [ ] Login met email + wachtwoord → redirect naar dashboard
- [ ] Verkeerd wachtwoord → foutmelding
- [ ] Wachtwoord vergeten → reset email ontvangen
- [ ] Uitloggen → terug naar login
- [ ] Na page refresh → blijf ingelogd (token in localStorage)

---

## 2. Dashboard (/)

- [ ] Dashboard laadt zonder errors
- [ ] "Mijn Taken" widget toont open taken
- [ ] Recente dossiers zichtbaar
- [ ] Klik op taak → gaat naar juiste dossier
- [ ] Klik op dossier → gaat naar dossier detail

---

## 3. Relaties (/relaties)

- [ ] Lijst met alle contacten laadt
- [ ] Zoeken/filteren werkt
- [ ] **Nieuw contact aanmaken** (/relaties/nieuw)
  - [ ] Naam, email, telefoon, adres invullen
  - [ ] Opslaan → verschijnt in lijst
- [ ] **Contact bewerken** (/relaties/[id])
  - [ ] Gegevens laden correct
  - [ ] Wijzigen + opslaan werkt
  - [ ] Veld leegmaken + opslaan → veld wordt daadwerkelijk gewist

---

## 4. Dossiers (/zaken)

### 4a. Dossierlijst
- [ ] Alle dossiers laden
- [ ] Zoeken op dossiernummer/cliënt werkt
- [ ] Filteren op status werkt
- [ ] Filteren op type werkt

### 4b. Nieuw dossier (/zaken/nieuw)
- [ ] Type selecteren (incasso/advies/insolventie/overig)
- [ ] Client kiezen uit relaties
- [ ] Wederpartij kiezen
- [ ] Beschrijving, referentie invullen
- [ ] Budget veld zichtbaar (als budget-module aan staat)
- [ ] Opslaan → dossier aangemaakt met dossiernummer
- [ ] Automatische taken aangemaakt (check Taken tab)

### 4c. Dossier detail (/zaken/[id])

#### Sidebar (rechts)
- [ ] Dossierinfo sectie toont type, status, datum, referentie
- [ ] Client sectie met link + email
- [ ] Wederpartij sectie met link + email
- [ ] Financieel snapshot (OHW, incasso-details)
- [ ] Budget progress bar (als budget-module aan + budget ingesteld)
  - [ ] Groen bij <80%
  - [ ] Amber bij 80-100%
  - [ ] Rood bij >100%
- [ ] Sidebar in/uitklappen werkt
- [ ] Sidebar state blijft behouden na page refresh

#### Overzicht tab
- [ ] Dossiergegevens tonen correct
- [ ] **Bewerken** knop → formulier verschijnt
  - [ ] Alle velden wijzigbaar
  - [ ] Veld leegmaken + opslaan → veld wordt gewist (niet oude waarde)
  - [ ] Opslaan → wijzigingen zichtbaar
  - [ ] Annuleren → wijzigingen ongedaan
- [ ] Notitie toevoegen → verschijnt in activiteiten
- [ ] Recente activiteiten tonen

#### Procesgegevens (G3)
- [ ] Procesgegevens card zichtbaar
- [ ] Rechtbank dropdown (alle 16 NL rechtbanken + gerechtshoven + Hoge Raad)
- [ ] Rechter, kamer, type procedure, procesfase invullen
- [ ] Opslaan werkt

#### Partijen tab
- [ ] Partijen overzicht laadt
- [ ] Conflict detectie werkt (als van toepassing)

#### Taken tab
- [ ] Automatisch aangemaakte taken zichtbaar
- [ ] **Nieuwe taak aanmaken**
  - [ ] Titel, type, deadline, omschrijving
  - [ ] Herhaling instellen (dagelijks/wekelijks/maandelijks/per kwartaal/jaarlijks)
  - [ ] "Herhalen tot" datumveld verschijnt bij recurring
  - [ ] Opslaan → taak verschijnt in lijst
- [ ] Taak voltooien → status wijzigt
- [ ] Recurring taak voltooien → nieuwe taak automatisch aangemaakt
- [ ] Recurring badge (blauw met 🔄) zichtbaar bij herhalende taken

#### Correspondentie tab
- [ ] Email lijst laadt (of lege state als geen emails)
- [ ] Filter tabs: Alles / Ontvangen / Verzonden
- [ ] **Sync inbox** knop (als email verbonden)
  - [ ] Sync draait → toast met resultaat
  - [ ] Nieuwe emails verschijnen
- [ ] **Email detail** — klik op email → detail panel rechts
  - [ ] Van/Aan/CC/Datum headers correct
  - [ ] HTML body correct gerenderd
  - [ ] **Bijlage downloaden** → bestand downloadt (geen 401) ← BUG-13 fix
  - [ ] **Bijlage opslaan in dossier** → groen vinkje → bestand verschijnt in Documenten tab ← BUG-14 fix
  - [ ] Knop disabled na opslaan (geen duplicaten)
- [ ] **Nieuwe e-mail** knop → compose dialog
  - [ ] Versturen werkt
  - [ ] Verzonden email verschijnt in timeline

#### Documenten tab
- [ ] Bestandslijst laadt
- [ ] **Bestand uploaden**
  - [ ] Bestand kiezen → upload → verschijnt in lijst
  - [ ] Bestandsgrootte en type tonen
- [ ] **Bestand downloaden** → bestand downloadt
- [ ] **Preview** (👁 knop) op PDF/afbeelding/DOCX → preview modal opent
  - [ ] PDF rendert in iframe
  - [ ] DOCX wordt geconverteerd naar PDF
  - [ ] Sluiten → modal verdwijnt
- [ ] **Documenttemplate genereren**
  - [ ] Template kiezen uit dropdown
  - [ ] Genereren → document verschijnt in lijst
  - [ ] Preview van gegenereerd document werkt
- [ ] **Bestand verwijderen** → bestand verdwijnt uit lijst

#### Vorderingen tab (incasso)
- [ ] Vorderingen lijst laadt
- [ ] Nieuwe vordering toevoegen
- [ ] Bedragen correct

#### Betalingen tab (incasso)
- [ ] Betalingen lijst laadt
- [ ] Nieuwe betaling toevoegen

#### Financieel tab (incasso)
- [ ] Overzicht met hoofdsom, betaald, openstaand
- [ ] Derdengelden tonen

#### Facturen tab
- [ ] Facturen voor dit dossier zichtbaar
- [ ] Nieuwe factuur aanmaken

---

## 5. Mijn Taken (/taken)

- [ ] Alle taken voor ingelogde gebruiker laden
- [ ] Filter knoppen werken (open/voltooid/alle)
- [ ] **Nieuwe taak** knop
  - [ ] Dossier dropdown toont alle actieve dossiers
  - [ ] Titel, type, deadline, omschrijving invullen
  - [ ] Herhaling instellen
  - [ ] Opslaan → taak verschijnt in lijst
  - [ ] Taak automatisch aan ingelogde gebruiker toegewezen
- [ ] Taak voltooien werkt
- [ ] Klik op taak → navigeert naar dossier

---

## 6. Correspondentie (/correspondentie) — Ongesorteerde email wachtrij

- [ ] Ongesorteerde emails laden (niet aan dossier gekoppeld)
- [ ] Zoeken op afzender/onderwerp werkt
- [ ] **Email detail** — klik → detail panel
- [ ] **Dossier-suggesties** per email (contact-match, dossiernummer, referentie)
- [ ] **1-click koppelen** aan voorgesteld dossier
- [ ] **Handmatig zoeken** en koppelen aan dossier
- [ ] **Negeren** → email verdwijnt uit wachtrij
- [ ] **Bulk selectie** — checkboxes + selecteer alles
- [ ] **Bulk koppelen** — meerdere emails aan 1 dossier
- [ ] **Bulk negeren** — meerdere emails negeren
- [ ] **Sidebar badge** toont correct aantal ongesorteerde emails

---

## 7. Incasso (/incasso)

### 7a. Werkstroom tab (default)
- [ ] Pipeline overzicht laadt — dossiers gegroepeerd per stap
- [ ] Kolommen: checkbox, dossiernr., cliënt, wederpartij, hoofdsom, openstaand, dagen in stap
- [ ] "Zonder stap" sectie voor niet-toegewezen dossiers
- [ ] **Smart Work Queue tabs**
  - [ ] "Alle dossiers" (default)
  - [ ] "Klaar voor volgende stap (X)" — filtert correct
  - [ ] "14d verlopen (X)" — filtert correct
  - [ ] "Actie vereist (X)" — filtert correct
- [ ] **Checkboxes** — selecteer individueel + "Selecteer alle in stap"
- [ ] **Floating action bar** bij selectie
  - [ ] "Wijzig stap" → stap wijzigen dialog
  - [ ] "Verstuur brief" → pre-flight wizard → document generatie
  - [ ] "Herbereken rente" → rente herberekend
- [ ] **Pre-flight wizard** toont blockers en bevestiging
- [ ] **Sidebar badge** toont "actie vereist" count

### 7b. Stappen beheren tab
- [ ] Lijst van pipeline stappen laadt
- [ ] **Stap toevoegen** → naam, wachtdagen, briefsjabloon
- [ ] **Stap bewerken** → inline editing werkt
- [ ] **Stap verwijderen** → stap verdwijnt
- [ ] **Herordenen** (up/down knoppen) werkt
- [ ] **Briefsjabloon dropdown** per stap toont alle docx-templates
- [ ] **Seed-knop** (als geen stappen) → standaardstappen aangemaakt

---

## 8. Uren (/uren)

- [ ] Urenlijst laadt
- [ ] Uren registreren werkt
- [ ] Timer start/stop werkt
- [ ] Koppeling aan dossier werkt

---

## 9. Facturen (/facturen)

- [ ] Facturenlijst laadt
- [ ] Status labels correct (concept, verzonden, betaald, etc.)
- [ ] **Nieuwe factuur** (/facturen/nieuw)
  - [ ] Dossier kiezen
  - [ ] Regels toevoegen
  - [ ] Opslaan werkt
- [ ] **Factuur detail** (/facturen/[id])
  - [ ] Factuurgegevens laden
  - [ ] Status wijzigen werkt

---

## 10. Documenten (/documenten)

- [ ] Documentenlijst laadt (alle gegenereerde documenten)
- [ ] Zoeken/filteren werkt
- [ ] Download werkt
- [ ] Preview werkt

---

## 11. Agenda (/agenda)

- [ ] Agenda laadt
- [ ] Deadlines van taken zichtbaar
- [ ] Navigeren tussen weken/maanden werkt

---

## 12. Instellingen (/instellingen)

### 12a. Algemeen
- [ ] Kantoorgegevens bewerken
- [ ] Opslaan werkt

### 12b. E-mail tab
- [ ] **Verbind met Gmail** knop (als niet verbonden)
  - [ ] OAuth popup opent
  - [ ] Na toestemming → "Verbonden" status
- [ ] **Verbind met Outlook** knop (als niet verbonden)
  - [ ] OAuth popup opent
  - [ ] Na toestemming → "Verbonden" status
- [ ] **Ontkoppelen** → status wijzigt naar niet verbonden

### 12c. Modules
- [ ] Module toggles zichtbaar (incasso, tijdschrijven, facturatie, wwft, budget)
- [ ] Module aan/uitzetten → sidebar items verschijnen/verdwijnen
- [ ] Budget module aan → budget veld verschijnt in dossier

---

## 13. Keyboard Shortcuts (op dossier detail)

- [ ] `T` → timer start/stop
- [ ] `N` → notitie (switch naar overzicht + focus textarea)
- [ ] `D` → documenten tab
- [ ] `E` → email compose dialog
- [ ] `F` → facturen tab
- [ ] `1-9` → tab switching
- [ ] Shortcuts NIET actief bij typing in input/textarea

---

## 14. Cross-cutting checks

- [ ] Pagina refresh → geen errors, data blijft
- [ ] Lege states → nette "geen data" berichten (niet crashes)
- [ ] Loading spinners bij data ophalen
- [ ] Toast meldingen bij succes/fout acties
- [ ] Mobile responsiveness (optioneel — maar sidebar collapse)
- [ ] Auto-sync emails elke 5 minuten (check na wachten)

---

## Gevonden bugs

| # | Pagina | Beschrijving | Ernst |
|---|--------|-------------|-------|
| | | | |
| | | | |
| | | | |

---

*Gegenereerd: 23 feb 2026 — Sessie 14*
