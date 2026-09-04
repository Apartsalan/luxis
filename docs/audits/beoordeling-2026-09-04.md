# Beoordeling Luxis — 4 september 2026 (S256, Fable 5.1)

> **Bijgewerkt dezelfde middag na de eerste uitvoerronde.** Vier correcties op de ochtendversie:
> 1. **Lisanne:** het slot van 19 aug verliep binnen het uur. Zij vroeg om 13:54 een nieuw wachtwoord aan,
>    de mail ging correct de deur uit (link klopte, pagina werkt), maar de link is nooit gebruikt.
>    Opgelost: nieuw wachtwoord gezet en geverifieerd (login 200). Teller staat op 0, geen valstrik.
> 2. **"4 herhalingen per taak" op de bel is géén fout:** bewust één herinnering per taak per maand,
>    per gebruiker (sinds S242). De ruis komt van 48 taken die niemand afhandelt, niet van de herhaling.
> 3. **"Termijnen op gesloten dossiers afboeken" was een VERKEERD voorstel.** Gemeten: 15 dossiers met
>    een actieve regeling en gemiste termijnen (24 termijnen, € 11.093,54). Tien daarvan staan in Luxis
>    op "afgesloten" terwijl BaseNet zei "Bijhouden regelingen". Dat zijn échte alarmen op échte
>    regelingen. NIET afboeken. Wél: de teller kan betalingen niet zien (1 van 266 termijnen is aan een
>    betaling gekoppeld; regelingen en betalingen kwamen apart uit de import) — dus tussen die 15
>    zitten ook debiteuren die wél betaald hebben (IN100543, IN100505, IN100494). Lijst hieronder.
> 4. **Facturen-tegeltje + dossier-factuursom GEFIXT en live** (commit aeb5d91, wachter
>    `test_frontend_money_sum_guard.py`, WAARHEDEN 35 ✅). Dashboard: € 78.469,57 / 88 onbetaald.
>    Dossier IN100016: € 1.062,05 (was € 145,21).
>
> **Regelingen met gemiste termijnen — voor Lisanne om te beoordelen (Luxis-status / BaseNet-fase /
> verschuldigd tot nu / betaald rond de regeling / betaald totaal):**
> IN100535 afgesloten, Regeling treffen, € 1.948,55 / 0 / 0 · IN100515 in behandeling, € 1.005,79 / 0 / 0 ·
> IN100026 afgesloten, Bijhouden, € 1.000 / 0 / 4.300 · IN100019 afgesloten, Dagvaarding naar DW, € 1.000 / 0 / 700 ·
> IN100582 afgesloten, Stukken opgevraagd, € 600 / 0 / 0 · IN100430 afgesloten, Bijhouden, € 400 / 0 / 0 ·
> IN100329 afgesloten, Regeling treffen, € 300 / 0 / 0 · IN100305 afgesloten, € 150 / 0 / 0 ·
> IN100215 in behandeling, € 1.049,21 / 250 / 250 · IN100494 nieuw, € 2.073,17 / 1.036,58 / 1.036,58 (helft betaald) ·
> IN100345 nieuw, € 100 / 50 / 350 · IN100497 afgesloten, € 796,05 / 0 / 3.192 (vrijwel volledig betaald) ·
> IN100454 afgesloten, € 186,73 / 0 / 1.494,30 · IN100505 afgesloten, € 267,80 / 0 / 267,80 (exact betaald) ·
> IN100543 nieuw, € 216,24 / 216,25 / 216,25 (betaald, alarm onterecht).


Vraag van Arsalan: wat vind je van Luxis, wat kan beter, wat is kapot, wat missen we nog.
Alles hieronder is deze sessie gemeten op productie (database, logboeken, schermen) of in de
broncode; waar dat niet lukte staat "niet geverifieerd".

