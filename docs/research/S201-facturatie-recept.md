# S201 — Bouwrecept BaseNet-facturatie

**Status:** onderzoeksrecept, read-only opgesteld op 12 juli 2026

**Besluit in één zin:** importeer 439 definitieve kantoorfacturen met 630 regels, zet 7 facturen met een Mollie/kop-conflict apart voor menselijke reconciliatie en importeer de 90 derdengelden-/verrekenstaten niet als omzetfacturen.

Bedragen in dit document zijn bruto, inclusief btw, tenzij expliciet anders vermeld. Alle tellingen komen uit de BaseNet-export `Xml_02-07-2026_2400.zip`, een volledige parserrun en read-only controles op de productiedatabase. Tijdens dit onderzoek zijn geen facturen, betalingen, uren of andere productiegegevens geschreven en is geen e-mail verstuurd.

## 1. Uitkomst

Luxis bevat op productie nog geen facturen, factuurregels, factuurbetalingen of tijdregels. De BaseNet-export bevat 567 factuurkoppen en 773 regels. Die 567 koppen mogen niet als één homogene groep worden gemigreerd:

| Besluitgroep | Koppen | Gekoppelde regels | Bruto totaal | Openstaand | Besluit |
|---|---:|---:|---:|---:|---|
| Definitieve kantoorfacturen zonder bronconflict | **439** | **630** | **€ 302.750,39** | **€ 72.762,09** | Automatisch importeren |
| Mollie betaald, factuurkop volledig open | **7** | **13** | **€ 10.854,66** | **€ 10.854,66** | Eerst Lisanne/boekhouding laten beslissen |
| Onregelmatige WIP/concepten | 12 | 9 | € 13.013,07 | € 13.013,07 | Niet automatisch; handmatig beoordelen |
| Lege systeemschillen | 19 | 0 | € 0,00 | € 0,00 | Overslaan |
| Derdengelden-/verrekenfamilie | **90** | **90** | **−€ 90.718,21** | **−€ 74.959,30** | Niet als verkoopfactuur importeren |
| Losse conceptregels zonder kop | — | 31 | € 6.779,81 | — | Overslaan en als controlelijst bewaren |

- Controlesom koppen: `439 + 7 + 12 + 19 + 90 = 567`.
- Controlesom regels: `630 + 13 + 9 + 90 + 31 = 773`.
- Controlesom kopbedragen: `€ 302.750,39 + € 10.854,66 + € 13.013,07 − € 90.718,21 = € 235.899,91`, exact het totaal van alle 567 BaseNet-koppen.

De automatische groep bestaat uit:

| Subgroep | Aantal | Bruto totaal | Openstaand | Luxis-status op 12-07-2026 |
|---|---:|---:|---:|---|
| Gewone, volledig betaalde facturen | 325 | € 248.364,17 | € 0,00 | `paid` |
| Gewone, definitieve open facturen zonder bronconflict | 88 | € 78.469,57 | € 78.469,57 | 86 `overdue`, 2 `sent` |
| Nul-facturen met BaseNet-status 9 | 3 | € 0,00 | € 0,00 | `paid` als beleidsmapping, zonder betaling |
| Creditnota’s | 23 | −€ 24.083,35 | −€ 5.707,48 | 16 `paid`, 7 `sent` |
| **Totaal** | **439** | **€ 302.750,39** | **€ 72.762,09** | 344 `paid`, 86 `overdue`, 9 `sent` |

De 86 te late facturen hadden op 12 juli 2026 een vervaldatum vóór die datum. De twee overige gewone open facturen vervallen op 13 juli 2026. Creditnota’s worden bewust niet `overdue`: de bestaande Luxis-job sluit creditnota’s eveneens uit. De zeven conflictfacturen zijn buiten deze statustelling gehouden.

## 2. Bronfeiten die het recept sturen

### 2.1 Facturen en btw

