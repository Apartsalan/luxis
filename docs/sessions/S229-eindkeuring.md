# S229 — Grote eindkeuring (Fable, 18 juli 2026)

Op verzoek Arsalan: één brede, zelfstandige keuring van heel Luxis — verzendroutes ×
huisregels, financiële steekproef op de cent, beveiligingsregels, en AI-antwoordkwaliteit
incl. de auto-concept-poort. **Alles alleen-lezen op productie; niets verstuurd, niets
gewijzigd.** Elke bewering hieronder is deze sessie zelf gemeten (bron erbij).

## Samenvatting

Het fundament staat er goed bij: alle verzendregels zijn in de praktijk gehouden, de
rekenmotor klopt op de cent (12/12 narekeningen), de rijbeveiliging is live bewezen.
**Drie echte vondsten:** (V1) 27 consumentenzaken dragen samen €9.794,65 méér
incassokosten dan de wettelijke staffel toestaat; (V2) het handelsrente-tarief van
1 juli 2026 (10,4%) ontbreekt in de rentetabel; (V3) de auto-concept-poort werd in S222
tegengehouden door een miskalibreerde beoordelaar, niet door de AI — 4 van de 6 "zware
fouten" zijn nu hard weerlegd.

---

## Spoor 1 — Verzendroutes × huisregels (GROEN)

**Code-kant:** route-inventaris vers opgebouwd (grep op de verzendlaag): 2 provider-
uitgangen (compose/send, gedeeld kanaal `send_with_attachment`) + 2 gemotiveerde
SMTP-uitgangen (instellingen-test, wachtwoord-reset) — exact gelijk aan de allowlists in
`tests/test_send_route_drift_guard.py`. Gates (mailslot, 14-dagenbrief incl. .eml-route,
rente-bijlage) aanwezig op alle routes. CI groen op laatste main (run 29602635217,
14m37s) = alle wachters groen.

**Praktijk-kant (prod-DB, read-only):**
- 34/34 uitgaande mails sinds 15 juli: afzender `incasso@kestinglegal.nl` (M1 ✅).
- 0 verzendlogs zonder bijbehorende synced-mail of dossier-activiteit (M2-drieluik ✅).
- Onderwerpen: allemaal huisformaat, Re:-formaat of gemotiveerde uitzondering (M4 ✅).
- 0 stap-teksten of antwoordsjablonen met oud adres/oud mailadres (S220/S226-sanering
  houdt stand ✅).
- 0 open concepten en 0 open adviezen op gesloten zaken (P3 ✅); 0 open taken op
  gesloten zaken; 0 wees-records (mails/vorderingen naar niet-bestaande zaken).
- 0 dubbele dossiernummers; 0 actieve B2C-zaken voorbij de 14-dagenbrief-stap zonder
  verstuurbewijs in de staphistorie.
- Observatie (niet verder uitgezocht): 22 wachtende classificaties, 146 ongelezen
  notificaties.

## Spoor 2 — Financiële steekproef (GROEN, met 2 vondsten in de randen)

**Rente op de cent: 12/12.** Eigen, onafhankelijke narekening (eigen script, niet de
app-code; `scratchpad/narekening.py`) tegen de systeemuitkomst via de prod-API, over 6
gevarieerde dossiers (IN100377, IN100049, IN100388, IN100604, IN100180, IN100531):
wettelijke rente met jaarkapitalisatie over de tariefwissel 6%→4% heen, contractuele
2%/mnd met deelmaanden en maandkapitalisatie, creditfacturen (negatieve rente),
bevriesdatums, vorderingen ná de bevriesdatum (terecht €0). Alle 12 bedragen exact
gelijk.

**Betaling-toerekening (art. 6:44) klopt:** IN100377 (300,00 = 66,75 kosten + 17,92
rente + 215,33 hoofdsom) en IN100180 (1.800,00 = 319,21 + 439,21 + 1.041,58) sluiten op
de cent, in de juiste volgorde; de rente-allocatie is exact de berekende rente op de
betaaldatum.

