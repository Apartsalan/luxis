# Demolijst S218 — alle fouten & wensen uit de demo van 15 juli 2026

Bron: demo Arsalan (+ eerdere vondsten dezelfde dag, sessie S218). Status per punt bijgehouden.
**Werkwijze afgesproken:** S219 = onderzoek (Fable), S220 = bouwen (Opus), daarna review (Fable).

> **S219 (15 juli): ALLE punten onderzocht** — oorzaken + fixrichtingen per punt hieronder,
> volledige metingen en bewijs in `S219-onderzoek.md`, bouwdraaiboek in `PROMPT-S220.md`.
> Belangrijkste nieuwe vondsten (buiten de oorspronkelijke lijst):
> **(N1)** de compose-verstuurknop verstuurt via het persoonlijke account van de klikker
> (Bayar-sommatie vertrok als seidony@ i.p.v. incasso@) én legt niets vast — de verstuurde
> mail is onvindbaar in Luxis; zelfde afzender-gat op het document-verzendpad.
> **(N2)** het oude adres + kesting@ zit in de 6 stap-mailteksten in de database
> (BaseNet-kopieën) — álle AI-concepten erven het, ook verse.
> **(N3)** zombie-concepten: net als de adviezen (punt 13) blijven oude AI-concepten open
> staan na een stap-wissel (IN100613 heeft er 2 die tot een dubbele sommatie uitnodigen).
> **(N4)** zes stille ruis-wachtrijen (470 classificaties, 348 notificaties, 79 ongelinkte
> mails, 14 intake, 3 verouderde adviezen, 18 onzichtbare geskipte taken).

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
   ONDERZOCHT (S219): BCC bestaat nergens in de hele keten (geen veld in schema's,
   providers, UI) → bouwen over de hele lijn. CC werkt server-side wél; het invoerveld
   verliest een getypt adres stilletjes als je niet eerst Enter/komma drukt vóór "Versturen"
   (meest waarschijnlijke demo-oorzaak; in S220 met test bevestigen).
5. **Mailonderwerp vast formaat:** klant / debiteur — sommatie tot betaling — ons dossiernummer.
   ONDERZOCHT (S219): er bestaan nu 5 verschillende onderwerpformaten naast elkaar
   (follow-up/batch, DOCX-route, compose-preview die de interne sleutel "Sommatie Drukte"
   lekt, lege BaseNet-slots "SOMMATIE TOT BETALING / / " in de stap-teksten, AI-concepten).
   Fix: één gedeelde onderwerp-bouwer in het gewenste formaat, overal aanroepen.

## B. Sjablonen — inhoud (elk punt × elk sjabloon checken)

6. **Adres staat nog op het Ijsbaanpad** (oud adres) in de brieven.
   ONDERZOCHT (S219) — bron gevonden: de kantoor-instellingen zijn al goed en de 8 Word-
   en 21 mail-sjablonen renderen daar vers uit (live geverifieerd). Het oude adres zit in
   (a) de 6 stap-mailteksten in de database (BaseNet-kopieën met vaste handtekening) —
   álle 10 AI-concepten dragen het, óók verse van 15-07; de verstuurde Bayar-sommatie ging
   met oud adres de deur uit; (b) Lisanne's origineel "verzoekschrift_bijlage" (Word).
   Fix: stap-teksten in DB herschrijven met {{ kantoor.* }}-handtekening (of handtekening
   centraal aanhaken) + bijlage-Word vervangen.
7. **Handtekening moet Incasso@kestinglegal.nl zijn**, niet kesting@kestinglegal.
   Voorbeeld-.eml staat in de projectmap.
   ONDERZOCHT (S219): de code switcht al goed op zaaktype (incasso → Incasso@); het gat is
   de staptekst "Eerste sommatie" (kesting@ hardcoded) → 5/10 concepten incl. de 2
   verstuurde droegen kesting@. Zelfde fix als punt 6.
8. **Aanhef valt soms weg** — "Geachte heer of mevrouw" ontbreekt bij het
   verzoekschrift-faillissement-concept. Alle sjablonen checken op aanhef.
   ONDERZOCHT (S219): 3 stap-teksten missen een aanhef (Laatste mogelijkheid,
   Verzoekschrift, Verweer beantwoorden) → de AI voegt er soms zelf één toe =
   niet-deterministisch. Fix: aanhef vast in de stap-teksten. Alle 21 code-sjablonen
   hebben er wél een (stijl wisselt: "heer/mevrouw" vs "heer, mevrouw" — gelijktrekken).