- `OutgoingInvoice` bevat 567 unieke `invnr`-waarden, 100000–100566.
- Jaren op factuurdatum: 2024 = 9, 2025 = 307, 2026 = 251.
- 542 koppen hebben regels; bij alle 542 is de som van `inlpricetot` exact gelijk aan `invtobepaid`.
- Alle 773 regels voldoen exact aan BaseNets regelberekening: `ROUND_HALF_UP(aantal × stukprijs × 1,21)` voor btw-code `1a` en zonder opslag voor code `0`.
- Gebruikte btw-codes: 528 regels met 21% en 245 regels met 0%.
- Onder de 542 facturen met regels zijn 354 volledig 21%, 104 volledig 0% en 84 gemengd.
- BaseNet rondt btw per regel af. Luxis rondt per btw-groep af. Dat geeft bij precies één factuur verschil: **100532** is in BaseNet € 1.631,74 en wordt met de huidige Luxis-herberekening € 1.631,73.

Daarom worden de BaseNet-kopbedragen niet opnieuw berekend tijdens de migratie. De import bewaart per regel het netto regelbedrag en per kop exact de som van BaseNets netto-, btw- en brutobedragen. Er komt geen kunstmatige correctieregel van één cent. Factuur 100532 heeft uitsluitend 21%-regels; de huidige PDF-template gebruikt bij één tarief het opgeslagen `btw_amount` en blijft daardoor optellend €1.348,54 + €283,20 = €1.631,74 tonen. De import mag voor deze historische factuur geen `_recalculate_totals` aanroepen. Een renderregressietest borgt de drie zichtbare bedragen.

### 2.2 Relaties en dossiers

De productiecontrole is tenant-gefilterd uitgevoerd voor `seidony@kestinglegal.nl`:

- Productie: 1.169 relaties, 607 dossiers en 0 facturen/regels/betalingen/tijdregels.
- Alle **58/58** unieke BaseNet-debiteurcodes vinden exact één bestaande Luxis-relatie via de `[BaseNet-import]`-marker; 0 ontbreken en 0 zijn dubbel.
- Alle **146/146** unieke incassocodes uit factuurprojecten vinden exact één bestaand Luxis-dossier; 0 ontbreken en 0 zijn dubbel.
- Binnen de automatische groep kunnen 137 facturen aan 127 bestaande IN-dossiers worden gekoppeld.
- De overige 302 automatische facturen horen bij D-projecten. Die kunnen nu veilig contact-only worden geïmporteerd en later deterministisch aan de nog te importeren D-dossiers worden gekoppeld.

Elke productiequery en elke latere schrijfactie moet naast RLS zelf op `tenant_id` filteren.

### 2.3 Derdengelden zijn geen omzet

Het oorspronkelijke simpele filter vond 84 negatieve debetkoppen met omschrijvingen als “Voor u ontvangen gelden”. Een bredere controle van dezelfde familie vond ook zes correcties/omkeringen. De complete familie bestaat daardoor uit **90** koppen:

- 85 debet en 5 credit;
- 90 gekoppelde regels;
- bruto −€ 90.718,21;
- openstaand −€ 74.959,30;
- de zes aanvullende factuurnummers zijn 100348, 100422, 100424, 100425, 100455 en 100460.

Deze 90 posten worden uitgesloten op basis van gemeten product/omschrijving en correctieverband, niet alleen op een negatief bedrag. Ze horen functioneel bij ontvangen en doorgestorte cliëntgelden. Importeren als negatieve omzet zou zowel omzet als openstaande-postrapportage vervuilen en dezelfde geldstroom mogelijk dubbel opnemen naast de derdengeldenadministratie.

## 3. Exacte veldmapping

### 3.1 Factuurkop

