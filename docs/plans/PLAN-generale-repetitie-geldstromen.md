# PLAN — Generale repetitie geldstromen (draaiboek, mens + systeem)

**Rang: 6 — plannen zodra Arsalan een dagdeel heeft; vóór de opzegging van BaseNet.**
Dit is het "één echt dossier van A tot Z"-blok uit het livegang-plan (S175b/S181).
Doel: bewijzen dat de hele geldketen werkt vóór er echt geld doorheen moet.

## De keten die getest wordt

bankafschrift importeren → betaling matchen aan zaak → art. 6:44-verdeling
(kosten→rente→hoofdsom) → derdengelden-administratie → doorbetaling opdrachtgever →
afwikkeling + factuur. Alle onderdelen bestaan en zijn los getest; deze repetitie test
de KETEN, met Arsalan als bediener (niet Claude — het gaat erom dat een mens het kan).

## Vooraf: "de rekening is toch niet gekoppeld?" — klopt, en dat hoeft ook niet

Luxis heeft géén live bankkoppeling nodig. Afschriften komen binnen via handmatige
CSV-upload; de parser ondersteunt het **Rabobank zakelijk**-formaat (26 kolommen) en
boekt bewust alleen bijschrijvingen (derdengeldrekening). Voorwaarden vóór de repetitie:
1. Bevestig bij welke bank de stichting-derdengeldenrekening loopt. Rabobank → klaar.
   Andere bank → eerst een tweede CSV-parser bouwen (klein, ~1 sessie; zelfde patroon).
2. Download een echte CSV-export van die rekening (mag een oude periode zijn).
Zie ook `PLAN-wet-en-regelgeving-livegang.md` §3 voor het werkritme na livegang.

## Voorbereiding (Claude, vooraf)

1. Kies een kandidaat-dossier: een heropende zaak met recente echte betaling, of één
   van de 3 "afsluiten"-zaken (IN100547 is volledig glad: hoofdsom+rente+kosten exact
   voldaan — ideaal voor de afwikkel-helft).
2. Zet een spiekbrief klaar met de exacte klikpaden per stap (schermen: Bankieren/
   payment-matching upload → match goedkeuren → dossier Betalingen-tab →
   Derdengelden-tab → afwikkelflow (FIN-2, S170) → factuur).
3. Check vooraf op prod: `trust_transactions`-saldo van het dossier, openstaande
   bedragen, zodat verwachte uitkomsten op papier staan VÓÓR de test (meten = eerst
   voorspellen, dan doen).

## De repetitie (Arsalan bedient, Claude kijkt mee)

1. **Import**: echt (of gisteren gedownload) bankafschrift uploaden via de
   payment-matching-import (`POST /api/.../import` zit achter de UI).
   Verwacht: transacties zichtbaar, matches voorgesteld.
2. **Match goedkeuren** voor het testdossier. Verwacht: betaling op de zaak, verdeling
   volgens 6:44 zichtbaar (kosten eerst — check de volgorde expliciet).
3. **Derdengeld**: ontvangst staat op de derdengeldenrekening-administratie van het
   dossier. Verwacht: saldo klopt met de betaling.
4. **Doorbetaling opdrachtgever** registreren. Verwacht: derdengeld-saldo naar 0,
   doorbetaling zichtbaar.
5. **Afwikkelen** (FIN-2-flow) + **factuur** maken voor kosten/provisie.
   Verwacht: zaak afgesloten, factuur met juiste bedragen (provisie-instelling van de
   opdrachtgever checken).
6. Elke afwijking noteren — niet ter plekke fixen (tenzij triviaal), eerst de hele
   keten aflopen.

## Randgevallen om expliciet te proberen

- Een betaling die op **meerdere zaken** zou kunnen slaan (zelfde debiteur) — kiest de
  matching de juiste? (De BaseNet-import matchte op dossiernummer in de omschrijving;
  echte overboekingen hebben dat kenmerk niet altijd.)
- Een **deelbetaling** (minder dan openstaand) — blijft de zaak open met juist restant?
- Een betaling **zonder herkenbaar kenmerk** — komt hij netjes in "unmatched" en is hij
  handmatig te koppelen?
- **Storno/negatieve regel** in het afschrift — wordt die niet als ontvangst geboekt?
  (De BaseNet-import filterde negatieve regels; de reguliere import-flow moet dat ook
  aankunnen.)
- Derdengelden: klopt de **verrekenclausule-vraag** (ARSALAN-TODO §4 — 3 open vragen aan
  Lisanne over de stichting) — die antwoorden zijn nodig vóór echte doorbetalingen.

## Acceptatiecriteria

1. De keten is één keer volledig doorlopen door Arsalan zonder Claude-ingreep in de UI.
2. Elke stap heeft een genoteerde verwachting vooraf en een uitkomst achteraf; 0
   onverklaarde verschillen.
3. De 4 randgevallen zijn geprobeerd (of expliciet gemotiveerd overgeslagen).
4. Bevindingenlijst in SESSION-NOTES; blokkerende bevindingen krijgen een eigen fix-plan
   vóór livegang.
5. De 3 derdengelden-vragen aan Lisanne (ARSALAN-TODO §4) zijn gesteld en beantwoord.
