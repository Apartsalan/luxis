# S230 — Werkorders uit de eindkeuring (V1-V4)

**Datum:** 20 juli 2026 · **Model:** Fable (onderzoek/nacontrole) + Opus (bouw)
**Uitgangspunt:** `docs/sessions/S229-eindkeuring.md` § "Werkorders deel 2".

Arsalan vroeg om elke bevinding uit de eindkeuring éérst opnieuw te bewijzen
("letterlijk vergelijken, pas doorgaan bij 100% zeker") vóór er iets gewijzigd
werd. Dat is per werkorder gedaan; hieronder staat per punt het bewijs, dan de
ingreep, dan de natelling.

---

## V4 — Rechten op het instellingenbestand (AF)

**Gemeten:** `/opt/luxis/.env` stond op 644. Eén stap dieper dan de werkorder:
er staan nog **vijf oudere kopieën** met echte waarden naast (`.env.production`,
`.env.bak-s158/s159/s160-sentry/s197`), allemaal 644 — dezelfde foutsoort, zes
keer. Ook gemeten wie er praktisch bij kan: naast `root` heeft **`github-runner`
een shell én zit in de `docker`-groep** (die groep is de facto root). De
S229-formulering "alleen root heeft shell-toegang → laag risico" was dus te
geruststellend.

**Gedaan:** alle zes bestanden met echte waarden op 600; de twee `*.example`-
bestanden bewust op 644 (staan in git, bevatten geen waarden).

**Natelling:** `find` toont 600 op alle zes, 644 op de twee voorbeelden. App
bleef draaien; daarna nog via de normale inlogroute ingelogd voor de V3-controle,
dus het uitlezen van de instellingen is aantoonbaar intact.

---

## V2 — Handelsrente per 1 juli 2026 (AF, live)

**Gemeten vóór de ingreep (drie onafhankelijke wegen):**
1. Prod-tabel `interest_rates`: nieuwste `commercial` én `government` = 1-7-2025
   (10,15%). 50 rijen per soort, **alle 150 rijen aangemaakt op 18-02-2026 en
   nooit gewijzigd** — de BaseNet-import heeft deze tabel dus nooit aangeraakt
   (dat was Arsalans expliciete twijfel). De importcode schrijft alleen een
   contractueel percentage op de zaak zelf (`scripts/basenet/mapping.py`).
2. Rijksoverheid.nl, letterlijk: *"De wettelijke rente voor handelstransacties
   is sinds 1 juli 2026 10,4%."* Consumentenrente blijft 4% (staat er al).
3. Rekenregel art. 6:119a lid 2 BW: ECB-basisherfinancieringsrente **2,40% per
   17-06-2026** + 8 procentpunt = **10,40%**. Sluit aan op bron 2.

Losse rentetabel-sites (wettelijke-rente.com, wettelijkerente.nl, cj-incasso)
liepen achter en noemden nog 10,15% — vandaar de kruiscontrole via de ECB-regel.
NB: handelsrente wordt níet bij Staatsblad-besluit vastgesteld (dat geldt voor
de consumentenrente, laatstelijk Stb. 2025, 438); hij volgt automatisch uit de
ECB-rente. De `Stb.`-bronvermeldingen bij de bestaande `commercial`-rijen zijn
overgenomen uit migratie 010 en strikt genomen een verkeerd etiket — niet
aangeraakt, buiten de opdracht.

**Impact vóór de ingreep:** nul. Alle 8 zaken met dit rentetype zijn afgesloten
en bevroren (laatste bevriezing 7-5-2026), dus niemand rekende te laag.

**Gedaan:** migratie `s230_handelsrente_2026_07` — `commercial` + `government`
per 2026-07-01 op 10,40, idempotent (`ON CONFLICT DO NOTHING`). Ook de losse
dev-seed (`scripts/seed_interest_rates.py`) bijgewerkt, anders krijgt een verse
ontwikkelaars-database hetzelfde gat terug.

**Natelling op prod:** 51 rijen per soort, nieuwste = 2026-07-01 · 10.40 voor
zowel `commercial` als `government`. Heen-en-weer getest op dev (downgrade → 0
rijen, upgrade → 2 rijen).