**Rentetabel gecontroleerd tegen de officiële bron:** consumententarieven kloppen
(6% 2025, 4% per 1-1-2026, conform Stb.-verwijzingen in de tabel).

### V1 — 27 consumentenzaken boven de wettelijke kosten-staffel (€9.794,65)
80 actieve B2C-zaken dragen een handmatig kostenbedrag (`bik_override`, BaseNet-import).
Bij 27 daarvan is dat een **vlakke 15% van de hoofdsom** waar de wettelijke staffel
(dwingend recht voor consumenten, art. 6:96 BW) lager uitkomt: samen **€9.794,65 te
veel**, gemiddeld exact 15,0%. Grootste: IN100082 (€4.908,21 waar €1.102,21 mag).
Alle betrokken opdrachtgevers zijn btw-plichtig → ook geen btw-opslag-recht dat het
verschil zou dichten; bij 12 zaken is het bedrag zelfs hoger dan staffel+21%.
Steekproef debiteuren: allemaal natuurlijke personen zonder KvK-nummer.
- De app-wachter (AUDIT-23) blokkeert dit op de wijzig-route; de import is er destijds
  omheen gekomen. Geen van de 27 staat op een actieve pijplijnstap (geen acute
  mailing), maar het bedrag zit in elk financieel overzicht en elk AI-antwoord dat het
  totaal noemt.
- **Nuance:** een natuurlijke persoon kan tóch ondernemer zijn (eenmanszaak) — dan is
  de staffel niet dwingend. De rechtsvorm-backfill beslecht dit definitief per zaak.
- **Werkorder (deel 2, na GO):** per zaak `bik_override` → NULL (systeem rekent dan
  zelf de staffel) voor bevestigde consumenten; lijst van 27 in deze sessie gemeten.
  Wachter-kandidaat: periodieke/DB-brede check `b2c && bik_override > staffel` (de
  soort, niet het geval — dezelfde fout kan bij elke toekomstige import terugkomen).

### V2 — Handelsrente 1 juli 2026 ontbreekt in de rentetabel
Officieel (Rijksoverheid): handelsrente **10,4% per 1-7-2026**. De tabel eindigt bij
10,15% (1-7-2025); de rij 2026-07-01 ontbreekt (tabel gevuld 18-2-2026). Gevolg: de 7
actieve zaken op wettelijke handelsrente rekenen sinds 1 juli 0,25 punt te láág
(nadeel cliënt; cent-werk na 17 dagen, maar het loopt op). Zelfde geldt voor het
overheidstarief (0 actieve zaken).
- **Werkorder:** rij toevoegen (data-only, dry-run + GO). **Wachter-kandidaat:** een
  actualiteitscheck "nieuwste tarief ouder dan ~7 maanden → waarschuwing" (de tabel
  wisselt elk halfjaar; niets bewaakt dat nu).

## Spoor 3 — Beveiliging (GROEN, 1 klein punt)

- **Rijbeveiliging live bewezen op prod:** app-databaserol is superuser, máár de app
  neemt per verzoek de beperkte rol `luxis_app` aan (geen superuser, geen bypass).
  Onder die rol: query zónder tenant-instelling → **foutmelding (faalt dicht)**;
  met vreemde tenant → **0 van de 626 dossiers**. Alle 44 tenant-tabellen: RLS aan +
  FORCE aan + policy aanwezig (enige uitzondering `users`, bewust).
- Secrets-scan backend+frontend: schoon; geen gevoelige `NEXT_PUBLIC_*`.
- Live: `/api/cases` zonder token → 401. Auth-wachter draait in CI (groen).
- Firewall: alleen 22/80/443. Upload-validatie-helpers aanwezig.
- **V4 (klein):** `/opt/luxis/.env` staat op 644 (leesbaar voor alle serveraccounts);
  600 is passend. Alleen root heeft shell-toegang → laag risico, wel even doen.