| BaseNet | Luxis | Transformatie |
|---|---|---|
| `systemid` | `Invoice.id` | Bestaande deterministische `_uid("invoice", systemid)` met de vaste BaseNet-namespace |
| tenant uit actieve gebruiker | `tenant_id` | Exact één tenant ophalen; overal expliciet meesturen en filteren |
| `invnr` | `invoice_number` | Exact numeriek BaseNet-nummer bewaren, bijvoorbeeld `100123` |
| `invdebcred` | `invoice_type` | `2 → credit_note`, anders `invoice` |
| gekoppeld origineel/`invcredinv` | `linked_invoice_id` | BaseNet origineel wijst naar creditnummer; mapping omkeren zodat de credit naar het origineel wijst |
| `invrcode` | `contact_id` | Exacte match op BaseNet-`rcode` in bestaande contactmarker |
| project → `inccode` | `case_id` | IN-project: bestaand dossier; D-project: voorlopig `NULL` |
| `invdatinv` | `invoice_date` | Python `date` |
| `invduedate` | `due_date` | Python `date`; alle 439 automatische koppen hebben een waarde |
| BaseNet betaaldstatus | `paid_date` | `NULL`; werkelijke ontvangstdatum is niet uit de export bewezen |
| regels netto | `subtotal` | Som `ROUND_HALF_UP(inlaantal × inlprice)` per regel |
| regel-btw | `btw_amount` | Som `inlpricetot − netto regelbedrag`, dus BaseNets per-regelafronding |
| `invtobepaid` | `total` | Exact bronbedrag; moet gelijk zijn aan `subtotal + btw_amount` |
| btw-codes | `btw_percentage` | 21 als minimaal één regel 21% heeft, anders 0; regels blijven leidend |
| bronstatus | `status` | Mapping uit §3.3; rechtstreeks zetten, niet door verzendworkflow voeren |
| herkomst/project | `reference` / `notes` | Machineleesbare `[BaseNet-import]`-marker met `systemid`, `invnr` en projectcode |
| — | `is_active` | `True` |

Het numerieke BaseNet-factuurnummer is de aanbevolen keuze. De huidige Luxis-generator zoekt alleen reeksen met `F{jaar}-`, `CN{jaar}-` of `VN{jaar}-`. Een nummer als `100123` botst daar niet mee en blijft herkenbaar voor bank, klant en Exact. Een extra `BN-`-voorvoegsel zou de historische externe referentie onnodig veranderen.

Let op voor de producttoekomst: invoice_number heeft nu een globale unieke databasebeperking, terwijl nummers functioneel tenantgebonden zijn. Dat probleem bestaat ook al voor twee tenants die allebei bij F2026-00001 beginnen. Het blokkeert Kestings huidige import niet, maar vóór een tweede tenant moet de uniekheid naar (tenant_id, invoice_number) worden gebracht.

### 3.2 Factuurregel

| BaseNet | Luxis | Transformatie |
|---|---|---|
| `systemid` | `InvoiceLine.id` | Deterministische `_uid("invoice_line", systemid)` |
| bijbehorende `inlinv` | `invoice_id` | Via `invnr` naar de vooraf opgebouwde factuurmapping |
| bronvolgorde | `line_number` | Stabiele volgorde binnen de factuur, vanaf 1 |
| `inldescinv` | `description` | Exacte omschrijving, alleen trimmen |
| `inlaantal` | `quantity` | `Decimal` |
| `inlprice` | `unit_price` | `Decimal`, exclusief btw |
| aantal × prijs | `line_total` | Netto, `Decimal("0.01")` met `ROUND_HALF_UP` |
| `inlvatcode` | `btw_percentage` | `1a → Decimal("21.00")`; `0 → Decimal("0.00")` |
| `Product.prodexledger` | `gl_account_code` | Overnemen wanneer het gebruikte product een code heeft |
| — | `product_id` | `NULL`; de historische productcatalogus hoeft niet mee |
| — | `time_entry_id` / `expense_id` | `NULL`; uren worden in een aparte migratie behandeld |

### 3.3 Statusmapping

De selectie voor automatische import is: definitief (`invstatus` 5 of 6), met gekoppelde regels, niet in de derdengeldenfamilie en niet in de zeven Mollie/kop-conflicten.

