**START DEZE SESSIE MET:** `claude --dangerously-skip-permissions` in de terminal. Dit geeft Claude volledige toegang zonder dat je elke actie hoeft te accepteren.

---

Sessie 105 — Uitgebreide End-to-End QA (alle wijzigingen sessie 90-103b)
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (secties: bugs, AI-UX, DF2, CQ, SEC) en SESSION-NOTES.md (sessie 90 t/m 104). Geef compacte samenvatting van ALLE wijzigingen die getest moeten worden."

## Taak

Dit is een UITGEBREIDE QA sessie. Test ALLES wat in sessies 90-103b is gebouwd/gefixt op de LIVE productieomgeving: https://luxis.kestinglegal.nl

Login: seidony@kestinglegal.nl (wachtwoord staat in memory)

**BELANGRIJK:**
- Test op de LIVE site via Playwright browser (NIET lokaal)
- Maak screenshots van ALLES
- Bij ELKE test: noteer PASS ✅ of FAIL ❌ met beschrijving
- Bij FAIL: maak een screenshot + beschrijf exact wat er misgaat
- Schrijf de resultaten naar `docs/qa/QA-SESSION-105.md`
- Sla quality checks (lint/build/pytest) over — dit is een FUNCTIONELE test

---

### BLOK 1: Login & Beveiliging (sessie 90-91)

**1.1 Login flow**
- [ ] Login pagina laadt correct (gradient achtergrond, dot grid, moderne styling)
- [ ] Login met correcte credentials werkt
- [ ] Login met verkeerd wachtwoord toont foutmelding
- [ ] Na 5x verkeerd wachtwoord: account lockout melding (SEC-20)
- [ ] Wacht 15 min of reset, login werkt weer

**1.2 JWT & Token handling**
- [ ] Na login: token wordt opgeslagen (check via browser devtools → localStorage/sessionStorage)
- [ ] Navigatie naar alle pagina's werkt zonder 401 errors
- [ ] Ververs de pagina (F5) → blijft ingelogd
- [ ] Token-store centraliteit: geen directe localStorage calls meer in console

**1.3 Security headers**
- [ ] Open devtools → Network → check response headers van de site
- [ ] X-Content-Type-Options: nosniff aanwezig
- [ ] X-Frame-Options aanwezig
- [ ] Content-Security-Policy aanwezig (geen unsafe-eval)

---

### BLOK 2: Dashboard (sessie 97, 100, 102)

**2.1 KPI-kaarten**
- [ ] Dashboard laadt met KPI-kaarten bovenaan
- [ ] Kaarten hebben gradient icoon-achtergronden + gekleurde shadows
- [ ] Hover over kaart → lift effect (subtle shadow vergroting)
- [ ] Relaties-kaart toont "X nieuw deze maand" (NIET "dossiers afgesloten")

**2.2 AI Widget (AI-UX-07)**
- [ ] Als er pending AI classificaties zijn: AI widget verschijnt op dashboard
- [ ] Widget toont pending counts + top 3 classificaties
- [ ] Confidence labels correct (Aanbevolen/Mogelijk/Onzeker met juiste kleuren)
- [ ] Links in widget navigeren naar juiste pagina's
- [ ] Als er GEEN pending items zijn: widget verschijnt NIET

---

### BLOK 3: Sidebar (sessie 97-98)

- [ ] Sidebar heeft sectiescheiding: Overzicht / Beheer / Financieel / Systeem
- [ ] Labels zijn zichtbaar en correct
- [ ] Incasso staat onder BEHEER (niet Financieel)
- [ ] Sidebar collapse werkt (klik op collapse knop)
- [ ] Na collapse: iconen nog zichtbaar, labels verborgen
- [ ] Hover op collapsed item → tooltip met label

---

### BLOK 4: Relaties (sessie 90-91, 93, 98)

**4.1 Relaties lijst**
- [ ] Navigeer naar Relaties
- [ ] Tabel laadt met data
- [ ] Tabel is responsive: verklein browser → overflow-x-auto werkt, geen afgebroken layout
- [ ] Sorteerkolommen werken (klik op header)
- [ ] Zoekfunctie werkt
- [ ] EmptyState component verschijnt bij lege zoekresultaten

