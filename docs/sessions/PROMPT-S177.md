# Sessieprompt S177 — Stap 0: Fable-nacheck S175-dag → daarna Opus: herstel-sprint

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model + volgorde (afspraak Arsalan, 6 juli avond)
**Start op Fable**: kritische nacheck van de S175-dag (stap 0 hieronder) — er zijn die dag
véél zelfstandige acties op prod gedaan en Arsalan constateerde fouten. Pas na de nacheck
en zijn akkoord schakelt hij naar **Opus** voor de herstel-sprint (stap A-C).
Lees vooraf: `docs/ARCHITECTUUR-KAART.md` + S175/b/c/d-entries + de S168-entry
(BaseNet-import, formaat-details in §A) in `SESSION-NOTES.md`.

## Stap 0 (Fable) — ✅ UITGEVOERD (6 juli, avond) — uitkomst: alles schoon
Alle 6 punten gecontroleerd tegen prod + code: klantkaart-rollback compleet (0 rijen),
proefzaken-rente conform XML én AV 13.3, heropening raakte géén automatisering (0
followups/drafts/docs/mails), slim-leren 103 goedgekeurd + teksten leesbaar + 0
dossiernummers, dashboard-fix consistent (1 klein gaatje → taak C.4), bulk-goedkeuren
raakt alleen status 'kandidaat'. Plan-review daarna: Aanleiding §2 en taken B/C
gecorrigeerd (verlezen €2.674, achterhaalde volgorde-instructie). Origineel hieronder.

## Stap 0 (origineel) — nacheck van alle S175-dag-acties, verse ogen
Gemaakte fouten die dag (erkend): ongevraagd klantkaart-rente-defaults gezet (7
opdrachtgevers — TERUGGEDRAAID zelfde avond, verifieer: `default_interest_type` moet
NULL zijn); D-Break genoemd/meegewogen terwijl dat geen vaste opdrachtgever is.
Loop kritisch na, tegen de daadwerkelijke prod-data:
1. **Proefzaken-rente** (IN100215/IN100040/IN100521): contractueel 2.00/monthly/enkelvoudig
   — klopt dat met BaseNet-XML (`incinterest`/`incssamengesteld`, lokaal:
   `Xml_02-07-2026_2400.zip`)? En met wat Lisanne verwacht?
2. **Heropening proefzaken**: status 'nieuw' zonder pijplijnstap — nog steeds geen
   automatisering geraakt? (`incasso_step_id IS NULL`, geen batch-mail/followup-logs.)
3. **Slim-leren-opschoning**: 11 rijen terug naar afgewezen + naam-sweep ('cliënte') +
   1 dossiernummer-vervanging — steekproef: teksten nog leesbaar, niets kapot-vervangen,
   103 goedgekeurd?