1. Gewone factuur met `invpaidstatus = 1` → `paid`.
2. Gewone factuur met `invpaidstatus = 0` → `overdue` als `due_date < 2026-07-12`, anders `sent`.
3. Nul-factuur met `invpaidstatus = 9` → beleidsmatig `paid` zonder betaling, plus de ruwe BaseNet-status in `notes`. De bron bewijst alleen status 9, totaal/openstaand €0 en geen betaling; “betaald” is gekozen omdat dit drie verzonden, volledig door korting/voorschot geneutraliseerde documenten zijn en `cancelled` onterecht zou suggereren dat ze niet zijn uitgegeven.
4. Creditnota met `invpaidstatus = 1` → `paid`; met `0` → `sent`.
5. Concept-, bijzondere en lege koppen vallen buiten de automatische selectie.

De import roept geen `approve`-, `send`- of `mark_paid`-service aan. Die paden zijn voor nieuwe werkstromen en kunnen e-mail versturen, bedragen herberekenen of `paid_date` op vandaag zetten. Historie wordt in één gecontroleerde transactie rechtstreeks ingevoegd.

## 4. Betalingen reconstrueren zonder te liegen

`invpaid` is op alle 567 BaseNet-koppen nul en is dus geen betaald bedrag. Het betaalde saldo is `invtobepaid − invopenamount`. De boekhoudkundige onderbouwing staat in `Memorial`/`MemorialLine`:

- 33 memoriaalkoppen en 777 regels;
- 551 regels verwijzen naar 422 facturen;
- voor alle **422/422** is som `credit − debit` exact gelijk aan het betaalde saldo;
- alle 369 facturen met een niet-nul betaald saldo zijn gedekt;
- alle **325** automatisch te importeren gewone betaalde facturen zijn exact gedekt, samen € 248.364,17;
- memoriaalboekingsdatums lopen van 31-03-2025 tot en met 16-06-2026.

`Payment` bevat 237 betaallinkrecords. Daarvan zijn **27** door de laatste Mollie-webhook hard als `paid` bevestigd: bij alle 27 zijn methode `ideal`, `paidAt`, bedrag en factuurnummer aanwezig en is `amountRefunded = 0`. Twintig sluiten ook aan op een betaalde factuurkop, samen **€ 21.913,73**. Zeven spreken de factuurkop tegen: Mollie zegt volledig betaald, maar `invpaidstatus = 0` en het volledige bedrag staat nog open.

| Factuur | Mollie betaald op (UTC) | Bedrag | BaseNet-kop |
|---|---|---:|---|
| 100314 | 30-12-2025 13:27 | € 372,25 | volledig open |
| 100321 | 12-01-2026 15:45 | € 1.452,00 | volledig open |
| 100316 | 31-01-2026 17:52 | € 505,78 | volledig open |
| 100342 | 03-02-2026 21:46 | € 2.657,64 | volledig open |
| 100332 | 04-02-2026 20:01 | € 292,82 | volledig open |
| 100441 | 23-03-2026 14:44 | € 566,17 | volledig open |
| 100533 | 19-05-2026 11:17 | € 5.008,00 | volledig open |
| **Totaal** |  | **€ 10.854,66** | **volledig open** |

Waarschijnlijk is hier niet teruggesynchroniseerd of niet afgeletterd, maar dat is **niet geverifieerd**. Deze zeven worden daarom niet automatisch als open of betaald geïmporteerd. De overige 210 betaallinkrecords zijn geen bewezen eindbetalingen en worden niet rauw overgenomen.

Aanbevolen betaalrecept:

- voeg als codewaarde `unknown` toe aan `PAYMENT_METHODS`, met Nederlandse UI-tekst “Onbekend (BaseNet)”;
- maak voor elk van de 325 gewone betaalde facturen precies één `InvoicePayment`;
- gebruik voor de 20 consistente Mollie-betalingen het exacte bedrag, de kalenderdatum uit `paidAt`, `payment_method = "ideal"` en de Mollie-payment-id als referentie;
- gebruik voor de overige 305 facturen `amount = invoice.total`, `payment_date = NULL` en `payment_method = "unknown"`; maak daarvoor alleen de databasekolom en responseweergave nullable, terwijl handmatig aangemaakte betalingen via het bestaande API-schema een datum blijven vereisen;
- zet bij die 305 `reference = "BaseNet memoriaal"` en de laatste `Memorial.medatein` uitsluitend als duidelijk gelabelde **boekingsmetadata** in `description`; bij 11 facturen ligt die datum vóór de factuurdatum en mag hij dus nooit als betaaldatum worden getoond;
- geef elke van de 325 samengevatte regels deterministisch `InvoicePayment.id = _uid("invoice_payment", source_invoice.systemid)`, zodat een tweede run geen duplicaat kan maken;
- `created_by` = de op uitvoerdatum exact één actieve gebruiker `seidony@kestinglegal.nl`, na tenantcontrole;
- zet `Invoice.paid_date` alleen voor de 20 Mollie-bevestigde facturen op de bewezen betaaldatum; laat het veld voor de overige 305 `NULL` en toon in de UI “Datum onbekend”;
- maak geen positieve betaalregel voor creditnota’s en geen betaalregel voor de drie nul-facturen; hun bronstatus wordt rechtstreeks bewaard.

Omdat de bestaande betaalservice `paid_date` automatisch op vandaag zet, voegt de migratie deze historische betaalregels rechtstreeks toe en zet zij de historische status expliciet.

**Kleine bouwvoorwaarde vóór import:** de huidige generieke betalingssamenvatting rekent met `total_paid >= invoice.total`. Bij een negatieve creditnota is daardoor nul betaald al “volledig betaald”, ook voor de 7 open credits. De factuurdetailpagina toont dan eveneens ten onrechte “Volledig betaald”. Laat de betalingsbalk daarom bij `invoice_type = "credit_note"` uitsluitend de opgeslagen afwikkelstatus tonen en bied daar geen positieve betalingregistratie aan. Voeg een regressietest toe voor één open en één afgewikkelde creditnota. Er zijn geen kunstmatige negatieve `InvoicePayment`-regels nodig.

## 5. Uren: nu niet importeren

De export bevat 1.320 unieke urenregels van 28-11-2024 tot en met 01-07-2026:

| Maatstaf | Gemeten |
|---|---:|
| Gewerkte uren | 741,62 |
| Te factureren uren (`h_to_inv`) | 670,72 |
| Regels met concrete factuurhistorie | 1.178 |
| Regels zonder concrete factuurhistorie | 142 |
| Uren op D-projecten | 1.236 regels / 709,82 gewerkt |
| Uren op IN-projecten | 84 regels / 31,80 gewerkt |
| D-projecten met uren | 54 |
| IN-dossiers met uren | 6 |

`hour_to_invlines` bevat 2.742 historie-/statusregels, geen 2.742 zelfstandige urensplitsingen. Alle 2.738 gevulde uurreferenties matchen. Van de 1.178 uren met concrete factuurhistorie hebben 1.145 zowel een definitief factuurnummer als een passende regel, 7 alleen een definitief factuurnummer en 26 alleen bruggeschiedenis door credit-/herfacturatie. De overige 142 hebben geen concrete factuurhistorie; daarvan staan 86 regels met samen 32,50 uur nog als declarabel. Of die werkelijk nog factureerbaar zijn, is niet geverifieerd.

Luxis vereist op elke `TimeEntry` een `case_id`. De 187 D-dossiers zijn nog niet geïmporteerd, terwijl 1.236 van de 1.320 uren daarop staan. Zelfs “alleen gefactureerde uren” lost dit niet op. Daarom:

1. importeer in deze factuurmigratie **geen uren**;
2. importeer eerst de 187 historische D-dossiers zonder incassopipeline en behoud hun bronstatus (waaronder 84 Lopend);
3. maak daarna een aparte, idempotente urenimport voor alle 1.320 regels, met uurtype- en gebruikersmapping;
4. zet alleen de 1.152 uren met een definitief numeriek `hinvoicenr` op `invoiced = true`; bewaar de overige bruggeschiedenis als herkomstbewijs en som die nooit rechtstreeks.