**4.2 Relatie detail**
- [ ] Klik op een relatie → detailpagina laadt
- [ ] Alle tabs zichtbaar en klikbaar

**4.3 Algemene Voorwaarden per cliënt (AI-UX-11)**
- [ ] Op relatie detailpagina: "Algemene Voorwaarden" sectie zichtbaar
- [ ] Upload een test PDF als AV bestand
- [ ] Na upload: bestandsnaam verschijnt
- [ ] Download knop werkt
- [ ] Verwijder knop werkt
- [ ] Bij relatie ZONDER AV: upload-prompt zichtbaar

**4.4 Input sanitization (SEC-22)**
- [ ] Maak een nieuwe relatie aan met `<script>alert('xss')</script>` in de naam
- [ ] Script tag wordt NIET uitgevoerd, tekst wordt wel opgeslagen (gesanitized)

---

### BLOK 5: Zaken/Dossiers (sessie 90-103)

**5.1 Zakenlijst**
- [ ] Navigeer naar Zaken
- [ ] Tabel laadt correct met data
- [ ] Status badges met kleurcodering zichtbaar
- [ ] Responsive tabel werkt

**5.2 Dossier aanmaken — Wizard**
- [ ] Klik "Nieuw dossier"
- [ ] Wizard stap 1: basisgegevens (cliënt, tegenpartij, type zaak)
- [ ] GEEN rentetype veld in stap 1 (DF2-05: verplaatst naar stap 3)
- [ ] Wizard stap 2: betrokkenen toevoegen
- [ ] Bij nieuwe betrokkene: contactdetails STANDAARD OPEN (DF2-06)
- [ ] Wizard stap 3: financiële details
- [ ] Rentetype veld IS HIER aanwezig (wettelijke rente / handelsrente / contractueel)
- [ ] Bij "contractueel": extra velden verschijnen (tarief, samengesteld ja/nee)
- [ ] Wizard voltooien → dossier wordt aangemaakt

**5.3 Dossier detail**
- [ ] Open het aangemaakte dossier
- [ ] DossierHeader: pipeline step dropdown zichtbaar (DF2-09)
- [ ] Wijzig pipeline stap via dropdown → update direct
- [ ] Alle 7+ tabs laden zonder errors

**5.4 DetailsTab — Bewerken**
- [ ] Klik op bewerk-knop in DetailsTab
- [ ] Rentetype IS bewerkbaar (BUG-64 fix)
- [ ] Wijzig rentetype → opslaan → waarde is geüpdatet
- [ ] Contractueel tarief en samengesteld vinkje ook bewerkbaar

**5.5 Uren tab**
- [ ] Voeg een uurregistratie toe
- [ ] Uurtarief wordt automatisch ingevuld vanuit default (BUG-60 fix)
- [ ] Bedrag wordt correct berekend (uren × tarief)
- [ ] EmptyState verschijnt bij lege uren

**5.6 Documenten tab**
- [ ] Upload een document
- [ ] Document verschijnt in lijst
- [ ] Download werkt
- [ ] EmptyState bij lege documenten

**5.7 Activiteiten tab**
- [ ] Activiteiten tijdlijn laadt
- [ ] AI-activiteiten (type ai_action/automation) tonen paarse AI badge (AI-UX-06)
- [ ] EmptyState bij lege activiteiten

**5.8 Betalingen tab**
- [ ] Voeg een betaling toe
- [ ] Check toerekening: kosten → rente → hoofdsom (art. 6:44 BW)
- [ ] EmptyState bij lege betalingen

**5.9 Vorderingen tab**
- [ ] Vorderingen worden correct weergegeven
- [ ] Bedragen zijn correct geformateerd (geen NaN — UX-20 fix)
- [ ] EmptyState bij lege vorderingen