**Wachter (de SOORT):** `tests/test_interest_rate_freshness_guard.py`. Een
ontbrekende rij geeft geen foutmelding — het systeem rekent stil door met het
laatst bekende tarief; dát is waarom dit anderhalf jaar onopgemerkt bleef. De
wekker valt om zodra de tabel >7 maanden niet tegen de officiële bron is gelegd.
Bewust een peildatum-constante en niet "nieuwste rij", zodat een halfjaar zónder
tariefwijziging geen vals alarm geeft. De wachter test óók zichzelf: één test
bewijst dat hij bij een verouderde datum echt afgaat.

---

## V1 — Incassokosten boven de WIK-staffel (AF — correctie uitgevoerd)

**GO ontvangen (Arsalan, 20-7):** alle 27 debiteuren zijn bevestigd particulier.
**Uitvoering:** oude waarden dubbel veiliggesteld (DB-tabel `_s230_bik_backup`,
27 rijen, som € 26.601,40 + lokale kopie). Telling vooraf 27 → update in één
transactie (gejoind op id én exact oud bedrag, `UPDATE 27`) → telling na: 0 met
handmatig bedrag. Natelling via drie wegen: de sweep vindt **0** gevallen; de
app-API toont voor IN100082 nu € 1.102,21 (was € 4.908,21) en voor IN100345
€ 385,30 — exact de staffel. Terugdraaien kan per dossier vanuit de backup-tabel.
**Doorwerking bewezen:** het openstaande saldo van IN100009 zakte van € 4.614,72
naar € 4.547,76 — precies de € 66,96 te veel geheven kosten van die zaak.

### Oorspronkelijke meting (vóór de GO)

**Vers gemeten, los van S229 en los van de app-code:** hoofdsom per dossier
opnieuw opgeteld uit de losse vorderingen (klopt bij alle 27 exact met het
opgeslagen totaal), daar met de hand de staffel van art. 6:96 BW op losgelaten:
**27 B2C-dossiers, samen € 9.794,65 te veel**, alle 27 exact 15,0% van de
hoofdsom. Grootste: IN100082 (€ 4.908,21 waar € 1.102,21 mag).

**Drie onafhankelijke wegen komen op dezelfde bedragen uit:**
1. eigen SQL-staffel (hierboven);
2. de app zelf via de live API `GET /api/cases/{id}/bik` — steekproef IN100082,
   IN100298, IN100345, IN100498: 1102,21 / 875,00 / 385,30 / 375,53, alle vier
   gelijk aan de eigen berekening;
3. de nieuwe sweep (zie onder), gedraaid op prod: 27 dossiers, € 9.794,65.

**Debiteurenkant:** alle 27 zijn in de administratie natuurlijke personen,
**0 met KvK-nummer, 0 met btw-nummer, 0 gekoppeld aan een bedrijf**. Alle drie
de opdrachtgevers zijn btw-plichtig, dus er is ook geen btw-opslag die het gat
dicht. Herkomst: alle 27 zijn op **3 juli 2026** in één keer geïmporteerd uit
BaseNet.

**Nieuw t.o.v. S229 — en de nuance die het weer terugdraait.** S229 noemde de 27
"actieve" zaken; vers gemeten staan er **26 van de 27 in Luxis als `afgesloten`**.
Dat leek eerst reden tot terughoudendheid (archiefbedragen wijzigen = afwijken
van wat BaseNet destijds in rekening bracht). Op de vraag van Arsalan — *zijn dit
afgehandelde zaken of moeten ze nog open?* — is doorgemeten, en het antwoord is
duidelijk: **het is een etiket uit de import, geen werkelijkheid.**

| | |
|---|---|
| Status in BaseNet bij de import | 21× Lopend · 3× Wacht · 2× Gereed · 1× Geannuleerd |
| Volledig betaald | **0 van de 27** |
| Nog geen cent ontvangen | **25 van de 27** |
| Nog openstaande hoofdsom samen | **€ 172.692,60** |
| Laatste mailverkeer | 16 van de 27 nog in 2026, laatste 18-06-2026 |

