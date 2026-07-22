# S239 — Scenario-nachtronde "Een week uit het leven van Lisanne"

**Doel:** 32 realistische scenario's doorlopen alsof Lisanne (advocaat, geen techneut)
ermee werkt. Per scenario vooraf: wat er hóórt te gebeuren + hoe ik dat controleer.
Vondsten in drie bakken: (a) kapot → direct fixen, (b) klein/verwarrend → direct fixen,
(c) ontbrekende functie → voorstel-lijst voor Arsalan.

**Spelregels (afgesproken met Arsalan 22-7 avond):** echte AI-aanroepen mogen; niets naar
echte debiteuren; testdossiers = 2026-00006 (mail → Arsalans gmail), 2026-00007, 2026-00019;
elke prod-mutatie wordt teruggedraaid + nageteld; elke echte fout krijgt eerst een rode
wachter-test; fixes klein houden (fouten + ergernissen, géén features).

**Statuslegenda:** ⬜ nog niet | ✅ goed | 🅰 kapot | 🅱 ergernis | 🅲 gemis (lijst) | ➖ droog doorlopen

---

## A. Lisanne's gewone werkdag

**A1. Ochtendronde — "wat moet ik vandaag doen?"** ⬜
Verhaal: Lisanne opent Luxis om 9:00. Verwacht: Taken-pagina + meldingen + follow-up
geven samen één kloppende werklijst; geen dubbele, stale of onbegrijpelijke taken.
Check: prod-lezing taken/meldingen/adviezen van vandaag; kruisverband (elke taak herleidbaar).

**A2. Nieuwe zaak aanmaken vanaf een factuur.** ⬜
Verhaal: cliënt stuurt een onbetaalde factuur; Lisanne maakt dossier aan (of intake-AI doet het).
Verwacht: dossier compleet — partijen, vordering, verzuimdatum, rentetype (handels/wettelijk),
b2b/b2c goed gezet; bedragen Decimal-precies. Check: testdossier aanmaken via app-API,
velden nameten, daarna verwijderen.

**A3. Eerste sommatie b2b — kloppen de cijfers op de cent?** ⬜
Verhaal: ze verstuurt de eerste sommatie. Verwacht: hoofdsom = som vorderingen; rente t/m
vandaag (2%/mnd samengesteld of wettelijk, wat het dossier zegt); BIK volgens staffel;
brief toont alles; dossier schuift door na verzending. Check: testdossier, brief genereren
(niet naar echte debiteur), bedragen onafhankelijk narekenen, staphistorie; terugdraaien.

**A4. B2C-dossier — de wettelijke bescherming.** ⬜
Verwacht: 14-dagenbrief verplicht vóór BIK; WIK-bijlage bij particulier/eenmanszaak/VOF;
b2c-zaak wordt nooit richting faillissementsstappen geduwd (S234-guard). Check: bestaand
b2c-testdossier of droog + guard-tests nalopen; gates in code + 1 live poging die geweigerd hoort te worden.

**A5. Debiteur belt — snel het dossier erbij.** ⬜
Verhaal: telefoon, "u schreef mij over factuur X". Verwacht: zoeken op naam/nummer werkt
vlot; dossierkop toont actuele tussenstand (openstaand incl. rente van vandaag) die ze
kan voorlezen. Check: prod read-only zoeken; tussenstand narekenen tegen eigen berekening.

**A6. "Ik heb gisteren al betaald."** ⬜
Verwacht: Lisanne kan een betaling boeken; verdeling kosten→rente→hoofdsom (art. 6:44 BW);
tussenstand direct bijgewerkt. Check: testdossier betaling boeken, verdeling narekenen, terugdraaien.

**A7. Deelbetaling — restant klopt overal.** ⬜
Verwacht: restant in dossierkop, in de volgende brief en in het follow-up-advies is
hetzelfde bedrag. Check: testdossier deelbetaling + brief genereren + narekenen; terugdraaien.

**A8. Telefonische betalingsregeling vastleggen.** ⬜
Verwacht: flexibel schema in te voeren (S235); zaak naar 'Bijhouden regeling'; bij
wanbetaling automatisch taak "vervolg bepalen". Check: testdossier regeling + wanprestatie
simuleren; terugdraaien.