Van de 1.320 regels horen 1.317 bij Lisanne en 3 bij de generieke BaseNet-medewerker “Incasso Advocaat”. Die drie vereisen vóór import een expliciete gebruikerskeuze. De 70 BaseNet-uurtypen kunnen naar de acht bestaande Luxis-activiteiten worden teruggebracht; 21 uren hebben geen brontype en worden `other`.

Bij omzetting naar minuten zijn 1.319 regels exact een geheel aantal minuten. Eén regel is 19,20 minuten; `ROUND_HALF_UP` per rij maakt het totaal 44.497 minuten, 0,20 minuut minder dan de bron. Die ene afwijking moet in de latere dry-run zichtbaar blijven en expliciet worden geaccepteerd of anders gemodelleerd.

## 6. Donker/Dinc: definitief buiten de factuurmigratie

De 12 eerder onverklaarde bankcredits tellen exact op tot **€ 21.738,96**:

| Spoor | Credits | Totaal | Factuurtoets |
|---|---:|---:|---|
| Donker Groep | 1 | € 17.500,00 | Relaties 100316/100737 hebben 0 uitgaande facturen; vier dagen later volgt een uitgaande betaling van € 17.500 met schadevergoedingsomschrijving |
| Van der Hem | 1 | € 500,00 | Wederpartij op D100060; de kantoorfacturen op dat project zijn aan andere partijen en geen € 500 |
| Dinc | 7 | € 1.900,00 | Wederpartij op D100085; kantoorfacturen zijn aan Gemeente Rotterdam/LAVG en geen € 100/€ 300 |
| Königel | 1 | € 1.708,00 | Wederpartij op D100079; geen factuurbedrag matcht |
| Makkinga | 1 | € 116,44 | Wederpartij op IN100506; de match is een negatieve “Voor u ontvangen gelden”-staat, geen omzetfactuur |
| Beerens | 1 | € 14,52 | Wederpartij op IN100547; geen factuurmatch, banktekst noemt nabetaling/rente |

Alle genoemde betalers hebben nul uitgaande kantoorfacturen op hun eigen relatie. Bedrag-, datum-, relatie- en projecttoets wijzen dezelfde kant op: dit zijn dossier-/derdengeldenontvangsten, geen betalingen op Lisannes kantoorfacturen. Het S195-besluit “niet via facturen boeken/importeren” blijft daarom staan. Het netto BaseNet-openstaandbedrag van € 21.670,52 leek erop, maar mengt positieve kantoorvorderingen met negatieve verrekenstaten en was dus een toevallige nettogelijkenis.

## 7. Bouwvolgorde voor de latere High-fase

### Stap 0 — Twee kleine eerlijkheidsvoorwaarden

Vóór de importer komen twee chirurgische productaanpassingen met regressietests:

1. maak `invoice_payments.payment_date` nullable in database/model/response en toon `NULL` als “Datum onbekend”; `InvoicePaymentCreate.payment_date` blijft verplicht voor alle normale handmatige invoer;
2. voeg `unknown` toe aan de betaalmethoden met UI-label “Onbekend (BaseNet)” en laat creditnota’s afwikkelstatus tonen zonder de positieve-betalingsbalk.

Deze voorwaarden zijn nodig om historische onzekerheid niet als een verzonnen datum of betaling te presenteren. De migratie voegt geen nieuwe tabel toe; de bestaande RLS-inrichting verandert niet.

### Stap 1 — Eén kleine importmodule

Maak `scripts/basenet/import_invoices.py` naar het patroon van `import_basenet.py`:

- `--dry-run` is de standaard en schrijft niets;
- `--execute` is apart en duidelijk;
- hergebruik `parse_entity`, de vaste UUID5-namespace en `[BaseNet-import]`;
- alle geldvelden zijn `Decimal` en elke afronding gebruikt `ROUND_HALF_UP`;
- elke databasequery bevat `tenant_id`;
- bouw eerst de hele importset in geheugen en schrijf pas als alle poorten groen zijn.