9. **Aanhef bevat soms de BV-naam** — "Geachte heer, mevrouw, [BV-naam]" bij treffen van
   regeling/vaststellingsovereenkomst. BV-naam weg; alle sjablonen checken.
   ONDERZOCHT (S219) — 3 vindplaatsen: e-mailsjablonen `vaststellingsovereenkomst` en
   `faillissement_dreigbrief` + Word-sjabloon verzoekschrift ("Geachte heer, mevrouw
   {{ wederpartij.naam }},"). De AI-prompt verbiedt het al — vaste sjablonen niet.
10. **Kenmerk van de klant staat in de tweede sommatie** — hoort er niet; alle sjablonen checken.
    ONDERZOCHT (S219): "Uw kenmerk: {klant-kenmerk}" staat in álle 5 Word-debiteurbrieven
    én in de e-mail-basislayout; de AI zet het kenmerk in de Betreft-regel. Fix: overal weg
    uit debiteurbrieven (het is het kenmerk van de opdrachtgever; het label "Uw kenmerk"
    klopt richting debiteur sowieso niet).
11. **Opmaak:** spaties onder "Bedrag" lopen niet goed, lettertypes niet uniform — verse blik
    op alle sjablonen.
    ONDERZOCHT (S219): AI-concepten bouwen tabellen met spaties (gemeten in de verstuurde
    Bayar-mail) → scheef in proportioneel lettertype; fix = echte HTML-tabellen laten
    genereren. Lettertypes: Word = Calibri maar document-standaard = Courier (valkuil),
    mails = Verdana, AI-concepten = geen font. Eén huisstijl-lettertype kiezen.
12. **Verzoekschrift faillissement: concept-verzoekschrift automatisch als bijlage** zodra het
    AI-concept gegenereerd is (nodig voor batch-verzending straks). Juiste PDF staat in de
    projectmap (huidige mist logo's).
    ONDERZOCHT (S219): de compose-dialog hangt hem al automatisch aan bij sjabloonkeuze
    "faillissement_dreigbrief"; de AI-concept-route niet (geen sjabloontype = zelfde wortel
    als punt 1). Let op: de brieftekst belooft "kopie in de bijlage" — vergeten = brief liegt.
    ⚠️ Beslispunt Lisanne: het Word-verzoekschrift bevat een vast, oud Rabo-derdengelden-
    IBAN + vaste kosten (EUR 2.195 / € 412,61) — kloppen die nog nu het kantoor op KNAB zit?

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
    ONDERZOCHT (S219) — oorzaak bewezen: de balk vinkt alles links van de huidige categorie
    groen af, doorlopen of niet (IN100410 staat op "Voorstel dagvaarding" = categorie 4 van 5).
    "Administratief" is bovendien geen fase (verweer/on-hold/voorstel zitten erin).
    Concurrenten (Clio/Smokeball): status als label/milestone met tijd-in-fase, per zaaktype
    instelbaar — niemand vinkt niet-doorlopen fasen af. Voorstel: huidige stapnaam +
    categoriekleur + "X dagen in deze stap" + volgende stap; het echte pad staat al in Tijdlijn.
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
      ONDERZOCHT (S219): vindplaats bevestigd (step_transitions, {"days": 7}); voorstel
      7 → 4 = één update. Alle overige regels staan al op 4 (14db→Eerste = 15, klopt).
16. **B2B/B2C-typering:** 105 dossiers staan in BaseNet op het B2C-spoor maar in Luxis als
    zakelijk (import: bedrijf → zakelijk). Raakt de WIK-bescherming (punt 1) en de
    14-dagenbriefroute. Beslismemo voor Lisanne maken. GEMETEN (S218): 105 zaken.
    ONDERZOCHT (S219): memo-structuur klaar (impact bij omzetten: 14-dagenbrief-plicht,
    BIK+BTW-regels, consumentenrente, WIK-bijlage). Lijst per dossier maken in S220 uit de
    BaseNet-XML; koppelen aan de KvK-rechtsvorm-backfill (sleutel ~1 week, melding Arsalan 15-07).

## D. Mail & AI

17. **Vanuit de tijdlijn in het dossier op een mail kunnen klikken** → voorbeeld/preview zien.
    ONDERZOCHT (S219): vereist éérst de N1-fix — de verstuurknop maakt nu helemaal geen
    mail-record/tijdlijn-regel aan. Daarna: activiteit koppelen aan de mail + preview
    (bouwsteen bestaat: Correspondentie-tab op het dossier).
18. **Vanuit de Mail-pagina op het zaaknummer kunnen klikken** → direct naar het dossier.
    ONDERZOCHT (S219): in het detailpaneel is de link er al; alleen de lijstrij mist hem — kleine fix.
19. **Classificatie van binnengekomen antwoorden: traag én handmatig.** Moet continu automatisch
    op de achtergrond. (Startpunt S219: de automatische classificatie draait volgens de planner
    elke 6 minuten — uitzoeken waarom de beleving dan toch "lang wachten + zelf klikken" is;
    vermoedelijk zit de vertraging in de keten kwalificeren→goedkeuren→overzicht, zie punt 24.)
    ONDERZOCHT (S219): keten ís automatisch en deed er in de echte casus 7,5 min over
    (worst-case ~12 door sync 5 min + classificatie 6 min + onderlinge race). De beleving komt
    door (a) auto-concept dat bewust UIT staat voor alles behalve verweer (kwaliteitsreden,
    oude keuze) en (b) 470 oude import-classificaties die de wachtrij onbruikbaar maken.
20. **AI-conceptgeneratie in het dossier is traag** — sneller zonder kwaliteitsverlies.
    ONDERZOCHT (S219) — gemeten: 39 seconden per concept (prompt 41k tekens, $0,07),
    zonder voortgang in de UI (IN100521 kreeg daardoor 2 identieke concepten). Fixrichtingen:
    concept vooraf klaarzetten bij stap-binnenkomst, voortgang tonen, prompt slanker.
21. **AI-antwoord slaat inhoudelijk de plank mis** (IN100607): debiteur vraagt "wie zijn jullie
    en wie is de klant" → concept geeft nietszeggend standaardantwoord i.p.v. klantnaam/facturen
    te benoemen. Simpele gevallen moet de AI goed beantwoorden.
    ONDERZOCHT (S219): vraag werd "ongemotiveerde betwisting" → standaard-weerlegging; de
    klantnaam zit wél in de promptcontext maar de instructie zegt niet dat vragen beantwoord
    moeten worden. Fix: apart type "identiteits-/informatievraag" + promptregel "beantwoord
    letterlijke vragen concreet (klantnaam, facturen, leveringscontext)".
22. *(vervallen — samengevoegd met 24)*

## E. Taken

23. **Taken moeten terug te draaien zijn.** Per ongeluk pijltje → overgeslagen/afgerond; nu is
    "urgent: escalatie-e-mail beoordelen" (IN100607) kwijt — onvindbaar waar hij vandaan kwam.
    ONDERZOCHT (S219): de taak bestaat nog (status 'overgeslagen', 29 sec na aanmaak per
    ongeluk geskipt; hij kwam van de escalatie-actie van de mail-classificatie). Niet kwijt,
    wel onzichtbaar: geen weergave voor overgeslagen taken (18 stuks!) en geen herstelknop.
    Fix: weergave + herstel-knop + "ongedaan maken"-melding direct na de klik.

## F. Keten & bouwklussen

24. **De hele antwoord-keten is traag en klik-zwaar:** kwalificeren → wachten → goedkeuren →
    pas dan in overzicht → pas dan antwoord maken. Wens: kwalificatie continu automatisch,
    conceptgeneratie sneller, minder klikken.
    ONDERZOCHT (S219) — ontwerp in PROMPT-S220: wachtrij-schoonmaak (go-live-cutoff),
    auto-concept weer aan per categorie, classificatie direct na de sync (race weg),
    één scherm met goedkeuren+uitvoeren in één klik (endpoint bestaat al).
25. **Bouwklus klaarliggend (uit S218-onderzoek):** renteoverzicht op de AI-concept-route +
    automatische bijlagen zichtbaar in het mailvenster + documentenroute-gaatje dichten.
    Ontwerp staat in de S218-sessienotities.
    S219: ongewijzigd geldig; uitbreiden met vondst N1 (afzender-vangrail + logging op de
    verstuurknop) — zie PROMPT-S220 blok 1.

## Vervallen

- ~~Nasturen bijlagen Bayar transport (IN100613)~~ — Arsalan: niet nodig.