## Eerst het goede nieuws (gemeten)
- Server gezond: alle containers healthy, code = 31 juli, CI groen, nul foutmeldingen in 7 dagen logboek.
- Backup elke nacht (laatste vannacht 03:00), schijf 29% vol, Next.js-lekken van S255 dicht.
- Nachtelijke controles draaien allemaal (heartbeat-tabel: 10 jobs, laatste run vandaag).
- Mailkoppelingen werken: incasso@ en seidony@ synchroniseren elke 5 minuten, tokens verversen zichzelf.
- De geld-keten (rente, staffel, brieven = scherm) is bewaakt met 34 wachters; 1336 tests in 128 bestanden.
- Verjaring: geen enkele open vordering verjaart binnen 12 maanden.

## Het echte probleem: Luxis wordt niet gebruikt, en drie dingen houden dat in stand

**1. Lisanne is op 19 augustus buitengesloten en nooit meer teruggekomen.**
Logboek: 8 mislukte inlogpogingen op haar account tussen 13:13 en 13:15 (NL-tijd), daarna slot.
Laatste geslaagde login: 6 augustus. Sinds 1 augustus: 1 werkdag gebruik (6 aug: 5 mails, 3 stappen),
0 nieuwe dossiers, 162 van 164 meldingen ongelezen. Ondertussen werkt zij gewoon door in Outlook
(27 aug-3 sep: actieve correspondentie op IN100330 vanuit kesting@).
→ Actie Arsalan: wachtwoord met haar resetten en een half uur samen inloggen.

**2. 405 dossiers staan in Luxis op "afgesloten" terwijl ze in BaseNet "Lopend/Wacht" waren.**
Van de 568 afgesloten dossiers waren er in BaseNet maar 148 echt gereed + 15 geannuleerd. De rest
(86 "vordering betwist", 56 "B2C 4e sommatie", 40 "procederen?", 37 "voorstel dagvaarden", …) is
bij de import dichtgezet in afwachting van de fase-heropening (bekend besluit: per groep GO).
Gevolg nu: sinds 1 juli kwam op 12 van die "gesloten" dossiers echte post binnen (IN100330 alleen al
4 mails in 30 dagen, IN100128, IN100480, IN100582…) zonder pijplijn, zonder termijn, zonder taak.
Zolang dit niet gebeurt is Luxis voor Lisanne een systeem met 38 echte dossiers naast een BaseNet
met 400. Dat is de belangrijkste reden dat ze er niet in werkt.
→ Keuze Arsalan/Lisanne: heropening starten (groep voor groep, met etiket-controle zoals afgesproken).

**3. De pijplijn wacht op een klik die niet komt.**
19 dossiers wachten 29-46 dagen op hun volgende brief (6× tweede sommatie, 12× derde, 1× eerste),
concept staat klaar, taak "Te laat" sinds 26 juli. De 4-dagen-cadans uit Lisanne's werkstroom
bestaat alleen als iemand op "Uitvoeren" drukt (bewust besluit S160: assistent, geen autonomie).
Debiteuren horen dus al zes weken niets. Daarnaast staan 11 dossiers 43 dagen in "Akkoord dagvaarden"
zonder vervolgstap: daar houdt de werkstroom gewoon op.
→ Keuze: (a) dagelijkse samenvattingsmail naar Lisanne ("5 brieven wachten op jouw ja"), of
(b) hoofdpad automatisch laten lopen met alleen een stop-knop. Dit is een beslissing, geen bouwklus.