**A9. AI-concept reviewen: aanpassen en versturen.** ⬜
Verwacht: concept openen, tekst wijzigen, bijlagen aan/uit, versturen als incasso@;
concept gemarkeerd verstuurd, taak dicht. Check: 2026-00006 (gaat naar Arsalans gmail) —
1 echte verzending op het testkanaal; naderhand mail + records verifiëren.

**A10. Volledige betaling — netjes afgehecht.** ⬜
Verwacht: zaak automatisch dicht; rente bevriest; melding "cliënt factureren?" bij
gebruikers; open concepten/adviezen opgeruimd (S235-gedrag). Check: testdossier vol
betalen, alle neveneffecten natellen; terugdraaien (heropening-vangnet meteen mee getest).

## B. De debiteur doet raar

**B11. Mail vanaf onbekend adres, geen dossiernummer.** ⬜ (bekend gat S237)
Verwacht (huidig): valt stil in ongesorteerde bak. Norm: Lisanne moet dit minstens
opmerken. Check: hoe zichtbaar is de bak (teller? melding?); dit is de kandidaat-fix.

**B12. Debiteur betaalt te véél.** ⬜
Verwacht: systeem accepteert; geen negatieve openstaande bedragen in kop of brieven;
zaak dicht; overschot zichtbaar. Check: testdossier overbetaling; alle weergaven; terugdraaien.

**B13. Betaling op een afgesloten dossier.** ⬜
Verwacht: boeken kan (nabetaling komt voor), zaak blijft dicht of heropent beredeneerd —
in elk geval geen crash of stille fout. Check: gesloten testdossier + boeking; terugdraaien.

**B14. Betwisting op een kruispunt: tijdens regeling / na deelbetaling.** ⬜
Verwacht: verweer-keten start (classificatie → zaak naar 'Verweer beantwoorden' → concept),
regeling-bewaking en sommatie-automatiek stoppen netjes. Check: testdossier met regeling +
betwistingsmail via testkanaal; echte AI-call; terugdraaien.

**B15. Rare mail: alleen bijlage / Engels / wollig.** ⬜
Verwacht: classificatie doet iets verstandigs (of eerlijk 'onzeker'), geen crash, geen
onzin-concept dat klaarstaat als 'te versturen'. Check: 2-3 testmails door de echte keten.

**B16. "Ik betaal eind van de maand."** ⬜
Verwacht: toezegging wordt herkend; er ontstaat iets dat bewaakt (taak/advies met datum) —
of dit blijkt een gemis (bak c). Check: testmail door de keten; wat blijft er staan?

**B17. Zelfde debiteur, twee dossiers — koppelt de mail goed?** ⬜
Verwacht: mail mét kenmerk → juiste dossier; zónder kenmerk → eerlijk ongesorteerd of
best-guess met menselijke controle, maar nooit stil aan het verkeerde dossier. Check:
matching-volgorde in code + proef op testdossiers.

**B18. Debiteur failliet.** ⬜
Verwacht: Lisanne kan de zaak passend wegzetten (stap/afsluiten); automatiek (sommaties,
adviezen) stopt. Check: droog + testdossier statuswissel; terugdraaien.

## C. De cliënt-kant

**C19. Cliënt belt: "hoe staan mijn zaken ervoor?"** ⬜
Verwacht: per cliënt in enkele klikken een tussenstand (zaken, stadium, openstaand).
Check: prod read-only — bestaat zo'n overzicht en klopt het?

**C20. Extra factuur op een lopend dossier.** ⬜
Verwacht: vordering toevoegen; hoofdsom/BIK/rente herrekend; volgende brief klopt.
Check: testdossier vordering erbij, alles narekenen; terugdraaien.

**C21. Cliënt trekt de zaak in (debiteur betaalde rechtstreeks).** ⬜
Verwacht: netjes afsluiten zonder betaling in Luxis; automatiek stopt; status eerlijk.
Check: testdossier sluiten; nalopen dat er geen adviezen/concepten blijven ratelen; terugdraaien.