De import zette vrijwel de hele BaseNet-inhoud op `afgesloten` (581 van 626)
omdat Luxis de dagelijkse gang nog niet overneemt. Dit zijn dus **lopende
incassodossiers met openstaande schuld**, niet afgewikkelde historie. Daarmee
vervalt het bezwaar: er is nog niets betaald, dus er is ook geen afgerond
bedrag dat een correctie zou "vervalsen".

**Advies na die meting: alle 27 rechtzetten** (`bik_override` → NULL, systeem
rekent dan zelf de staffel), onder het enige voorbehoud dat er vanaf het begin
lag en dat alleen Lisanne kan wegnemen: **is elke debiteur particulier, of zit
er een eenmanszaak tussen?** De administratie geeft geen enkele aanwijzing voor
ondernemerschap (0 KvK, 0 btw-nummer, 0 bedrijfskoppeling), maar dat sluit een
eenmanszaak niet uit. Niet uitgevoerd deze sessie — wacht op dat oordeel. De
lijst met dossiernummer, debiteur, opdrachtgever en bedragen is klaargezet
(bewust buiten de repo — persoonsgegevens). De oude waarden zijn apart bewaard,
zodat elke correctie per dossier terugdraaibaar is.

**Wél gebouwd — de wachter voor de SOORT:** er stonden al twee wachters op dit
punt (`cases/service.py` AUDIT-23 op de wijzig-route, en de verzendcontrole in
`pre_send_compliance_check`), maar allebei kijken naar het **moment van
handelen**. De import kwam er buitenom en bleef daardoor stil staan.
`find_bik_above_staffel()` loopt nu de **hele database** af; een dagelijkse taak
(06:45 UTC) meldt de uitkomst, gededupliceerd per week. Vijf tests eromheen:
vlakke 15% wordt gevonden (met de hand nagerekend op IN100298), precies-op-de-
staffel niet, B2B niet, zonder handmatig bedrag niet, en de btw-variant
(niet-btw-plichtige opdrachtgever → staffel + 21%) met eigen bedragen.

---

## V3 — Auto-concept-poort (bijgesteld, meting loopt)

**Herbeoordeling van S222 zelf nagerekend op prod (niet overgenomen uit S229):**
- IN100418 — "verzonnen € 40,87": de financiële samenvatting van het systeem
  geeft openstaand **€ 40,87** (totaal 3.774,54 − betaald 3.733,67). AI had gelijk.
- IN100122 — "verzonnen € 22,64": openstaand **€ 22,64** (361,35 − 338,71). Idem.
- IN100370 — "dossiernummer verzonnen": staat **letterlijk in de onderwerpregel**
  van meerdere inkomende mails op die zaak.

De poort werd dus tegengehouden door de beoordelaar, niet door de antwoordroute.

**Gedaan (a) — corrector herkalibreerd** met drie regels, precies op die
misgrepen: (1) het openstaande bedrag uit de dossiergegevens is leidend, nooit
zelf facturen optellen, en afwijken van een verouderd bedrag in de oude
mailwisseling is geen fout; (2) eigen kantoornaam en een dossiernummer uit
onderwerp/body zijn geen verzinsels; (3) voorleggen mét expliciete "verplichting
blijft onverkort gelden" is geen toezegging. De echte vangnetten (verzonnen
feiten, bevestigde toezeggingen) zijn ongemoeid gelaten.

**Gedaan (b) — generatie-fouten bij de wortel.** De vraag-zoeker pakte soms een
inkomende mail van de **opdrachtgever** in plaats van de debiteur; het
cliënt-domein wordt nu uitgesloten. En een weigering in proza telt niet langer
als storing: die krijgt een eigen rubriek in het rapport. Tijdens de eerste run
bleek meteen dat het niet alleen om opdrachtgever-mails gaat — ook bij een
juridisch gevoelige mail (AVG-verzoek, inhoudelijke betwisting) schrijft het
model soms een korte redenering in proza in plaats van het voorgeschreven
JSON-antwoord. Dat is een echte observatie voor de volgende ronde, geen storing.

