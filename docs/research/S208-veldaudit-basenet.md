# S208 — Veld-voor-veld-audit BaseNet-export → Luxis

**Status:** read-only onderzoek, 13 juli 2026 (Fable). Geen productiewijziging uitgevoerd.
**Bron:** `Xml_02-07-2026_2400.zip` (137 XML-bestanden), zelf uitgepakt en geparsed met
`scripts/basenet/parse.py`. Productie gecontroleerd met read-only queries via SSH.
**Aanvulling op:** `docs/research/S201-volledigheidsmatrix.md` (entiteit-niveau, 12 juli).
Deze audit gaat één laag dieper: **binnen** de wél-geïmporteerde entiteiten, veld voor veld.

## 0. Aanpak en dekking

De import gebruikt 9 van de 137 bestanden: Company, Person, Contact, Incasso, IncassoLine,
IncassoBetalingAnders, IncassoBetalingsRegeling, Letter, CashBankLine. Voor de eerste 7 is
elk veld geteld (vul-graad + voorbeeldwaarden) en vergeleken met wat `mapping.py` en de
import-runners daadwerkelijk lezen. Recordtellingen komen exact overeen met de S201-matrix
(815/208/145/607/1.563/56/323) — onafhankelijke bevestiging van beide metingen.
**Niet gedekt:** de velden van `Letter` (17.928 records) — de aansluiting daarvan is op
record-niveau al sluitend verklaard in S201 §3; een veld-audit daarvan is apart werk.

## 1. Rentetype per dossier nooit geïmporteerd — GECORRIGEERD: besluit S188b dekt dit al

> **Correctie 13 juli (zelfde dag, na tegenonderzoek):** de eerste versie van dit rapport
> presenteerde de 19 afwijkende zaken als open beslispunt voor Lisanne. Dat was fout:
> **besluit Arsalan 9 juli (S188b, `docs/plans/PLAN-heropening-werkvoorraad.md` §4b)** legt
> vast dat alle b2b-zaken van de holding-opdrachtgevers de contractuele AV-rente (art. 13.3,
> 2%/mnd) krijgen en b2c wettelijke rente — óók waar BaseNet iets anders had staan (de
> COLLECT 1-afwijkers worden daar zelfs expliciet genoemd, S185-regel). De prod-stand is
> dus **conform het genomen besluit; er hoeft aan de rente niets te veranderen.** De waarde
> van deze sectie is documentair: wélke zaken het oude systeem lager had staan, zodat
> niemand dat later voor een fout aanziet.

BaseNet heeft per dossier een veld `incinteresttype`. Dat is nooit geïmporteerd; de
rente-uitrol van 13 juli (`rollout_av_rente.py`) selecteerde daardoor **per opdrachtgever**
(iedereen met AV-tarief → alle niet-consumentenzaken op 2%/mnd samengesteld), terwijl
BaseNet **per dossier** varieert — óók binnen één opdrachtgever (COLLECT 1 heeft zowel
type-8- als type-5-zaken).

Verdeling over 607 dossiers: type 8 = 573 · type 1 = 19 · type 9 = 6 · type 2 = 4 ·
type 5 = 4 · type 6 = 1.

De betekenis van de typen is niet publiek gedocumenteerd; ze is hier **teruggerekend uit
BaseNet's eigen cijfers** (rente ÷ (hoofdsom × looptijd), per dossier; script
`rentetempo.py`, scratchpad). Controlegroep type 8 komt uit op 24,6–27,5%/jr — precies
2%/mnd samengesteld, dus de methode klopt:

| type | impliciet tempo | betekenis (afgeleid) |
|---|---|---|
| 8 | ~25–27%/jr | 2%/mnd samengesteld (AV art. 13.3) |
| 1 | ~10–12%/jr | wettelijke handelsrente |
| 2 | ~5–6%/jr | wettelijke rente (consument) |
| 5 | exact ~2%/jr | 2% per JAAR |
| 6 | ~24,6%/jr | 2%/mnd (klopt met prod) |
| 9 | 0 | géén rente |

**Op prod gemeten (13 juli): 19 dossiers staan op contractual 2%/mnd terwijl BaseNet een
lager/geen tarief rekende:**

- type 1 (~11%/jr → nu 27%/jr): IN100079, IN100080, IN100081, IN100203, IN100273,
  IN100274, IN100302, IN100324, IN100326, **IN100598 (status in_behandeling — actief!)**
- type 5 (2%/jr → nu ±13× te hoog): IN100277, IN100278, IN100291
- type 9 (géén rente → nu 2%/mnd): IN100064 t/m IN100069 (alle Geannuleerd; hoofdsom
  samen € 39.549,99 — spookrente op het restant niet becijferd)

