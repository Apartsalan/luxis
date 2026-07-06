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

## Stap 0 (Fable) — nacheck van alle S175-dag-acties, verse ogen
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
2. **Rente klopt niet (IN100521).** BaseNet €2.674, Luxis €3.008 (handelsrente). Contract
   = 2%/mnd vanaf vervaldatum → dat zou t/m vandaag ~€7.113 zijn. Conclusie: (a) tarief
   staat fout (import zette b2b→handelsrente, contractueel tarief ging verloren), én
   (b) BaseNet's bedrag kan alleen kloppen met verwerkte deelbetalingen (fase 1b = bewust
   overgeslagen) en/of een eerdere peildatum. Vergelijken is pas zinvol na betalingen-import
   + zelfde peildatum + juist tarief.

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
### B. Betalingen (fase 1b) — voor de 3 proefzaken, daarna het recept voor de rest
Uit de metadata-XML (of handmatig van Lisanne per proefzaak): betalingen invoeren.
LET OP art. 6:44: kosten → rente → hoofdsom; betaaldatum bepaalt rente-knip.
### C. Rente-config heropende zaken
Per heropende zaak het contract-tarief zetten: IN100521 = contractueel 2%/mnd
(`interest_type='contractual'`, `contractual_rate=2.00`, claims `rate_basis='monthly'`,
`contractual_compound`: navragen bij Lisanne, default enkelvoudig=false). Voor
IN100215/IN100040 (Incassocenter): tarief navragen. PAS NA de betalingen omzetten —
anders schrikt iedereen weer van een hoger bedrag. Daarna: rente naast BaseNet leggen
op DEZELFDE peildatum (Lisanne opent BaseNet's rente-specificatie).

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
3. AV zegt niets over rente (al bekend: de huidige documenten van Collect 1 en
   Incassocenter bevatten géén rente-percentage — mogelijk moet de echte debiteur-AV
   nog geüpload worden) → terugval wettelijk + dit zichtbaar melden bij de cliënt.
4. D-Break is geen vaste opdrachtgever — niet meenemen in tests/voorbeelden.

## NIET doen
- Geen zips committen (8,5 GB). Geen fuzzy dossier-koppeling zonder akkoord.
- Archief-zaken (afgesloten) NIET van tarief wisselen — alleen heropende werkvoorraad.
- Geen klantkaart-defaults zetten zonder het akkoord-lijstje uit stap D.2.

## Sessie-einde
SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-177`, PROMPT-S178.