**5.10 AI Suggestion Banner (AI-UX-04)**
- [ ] Als er een pending classificatie is: banner verschijnt bovenaan dossierpagina
- [ ] Banner is inklapbaar
- [ ] Akkoord/Afwijzen knoppen werken
- [ ] Na actie: banner verdwijnt

---

### BLOK 6: Correspondentie (sessie 98-103b)

**6.1 Correspondentie pagina (globaal)**
- [ ] Navigeer naar Correspondentie
- [ ] Emails laden met gekleurde linkerrand (blauw = in, groen = uit)
- [ ] Date grouping met sticky headers zichtbaar
- [ ] Zoekfunctie werkt

**6.2 Correspondentie tab op dossier**
- [ ] Open een dossier met emails
- [ ] Emails correct geladen
- [ ] AI classificatie badges zichtbaar op email-rijen (AI-UX-01)
- [ ] Confidence kleurcodering correct (groen/geel/rood)
- [ ] "Wacht op review" indicator bij pending classificaties (AI-UX-02)
- [ ] Klik op email → detail panel opent
- [ ] Bijlagen zichtbaar en downloadbaar

**6.3 Email Compose (DF2-01) — KRITIEKE TEST**
- [ ] Klik "Nieuwe email" of compose knop op dossier
- [ ] Email compose dialog opent (680px breed)
- [ ] Template selector aanwezig en werkt
- [ ] Kies een template → inhoud wordt pre-filled
- [ ] Bijlage dropdown: "Uit dossier" en "Uploaden" opties
- [ ] Selecteer een dossierbestand als bijlage (checkboxes)
- [ ] Upload een bijlage
- [ ] Attachment badges verschijnen
- [ ] "Open in Outlook" knop aanwezig (NIET "Versturen")
- [ ] Klik "Open in Outlook" → draft wordt aangemaakt in Outlook
- [ ] Check Outlook: draft staat er met juiste ontvangers, onderwerp, body en bijlagen

**6.4 AI Concept knop (AI-UX-09/13/14)**
- [ ] Op correspondentie tab: "AI Concept" knop zichtbaar
- [ ] Klik → AI genereert een concept-antwoord
- [ ] Concept verschijnt met dossiercontext (emails, vorderingen, betalingen)
- [ ] Concept kan bewerkt worden voordat het verstuurd wordt

---

### BLOK 7: Incasso Pipeline (sessie 98, 100, 103)

**7.1 Pipeline overzicht**
- [ ] Navigeer naar Incasso
- [ ] Pipeline tabel laadt met alle stappen
- [ ] Lege stappen standaard ingeklapt (opacity + chevron toggle)
- [ ] "Zonder stap" sectie heeft amber warning-styling
- [ ] Uitklappen van sectie werkt
- [ ] AI badge zichtbaar op dossiers met pending classificatie (AI-UX-05)

**7.2 Inline stap bewerken**
- [ ] Klik op pencil icon naast een stap (DF2-02)
- [ ] Bewerkformulier verschijnt inline
- [ ] Wijzig stap → opslaan → stap is geüpdatet

**7.3 Incasso brieven als HTML email (DF2-08)**
- [ ] Verstuur een incasso actie (aanmaning, sommatie, 14-dagenbrief)
- [ ] Check: email wordt verstuurd met HTML body (Kesting Legal branding: logo, navy/goud)
- [ ] NIET als plain text of PDF bijlage (behalve dagvaarding + renteoverzicht)

---

### BLOK 8: Facturatie (sessie 101-103)

**8.1 Facturenlijst**
- [ ] Navigeer naar Facturen
- [ ] Tabel laadt correct

**8.2 Nieuwe factuur — BTW per regel (DF2-03) — KRITIEKE TEST**
- [ ] Klik "Nieuwe factuur"
- [ ] Voeg meerdere regels toe
- [ ] Per regel: BTW dropdown aanwezig (21% / 9% / 0%)
- [ ] Stel regel 1 in op 21%, regel 2 op 0%
- [ ] Check subtotaal: correct per tariegroep
- [ ] Check BTW: alleen berekend over de 21% regels
- [ ] Check totaal: subtotaal + BTW correct
- [ ] Sla op en open de factuur
- [ ] PDF preview: BTW uitsplitsing per tariegroep zichtbaar