11 van de 19 zijn Lopend/Wacht in BaseNet = "Nog te openen" → gaan bij de fase-heropening
**actief** rente aanwas geven op het verkeerde tarief. De overige afwijkers staan op prod op
statutory/commercial en sporen daarmee grofweg met BaseNet (o.a. IN100031, IN100072,
IN100082, IN100167, IN100405, IN100470, IN100541); IN100540 (BaseNet ~10%/jr) staat op
statutory (≈7%) = aan de lage, veilige kant. IN100441 (type 6) klopt. IN100276 (type 5)
staat op statutory (~6–7% waar 2%/jr hoort) — klein te hoog.

**Duiding na tegenonderzoek (13 juli):**
- Alle afwijkers op contractual zijn **b2b van de 8 AV-opdrachtgevers** (prod-query:
  CM Zakelijk, COLLECT 1, Facturen Legalwork, INC Zakelijk, Incassocenter,
  Invorderingsbedrijf, LegalWork, SYN Finance — allemaal 2%/mnd uit de AV) → besluit
  S188b van toepassing, geen correctie.
- De 3 zakelijke type-5-zaken (IN100277/278/291, 2%/jr in BaseNet) hebben **4 verschillende
  debiteuren in één opeenvolgende invoerreeks** (IN100276–278 + 291) — geen gezamenlijke
  debiteur-deal, vrijwel zeker een BaseNet-invoerkeuze. IN100276 is b2c en staat al goed
  (wettelijke rente). Het heropening-draaiboek bevat al de S185-controle "rentetype per
  groep checken vóór er brieven met bedragen uitgaan" — dit lijstje is daarvoor de input.
- De 6 type-9-zaken (geen rente) zijn allemaal Geannuleerd = BaseNet-archief, gaan nooit
  open → geen actie.
- IN100598 was zelf het S188b-ijkpunt (€600,23 bij 2%/mnd) — bewust zo gezet.
- Blijvend nuttig: `incinteresttype` + `incssamengesteld` bij de volgende import als
  veld meenemen (documentatie/context, niet ter correctie).