**Gedaan (c) — verse ronde, mét voorbehoud.** Eerste poging draaide onbedoeld op
de óude corrector: `scripts/` zit in het backend-image, dus een `docker cp` van
het bijgewerkte script wordt bij de eerstvolgende container-hercreatie
teruggedraaid. Afgebroken en overgedaan in een losse `docker compose run`-
container met `/opt/luxis/scripts` als mount — die overleeft een deploy én leest
altijd de versie uit git. (Leerpunt voor volgende keer; hoort in de deploy-regels.)

**Uitkomst van de geldige ronde — 29 beoordeelde antwoorden, 29 groen:**
alle vijf de controles (beantwoordt de vraag / feiten kloppen / geen toezegging /
escaleert waar nodig / toon passend) staan op `true` bij alle 29, en **0 zware
fouten**. Ter vergelijking: met de miskalibreerde corrector scoorden vier rondes
in S222 83% → 89% → 94% → 89%. De gecorrigeerde weigering-rubriek werd één keer
geraakt en telt nu terecht niet als storing.

**Volledige ronde (na bijvullen tegoed) — 55 gevallen, 0 storingen, 1 weigering
in proza, 54 beoordeeld.** De corrector keurde er 3 af. Alle drie zelf nagetrokken
op prod:

| Zaak | Corrector zei | Werkelijkheid |
|---|---|---|
| IN100122 | "€ 22,64 vermoedelijk een datafout" | **corrector-misser** — het ís het openstaande bedrag (361,35 − 338,71 betaald). Hij noemde het bedrag zelf in de dossiergegevens en overrulede het daarna. |
| IN100370 | "dossiernummer verzonnen" | **corrector-misser** — IN100370 is het dossiernummer van die zaak. Idem de niet-zware vlag op IN100350: dat staat letterlijk in de onderwerpregel. |
| IN100411 | "'onderneem geen verdere actie' = toezegging" | **echte vondst.** Die zin leest als opschorting en spreekt de zin twee alinea's eerder tegen ("wordt onverkort voortgezet"). |

**Netto: 1 echte fout op 54 antwoorden (~2%), 0 verzonnen bedragen, 0 verzonnen
dossiernummers.** Twee ingrepen daarop: een spelregel in de productie-prompt
(de debiteur nooit vragen te wachten) en de corrector nogmaals aangescherpt —
regel 1 kreeg tanden (staat het bedrag in de dossiergegevens, dan klopt het;
twijfel hoort in de toelichting) en regel 2 dekt nu ook het eigen dossiernummer
uit de dossiergegevens en de onderwerpregel, niet alleen uit de body.

### Eerdere, afgebroken ronde (voor de volledigheid)

**Voorbehoud, hard:** die ronde was **niet af**. Na 30 van de 55 gevallen viel de
Anthropic-sleutel stil met *"credit balance is too low"* — 24 gevallen zijn
daardoor nooit gedraaid. Wat wél gedraaid is: de complete zelfgeschreven
proefset (18) plus 12 goud-gevallen (echte dossiers). De zwaarste categorie —
goud — is dus maar deels gemeten. De 29/29 is echt, maar op een kleinere en
gemiddeld makkelijkere set dan bedoeld. De ronde moet over zodra er weer
tegoed is.

**Nieuw en urgent (buiten de opdracht gevonden):** diezelfde sleutel is de
productiesleutel. Live nagetrokken met één minimale aanroep vanuit de
prod-container: **de AI-functies van Luxis lagen stil** — geen classificatie van
inkomende mail, geen intake-detectie, geen conceptgeneratie. De dagelijkse taken
draaiden wél (heartbeat groen) maar konden niets afhandelen; er stonden 96 nog
niet gekoppelde mails te wachten. Arsalan heeft tegoed bijgevuld; daarna live
bevestigd dat de sleutel weer werkt.

### Kosten meetbaar gemaakt (op verzoek Arsalan, zelfde dag)