### Stap 2 — Classificeren vóór mappen

De classificatie moet de vijf disjuncte kopgroepen en de losse regels exact reproduceren. De derdengeldenfamilie krijgt een expliciete herkenningsfunctie met een regressielijst voor de zes correcties; een simpele `total < 0`-regel is onvoldoende. De zeven Mollie/kop-conflicten krijgen eveneens een vaste uitzonderingenlijst.

### Stap 3 — Alle relaties vooraf oplossen

Bouw mappings voor 58 debiteurcodes, 146 IN-codes, 567 factuurnummers, gebruikte producten en creditverbanden. Eén ontbrekende of dubbele verplichte match breekt de run af. D-projecten krijgen aantoonbaar `case_id = NULL` en hun projectcode blijft in de marker staan.

### Stap 4 — Droogloop met harde poorten

De dry-run moet minimaal afdrukken en afdwingen:

- 567 koppen / 773 regels gelezen; 2 mislukte `LetterTemplate`-fragmenten staan los van facturatie;
- partitionering 439 / 7 / 12 / 19 / 90 en 31 losse regels;
- automatische groep 439 koppen / 630 regels / € 302.750,39 / € 72.762,09 open;
- uitzonderingsgroep 7 koppen / 13 regels / € 10.854,66, met per factuur een Mollie-`paidAt` maar een volledig open kop;
- 58/58 contacten en 146/146 IN-codes exact één match;
- 137 IN-facturen aan 127 dossiers; 302 D-facturen contact-only;
- 325 betaalregels samen € 248.364,17: 20 bewezen iDEAL-datums en 305 keer datum onbekend met memoriaalboekingsdatum alleen als metadata;
- 23/23 creditnota’s gekoppeld aan hun origineel;
- 773/773 BaseNet-regelformules exact;
- alleen factuur 100532 heeft de bekende één-centafwijking tegen Luxis-groepsafronding;
- 0 bestaande conflicterende `invoice_number`-waarden en 0 UUID-conflicten.

### Stap 5 — Eén transactie, geen neveneffecten

Na apart akkoord voor de productie-import:

1. controleer opnieuw tenant, actieve gebruiker, mailslot en lege doeltabellen;
2. voeg 439 facturen, 630 regels, 23 creditlinks en 325 betaalregels in één transactie toe;
3. roep geen verzend-, herinnerings-, PDF- of callbackpad aan;
4. breek de hele transactie af bij één afwijking;
5. een identieke tweede dry-run meldt alleen exact dezelfde bestaande import, nooit duplicaten;
6. verifieer na commit met tenant-gefilterde `SELECT`-queries dezelfde aantallen en geldsommen.

Productie-uitvoering is een afzonderlijke, naar buiten gerichte schrijfactie en vereist vooraf expliciet akkoord van Arsalan.

## 8. Testrecept

De latere bouwfase laat minimaal deze runbare tests achter:

- bekende 21%- en 0%-regel met `Decimal` en `ROUND_HALF_UP`;
- gemengde btw-factuur;
- regressie voor factuur 100532: opgeslagen kop én gerenderde PDF tonen €1.348,54 netto + €283,20 btw = €1.631,74 zonder correctieregel;
- volledige bronpartitionering en controlesommen;
- 90 derdengeldenposten uitgesloten, inclusief de zes correcties;
- statusmapping 344 betaald / 86 te laat / 9 verzonden;
- de zeven Mollie/kop-conflicten worden niet stil als open of betaald geclassificeerd;
- een open negatieve creditnota verschijnt niet als “Volledig betaald” en biedt geen positieve betalingregistratie aan;
- 58 contacten en 146 dossiers tenant-veilig gematcht;
- 23 creditlinks juist omgekeerd;
- 20 iDEAL-betalingen met exact `paidAt` en 305 betalingen met nullable datum/boekingsmetadata, zonder een betaaldatum te verzinnen;
- alle 325 payment-id's zijn deterministisch en een tweede run voegt niets toe;
- D-factuur mag `case_id = NULL` maar moet contact en bronproject houden;
- een mislukte match veroorzaakt rollback;
- twee runs maken geen dubbelen;
- e-maillogtelling verandert niet en het mailslot blijft aan.