- ⚠ Doc-afwijking gevonden: plan §4b zegt `contractual_compound=false` (enkelvoudig);
  de uitrol van 13 juli zette bewezen-correct `true` (samengesteld, op de cent gelijk aan
  BaseNet's rentespecificatie IN100197). Plan-regel is verouderd → bijwerken, anders zet
  een toekomstige uitvoerder de heropende groepen per ongeluk op enkelvoudig.

Los daarvan: `incssamengesteld` staat op **false bij 606/607** dossiers, óók bij IN100197
waarvan de rentespecificatie regel-voor-regel maandelijkse kapitalisatie toont. De vlag
betekent dus iets anders dan "maandelijks samengesteld" (vermoedelijk jaar-kapitalisatie
van wettelijke rente; alleen IN100301 = true). Geen actie, wel genoteerd.

## 2. Dossiernotities en waarschuwingen — niet geïmporteerd (kennisverlies)

- **`pmemo` — 99 dossiers** met echte werknotities ("Debiteur is solvabel", "Exploot naar
  deb gestuurd", "Niet naar Arno want particulier", …). Nergens in Luxis geland.
- **`palert` — 13 dossiers** met waarschuwingsbanners: "Failliet" (IN100102), "NIET
  REAGEREN → procedure is aanhangig" (IN100098), 6× "Regeling", en IN100456/IN100591
  met betaal-/factuurinstructies die de heropening raken.

Aanbeveling: importeren naar de dossiernotitie (veld bestaat al: `debtor_notes`), alerts
bovenaan. Klein script, idempotent via de bestaande marker. **Vóór de fase-heropening**,
want juist deze context stuurt de eerste actie per zaak.

## 3. Land bij adressen — kan niet eens geïmporteerd worden (schema-gat)

BaseNet vult `ocountry`/`mcountry`/`hcountry` bij ~96% van de relaties; **52 relaties zijn
niet-Nederlands** (46 bedrijven, 4 personen, 2 contactpersonen — o.a. Duitsland, België,
VK, VS, Turkije, Dubai). Luxis-adressen hebben **geen land-veld** (`visit_*`/`postal_*`
kennen alleen straat/postcode/plaats). Aanmaningen/brieven aan buitenlandse debiteuren
missen dus het land. Aanbeveling: kolommen `visit_country`/`postal_country` + migratie +
backfill uit de export; UI toont het alleen indien gevuld.

## 4. Kleinere veld-gaten (gemeten, met aantallen)

| Veld (bron) | Gevuld | Luxis-doel | Oordeel |
|---|---|---|---|
| `birthday` (Person) | 28 | `date_of_birth` bestaat al | Backfillen (was al P2 in S201) |
| `initials` (Person/Contact) | 100+56 | geen veld | Meenemen in naam of laten; laag belang |
| `title` ("De heer"/"Mevrouw") | 194+105 | `salutation` al gevuld via sex/saluation | Geen actie |
| `incprovisie` (Incasso) | 39 dossiers, 15% | `provisie_percentage` bestaat al | Backfillen — raakt afdracht/facturatie (5 opdrachtgevers: INC Zakelijk 16, Incassocenter 15, COLLECT 1 6, CM Zakelijk 1, LegalWork 1) |
| `pemployee_responsible` | 607 (86 Lisanne / 521 incasso@) | `assigned_to_id` bestaat al | Optioneel backfillen bij heropening |
| `pvoorschot` (IN100555) | 1 × € 1.000 | budget/voorschot | Handmatig beoordelen |
| `increchtbankid`/`incwadvocaat`/`incprocureur` (IN100185) | 1 dossier | `court_name` e.d. bestaan | Handmatig overnemen |
| `incfinishreason` (IN100405) | 1 ("Geannuleerd") | — | Geen actie |
| `bsn` (Person) | 3 | geen veld | **Bewust NIET importeren** (AVG/dataminimalisatie); wel weten dat het in de export zit |
| `fax`/`homepage`/`rechtsvorm`/`typerela` (Company) | 1/1/1/2 | — | Geen actie; rechtsvorm is in BaseNet leeg (1/815) → bevestigt dat de WIK-bijlage een KvK-koppeling nodig heeft |
| `ostreet2`/`mstreet2` (adresregel 2) | 15/14 | geen veld | Bij land-migratie meenemen of laten |

## 5. Wat bewezen WÉL compleet is (deze sessie zelf gecontroleerd)

- **Betalingen aan de cliënt** (`IncassoBetalingAnders`): som per dossier == BaseNet's
  eigen totaal `cachedpaymentsklant`, € 165.697,01 == € 165.697,01, **0 verschillen**.
- **Vorderingen**: de bestaande driftguard (cachedhoofdsom == hoofdsom+rente) stond al in
  de import; S201 bevestigde 1.563/1.563 en 607/607 op prod.
- **Regelingtermijnen**: enige niet-gemapte veld is `incbreminders`, overal 0.
- `incinterestdate` (rentedatum, 601/607 gevuld): sinds S207c gebruikt als anker voor de
  bevriesdatum-backfill — dat gat is al gedicht.
- Kantoorbetalingen via bank: niet herteld; S180/S195 auditten die al 1-op-1 (255
  betalingen op 135 zaken).

## 6. Entiteit-niveau (geen herhaling van S201)

De grote niet-geïmporteerde blokken blijven zoals de S201-matrix ze prioriteert:
**187 D-dossiers** (P1, ruggengraat voor 8.637 correspondentie-items en 1.320 uren),
**439 kantoorfacturen** (P1, apart recept), contactpersoon-koppelingen (145),
agenda-handcontrole (P0). Niets in deze veld-audit spreekt die prioritering tegen.

## 7. Niet geverifieerd / beperkingen

- Betekenis van de rentetype-nummers is afgeleid uit terugrekening (sterke consistentie,
  controlegroep klopt), niet uit BaseNet-documentatie — die is niet openbaar (webzoektocht
  13 juli leverde niets op). Definitieve bevestiging: BaseNet-scherm of rentespecificatie
  van één type-1-zaak opvragen.
- De spookrente op de 6 type-9-zaken (restant-effect) is niet per zaak becijferd.
- `Letter`-velden en `CashBankLine`-velden zijn niet veld-voor-veld geauditeerd (dekking:
  S201 §3 resp. S180/S195-audits).
- Of Lisanne bij de 19 afwijkers bewust van de AV afweek, weet alleen Lisanne.

## 8. Voorgestelde volgorde (voorstellen — niets uitgevoerd)

1. ~~Beslislijst rente-afwijkers naar Lisanne~~ **VERVALLEN na tegenonderzoek** — besluit
   S188b dekt de rente al; er hoeft niets te veranderen. Wel: (a) plan §4b-regel
   `contractual_compound` bijwerken naar samengesteld (doc-fix), (b) het type-5-lijstje
   (IN100277/278/291) meenemen in de bestaande S185-controle bij heropening van de
   COLLECT 1-groep.
2. **pmemo/palert-import** naar dossiernotities (klein, idempotent, vóór heropening).
3. **Land-veld** toevoegen + backfill (52 buitenlandse relaties).
4. **Provisie- en geboortedatum-backfill** (39 + 28 records, velden bestaan al).
5. Bij de **volgende verse export**: `incinteresttype`, `incssamengesteld`, `pmemo`,
   `palert`, landen en provisie structureel in `mapping.py` opnemen (+ de
   incstatus-valkuil die er al in staat).