## Kapot (klein, wel echt)
- ~~**Dashboard "Open facturen € 0,00"**~~ GEFIXT (zie boven) — was: 88 vervallen facturen (€ 78.469,57) onzichtbaar.
  Het tegeltje telt alleen status "verzonden" (7 stuks, samen −€ 5.707 aan creditnota's) en telt
  bedragen als tekst op in plaats van als getal. Bron: `OpenInvoicesCard` in het dashboard.
- **Dashboard "€ 13.690,26 ontvangen"** is de som van alle betalingen ooit op de 52 actieve dossiers,
  niet "deze maand" (deze maand: € 0). Het etiket suggereert iets anders dan het cijfer.
- **Taaktekst bevriest**: taak zegt "staat 4 dagen in stap Tweede sommatie" terwijl het er 44 zijn.
- **Mail met dossiernummer mét spatie** ("Dossier IN 100292") wordt niet gekoppeld. Klein gat in de matcher.

## Ruis die het gebruik ontmoedigt
- **Bel: 425 ongelezen meldingen**, waarvan 173 "deadline verlopen" (4 herhalingen per taak) en
  48 "termijn te laat" — 24 van de 32 termijn-meldingen in augustus gaan over afgesloten dossiers
  (bewust zo gebouwd volgens de code, maar het gevolg is dat niemand de bel nog leest).
- **Mail-lijst toont Arsalans privé-post** (Hetzner-facturen, Philips Hue-nieuwsbrieven, Microsoft)
  tussen de dossiermail, omdat seidony@ als kantoormailbox meesynct. 63 "ongesorteerd".
- **Lisanne's eigen mailbox (kesting@) is niet gekoppeld.** Alleen incasso@ en seidony@. Haar
  directe correspondentie zie je alleen als incasso@ in de cc staat (4 mails sinds juli).
- **14 testdossiers (2026-00006…00019) staan tussen de echte** in Incasso, Follow-up en het
  dashboard ("52 actieve dossiers" = 38 echt + 14 test; "TEST Debiteur Fable-review B.V." met een
  echte Uitvoeren-knop).
- **143 mail-classificaties wachten op beoordeling** (70× "niet gerelateerd" uit juli), 26 AI-concepten
  gegenereerd en nooit bekeken, 3 intake-verzoeken sinds 19 aug onbeoordeeld.
- Dashboard zeurt over "geen uren geschreven" terwijl Kesting Legal geen uren registreert (0 ooit).

## Gebouwd maar ongebruikt (niet slopen, wel weten)
Uren (0), derdengelden (0), agenda (1 afspraak), facturen (alleen import, laatste 17 juli),
Exact Online (0 koppelingen), KYC. Consistent met de architectuurkaart ("slapend maar af").

## Wat mist (functioneel, voor een incassopraktijk)
1. **Gerechtelijke fase na "Akkoord dagvaarden"**: dagvaarding, rol, vonnis, executie/deurwaarder.
   De velden bestaan op het dossier (rechtbank, rolnummer, procedure_phase) maar er is geen werkstroom;
   11 dossiers staan er stil.
2. **Stuiting van verjaring** (bekend ❓): sommaties bevatten een stuitingsclausule, de teller weet dat niet.
3. **Cliënt-rapportage**: opdrachtgevers (Collect 1, Incassocenter) mailen "wat was de hele vordering";
   een statusbericht per dossier bestaat als AI-concept maar niet als vaste, klikbare rapportage.
4. **Regelingen op gesloten dossiers**: 84 termijnen "te laat", vrijwel allemaal op afgesloten dossiers
   uit de import; niemand ruimt ze op en ze voeden de bel.

## Wat ik NIET zou doen
Nieuwbouw. De koersregel klopt. De vier open ⚠️'s (tarieven-alarm, sjabloonmenu-wachter,
sleutelwissel, kennisregels-admin) zijn netjes maar veranderen niets aan bovenstaande.

## Voorstel volgorde (Arsalan kiest)
1. Lisanne weer binnen (wachtwoord, half uur samen) — vandaag/morgen, geen code.
2. Besluit over de pijplijn-cadans (samenvattingsmail of automatisch) — één gesprek.
3. Opruimronde ruis: testdossiers verbergen op prod, privé-mail uit de lijst, bel-herhalingen dempen,
   termijnen op gesloten dossiers afboeken — één sessie, allemaal klein.
4. Dashboard-tegeltje facturen fixen (30 minuten) + matcher-spatie.
5. Fase-heropening 405 dossiers, groep voor groep, met GO per groep.
6. Daarna pas de gerechtelijke fase ontwerpen.

## Niet geverifieerd
- Of Lisanne zelf achter de 8 inlogpogingen zat (IP is de interne proxy).
- Hoe de bel "4 herhalingen per taak" precies ontstaat (weekritme vermoed, niet in code nagelezen).
- Sentry-dashboard niet bekeken (geen toegang vanuit deze sessie).
