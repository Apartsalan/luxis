# P1 Incasso Flow — Smoke Test Checklist

Handmatige end-to-end verificatie van de volledige batch brief + email flow.
Voer dit uit na deployment op de VPS of in de dev omgeving.

## Voorwaarden

- [ ] Applicatie draait (frontend + backend + db)
- [ ] Email provider verbonden (Gmail of Outlook via /instellingen)
- [ ] Pipeline stappen bestaan (Aanmaning, Sommatie, etc.)
- [ ] Minimaal 1 incasso dossier met wederpartij die een emailadres heeft

## Test 1: Batch Brief Genereren (zonder email)

1. [ ] Ga naar `/incasso` (Werkstroom tab)
2. [ ] Selecteer 1 dossier in de "Aanmaning" kolom
3. [ ] Floating action bar verschijnt met "Verstuur brief" knop
4. [ ] Klik "Verstuur brief"
5. [ ] PreFlightDialog opent met correcte telling (Geselecteerd: 1, Gereed: 1)
6. [ ] Zet email toggle UIT
7. [ ] Klik "Uitvoeren (1 dossier)"
8. [ ] Toast verschijnt: "1 document gegenereerd"
9. [ ] Dossier is doorgeschoven naar "Sommatie" kolom
10. [ ] Ga naar Taken pagina → aanmaning-taak staat op "afgerond"

## Test 2: Batch Brief + Email Verzenden

1. [ ] Ga naar `/incasso`
2. [ ] Selecteer 1 dossier met wederpartij die emailadres heeft
3. [ ] Klik "Verstuur brief"
4. [ ] PreFlightDialog toont "E-mail gereed: 1"
5. [ ] Email toggle staat AAN
6. [ ] Klik "Genereer en verstuur (1 dossier)"
7. [ ] Toast verschijnt: "1 document gegenereerd, 1 e-mail verzonden"
8. [ ] Check je inbox (of de inbox van de wederpartij): email ontvangen?
9. [ ] Email heeft PDF als bijlage?
10. [ ] PDF bevat correcte zaakgegevens (zaaknummer, bedragen, datums)?
11. [ ] In het dossier → Correspondentie tab: uitgaande email zichtbaar?

## Test 3: Batch met Meerdere Dossiers

1. [ ] Selecteer 3+ dossiers in dezelfde stap
2. [ ] Klik "Verstuur brief" → PreFlightDialog toont correct aantal
3. [ ] Bevestig → toast toont "3 documenten gegenereerd, X e-mails verzonden"
4. [ ] Alle dossiers doorgeschoven naar volgende stap
5. [ ] Alle taken op "afgerond"

## Test 4: Edge Cases

1. [ ] Selecteer een dossier ZONDER wederpartij emailadres
   - [ ] PreFlightDialog toont "E-mail geblokkeerd: 1" met reden
   - [ ] Brief wordt WEL gegenereerd, email NIET verzonden
2. [ ] Selecteer een dossier met status "betaald"
   - [ ] "Wijzig stap" → PreFlightDialog toont "Geblokkeerd: 1"
3. [ ] Selecteer een dossier zonder pipeline stap
   - [ ] "Verstuur brief" → PreFlightDialog toont "Zonder stap: 1"

## Test 5: Deadline Kleuren

1. [ ] Dossier net toegewezen aan stap → groene dot (wachtperiode)
2. [ ] Dossier langer dan min_wait_days in stap → oranje dot (klaar voor actie)
3. [ ] Dossier langer dan max_wait_days → rode dot (te laat)
4. [ ] Dossier zonder stap → grijze dot

## Test 6: Queue Filters

1. [ ] "Alle dossiers" tab toont alle incasso dossiers
2. [ ] "Klaar voor volgende stap" toont alleen dossiers voorbij de wachtperiode
3. [ ] "14d verlopen" toont dossiers in eerste stap die > 14 dagen oud zijn
4. [ ] "Actie vereist" combineert bovenstaande + ongeassigneerde dossiers
5. [ ] Badge counts kloppen met de gefilterde resultaten

## Resultaat

- [ ] **PASS** — Alle checks groen
- [ ] **FAIL** — Noteer welke checks faalden + foutmelding/screenshot

Datum: ___________
Getekend: ___________