**C22. Nieuwe cliënt + eerste dossier.** ⬜
Verwacht: relatie aanmaken zonder valkuilen (dubbele-detectie, verplichte velden helder),
dossier koppelt goed. Check: via app-API aanmaken + opruimen.

## D. Tijd en termijnen

**D23. De stille debiteur — het hele pad tot dagvaarding-advies.** ⬜
Verwacht: follow-up-adviseur stelt per stap de juiste vervolgstap voor, t/m 'Voorstel
dagvaarding'; hold-stappen (regeling) worden met rust gelaten. Check: prod-adviezen
doorlichten + code van de adviseur.

**D24. Rentewijziging 1 juli 2026 — staan de nieuwe tarieven erin?** ⬜ (harde datacheck)
Verwacht: wettelijke rente + handelsrente per 1-7-2026 aanwezig in de tarieventabel;
berekeningen gebruiken het juiste halfjaar. Check: prod-tabel lezen + narekenen + extern
verifiëren wat het tarief per 1-7-2026 is.

**D25. Laatste termijn van een regeling betaald.** ⬜
Verwacht: regeling afgerond; zaak dicht (vol betaald) of terug het pad op; geen zwevende
'Bijhouden regeling'. Check: testdossier regeling uitbetalen; terugdraaien.

**D26. Termijn verloopt in het weekend.** ⬜
Verwacht: deadline-kleuren en adviezen blijven logisch (geen 'te laat' paniek op zaterdag
die maandag onzin is); geen verzending op rare momenten zonder mens. Check: droog —
deadline-berekening + scheduler-tijden lezen.

**D27. Bijna-verjaarde vordering.** ⬜
Verwacht: waarschijnlijk niets (geen verjaring-bewaking) → dan bak c met onderbouwing
(5 jaar handelsvordering, stuiting). Check: code/velden zoeken; prod oudste verzuimdatums meten.

## E. Rand en systeem

**E28. Mobiel: de ochtendronde op de telefoon.** ⬜
Verwacht: dashboard/taken/dossier/mail leesbaar en klikbaar op telefoonformaat (S228).
Check: Playwright mobiel-formaat tegen prod, ingelogd, 4 schermen, screenshots.

**E29. De medewerker-rol ziet alleen wat mag.** ⬜
Verwacht: rollen-matrix (docs/security/rollen.md) klopt live — medewerker kan geen
gebruikersbeheer/gevoelige acties. Check: rollen-matrix vs. route-guards in code; steekproef API.

**E30. Verkeerde bijlage bij een mail.** ⬜
Verwacht: te groot (>3MB per stuk, >25MB totaal) of verkeerd type → nette Nederlandse
foutmelding, geen stille weigering. Check: compose-API met te grote/verkeerde bijlage op testdossier.

**E31. Zoeken door het hele systeem.** ⬜
Verwacht: dossiernummer, debiteurnaam, cliëntnaam en factuurnummer zijn allemaal vindbaar
(waar dat hoort). Check: prod read-only zoekroutes proberen met bestaande waarden.

**E32. Dubbele mail / hersync.** ⬜
Verwacht: dezelfde mail twee keer gesynct → één record, één melding, één beoordeling
(S236-les). Check: ontdubbel-poorten in code + prod-telling op dubbele Graph-ids.

---

## Vondsten (loopt vol tijdens de nacht)