## 9. Premortem vóór uitvoering

Stel dat de import zes maanden later als mislukt geldt. De drie waarschijnlijkste oorzaken zijn:

1. **Derdengelden zijn toch als omzet geboekt.** Tegenmaatregel: de 90-delige familie is een harde, geteste uitsluiting met zes expliciete correcties en een exacte geldcontrolesom.
2. **Een bronconflict is als waarheid gekozen.** Tegenmaatregel: de zeven Mollie/kop-conflicten blijven buiten de automatische transactie totdat Lisanne of de boekhouding ze per factuur heeft bevestigd.
3. **D-facturen zijn later niet meer aan hun dossier te koppelen.** Tegenmaatregel: elke contact-only factuur bewaart de exacte D-projectcode en deterministische bron-id; de latere D-migratie kan daarop zonder naamgok koppelen.

Waarom toch doorgaan: de overblijvende 439 facturen hebben sluitende kop-regelsommen, alle 58 debiteuren matchen uniek, de doeltabellen zijn leeg en de hele uitvoering kan idempotent in één transactie met een voorafgaande dry-run.

## 10. Concrete beslislijst voor Arsalan

| Groep | Aanbeveling | Omvang |
|---|---|---|
| Definitieve kantoorfacturen zonder bronconflict | **Ja, automatisch importeren** | 439 koppen, 630 regels, € 302.750,39 bruto |
| Mollie betaald / factuurkop open | **Nog niet; per factuur reconciliëren** | 7 koppen, 13 regels, € 10.854,66 |
| Gewone betaalhistorie | **Ja, als 325 samengevatte boekingen** | € 248.364,17; 20 iDEAL + 305 “Onbekend (BaseNet)” |
| Creditnota’s | **Ja, binnen de 439 en gekoppeld aan origineel** | 23; −€ 24.083,35 |
| Open kantoorfacturen | **Ja, binnen de 439 voor debiteurenbeheer** | 88 gewone (€ 78.469,57) plus 7 open credits (−€ 5.707,48) |
| Derdengelden-/verrekenstaten | **Nee, niet als factuur** | 90; −€ 90.718,21 |
| Onregelmatige WIP/concepten | **Nee, eerst handmatig beoordelen** | 12 koppen, 9 regels, € 13.013,07 |
| Lege koppen | **Nee, overslaan** | 19 koppen, € 0,00 |
| Losse conceptregels | **Nee, alleen controlelijst bewaren** | 31 regels, € 6.779,81 |
| Uren | **Nee in deze migratie; later alle 1.320 na D-dossiers** | 741,62 gewerkt uur |
| Donker/Dinc-bankcredits | **Nee, buiten facturatie houden** | 12 credits, € 21.738,96 |

## 11. Niet geverifieerd / bewust open

- Buiten de 20 consistente Mollie-betalingen zijn de werkelijke bankontvangstdatum en betaalmethode per historische factuur niet bewezen; alleen bedrag en memoriaalboekingsdatum zijn bewezen.
- De werkelijke zakelijke uitkomst van de zeven Mollie/kop-conflicten is niet geverifieerd.
- Niet vastgesteld is welke van de 12 WIP/conceptkoppen Lisanne nog zichtbaar wil houden. Daarom worden ze niet automatisch geïmporteerd.
- De gebruikersmapping voor de drie generieke “Incasso Advocaat”-uren en de vraag of 86 losse declarabele registraties nog factureerbaar zijn, zijn niet geverifieerd.
- De twee niet-parseerbare `LetterTemplate`-fragmenten raken de factuurdata niet, maar zijn niet inhoudelijk hersteld.
- De productie-import zelf is **niet uitgevoerd**.