Het tegoed ging snel op (€ 10 in een paar dagen) en niemand kon zien waaraan:
`ai_drafts.token_count` bleef leeg en classificatie/intake registreerden niets.
Nu schrijft **elke AI-aanroep** (alle zes aanroeppunten in `kimi_client`) één
regel naar de nieuwe globale tabel **`ai_usage`**: doel, model, vier
tokentellingen (in/uit/cache-lezen/cache-schrijven) en de geschatte kosten in
USD als `Decimal`. Prijzen vers uit de officiële Anthropic-tabel (Sonnet 4.6
$3/$15, Haiku 4.5 $1/$5 per miljoen tokens; cache-lezen 0,1×, cache-schrijven
1,25×). Registratie in een eigen sessie met gedempte fouten — meten mag een
aanroep nooit laten falen. Zes tests, waaronder de formule met de hand
nagerekend. **Live bewezen op prod:** één proefaanroep → één regel
(`compose_text · claude-sonnet-4-6 · 35 in / 13 uit · $0,000300`). Eerste
poging faalde overigens netjes-gedempt in script-context (incompleet
model-register, zelfde valkuil als eerder die dag) — gefixt door de registry
eenmalig te laden.

Overzicht voor de review (psql):
`SELECT date_trunc('day', called_at)::date, purpose, count(*), sum(cost_usd)
FROM ai_usage GROUP BY 1,2 ORDER BY 1,4 DESC;`
Kanttekening: de meting begint bij vandaag — waar de eerdere € 10 heenging is
niet meer te achterhalen, alleen te voorkomen dat het nóg eens onzichtbaar
gebeurt. Voorstel (niet gebouwd): een klein kostenblokje op het dashboard.

**Steekproef (op verzoek Arsalan door Fable gedaan i.p.v. Lisanne, 20-7):**
10 goud-gevallen integraal gelezen — concept naast Lisanne's echte antwoord —
plus de 3 corrector-vlaggen. Alle bedragen uit de steekproef-concepten
onafhankelijk gecheckt tegen de live financiële samenvatting: **6/6 exact**
(IN100453 361,93 · IN100034 6.428,97 · IN100037 4.768,64 · IN100368 726,33 ·
IN100150 1.296,87 · IN100418 40,87). Oordeel: geen verzonnen feiten, toezeggingen
correct vermeden, escalatie (advocatenbrief/deken/AVG/beschuldiging) telkens
juist. Structureel verschil met Lisanne: zij is scherper en neemt inhoudelijke
standpunten in ("uw verweer gaat niet op"), de AI blijft bewust neutraal en
procedureel — passend voor een concept dat de behandelaar aanscherpt (via de
INSTRUCTIE-regel kan dat per geval). Twee stijlpunten genoteerd, geen fouten:
(a) op deels betaalde zaken noemt het concept facturen én een veel lager
openstaand bedrag zonder de betalingen te benoemen — klopt, maar kan de debiteur
verwarren; (b) sommige ontvangstbevestigingen zijn erg kaal waar Lisanne
inhoudelijk zou antwoorden.

**Poort AAN (20-7):** `pipeline_auto_drafts_enabled` → true, na bewijs dat de
batch alléén concepten maakt met een taak "Bekijk en verstuur" (mens verstuurt;
plafond 50/dag; ontdubbeling per zaak+stap sinds S221). Eerste batch draait
morgen 08:00 UTC; de concepten verschijnen in /taken.

**Open:** een derde testronde meet alleen nog het effect van de twee laatste
ingrepen (± 110 AI-aanroepen) — bewust niet ongevraagd gedraaid gezien het
kostenpunt hierboven. Lisanne kan de eerste echte batch als praktijk-steekproef
gebruiken.

---

## Wat er níet is gedaan

- **De 27 correcties zelf** — wacht op één oordeel van Lisanne: particulier of
  eenmanszaak (zie V1). De rest van de onderbouwing is rond.
- **AI-tegoed bijvullen** — kan alleen Arsalan; de AI-functies liggen tot die
  tijd stil (zie V3).
- **Onverwerkt uit S228/S227:** fysieke-telefoon-check, opmaak-restpunt S227,
  S221b-UX-rest, DMARC, testdata 2026-00007 t/m -00019 opruimen.
- **KvK:** conform instructie niet naar gevraagd en niet gecheckt.
