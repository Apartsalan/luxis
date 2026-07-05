# Ontwerp: Dossier-afwikkelflow (FIN-2 restant / CONN-7)

*Sessie 170 (5 juli 2026, Fable). Ontwerp voor de bouwsessie (Opus). Basis:
`docs/research/financiele-samenhang.md` (S158) + code-verkenning van vandaag.
Input Arsalan (5 jul): het verdienmodel verschilt per cliënt — soms honorarium
verrekenen en restant doorbetalen, soms alles doorbetalen en later factureren.
De flow mag dus geen vaste volgorde afdwingen.*

---

## 1. Probleem

Na "dossier betaald" moet Lisanne uit haar hoofd weten: factureer → verstuur →
verreken → keer rest uit → sluit af. Niets rekent "uit te betalen aan cliënt =
saldo − verrekening" voor, en niets signaleert dat geld te lang op de
stichtingsrekening blijft staan (Voda 6.19: doorbetalen "zodra de gelegenheid
zich voordoet" — talmen is tuchtrechtelijk riskant). De archive-guard
(`get_unsettled_reason`, S158) is het vangnet; de geleide route ontbreekt.

## 2. Kernontwerpkeuzes (met motivering)

### 2a. Trigger = het saldo, niet een status
De S158-ontwerpvraag ("aan welke 'klaar'-status hang je dit op — er zijn twee
status-systemen") lossen we op door hem te omzeilen: het afwikkel-paneel
verschijnt zodra **derdengelden-saldo ≠ 0** op het dossier staat (of er een
afwikkeling loopt). Statussen (dossier-status én pipeline-stap) kunnen
uiteenlopen; het saldo is de waarheid. Geen koppeling aan `betaald` nodig —
en `betaald` blokkeert dus ook niets (bestaande regel, blijft).

### 2b. Paneel (checklist), geen modal-wizard
Afwikkelen duurt per definitie meerdere dagen: vier-ogen-goedkeuring,
SEPA-bestand → bank, en in route B wachten op factuurbetaling door de cliënt.
Een pop-up-wizard die je in één keer doorloopt past daar niet. Het wordt een
**persistent "Afwikkeling"-paneel** op het dossier (in/naast FinancieelTab)
met stappen die elk hun eigen status tonen (te doen / wacht op goedkeuring /
wacht op bank / klaar) en die elk de **bestaande** dialoog openen. Het paneel
is een view over bestaande data — geen nieuwe state machine.

### 2c. Twee routes, keuze per dossier
Stap 1 van het paneel is de routekeuze (radio, opgeslagen op het dossier):

- **Route A — Verrekenen:** factuur naar cliënt → verrekening met het saldo
  (toestemming + vier-ogen, bestaande OffsetToInvoiceDialog) → **restant**
  uitbetalen aan cliënt → afsluiten.
- **Route B — Alles doorbetalen:** **volledige saldo** uitbetalen aan cliënt →
  factuur naar cliënt (die zij zelf betaalt, van haar eigen rekening) →
  afsluiten zodra factuur betaald (of eerder; factuur blokkeert sluiten niet —
  debiteuren-aging bewaakt de factuur al).

Opslag: één nullable kolom `settlement_route` op `Case`
(`'verrekenen' | 'doorbetalen'`), wijzigbaar zolang er nog niet geboekt is.
Geen tenant-default, geen per-cliënt-default (YAGNI — toevoegen zodra Lisanne
erom vraagt; de keuze is één klik).

### 2d. Sluit-guard als data-vlag, niet op naam
De pipeline-stappen "Betaald" en "Afgesloten" zijn allebei `is_terminal`, maar
alleen "Afgesloten" mag blokkeren op onafgewikkelde derdengelden. Onderscheid
via een nieuwe boolean **`requires_settled`** op de stap (en op
WorkflowStatus): seed/migratie zet hem aan voor "Afgesloten"-achtigen, uit
voor "Betaald". `move_case_to_step` + status-transitie naar zo'n stap roepen
`get_unsettled_reason` aan en weigeren met die melding. Geen naam-matching in
code (product blijft generiek; teller "hardcoded begrippen" stijgt niet).

### 2e. Talm-signaal
Dagelijkse job (patroon = CONN-1 factuur-overdue-job): dossiers met saldo ≠ 0
waarvan de **laatste trust-mutatie ouder is dan 7 dagen** → notificatie
"€X staat al N dagen op derdengelden — wikkel dossier af" (dedup: max 1
notificatie per dossier per 7 dagen). Drempel als constante in code met
`ponytail:`-comment; tenant-instelling pas als iemand erom vraagt.

## 3. Wat er gebouwd wordt

### Backend (~1 sessie, Opus)
1. Migratie: `cases.settlement_route` (nullable String) +
   `requires_settled` boolean op incasso-stap én WorkflowStatus (seed:
   True voor "Afgesloten", False voor al de rest).
2. `GET /api/cases/{id}/settlement` — de afwikkelstaat, volledig afgeleid:
   saldo + pending (bestaand `get_balance`), gekozen route, relevante factuur
   (+ status), al-geboekte verrekening(en), al-geboekte/pending uitbetaling(en),
   en het **voorgerekende restant** ("uit te betalen = saldo − openstaande
   verrekening"). Geen nieuwe boekingslogica — alleen lezen/rekenen.
3. `PATCH .../settlement` — routekeuze opslaan (weigeren als er al geboekt is
   in de andere route).
4. Guard: `move_case_to_step` / status-transitie → bij `requires_settled`-doel
   eerst `get_unsettled_reason` (zelfde melding als archive-guard).
5. Scheduler-job talm-signaal (§2e) + notificatie met tab-context
   (bestaand CONN-5-patroon → opent Betalingen-tab).
6. Tests: settlement-endpoint (beide routes, restant-berekening met
   deelverrekening), guard rood→groen ("Betaald" blokkeert NIET,
   "Afgesloten" wél bij saldo), talm-job (dedup + drempel).

### Frontend (~1 sessie, Opus)
1. `AfwikkelingPanel` op dossierdetail — zichtbaar bij saldo ≠ 0 of gekozen
   route. Routekeuze bovenaan; daaronder de stappen als checklist met
   statuschips. Elke stap = knop naar de **bestaande** flow:
   factuur → `facturen/nieuw?case_id=` (incassokosten-preview bestaat al),
   verrekening → OffsetToInvoiceDialog, uitbetaling → disbursement-dialoog
   (bedrag vooringevuld met het voorgerekende restant/saldo), afsluiten →
   bestaande stap-wissel (nu mét guard).
2. Voortgang zichtbaar: "wacht op 2e goedkeuring", "SEPA geëxporteerd op …",
   "factuur verzonden, nog niet betaald".
3. Geen nieuwe dialogen bouwen; alleen de bestaande aaneenrijgen.

## 4. Wat er bewust NIET komt
- Geen automatisch boeken — elke financiële actie blijft een menselijke klik
  (S160: assistent, geen autonomie).
- Geen nieuwe state machine / geen aparte settlement-tabel — de staat wordt
  afgeleid uit bestaande boekingen; alleen de routekeuze is nieuwe data.
- Geen per-cliënt fee-model-instelling (verdienmodel verschilt per afspraak;
  de routekeuze per dossier dekt dit — uitbreiden kan altijd nog).
- Geen blokkade op "Betaald" (geld staat daar terecht, wachtend op afwikkeling).
- Route B: factuurbetaling blokkeert het sluiten niet (aging bewaakt de
  factuur al; anders blijft een dossier eeuwig open hangen op een trage cliënt).

## 5. Pre-mortem (3 faalredenen + waarom toch deze aanpak)
1. **Te rigide → Lisanne werkt eromheen** (deelbetalingen, meerdere stortingen
   verspreid over maanden, tussentijds tóch verrekenen). Daarom: paneel is een
   view, geen dwingende volgorde; elke stap blijft ook los bruikbaar via de
   bestaande schermen; routekeuze is wijzigbaar zolang niet geboekt.
2. **Verkeerd voorgerekend restant → vertrouwen weg** (voorschotten,
   deelverrekening, bestaande facturen). Daarom: alle bedragen komen uit de
   al-geauditeerde bronnen (`get_balance`, `get_financial_summary`,
   incasso-factuur-preview), alles is een bewerkbaar vóórstel, niets boekt
   automatisch.
3. **Guard blokkeert legitiem sluiten** (oninbaar dossier; edge met pending
   storno). Daarom: guard hergebruikt het al-getestte `get_unsettled_reason`
   (oninbaar = saldo 0 → geen blokkade) en zit alleen op stappen met de
   `requires_settled`-vlag — per tenant bij te stellen als data.

## 6. Volgorde & meting
1. Backend (migratie → endpoint → guard → job → tests) — commit + deploy.
2. Frontend paneel — commit + deploy + browser-verificatie op prod-dossier.
3. Meting: geen aparte metriek nodig; succes = dalende "saldo staat stil"-
   notificaties + get_unsettled_reason-weigeringen die niet meer voorkomen.

*Geschat: 1,5–2 Opus-sessies. Afhankelijkheden: geen (los van K1-kennisbank).*
