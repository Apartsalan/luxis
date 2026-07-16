# S222-review — Fable-natoets van Deel 1 (verzoekschrift) + S220/S221 + testronde + backfills

**Datum:** 16 juli 2026 (nachtsessie, autonoom — Arsalan slaapt)
**Reviewer:** Fable (Deel 2 van PROMPT-S222); Deel 1 gebouwd door Opus eerder deze sessie.
**Prod-stand bij start review:** commit `d926d57`, migratie `s221_ai_draft_intent_step` = head.
Tijdens de review is `118617a` (script-fix, zie C1) gedeployed.

---

## A — Verzoekschrift exacte nabouw (Deel 1) ✅ bevestigd, wacht op GO

Getoetst op de ingevulde testrender (testgegevens, geen echte debiteur) naast Lisanne's
doel-PDF (`templates/lisanne/CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf`):

| Toets | Uitkomst |
|---|---|
| Lay-out = doel-PDF | ✅ crème-balk (#fbf5ed) + gecentreerd logo p1, logo-kop p2-5, voettekst "Pagina X van 5", Calibri, randloze tabellen met dunne lijnen — pagina voor pagina visueel vergeleken |
| Bedragen op de juiste plek | ✅ beide tabellen (brief p1 + verzoekschrift p3/4) tellen exact op: 3.500 + 1.200 = 4.700 → +145,32 → +588,50 +123,59 = 5.557,41; betaal-scenario: −1.000 → 4.557,41. Twee scenario's gerenderd (met/zonder deelbetaling) |
| Logo + huidig adres | ✅ KESTING LEGAL-logo in de kop; Willem Fenengastraat 16E / 1096 BN / incasso@ / 020-3086621 op p5 (oud IJsbaanpad/1076 CV/kesting@ vervangen) |
| Geen BaseNet-resten | ✅ onafhankelijke hercheck op het eindbestand: 0× MERGEFIELD/$data/#foreach; enige veld-resten = PAGE/NUMPAGES (paginanummering, hoort zo). 48 invulvelden + 4 lus-markeringen |
| Reseed byte-identiek op prod | ✅ **LIVE (16 juli, GO Arsalan + 4 keuzes bevestigd: watermerk houden, Verzuimdatum, 1 betaalregel, witruimte-handtekening).** Back-up `/root/backup_managed_templates_pre_s222_verzoekschrift.sql`; alleen de verzoekschrift-rij bijgewerkt (45658→86951 bytes); DB-hash = schijf-hash = lokaal-hash. **Live-render door het echte systeem op zaak IN100521:** debiteur/opdrachtgever/3 facturen correct, totalen op de cent (€ 75.322,42), BTW-regel valt terecht weg (btw-plichtige cliënt). |

**Kanttekening (bouwkeuzes die afwijken van Lisanne's origineel, gemeld aan Arsalan):**
de per-zaak-gegevens die haar sjabloon wél toont maar Luxis niet apart bijhoudt
("Voldaan bij klant" vs "Door ons ontvangen", losse overige-kostenregels) zijn
samengevoegd naar de bewezen Luxis-velden. Geen bedrag verzonnen; alles komt uit de
bestaande render-service.

## B — S220/S221 natoetsen op prod

### B1 Overgeslagen/afgeronde taken (3.4) ✅ LIVE BEWEZEN (het gat uit S221 gedicht)
Live doorgeklikt op prod (was in S221 niet gelukt door browserlock):
- "Afgerond"-weergave toont 19 taken (afgerond + overgeslagen) met terugzet-knop.
- Terugzetten op taak van testdossier 2026-00006: teller 8→9 open / 19→18 afgerond,
  taak verscheen als "Gepland" op de werklijst. ✅
- Daarna weer overgeslagen (oorspronkelijke staat hersteld): melding "Taak overgeslagen"
  mét "Ongedaan maken"-knop verscheen. ✅
- Dashboard-widget toont nog steeds alleen open taken. ✅

### B2 Ontdubbelen + zombie-opruiming (3.2/N3) ✅ code bewezen, ⚠️ prod-gedrag nog onbenut
- Migratie `s221_ai_draft_intent_step` staat op head op prod. ✅
- 0 dubbele open concepten per zaak+stap én per zaak+bronmail (SQL-telling). ✅
- 23 tests groen (dedupe ×3, discard, supersede-suite). ✅
- **Maar:** alle 10 concepten op prod dateren van vóór de uitrol (`intent` overal leeg)
  — er is nog géén concept via het nieuwe pad gemaakt. Het prod-gedrag zelf is dus
  onbenut; bewijs komt uit de tests.
- **Nieuwe vondst 1:** IN100613 is **afgesloten** (15-07 19:27) maar houdt 2 open
  concepten vast → zaak-sluiten ruimt concepten NIET op (stap-wissel wél). Gat naast
  S221-bouw; zelfde familie als de zombie-vondst N3.
- **Nieuwe vondst 2:** IN100521 heeft 2 identieke open verzoekschrift-concepten
  (beide 15-07, vóór de migratie, `intent` leeg) → de ontdubbeling werkt alleen op
  nieuwe concepten; deze twee blijven staan tot iemand ze opruimt (→ backfills, zie D).

### B3 Classificatie direct ná sync (blok 4) ⚠️ AANNEMELIJK, NIET BEWEZEN
- Code staat in de draaiende prod-container (regel 309 `if total_new > 0` + S221-comment,
  in de container zelf gecontroleerd). ✅
- **Maar:** (a) er is sinds de uitrol geen nieuwe mail binnengekomen → de trigger heeft
  nog nooit gevuurd (logs: alle syncs "0 nieuw"); (b) er bestaat **geen test** die dit
  gedrag dekt (hele testmap: 0 verwijzingen naar de trigger). De S221-claim
  "latency → ~5 min" is dus theorie. **Advies:** test toevoegen + bij de eerstvolgende
  echte mail de logvolgorde controleren (sync → classificatie → "auto-sync klaar").

### B4 UX-punten ✅ allemaal live gecontroleerd
- Zijbalk: geen "Intake" meer (ingang via Mail-tab); "Betalingen" i.p.v. "Bankimport". ✅
- Rapportages: "Geïnd op lopende zaken" (4,8%) mét uitleg-tooltip. ✅
- Maillijst: dossiernummers zijn klikbare links naar de zaak. ✅
- Lettertype: alle 9 prod-sjablonen op Calibri (theme-check in prod-DB). ✅
- "Geen spatie-kolommen": bewezen op de 58 verse AI-antwoorden uit de testronde —
  0 antwoordregels met kolom-lay-out, 17 gelabelde regels ("Hoofdsom: € 3.500,00"). ✅

## C — AI-antwoord-testronde (goud 40)

### C1 Script-bug gevonden + gefixt (commit `118617a`, gedeployed)
De goud-route (`--goud`) crashte direct op prod met een mapper-fout: het losse script
laadt de modellen niet die de zaak- en mailtabellen nodig hebben (IncassoPipelineStep,
EmailAccount, …). **De S221-rookproef draaide alleen de zelfgeschreven set — het
goud-pad was nooit uitgeprobeerd.** Fix: volledige model-registry laden (zelfde lijst
als de migratietool), lokaal bewezen, gecommit, gepusht en gedeployed.

### C2 Goud-vergelijking toetste het verkeerde ding (ontwerpfout, gevonden + gefixt)
Tijdens ronde 1 weigerde de AI 17 goud-gevallen: "dit is een uitgaande mail van uw
eigen kantoor". Eerste hypothese (bibliotheek-vervuiling) bleek FOUT na meting:
**alle 103** goedgekeurde bibliotheek-antwoorden hebben een eigen-kantoor-mail als
bron — en dat hoort zo: `source_synced_email_id` is per modeldefinitie *"de
verstuurde mail waaruit het antwoord is geknipt"* (Lisanne's antwoord). Het
S221-script voerde die antwoorden echter als te beantwoorden *vraag* aan de AI —
de goud-ronde mat dus niets, en de weigeringen waren correct AI-gedrag.
**Fix (commit `90ad871`, gedeployed):** de lader zoekt nu per goud-geval de laatste
inkomende debiteurenmail vóór Lisanne's antwoord in dezelfde zaak (alle 103 gevallen
hebben er een — geteld) en legt díe voor; Lisanne's antwoord blijft de referentie.

### C3 Uitkomst ronde 1 (58 gevallen: 18 proefset + 40 goud)
- **Proefset (geldig): 15/18 groen = 83%** — onder de 90%-lat. 3 zware fouten,
  2 patronen: (1) *betaalbelofte/kwijtschelding*: het "voorleggen aan de cliënt" las
  als impliciete opschorting/toezegging; (2) *boze mail*: de AI rekende zelf een
  uitsplitsing uit ("kosten en rente € 112,40" = 812,40 − 700) die niet in het
  dossier staat. Verder: 0 generatie-fouten, geen verzonnen namen/factuurnummers,
  identiteitsvraag/advocatenbrief/AVG/faillissement allemaal correct behandeld.
- **Goud ronde 1: ongeldig** (zie C2) — 17 weigeringen + 5 "zware" op verkeerde input.
- **Bijvangst:** 0 spatie-kolommen in alle 58 antwoorden (bewijs voor B4/punt 11).

**Corrector zelf gecontroleerd:** de 2 hardste afkeuringen zelf nagelezen — beide
terecht (betaalbelofte: "voldoen zodra u een bevestiging van ons heeft ontvangen"
maakt betaling afhankelijk van ons bericht; boze mail: "Kosten en rente: € 112,40"
is een eigen rekensom, geen dossierfeit). De corrector oordeelt streng maar juist.

**Spelregels aangescherpt (zelfde commit):** (1) bedragen alleen letterlijk uit het
dossier, geen eigen uitsplitsingen/aftreksommen; (2) verzoek doorzetten mag, maar
altijd met de melding dat betalingsverplichting en termijnen doorlopen — nooit de
indruk wekken dat de invordering stilligt.

### C4 Uitkomst ronde 2 (na fixes, zelfde set + geldige goud-vergelijking)
55 gevallen (18 proefset + 37 goud; 3 goud-gevallen vielen af zonder bruikbare vraag).

- **Proefset: 16/18 groen = 89%** (was 83%). De uitsplitsingen-fout is weg (boze mail
  nu groen). De 2 resterende afkeuringen zijn allebei hetzelfde patroon én allebei een
  **kalibratiekwestie, geen duidelijke AI-fout**: de AI neemt een betaalbelofte "voor
  kennisgeving aan" en vraagt betaling op de beloofde datum (corrector: "impliciet
  uitstel"), en belooft een kwijtscheldingsverzoek "voor te leggen mét terugkoppeling"
  (corrector: "procedure-toezegging"). In de praktijk zou Lisanne dit vermoedelijk ook
  zo schrijven — of de corrector hier te streng is, is een inhoudelijke keuze voor
  Arsalan/Lisanne (zie beslispunten).
- **Goud (eerste geldige meting): 29/37 groen = 78%, 6 "zwaar", 2 generatie-fouten.**
  Maar de 6 afkeuringen zijn niet zonder meer AI-fouten: 1 is een aantoonbare
  corrector-misser (toelichting spreekt zichzelf tegen; het antwoord noemt exact het
  dossierbedrag én de juiste blijft-gelden-formule — zelf nagelezen, antwoord is
  voorbeeldig), en meerdere andere zijn "dossierbedrag ≠ bedrag in de oude mailwisseling"
  — terwijl het dossierbedrag mét aangegroeide rente per spelregel juist het énige
  toegestane bedrag is. De corrector kan actuele bedragen niet van verouderde
  thread-bedragen onderscheiden. De 2 generatie-fouten: de vraag-zoeker pakte een mail
  van de **opdrachtgever** i.p.v. de debiteur (AI weigerde terecht) — bekende beperking,
  makkelijk aan te scherpen.
- Óók in ronde 2: 0 spatie-kolommen, 0 verzonnen namen/factuurnummers in de proefset.

### C5 Eindoordeel poort (auto-concept per categorie)
**Formeel NIET gehaald** (>90% groen én 0 zware fouten) → **auto-concept blijft UIT.**
Eerlijke duiding: de antwoordroute zelf is duidelijk verbeterd (83→89% op de zuivere
set; het bedragen-verzin-patroon is weg; escalatie en identiteitsvragen foutloos), en
een flink deel van de resterende afkeuringen ligt aan de méétlat (corrector), niet aan
de antwoorden. Verder blind itereren tegen deze corrector heeft geen zin — eerst de
kalibratievraag beantwoorden (mag "voor kennisgeving aannemen"/"voorleggen mét
terugkoppeling"?), dan de corrector daarop bijstellen, dan pas opnieuw meten.

## D — Backfill-wachtrijen (alleen gemeten, NIETS opgeruimd — wacht op GO)

Alle cijfers rechtstreeks uit de prod-database (16-07 nacht):

| Wachtrij | Stand | Herkomst | Veilig op te ruimen? |
|---|---|---|---|
| A. Classificaties `pending` | **470** | 297 mails van vóór 2026, 170 jan–jun; oudste 30-12-2024 → vrijwel alles BaseNet-import-historie | **339** horen bij een afgesloten/betaalde zaak → JA (sluiten). Nog eens **110** = actieve zaak maar mail vóór 1 juni → JA. Rest = **21** recente op actieve zaken (11 échte debiteurreacties + 10 "niet gerelateerd"/uithanden-mails) → handmatig/deels |
| B. Intake | **14** `pending_review` (+1 failed, 7 rejected) | allemaal 15-07 (demodag-ruis; "intake-detectie dempen" staat al op de restlijst) | beoordelen of dempen; geen historie-probleem |
| C. Concepten open | **8** | 2× IN100613 (zaak afgesloten!), 2× IN100521 (identiek, pre-migratie), 4 overige 09–15 juli | de 2 op de afgesloten zaak + 1 van het IN100521-duo → JA; rest is actueel werk |
| D. Follow-up-adviezen | **15** `pending` (09–13 juli) | dit is de actuele werklijst (badge "Follow-up 15") | **NEE — geen opruimkandidaat.** De "3 stale adviezen" uit S219 bestaan niet meer als aparte groep |
| E. Ongelinkte mails | **96** totaal = 40 échte open inkomende (30 ouder dan 30 dagen) + 39 uitgaand + 17 dismissed/bounce | zijbalk telt 79 = 96 minus 17 dismissed | koppelen is handwerk; de 39 uitgaande zijn kandidaat voor automatische demping in de teller |
| F. Notificaties ongelezen | **348** | **302 = "classificatie klaar"-ruis**; 261 ouder dan 7 dagen | JA: bulk gelezen-markeren ouder dan 7d + type dempen is een beslispunt |

**Opruimrecept UITGEVOERD (16 juli ochtend, GO Arsalan):** proefronde → uitvoering in
één transactie → natelling, alle aantallen exact: 339 + 110 classificaties afgevoerd
(status "rejected" + beoordelaar + notitie "S222-opruimrecept", zoals de afwijs-knop),
**21 recente blijven als echte werklijst**; 3 concepten dichtgezet (2 op afgesloten
IN100613 + oudste IN100521-duplicaat) → 5 open; 232 ruis-meldingen op gelezen (0 over
ouder dan 7 dagen), echte meldingen (termijnen/betalingen/verjaring) onaangeroerd.
Intake-14 en adviezen-15 bewust niet aangeraakt. Niets verwijderd — alles heeft een
spoor en is terug te vinden.

---

## Doorgevoerde wijzigingen deze sessie (review-deel)
1. `118617a` — fix goud-pad testronde-script (imports; zie C1) + deploy.
2. `90ad871` — 2 aangescherpte spelregels in `_REPLY_PROMPT` (zie C3) + goud-lader
   voedt nu de echte debiteurenvraag (zie C2) + deploy. Tests: 20 groen.
3. Prod-taak op testdossier 2026-00006: terugzetten + opnieuw overslaan (netto geen
   wijziging; bewijs voor B1).
4. Verder alles read-only.

## Openstaande beslispunten voor Arsalan/Lisanne
1. ✅ **GEDAAN — verzoekschrift LIVE** (16 juli, alle 4 keuzes bevestigd + live-render bewezen).
2. ✅ **GEDAAN — opruimrecept uitgevoerd** (16 juli ochtend, GO Arsalan; natelling exact, zie D).
3. ~~Goud-bibliotheek schonen~~ — vervallen: de "vervuiling" bleek een ontwerpfout in
   het testscript, niet in de bibliotheek (zie C2). De bibliotheek is in orde.
4. Test voor de sync→classificatie-trigger toevoegen (B3) — klein Opus-klusje.
5. **Kalibratie antwoord-lat (C5):** mag de AI een betaalbelofte "voor kennisgeving
   aannemen" en een verzoek "voorleggen mét terugkoppeling"? Zo ja → corrector-checklist
   daarop bijstellen en testronde herhalen; de 90%-lat is dan realistisch haalbaar.
   Zo nee → hardere spelregel ("nooit een betaaldatum impliciet accepteren") en opnieuw.
6. Vraag-zoeker goud-pad ook opdrachtgever-adressen laten uitsluiten (2 gevallen).

## Kleinere observaties (geen actie vereist)
- AI ondertekende één proefantwoord met "Incasso-afdeling" — Kesting Legal heeft geen
  afdelingen (1 advocaat). Cosmetisch; kan in een volgende spelregel-rondje mee.
- Zaak sluiten laat open concepten staan (IN100613, zie B2) — overweeg concepten
  mee te laten vervallen bij sluiten, zoals bij stap-wissel al gebeurt.
