# S240 — Testronde 2: slordige gebruiker + klik-ronde als Lisanne

**Vooraf (discipline S239):** per scenario stond het verwachte resultaat er vóór de
uitvoering. Vondsten in drie bakken: 🅰 fout (fixen, rode test eerst) · 🅱 ergernis
(fixen) · 🅲 gemis (voorstel-lijst). Elke prod-mutatie teruggedraaid + nageteld.
Testterrein: wegwerpdossier 2026-00021 (aangemaakt → volledig gewist, nageteld 0) +
testdossier 2026-00006 (alleen gelezen). Niets verstuurd.

**Context:** direct ná de S240-bouw (bak-melding + belofte-bewaking) en de
Fable-review daarop. Ronde gedraaid op Fable, na modelwissel door Arsalan.

---

## Bril 1 — De slordige gebruiker (prod-API, wegwerpdossier 2026-00021)

| # | Scenario | Verwacht | Resultaat |
|---|----------|----------|-----------|
| G1 | Dossier aanmaken zonder verplichte velden | nette weigering, geen half dossier | ✅ 422 met veldnamen (client + openingsdatum verplicht) |
| G2 | Vordering 0 / negatief / "1.234,56" | geweigerd, nooit stil verkeerd | ✅ 3× 422; komma-notatie geweigerd i.p.v. misgelezen. UI is bovendien een getalveld (browser vangt NL-notatie af) |
| G3 | Beschrijving van 1000 tekens | geweigerd of afgekapt, geen 500 | ✅ 422 (max 500 tekens) |
| G4 | Betaling 0 / negatief / veel te hoog | geweigerd met NL-melding | ✅ 422 / 422 / 400 "hoger dan het openstaande bedrag van €140.57" (bedrag klopte exact) |
| G5 | Dubbelklik: 2× dezelfde deelbetaling gelijktijdig | eerlijk vaststellen | 🅲 beide 201 → 2 betalingen geboekt. UI-knop disable't tijdens verzenden (dempt het), maar echte dubbelklik/2 tabs boekt dubbel. → voorstel-lijst |
| G6 | Regeling: som≠totaal / 0 termijnen / negatieve termijn | geweigerd | ✅ 400 met NL-melding / 422 / 422 |
| G7 | Mail naar leeg / ongeldig adres | geweigerd vóór verzending | ✅ 2× 422, o.a. "Ongeldig e-mailadres: 'geen-apenstaart'" |
| G8 | Dossier verwijderen met vordering+betalingen erop | geen crash | ✅ 204; vorderingen blijven actief achter = bekend S239-voorstel 6 (cascade), niets nieuws |

## Bril 2 — Klik-ronde als Lisanne (Playwright tegen prod, ingelogd als seidony@)

| # | Scenario | Resultaat |
|---|----------|-----------|
| K1 | Login + dashboard + taken + mail (desktop) | ✅ Alles laadt; tellers kloppen exact (Mail-badge 81 = databasetelling; ongesorteerd-kaart 81). Bekende vervuiling zichtbaar: 61 taken (40+ oude test-taken → opruimronde), 112 meldingen (voorstel 3 bundeling) |
| K2 | Doorklik ongesorteerd-filter (nieuw S240) | ✅ ná extra fix — zie vondst 1. Dashboard-kaart → Ongesorteerd-tab ✓; melding in de bel → tab wisselt ook als de Mail-pagina al open staat ✓ (beide live geklikt) |
| K3 | Dossier 2026-00006: kop, stap, tabs, cijfers | ✅ Stap "Tweede sommatie, 7 dagen, volgende: Derde"; €100 + €0,57 rente + €40 BIK = €140,57 — overal consistent én handmatig nagerekend (52 dagen wettelijke rente) |
| K4 | Betaling boeken via UI | ➖ formulier aanwezig (Financieel-tab, "Betaling registreren"); niet geboekt — het boekpad is uitputtend gedekt via G4/G5 + S239-liveproeven; geen extra prod-mutatie |
| K5 | Mobiel 390×844: dashboard, mail, taken | ✅ Alles leesbaar/klikbaar, geen horizontale overloop; mobiele balk met badges; Ongesorteerd-doorklik werkt ook mobiel (screenshots s240-mobiel-*.png) |
| K6 | Meldingen-bel: lijst + nieuw meldingtype | ✅ Nieuw type toont met eigen label/icoon; klik werkt (zie K2); 0 consolefouten in de hele ronde |

## Vondsten

| # | Bron | Bak | Wat | Status |
|---|------|-----|-----|--------|
| 1 | K2 | 🅰 | Melding-doorklik naar exact dezelfde URL (na eerdere doorklik + handmatige tabwissel) deed niets — de pagina zag de navigatie niet. Wortel: het filter bleef in de URL plakken. | GEFIXT (`6192ac3`): handmatige tabwissel maakt de URL weer kaal; live herbeklikt en bewezen |
| 2 | G5 | 🅲 | Dubbelklik/2 tabs kan een deelbetaling dubbel boeken (geen dubbel-indienings-slot; volbetaald-poort S239 vangt alleen het teveel). | voorstel-lijst |
| 3 | K1 | — | Ongesorteerde bak bevat veel reclame/Hetzner/oude testmails (81 stuks) — schonen hoort bij de opruimronde met Lisanne; de nieuwe melding geldt alleen NIEUWE binnenkomers, dus de oude 81 spammen niet. | opruimronde |

**Bijvangst (géén testdata, echt):** debiteur Onbevreesd (IN100592, Zwartbol) mailde
vanochtend 08:42 opnieuw, nu mét dossiernummer → automatisch gekoppeld, beoordeeld
als juridisch verweer (0.75, vertegenwoordiging). Ligt op het dossier, wacht op
behandeling — niets mee gedaan (echte debiteur).

## Eindstand

Bril 1: 8/8 gedraaid — 7 ✅, 1 gemis (dubbelklik-betaling → voorstel).
Bril 2: 6/6 gedraaid — 1 fout gevonden en direct gefixt + live herbewezen (vondst 1).
Wegwerpdossier 2026-00021 volledig gewist (natelling 0); klikproef-melding gewist
(natelling 0); geen enkele mail verstuurd.