| # | Scenario | Bak | Wat | Status |
|---|----------|-----|-----|--------|
| 1 | A1 | a | Concept weggooien (handmatig/zaak-sluiten/stap-wissel) sluit de nakijk-taak NIET → 8 spooktaken op prod wijzen naar weggegooide concepten. Sluiten gebeurt alleen bij versturen (incasso/router.py) en stap-skip. | te fixen |
| 2 | A5/E31 | b | Factuurnummer van een vordering (claims.invoice_number) zit in GEEN enkel zoekpad (cases-lijst én globale zoek). Debiteur belt met factuurnummer → dossier onvindbaar (alleen via toevallige PDF-bestandsnaam). | te fixen |
| 3 | B13 | a | Betaling op volbetaalde zaak wordt stil geaccepteerd → totaal openstaand −100,00 (negatief!). Guard collections/service.py:487 slaat alleen aan als er nog iets openstaat. Live gereproduceerd op wegwerpdossier 2026-00020, daarna teruggedraaid. | te fixen |
| 4 | rollback | b | Dossier verwijderen laat vorderingen actief staan (soft-delete cascadeert niet naar claims). | beoordelen |
| 5 | A1 | c | 215 ongelezen meldingen in 2,5 week (70× 'classificatie klaar', 52× 'deadline verlopen') — meldingen-moeheid; voorstel nodig (bundelen/afvoeren), geen nachtfix. | voorstel |
| 6 | A1 | data | 40+ oude open nakijk-/controleertaken op testdossiers van vóór de S234/S236-fixes vervuilen de Taken-pagina → hoort bij de opruimronde (GO Arsalan+Lisanne). | opruimronde |
| 7 | B12 | c | Échte overbetaling (debiteur maakt te veel over) kan nergens geregistreerd worden — handmatige route weigert (terecht als tikfout-bescherming), maar het geld ís er dan wel. Antwoord zit er al half in: de derdengelden-route boekt het surplus netjes; de nieuwe foutmelding wijst daar nu naar. | voorstel |
| 8 | B11/E32 | a | Samengesteld kenmerk (`D102733_I71828409`) werd nooit herkend (underscore = woordteken → slot-\b matcht niet). Echte cliënt-mail (update-verzoek Invorderingsbedrijf 13-7) lag 9 dagen ongesorteerd. | GEFIXT + live: sync koppelde direct 2 echte mails (IN100128, IN100586) |
| 9 | B16 | c | Betaalbelofte wordt perfect herkend (datum+bedrag live bewezen: 31-7-2026, €100) maar `promise_date` wordt door NIETS bewaakt — belofte verlopen zonder betaling = geen enkel signaal. Voorstel: taak op belofte-datum (zelfde recept als regeling-taken). | voorstel |
| 10 | B15 | c | Vage/verwarde debiteur-mail heet 'niet_gerelateerd' terwijl de AI-redenering zelf zegt dat het een reactie op de sommatie is — categorie-ontwerp mist een bak 'onduidelijk/overig-gerelateerd'. | voorstel |
| 11 | D25 | a | Regeling volledig nagekomen maar dossier niet vol betaald (rente liep door) → zaak bleef eeuwig stil op pauzestap 'Bijhouden regeling'; adviseur laat pauzestappen met rust → niemand hoort er ooit meer iets van. | GEFIXT (taak 'Regeling afgerond — vervolg bepalen', wachters + tegenproef) |
| 12 | D26 | c | Deadline-kleuren rekenen in kale dagen, geen weekend/feestdag-logica — cosmetisch, adviezen zijn advies. | voorstel (laag) |
| 13 | B11 | c | Nieuwe ongesorteerde mail van onbekende afzender geeft geen enkele melding (44 stuks in de bak, 6 in laatste 14 dagen, waarvan 2 echte zakelijke mails) — het S237-gat, nu gekwantificeerd. Voorstel: melding bij binnenkomst in de ongesorteerde bak, of dagelijkse teller. | voorstel (kandidaat-hoofdklus) |

**Status fixes:** 1 (spooktaken), 3 (negatief openstaand), 8 (kenmerk), 11 (regeling-einde) en
2 (zoeken op factuurnummer) zijn GEFIXT, getest (10 nieuwe wachters, 351 tests groen, ruff schoon),
gedeployd (commit `6f15a13`, backend via SSH `--force-recreate`) en live nageteld:
zoeken T10-10 → 2026-00019 ✓; discard op prod → taak `skipped` ✓ (bijvangst: 1 spooktaak
2026-00012 opgeruimd); sync-hersteld: 2 echte mails automatisch gekoppeld ✓; poort-fix gedekt
door wachters (bug was vóór de fix live gereproduceerd op wegwerpdossier 2026-00020, exact
teruggedraaid). Prod-logs sinds deploy: 0 fouten.

