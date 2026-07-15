# Demolijst S218 — alle fouten & wensen uit de demo van 15 juli 2026

Bron: demo Arsalan (+ eerdere vondsten dezelfde dag, sessie S218). Status per punt bijgehouden.
**Werkwijze afgesproken:** S219 = onderzoek (Fable), S220 = bouwen (Opus), daarna review (Fable).

## Spelregels (gelden voor ALLE punten)

- **Breed checken:** elk punt niet alleen in de gemelde situatie onderzoeken, maar overal
  waar hetzelfde kan spelen (andere schermen, andere routes, andere sjablonen).
- **Sjabloon-punten gelden voor álle sjablonen:** zowel de AI-gegenereerde als de vaste
  sjablonen, stuk voor stuk nalopen op elk genoemd punt. ("Brief" = de mail die verstuurd wordt.)
- Referentiebestanden in de projectmap (bewust untracked):
  - `CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf` — de JUISTE versie van het
    concept-verzoekschrift (voor punt 12; huidige PDF mist logo's).
  - `SOMMATIE TOT BETALING _  _ voorbeel voor handtekening.eml` — voorbeeld voor de
    handtekening (punt 7).

## A. Verzenden & bijlagen

1. **AI-concept stuurt geen renteoverzicht-PDF mee.** Bewezen op IN100613 (15 juli 12:24):
   verstuurd via AI-concept → compose; zonder sjabloonkeuze weet de server het brieftype niet
   → geen bijlage. WIK vraagt rente-inzicht voor particulieren/eenmanszaken/VOF's. Rente stond
   wél in de mailtekst, niet als PDF. Dit is de hoofdroute van Lisanne/Arsalan.
   ONDERZOCHT (S218) — oorzaak bekend, fix ontworpen: brieftype afleiden uit de pijplijnstap
   bij verse dossier-mail aan de debiteur; antwoorden/doorsturen blijven zonder bijlage.
   Facturen NIET automatisch toevoegen op deze route ("we sturen normaal geen facturen mee").
2. **Mailvenster toont niet welke bijlagen automatisch meegaan.** ONDERZOCHT (S218) — bevestigd:
   automatische bijlagen worden pas server-side bij verzending toegevoegd, nergens zichtbaar.
3. **Documentenroute mist het renteoverzicht ook:** brief laten maken via tabblad Documenten en
   van daaruit mailen → renteoverzicht gaat niet mee (het bijlage-regeltje herkent op die route
   alleen de 14-dagenbrief, niet de eerste sommatie). ONDERZOCHT (S218) — oorzaak bekend.
4. **CC én BCC werken niet in het AI-concept-verstuurscherm.** BCC-optie ontbreekt helemaal;
   CC doet het ook niet. In de normale mailfunctie bestaat het wel.
5. **Mailonderwerp vast formaat:** klant / debiteur — sommatie tot betaling — ons dossiernummer.

## B. Sjablonen — inhoud (elk punt × elk sjabloon checken)

6. **Adres staat nog op het Ijsbaanpad** (oud adres) in de brieven.
7. **Handtekening moet Incasso@kestinglegal.nl zijn**, niet kesting@kestinglegal.
   Voorbeeld-.eml staat in de projectmap.
8. **Aanhef valt soms weg** — "Geachte heer of mevrouw" ontbreekt bij het
   verzoekschrift-faillissement-concept. Alle sjablonen checken op aanhef.
9. **Aanhef bevat soms de BV-naam** — "Geachte heer, mevrouw, [BV-naam]" bij treffen van
   regeling/vaststellingsovereenkomst. BV-naam weg; alle sjablonen checken.
10. **Kenmerk van de klant staat in de tweede sommatie** — hoort er niet; alle sjablonen checken.
11. **Opmaak:** spaties onder "Bedrag" lopen niet goed, lettertypes niet uniform — verse blik
    op alle sjablonen.
12. **Verzoekschrift faillissement: concept-verzoekschrift automatisch als bijlage** zodra het
    AI-concept gegenereerd is (nodig voor batch-verzending straks). Juiste PDF staat in de
    projectmap (huidige mist logo's).

## C. Follow-up & pijplijn

13. **IN100607 staat in het dossier op Tweede sommatie maar verschijnt niet in Follow-up.**
    ONDERZOCHT (S218) — oorzaak gevonden en gemeten, tweeledig:
    (a) **Verouderde adviezen worden nooit opgeruimd.** Wordt een stap buiten de Follow-up-knop
    om uitgevoerd (AI-concept, handmatig doorschuiven), dan blijft het oude advies gewoon
    "open" staan. IN100607 stond dus WÉL in de lijst — maar onder "Eerste sommatie" (advies
    van 9 juli), terwijl die al verstuurd was. Erger dan ontbreken: het nodigt uit tot dubbel
    versturen. Live gemeten: 3 van de 15 open adviezen zijn zo verouderd (IN100607, IN100613,
    IN100521 — die laatste adviseert "Voorstel dagvaarding" terwijl de zaak al op
    Verzoekschrift faillissement staat).
    (b) **Een open advies blokkeert élk nieuw advies voor dat dossier.** De scanner slaat een
    dossier met een openstaand advies over (ontdubbeling per dossier, niet per stap). Zolang
    het oude advies blijft staan, verschijnt "Tweede sommatie" dus NOOIT — ook niet na de
    wachttijd. Dit bevestigt Arsalans vermoeden dat het systeembreed speelt.
    **Fixrichting (bouwsessie):** bij elke stap-wissel de open adviezen van de oude stap
    automatisch afsluiten (met reden "stap al uitgevoerd buiten follow-up"), zodat de scanner
    weer vrij is om het volgende advies te maken.
14. **Stappenbalk in het dossier toont vijf vaste fasen** (minnelijk → gerechtelijk → regeling →
    communicatie → afsluiting) alsof elke zaak die route loopt — klopt niet (IN100410: alleen
    minnelijk overleg, staat toch als gerechtelijk/regeling). Liever de echte status tonen.
    **Inclusief onderzoek hoe concurrenten (Clio, Smokeball, e.d.) dit tonen.**
15. **Wachttijden tussen stappen inzichtelijk maken** — BEANTWOORD (S218, gemeten in de
    productie-instellingen). Er lopen twee klokken:
    - **Follow-up-advies** (scanner draait elk half uur): het advies voor een stap verschijnt
      zodra het dossier de minimale wachttijd op die stap heeft bereikt. Eerste sommatie: direct.
      Tweede sommatie: 4 dagen na de eerste. Derde sommatie: 4 dagen. Sommatie laatste
      mogelijkheid: 4 dagen. Verzoekschrift faillissement: 4 dagen. 14-dagenbrief (alleen
      consument): direct, daarna 15 dagen wachten vóór de eerste sommatie.
    - **Dagelijkse automatisering** (timeout-regels, 1× per dag): laat een dossier X dagen op
      een stap staan zonder actie, dan maakt Luxis zelf een AI-concept + taak voor de volgende
      stap. Termijnen: 14-dagenbrief→Eerste sommatie 15 dagen; Eerste→Tweede 7 dagen;
      Tweede→Derde 4; Derde→Laatste mogelijkheid 4; Laatste→Verzoekschrift 4.
    - ⚠️ **Inconsistentie gevonden:** Eerste→Tweede staat in de timeout-regel op 7 dagen,
      maar de stap-wachttijd (waar follow-up en de kleuren op sturen) is 4 dagen. Lisanne's
      officiële workflow zegt 4 dagen. Keuze maken en gelijktrekken (bouwsessie).
16. **B2B/B2C-typering:** 105 dossiers staan in BaseNet op het B2C-spoor maar in Luxis als
    zakelijk (import: bedrijf → zakelijk). Raakt de WIK-bescherming (punt 1) en de
    14-dagenbriefroute. Beslismemo voor Lisanne maken. GEMETEN (S218): 105 zaken.

## D. Mail & AI

17. **Vanuit de tijdlijn in het dossier op een mail kunnen klikken** → voorbeeld/preview zien.
18. **Vanuit de Mail-pagina op het zaaknummer kunnen klikken** → direct naar het dossier.
19. **Classificatie van binnengekomen antwoorden: traag én handmatig.** Moet continu automatisch
    op de achtergrond. (Startpunt S219: de automatische classificatie draait volgens de planner
    elke 6 minuten — uitzoeken waarom de beleving dan toch "lang wachten + zelf klikken" is;
    vermoedelijk zit de vertraging in de keten kwalificeren→goedkeuren→overzicht, zie punt 24.)
20. **AI-conceptgeneratie in het dossier is traag** — sneller zonder kwaliteitsverlies.
21. **AI-antwoord slaat inhoudelijk de plank mis** (IN100607): debiteur vraagt "wie zijn jullie
    en wie is de klant" → concept geeft nietszeggend standaardantwoord i.p.v. klantnaam/facturen
    te benoemen. Simpele gevallen moet de AI goed beantwoorden.
22. *(vervallen — samengevoegd met 24)*

## E. Taken

23. **Taken moeten terug te draaien zijn.** Per ongeluk pijltje → overgeslagen/afgerond; nu is
    "urgent: escalatie-e-mail beoordelen" (IN100607) kwijt — onvindbaar waar hij vandaan kwam.

## F. Keten & bouwklussen

24. **De hele antwoord-keten is traag en klik-zwaar:** kwalificeren → wachten → goedkeuren →
    pas dan in overzicht → pas dan antwoord maken. Wens: kwalificatie continu automatisch,
    conceptgeneratie sneller, minder klikken.
25. **Bouwklus klaarliggend (uit S218-onderzoek):** renteoverzicht op de AI-concept-route +
    automatische bijlagen zichtbaar in het mailvenster + documentenroute-gaatje dichten.
    Ontwerp staat in de S218-sessienotities.

## Vervallen

- ~~Nasturen bijlagen Bayar transport (IN100613)~~ — Arsalan: niet nodig.