**8.3 Voorschotfactuur — Uren auto-berekening (DF2-04)**
- [ ] Maak een factuur met type "voorschot"
- [ ] Importeer uren → bedrag wordt auto-berekend (uren × uurtarief)
- [ ] Bedrag correct weergegeven (geen `toFixed` error — BUG-61 fix)

**8.4 Incasso facturatie (IncassoKostenPanel)**
- [ ] Open een incasso dossier
- [ ] Ga naar factuur aanmaken
- [ ] IncassoKostenPanel verschijnt (ALLEEN bij incasso dossiers)
- [ ] BIK quick-add knop: voegt BIK bedrag toe als factuurregel
- [ ] Rente quick-add: voegt vervallen rente toe
- [ ] Provisie quick-add: voegt provisie toe
- [ ] "Al gefactureerd" waarschuwing verschijnt indien van toepassing

**8.5 Provisie-instellingen**
- [ ] Op dossier: ProvisieSettingsSection zichtbaar
- [ ] Berekeningsbasis toggle werkt (geïnd bedrag / totale vordering)

---

### BLOK 9: Taken (sessie 99-100)

- [ ] Navigeer naar Taken
- [ ] AI-secties hebben paarse "AI" badge op headers (AI-UX-03)
- [ ] Lege state tekst zichtbaar bij lege AI-secties

---

### BLOK 10: Intake/Classificatie (sessie 100)

**10.1 Intake pagina**
- [ ] Navigeer naar Intake
- [ ] Pending classificaties worden getoond
- [ ] Confidence labels correct (Aanbevolen/Mogelijk/Onzeker — AI-UX-08)
- [ ] Klik op een classificatie → detailpagina

**10.2 Classificatie detail**
- [ ] Detail pagina laadt
- [ ] Confidence weergave met juiste labels en kleuren
- [ ] Akkoord/Afwijzen knoppen werken

---

### BLOK 11: Email Matching & Sync (sessie 101-102) — KRITIEKE TEST

**11.1 Thread matching (BUG-63 fix)**
- [ ] Check bestaande emails: zijn ze aan het JUISTE dossier gekoppeld?
- [ ] Geen emails bij verkeerde dossiers
- [ ] Bounce/NDR emails: worden ze correct als bounce gemarkeerd (niet aan dossier gekoppeld)?

**11.2 Matching methoden**
- [ ] Email met dossiernummer in onderwerp → correct gekoppeld
- [ ] Email van bekende contactpersoon → correct gekoppeld aan diens dossier
- [ ] Email met case reference → correct gekoppeld
- [ ] Ongelinkte emails verschijnen in "Ongesorteerd" wachtrij

**11.3 OAuth & Sync**
- [ ] Email sync draait (check via backend logs of sync status)
- [ ] Geen OAuth token errors (Fernet key derivatie fix uit sessie 102)

---

### BLOK 12: Instellingen (sessie 101)

- [ ] Navigeer naar Instellingen
- [ ] Weergave tab: GEEN Dark mode / Systeem knoppen meer (BUG-62 fix)
- [ ] Inline form validatie werkt (UX-15)

---

### BLOK 13: AI Features — Functionele Test (sessie 99-100)

**13.1 Factuur parsing (DF2-07)**
- [ ] Upload een factuur PDF (bij voorkeur een scan/afbeelding)
- [ ] AI extraheert gegevens correct
- [ ] Bij scan: fallback naar Claude native PDF analyse werkt

**13.2 Dossier classificatie**
- [ ] Maak een nieuw dossier aan
- [ ] AI classificeert het dossier
- [ ] Classificatie verschijnt met confidence score

**13.3 AI Draft (AI-UX-09)**
- [ ] Op een dossier met correspondentie: klik "AI Concept"
- [ ] AI genereert een concept met dossiercontext
- [ ] Concept is bruikbaar en bevat relevante info uit het dossier

---