4. **Dashboard-fix** (`status != 'afgesloten'` in KPI's): geen KPI vergeten/te veel
   gefilterd? (opened/closed-per-maand bewust ongemoeid.)
5. **Bulk-goedkeuren-feature**: raakt hij echt alleen status 'kandidaat'?
6. Beantwoord Arsalans openstaande vragen uit het gesprek en rapporteer in gewoon
   Nederlands (geen jargon): wat was goed, wat was fout, wat is hersteld.
Daarna wacht op Arsalans go → hij zet Opus aan voor de herstel-sprint.

## Aanleiding (Lisanne's check van de proefzaken, 6 juli)
1. **Bijlagen ontbreken.** 3.367 geïmporteerde mails hebben `has_attachments=true`, maar er
   bestaan maar 34 echte `email_attachments`-records (allemaal van de live Graph-sync). De
   S168-import zette alleen de vlag; bijlagen zijn nooit uitgepakt. Ook de losse
   dossier-documenten (PDF's zoals `100062_Sommatie.pdf`, `.msg`) zijn nooit geïmporteerd
   (leinout=6 werd bewust geskipt).
2. **Rente (IN100521) — GECORRIGEERD in S175d + nacheck S177, oude analyse hieronder
   doorgestreept.** "BaseNet €2.674" was een verlezen getal: BaseNet's eigen som
   (`inclcalculatedinterest`) = **€6.274,76** (476,67 + 5.181,24 + 616,85, peildatum
   9 juni). De zaak heeft GÉÉN deelbetalingen (`cachedpayments*=0.00`, ook niets in de
   betalingen-XML). Het tarief stond wel echt fout (import: b2b→handelsrente) — dat is
   in S175d al GEFIXT: alle 3 proefzaken staan live op contractueel 2%/mnd enkelvoudig
   (nacheck S177 bevestigt). Restverschil op peildatum 9-6: Luxis €5.942,54 vs BaseNet
   €6.274,76 (+5%) — BaseNet laat rente vóór de vervaldatum ingaan (±verstuurdatum,
   30-dagen-maanden); Luxis rekent juridisch zuiver vanaf vervaldatum.
   **Beoordelingsvraag Lisanne, geen bug.** ~~Oud (fout): "BaseNet €2.674 kan alleen
   kloppen met deelbetalingen en/of eerdere peildatum; vergelijken pas zinvol na
   betalingen-import."~~

## Bronnen (haalbaarheid gecheckt)
- **11 documenten-zips staan lokaal**: `C:\Users\arsal\Documents\luxis\1601*.zip` (~8,5 GB,
  NIET committen, `.gitignore` dekt al). Map per dossier `"D{lepcode} {opdrachtgever} _
  {wederpartij}"`, bestand-prefix = `letterno`. Bevat .eml (correspondentie, mét bijlagen
  erin) + losse .pdf/.msg (documenten).
- **Metadata-XML GEVONDEN (6 juli):** `C:\Users\arsal\Documents\luxis\Xml_02-07-2026_2400.zip`
  (3,8 MB, NIET committen). Bevat alles wat nodig is — geverifieerd:
  `304_68..71 Letter.xml` (4 delen, ~29 MB → letterno→systemid, exacte bijlage-match),
  `230_55 Incasso.xml` (2,9 MB → lepcode→inccode + **incinterest = contract-tarief per
  zaak** → rente-config automatisch te zetten), `231_56 IncassoBetalingAnders.xml` +
  `232_57 IncassoBetalingsRegeling.xml` (= fase 1b betalingen). `Payment.xml` =
  kantoorfacturen, skippen (S168 §A). Parser-kennis: `scripts/basenet/parse.py`.

## Taken (volgorde belangrijk)
### A. Bijlagen-backfill (grootste zichtbare gemis)
1. Script (lokaal parsen, upload naar VPS): per .eml met bijlagen → match synced_email
   (systemid via XML, anders onderwerp+datum) → bijlage-bestanden opslaan zoals de
   Graph-sync dat doet (zelfde storage-pad-conventie + `email_attachments`-records).
   Bestudeer eerst `email/sync_service.py` bijlage-opslag + `attachment_models.py`.
2. Dry-run met tellingen (verwacht: duizenden bijlagen bij 3.367 mails) → steekproef
   5 dossiers met Arsalan → uitvoeren. Frontend: bijlagen openen moet dan gewoon werken
   (bestaand download-endpoint).
3. Losse .pdf/.msg-documenten → `case_files` ("Bestanden"-tab), alleen als de
   metadata-zip er is (anders doorschuiven — geen fuzzy koppeling op prod-dossiers).
### B. Betalingen (fase 1b) — batch-recept; proefzaken zijn vrijwel leeg (nacheck S177)
Geverifieerd tegen de XML: IN100521 en IN100040 hebben GÉÉN betalingen;
IN100215 heeft 2 regeling-termijnen. B is dus vooral voor de batch, niet om de
proefzaken "kloppend" te maken (dat was de verlezen-getal-aanname, zie Aanleiding §2).
Bronnen: `231_56 IncassoBetalingAnders.xml` (echte betalingen: `incppaydate`/
`incpamount`/`incpincassoid`) + `232_57 IncassoBetalingsRegeling.xml`.
⚠️ **Regeling ≠ betaling:** 232 bevat termijn-AFSPRAKEN (gepland); klakkeloos
importeren als ontvangen geld maakt de rente juist fout. Eerst per zaak toetsen
(tegen `cachedpayments*` in Incasso.xml of navraag Lisanne) of termijnen echt
betaald zijn.
LET OP art. 6:44: kosten → rente → hoofdsom; betaaldatum bepaalt rente-knip.
### C. Rente-config heropende zaken — GROTENDEELS KLAAR (S175d, nacheck S177 bevestigt)
Alle 3 proefzaken staan al live op contractueel 2.00/monthly/enkelvoudig — exact
conform BaseNet-XML (`incinterest=2.00`, `incssamengesteld=false`; geldt voor 573
van de ~607 zaken) én conform AV art. 13.3 (2%/mnd). Wat er nog WEL ligt:
1. **Conventie-vraag Lisanne:** BaseNet laat rente ±verstuurdatum ingaan
   (30-dagen-maanden), Luxis vanaf vervaldatum (+5% verschil op IN100521 per 9-6).
   Welke houden we aan? (Luxis' aanpak is juridisch zuiver — advies: zo laten.)
2. **Bevestiging Lisanne** dat 2%/mnd ook voor de Incassocenter-proefzaken klopt
   (XML zegt 2.00, staat al zo ingesteld — alleen bevestigen, niet navragen-en-wachten).
3. **Batch-recept** voor toekomstige heropeningen: tarief uit Incasso.xml per zaak
   (klaar om te automatiseren zodra meer zaken heropend worden). Archief NIET aanraken.
4. **Klein gaatje uit nacheck S177:** het pijplijn-verdeling-overzicht op de
   rapportenpagina mist het archief-filter (`status != 'afgesloten'`) dat de rest van
   de KPI's in S175b wel kreeg. Nu onschadelijk (0 zaken in een stap), wel dichtzetten.

### D. FEATURE: Luxis leest de rente-afspraak zelf uit de AV van de cliënt (opdracht Arsalan, 6 juli avond)
**Principe (letterlijk Arsalans wens):** Luxis voert ALTIJD uit wat er in de algemene
voorwaarden van de cliënt staat. De 2% is maar een voorbeeld — wat er in de AV staat,
geldt. Luxis LEEST dat zelf en houdt het aan, tenzij wij het veranderen. Override-
hiërarchie: **dossier > klantkaart > uit-AV-gelezen > wettelijk**. De bestaande
aanpas-schermen (klantkaart-rente-instellingen + dossier-formulier, DF138-13) blijven
exact zoals ze zijn — die zíjn de override.
Bouwrichting (4-stappen-werkwijze: eerst plan presenteren!):
1. Bij AV-upload (`contact_terms`) én eenmalig voor bestaande AV's: rente-bepaling uit de
   PDF-tekst halen (regex eerst; AI-extractie als vangnet — Haiku, één call per document).
2. Gelezen waarde als standaard op de cliënt toepassen, mét zichtbare herkomst in de UI
   ("uit AV gelezen: 2%/maand, artikel X") zodat het transparant en corrigeerbaar is.
   Handmatig aangepaste waarden NOOIT overschrijven bij een her-upload.
3. AV zegt niets over rente → terugval wettelijk + dit zichtbaar melden bij de cliënt.
   **CORRECTIE (6 juli, arsalan + geverifieerd tegen de PDF's op prod):** alle drie de
   AV-documenten (Invorderingsbedrijf, Collect 1, Incassocenter) bevatten WÉL een
   rente-bepaling: artikel 13.3 = 2% per maand vanaf de vervaldag van de factuur.
   De eerdere claim "geen rente-percentage" was fout. Nuance: 13.3 gaat letterlijk over
   facturen van het incassobureau aan haar eigen klanten; toepassing op de ter incasso
   aangeboden vorderingen loopt via art. 2.8 — Lisanne hanteert 2%/mnd als contractueel
   tarief, dat is leidend.
4. D-Break is geen vaste opdrachtgever — niet meenemen in tests/voorbeelden.

## NIET doen
- Geen zips committen (8,5 GB). Geen fuzzy dossier-koppeling zonder akkoord.
- Archief-zaken (afgesloten) NIET van tarief wisselen — alleen heropende werkvoorraad.
- Geen klantkaart-defaults zetten zonder het akkoord-lijstje uit stap D.2.

## Sessie-einde
SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-177`, PROMPT-S178.