## Spoor 4 — AI-antwoordkwaliteit + auto-concept-poort

De S222-poortmeting (55 gevallen, "6 zware fouten, 4 generatiefouten" → poort DICHT)
is nagelezen; de 6 zware gevallen zijn stuk voor stuk herbeoordeeld, mét feitencheck
op prod waar dat kon:

| # | Geval | Corrector zei | Werkelijkheid (bewijs) |
|---|-------|----------------|------------------------|
| 1 | IN100418 "€40,87 verzonnen" | bedrag klopt niet met facturen | **AI had gelijk**: echt openstaand = €40,87 (hoofdsom 3.246,67 op 40,87 na betaald — financial-summary prod) |
| 2 | IN100122 "€22,64 verzonnen" | onrealistisch laag | **AI had gelijk**: echt openstaand = €22,64 (338,71 van 361,35 betaald) |
| 3 | IN100370 "dossiernummer verzonnen" | nummer nergens te vinden | **aantoonbaar onzin**: IN100370 staat letterlijk in het onderwerp van de inkomende mail |
| 4 | "Kesting Legal te Amsterdam verzonnen" | naam/plaats niet in dossierfeiten | kantoornaam is geen dossier-feit; zelfde formulering elders goedgekeurd |
| 5 | Deelbetaling "impliciete toezegging" | terugkoppel-uitnodiging = toezegging | te streng: de mail zegt expliciet dat de verplichting onverkort blijft |
| 6 | Betaalbelofte "aanstaande vrijdag" | verkeerde datum + toezegging | **deels terecht**: debiteur beloofde "volgende week vrijdag", AI eiste "aanstaande vrijdag" zonder dat verschil te benoemen — onhandig, hooguit middelzwaar |

**Herscoord: hooguit 1 middelzware fout op 51 geslaagde generaties (~2%), 0 verzonnen
bedragen.** De 4 "generatiefouten" waren gevallen waarin de goud-lader een interne
ketenmail (niet van de debiteur) aanbood; de AI signaleerde dat correct maar crashte op
het antwoordformaat — een gebrek in het testtuig, feitelijk gewenst modelgedrag.

**Advies poort:** de poort werd tegengehouden door de beoordelaar, niet door de AI.
Volgorde voor deel 2: (a) corrector herkalibreren met drie regels — openstaand bedrag
toetsen aan dossierdata i.p.v. factuur-optelsom; kantoornaam/dossiernummer-uit-onderwerp
zijn geen hallucinaties; terugkoppel-uitnodiging naast een expliciet
"verplichting blijft" is geen toezegging — (b) niet-debiteur-mails netjes laten
weigeren i.p.v. JSON-crash, (c) verse ronde draaien, en dan (d) de afgesproken
menselijke steekproef (Lisanne, ~10 concepten) als laatste poort. Geen verse testronde
gedraaid vandaag: met een miskalibreerde beoordelaar reproduceert die alleen dezelfde
ruis (en kost hij geld).

---

## Werkorders deel 2 (volgorde-voorstel)

1. **V1** B2C-kostenlijst (27 zaken) → met Arsalan/Lisanne: bevestigde consumenten
   `bik_override` leegzetten (dry-run + telling + GO); eenmanszaak-twijfelgevallen
   parkeren tot de rechtsvorm-backfill. + DB-wachter voor de soort.
2. **V2** Handelsrente-rij 1-7-2026 toevoegen (data-only, GO) + actualiteits-wachter.
3. **V3** Corrector herkalibreren + goud-lader-fix + verse ronde + Lisanne-steekproef.
4. **V4** `.env` naar 600 (één commando).

*Niet geverifieerd vandaag:* wat de 22 wachtende classificaties/146 ongelezen
notificaties precies zijn (observatie, geen oordeel); of de 27 V1-debiteuren écht
allemaal consument zijn (10 gecheckt, allen particulier ogend; KvK-backfill beslecht).