### BLOK 14: Financiële Berekeningen — REKENCONTROLE

**14.1 WIK-staffel (BIK berekening)**
- [ ] Dossier met hoofdsom €1.000 → BIK = €150 (15% van eerste €2.500)
- [ ] Dossier met hoofdsom €3.000 → BIK = €375 + €50 = €425? NEE: €2.500×15% + €500×10% = €375 + €50 = €425. Nee wacht: €2.500×15% = €375, €500×10% = €50 → totaal €425
- [ ] Dossier met hoofdsom €100 → BIK = €40 (minimum)
- [ ] Check of BTW correct wordt toegepast als schuldeiser niet BTW-plichtig is

**14.2 Rente berekening (CQ-14)**
- [ ] Check rente op een dossier met bekende verzuimdatum
- [ ] Compound interest: rente kapitaliseert op verjaardag verzuimdatum (NIET 1 januari)
- [ ] Bedragen correct afgerond (2 decimalen, ROUND_HALF_UP)

**14.3 Betalingstoerekening (art. 6:44 BW)**
- [ ] Voeg deelbetaling toe op dossier met kosten + rente + hoofdsom
- [ ] Toerekening: eerst kosten → dan rente → dan hoofdsom
- [ ] Restant correct berekend

---

### BLOK 15: UI/UX Kwaliteit — Visuele Inspectie

**15.1 Typografie & Design**
- [ ] Inter font correct geladen op alle pagina's
- [ ] Teksten goed leesbaar, geen font-fallback (serif)
- [ ] Microinteracties: hover effects op buttons, links, kaarten

**15.2 Empty States**
- [ ] Test elke tab op een leeg dossier: EmptyState component verschijnt (niet lege tabel)
- [ ] Tabs: Uren, Betalingen, Vorderingen, Documenten, Activiteiten, Correspondentie, Facturen

**15.3 Responsive design**
- [ ] Verklein browser naar tablet-breedte → layout past aan
- [ ] Tabellen: hidden columns op kleine schermen
- [ ] Sidebar collapse bij kleine schermen

**15.4 Toast notificaties**
- [ ] Bij succesvol opslaan: toast melding verschijnt
- [ ] Bij error: rode toast met foutmelding
- [ ] Error handling: geen silent failures (CQ-12 fix)

**15.5 Inline validatie (UX-15)**
- [ ] Op factuur form: valideer verplichte velden
- [ ] Op email compose: valideer ontvangers
- [ ] Op betaling form: valideer bedrag
- [ ] Op instellingen: valideer formaat

---

### BLOK 16: Health & Infra check

- [ ] GET https://luxis.kestinglegal.nl/api/health → 200 OK
- [ ] SSH naar VPS: `docker compose ps` → alle 5 containers "healthy"
- [ ] Check disk space: `df -h` → voldoende ruimte
- [ ] Check uptime cron: `crontab -l` → health check elke 5 min

---

## Resultaten opslaan

Schrijf ALLE resultaten (PASS/FAIL per item) naar: `docs/qa/QA-SESSION-105.md`
Format:
```
# QA Sessie 105 — 25 maart 2026
## Samenvatting: X/Y PASS, Z FAIL
### BLOK 1: Login & Beveiliging
- ✅ 1.1 Login pagina styling — correct
- ❌ 1.2 Account lockout — melding verschijnt niet [screenshot: qa-105-lockout.png]
...
```

Bij FAILS: maak screenshots en beschrijf exact wat er misgaat. Maak een BUG-entry in de resultaten.

## Constraints (wat NIET doen)
- GEEN code wijzigen — dit is alleen testen
- GEEN lint/build/pytest draaien — alleen functionele tests op productie
- GEEN nieuwe features bouwen
- GEEN worktrees gebruiken
- Als iets FAIL is: ALLEEN documenteren, niet fixen

## Na afloop
- Commit `docs/qa/QA-SESSION-105.md` + eventuele screenshots
- Push naar main
- Geef samenvatting: hoeveel PASS, hoeveel FAIL, welke FAILS kritiek zijn