**Al goed bevonden:** A2 ✅ (aanmaken compleet), A3 ✅ (rente 48,02 + BIK 570,68 exact = eigen narekening),
A6/A7 ✅ (verdeling kosten→rente→hoofdsom op de cent, ook na extra vordering C20 ✅), A10 ✅ (autosluiting
+ factureer-melding ×2 gebruikers + rente bevroren), heropening-vangnet ✅, D24 ✅ (handelsrente 10,40%
per 1-7-2026 aanwezig; consumentenrente 4% ongewijzigd — extern geverifieerd via rijksoverheid.nl),
zoeken op naam/dossiernummer ✅ (A5/E31 deels), B12-weigering nette NL-melding ✅.

## Eindstand per scenario

**Live getest en goed (of gefixt):** A1 (vondsten 1/5/6), A2, A3, A5, A6, A7, A10, B12, B13
(vondst 3 → gefixt), B15, B16 (vondst 9 → voorstel), C20, D24, E31 (vondst 2 → gefixt), E32,
B11 (vondsten 8+13), D25 (vondst 11 → gefixt).
**Droog bewezen (code + bestaande wachters/sessies):** A4 (S234-guard-matrix, vannacht groen
meegedraaid), A8 (S235 live), A9 (S236/S238 live-verzendbewijs; niet opnieuw afgevuurd),
B14 (verweer tijdens regeling = bewust 'geen actie' — zijpad-regel, gedocumenteerde keuze),
B17 (kenmerk eerst; contact-match alleen bij exact één dossier — precies goed), B18
(faillissementsstap bestaat; sluitroutes ruimen op — P3-wachters), C19 (filter per cliënt
op de API), C21 (P3-wachters + evaluator filtert gesloten zaken), C22 (relatie-CRUD,
dagelijks gebruik + suite), D23 (S237: 14/14 escalatie-adviezen live nageteld), D27
(verjaring-monitor bestaat, 2 actieve waarschuwingen op prod), E29 (20 require_role-poorten,
S183-audit dekt de matrix), E30 (S232-groottegrens, tests groen).
**Niet gedaan:** E28 mobiel niet opnieuw geklikt — S228 deed de volledige mobiele ronde en
vannacht is geen frontend-regel gewijzigd.

## Voorstel-lijst voor Arsalan (bak c — niet gebouwd, jouw besluit)

1. **Melding/teller voor de ongesorteerde bak** (vondst 13, het S237-gat) — sterkste
   kandidaat: 2 échte zakelijke mails bleven er dagen/weken in hangen. Kant-en-klaar
   ontwerp-idee: zelfde meldingsrecept als case_closed_invoice, alleen bij inbound
   zonder koppeling; plus badge-teller op de Mail-pagina.
2. **Betaalbelofte bewaken** (vondst 9): taak "Betaalbelofte controleren — {zaak}" met
   due = promise_date, alleen als de zaak dan nog niet betaald is. Datum en bedrag
   worden al perfect uit de mail gehaald — er hoeft alleen een taak aan.
3. **Meldingen-moeheid** (vondst 5): 145 zichtbare ongelezen meldingen in 2,5 week
   (52× deadline, 48× mail). Voorstel: bundelen per dag of per dossier.
4. **Categorie 'onduidelijk/overig-gerelateerd'** voor de mail-beoordeling (vondst 10).
5. **Overbetaling-registratie** (vondst 7): de derdengelden-route dekt het al; eventueel
   een knopje "registreer als derdengelden" in de foutmelding-flow.
6. **Dossier verwijderen laat vorderingen/betalingen actief** (vondst 4) — data-hygiëne,
   samen beoordelen of cascade-soft-delete gewenst is.
7. **Weekend-logica deadlines** (vondst 12) — laag.

## Opruimronde-input (naast de bestaande punten uit S237/S238)

- 8 spooktaken (nakijk-taken van weggegooide concepten) — waarvan 1 vannacht al dicht
  (2026-00012, live natelling van de fix); de rest sluit niet vanzelf: de fix werkt
  alleen vooruit.
- 40+ oude open nakijk-/controleertaken op testdossiers van vóór S234/S236.
- **Actie voor de ochtend: de mail van Invorderingsbedrijf (13-7, update-verzoek
  IN100128) staat nu op het dossier maar wacht al 9 dagen op een ANTWOORD.** Zelfde
  voor de uithanden-mail op IN100586 (17-6) — beoordelen wat daarmee moet.
