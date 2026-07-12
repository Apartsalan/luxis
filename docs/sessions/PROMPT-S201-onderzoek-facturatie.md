# Sessie-prompt S201 — Onderzoek: facturatie-migratie + volledigheidsmatrix export

**Model: Fable (laatste gratis dag = 12 juli; daarna betaald). 100% read-only op prod —
niets bouwen, niets muteren. Output = recepten waarop Opus/Sol daarna blind kan bouwen.**

Vooronderzoek al gedaan (lees eerst): `docs/research/vooronderzoek-facturatie-migratie.md`.
Kern: Lisannes eigen facturen (567), factuurregels (773), uren (1.320) en uur→factuur-
koppelingen (2.742) zitten in de BaseNet-export maar zijn nooit gemigreerd; `invoices`/
`time_entries` op prod = 0 rijen. Bron-zip: `Xml_02-07-2026_2400.zip` (repo-root);
leescode: `scripts/basenet/parse.py`.

## Deel 1 — Facturatie-recept (hoofdtaak)

Lever een compleet, bouwklaar migratierecept op (à la S180-betalingen: meten vóór matchen):

1. **Veldsemantiek vaststellen** (nu onbekend — niet gokken, meten):
   - `invtobepaid`/`invpaid`/`invopenamount` op de factuurkop: wat betekenen ze écht?
     Waarom zijn sommige klanttotalen negatief (creditfacturen? saldo-conventie?).
   - Regelbedrag-veld op `OutgoingInvoiceLine` vinden (kolomnaam), BTW-velden, en de
     kop-regel-koppeling (invnr? systemid?). Som regels ≟ kopbedrag op een steekproef ≥20.
   - Statuscodes `invstatus` (1/2/5/6/9 komen voor) ontcijferen — vergelijk met wat
     Lisanne in BaseNet ziet (concept/verzonden/betaald/credit?). `invcredinv` = link
     naar gecrediteerde factuur?
2. **Mapping ontwerpen** naar Luxis: `invoices` + `invoice_lines` (+ `invoice_payments`?
   check of betaald-info per factuur bestaat of alleen als saldo), relatiecode → bestaand
   contact (op naam, zoals S168; meet de match-rate!), BTW-percentages, factuurnummers
   (conflict met Luxis' eigen nummerreeks? — Luxis begint blanco, dus BaseNet-nummers
   overnemen of apart veld?), status-mapping naar Luxis-statussen.
3. **Uren meenemen of niet — advies met cijfers:** 1.320 Hour-records + koppelingen.
   Luxis heeft `time_entries` + urenscherm. Hoeveel uren hangen aan facturen (via
   HourToOutgoingInvoiceLine) vs los? Advies: alles, alleen-gefactureerd, of niets —
   met de afweging voor Lisanne (historie-inzicht vs vervuiling).
4. **Donker/Dinc-spoor sluiten:** match de 12 onverklaarde bankcredits (±€21,7k, S195 —
   zie sessienotities S195) op factuurbedragen/-nummers/-data uit de export. Uitkomst:
   verklaard (welke facturen) of definitief begraven (met bewijs).
5. **Beslislijst voor Arsalan:** zoals S194-bankimport — per groep (bijv. betaalde
   facturen 2024/2025, open facturen, creditfacturen, uren) importeren ja/nee, met
   aantallen en euro's. Géén uitvoering in deze sessie.

## Deel 2 — Volledigheidsmatrix (de gegeneraliseerde vraag)

De facturen bleken een gemiste categorie — zijn er méér? Maak een matrix over ÁLLE
export-bestanden met records (tellingen staan al in het vooronderzoek): per entiteit →
geïmporteerd (ja/nee/deels) → relevant voor Lisanne (ja/nee + één zin waarom) →
actie (importeren / bewust laten / navragen). Let vooral op:
- **~18.000 Letters** (correspondentie) vs de 6.393 geïmporteerde mails — overlap of gat?
- **Journal/MemorialLine/Dcinfo** (boekhouding) — raakt dit de rapportages of Exact?
- **Task/TaskHistory** (1.613) — zit hier lopend werk in dat Luxis-taken zou moeten worden?
- **Project** (794) — waar hangen de uren aan?

## Verificatie-eisen
- Elke bewering over de export: gemeten met een script/telling in déze sessie.
- Elke bewering over prod: read-only query in déze sessie.
- Steekproeven benoemen (n=…); "niet geverifieerd" expliciet labelen.

## Output
- `docs/research/S201-facturatie-recept.md` (deel 1) en
  `docs/research/S201-volledigheidsmatrix.md` (deel 2), beide met beslislijst.
- SESSION-NOTES + roadmap bijwerken via `/sessie-einde`.

## Constraints
- GEEN prod-mutaties, GEEN import-uitvoering, GEEN mail. Bouwen = latere Opus/Sol-sessie.
- Testdossier bestaat niet meer; werkvoorraad = 27 zaken (na S199-opruimronde).
