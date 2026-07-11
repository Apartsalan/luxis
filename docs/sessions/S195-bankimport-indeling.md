# S195 — Complete indeling bankafschrift derdengelden (alle 212 bijschrijvingen)

> ⚠️ **CORRECTIE (zelfde dag, na 1-op-1 audit — zie `S195-1op1-audit.md`):** de groepen B en C
> hieronder zijn GEEN gaten. 34 van de 36 rijen zijn wél geboekt, maar op een bewust gecapt
> (lager) bedrag — de datum+bedrag-match zag ze daardoor onterecht als 'nooit geboekt'.
> Echt onboekt uit B+C: alleen de 2 Saltik-termijnen (IN100345, 2×€50). De audit bevat de
> volledige lijst van 64 gecapte betalingen (totaal €6.198,46) met heropenings-instructie.

Afschrift NL20 RABO 0388 5065 20, 9 juli 2025 t/m 9 juli 2026. Alleen-lezen analyse tegen prod, 11 juli 2026. Vervolg op `S194-bankimport-droogloop.md`.

## Kernfeiten

- **GEBOEKT** = datum+bedrag exact gelijk aan een bestaande Luxis-betaling (elke betaling telt 1×). Sluit op de cent aan op S194 (138 / €80.387,52). Groep A ook (17 / €8.836,39).
- **Indeling t.o.v. S194 licht verbeterd:** (1) Breedijk Styling €896,27 (S194: onbekend) is via de tegenpartij-naam herleid naar IN100302 → van D naar C. (2) De 2 Saltik-termijnen IN100345 (2×€50, échte regeling-record, omschrijving zegt 'Betalingsregeling') horen bij de regeling-groep → van C naar B. S194's B-zestal is exact gereconstrueerd (enige combinatie die op €3.475,50 sluit).
- **Echt banksaldo einde afschrift (8 juli 2026): €12544,99** — maar de derdengelden-administratie in Luxis is LEEG (0 transacties): de historische betalingen (S179/S180) zijn bewust als kale betalingen geboekt, zonder derdengelden-boekingen.
- **Vrijwel al het binnengekomen geld is in hetzelfde jaar ook weer uitgegaan** (rekensom: €176.905,81 ontvangen, saldo nog €12.544,99 → doorstortingen aan opdrachtgevers/terugbetalingen). Van groep A (17 nieuw) is per stuk geverifieerd: **11 al uitbetaald** met zelfde kenmerk en bedrag; 6 vermoedelijk nog op de rekening (~€1.678,51). ⚠️ De kolom 'Uitbetaald' is alléén betrouwbaar voor 2026-rijen: uitbetalingen uit het BaseNet-tijdperk (2025) dragen een D-nummer zonder IN-kenmerk en zijn per rij niet herleidbaar — 'niet gevonden' bij 2025-rijen betekent dus NIET dat het geld er nog staat.
- ⚠️ **Import-valkuil bovenop de S194-dubbeltel-valkuil:** elke goedgekeurde match maakt óók een derdengelden-bijschrijving aan (import boekt storting + betaling samen). Historische credits goedkeuren zonder de bijbehorende uitbetalingen te boeken blaast het derdengeldensaldo in Luxis kunstmatig op. De module kent wel uitbetalingen ('disbursement'), maar die importeert de bankimport bewust niet (afschrijvingen worden overgeslagen).
- **B-groep-patroon (slottermijnen):** bij 5 van de 6 S194-B-rijen ontving de bank de vólle termijn, terwijl Luxis op dezelfde dag een lager bedrag geboekt heeft (het restant dat de zaak precies dichtboekte). Het verschil is niet zoekgeraakt: doorstortingen aan de opdrachtgever staan in het afschrift. Deze 6 'bijboeken' zou dus deels dúbbel boeken. Detail onderaan.

| Groep | Aantal | Som |
|---|---|---|
| GEBOEKT | 138 | €80,387.52 |
| A | 17 | €8,836.39 |
| B | 8 | €3,575.50 |
| C | 28 | €44,540.91 |
| D | 21 | €39,565.49 |
| **Totaal** | **212** | **€176,905.81** |

S194 ter vergelijking: GEBOEKT 138/€80.387,52 · A 17/€8.836,39 · B 6/€3.475,50 · C 29/€43.744,64 · D 22/€40.461,76 (zelfde 212 rijen, B/C/D-grens zoals hierboven toegelicht).


## AL GEBOEKT — staat al in Luxis (S179/S180). Bij import per stuk AFWIJZEN, anders dubbel — 138 stuks, €80,387.52

| Datum | Bedrag | Tegenpartij | Geboekt op zaak |
|---|---|---|---|
| 2025-07-10 | €2,057.96 | MUHIBBULLAH ARSHAD | IN100276 |
| 2025-07-14 | €3,503.74 | KINDERRIJKHUIS | IN100256 |
| 2025-07-18 | €393.25 | Westdijk Bouwmanagement B.V. | IN100270 |
| 2025-07-21 | €1,000.00 | DOCO INTERNATIONAL BV | IN100272 |
| 2025-07-29 | €500.00 | Mw E Ozcelik | IN100234 |
| 2025-07-29 | €750.00 | Airco Partners Nederland B.V. | IN100224 |
| 2025-07-31 | €1,309.86 | Avetica B.V. | IN100148 |
| 2025-08-05 | €259.15 | DönerGo | IN100210 |
| 2025-08-19 | €1,238.00 | BOTEX HOLDING BV | IN100132 |
| 2025-08-21 | €2,433.52 | 2B daken B.V. | IN100403 |
| 2025-08-22 | €100.00 | H.A.H.M. van Bottenburg | IN100400 |
| 2025-08-22 | €14,851.50 | O. Gilad eo D.E. Tomasouw | IN100344 |
| 2025-08-25 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-08-25 | €500.00 | Mw F van Alphen | IN100026 |
| 2025-08-25 | €500.00 | Mw E Ozcelik | IN100234 |
| 2025-09-01 | €250.00 | AAFI Solutions B.V. | IN100170 |
| 2025-09-01 | €371.98 | KDV Little Super Stars | IN100366 |
| 2025-09-01 | €371.98 | Kinderdagverblijf Little Super Star | IN100366 |
| 2025-09-02 | €259.15 | DönerGo | IN100210 |
| 2025-09-22 | €50.00 | Mw Z C Stuart | IN100394 |
| 2025-09-23 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-09-23 | €250.00 | Ruizendaal Vloeren | IN100019 |
| 2025-09-24 | €1,196.60 | Erven van Hr FJ Goossens,Mw CJH Goossens | IN100311 |
| 2025-09-26 | €250.00 | Ruizendaal Vloeren | IN100019 |
| 2025-09-26 | €371.98 | KDV Little Super Stars | IN100366 |
| 2025-09-26 | €371.98 | Kinderdagverblijf Little Super Star | IN100366 |
| 2025-09-26 | €1,800.00 | STOKVIS TAPES BENELUX BV | IN100180 |
| 2025-09-30 | €57.53 | Hr KT Mugne | IN100431 |
| 2025-09-30 | €257.13 | E. Musabelli | IN100390 |
| 2025-10-01 | €528.56 | ACRUZ BRANDPREVENTIE EN | IN100241 |
| 2025-10-01 | €662.92 | S. Jarra | IN100281 |
| 2025-10-02 | €1,029.05 | M.C.M. Schellekens eo JAPM Schellekens-v | IN100452 |
| 2025-10-06 | €250.00 | AAFI Solutions B.V. | IN100170 |
| 2025-10-07 | €259.15 | DönerGo | IN100210 |
| 2025-10-13 | €186.69 | NanaSweets | IN100454 |
| 2025-10-15 | €700.00 | FBC Trade B.V. | IN100368 |
| 2025-10-16 | €156.74 | L ZANIEWICZ | IN100296 |
| 2025-10-17 | €100.00 | RUITER GLAS TIMMERWERKZA | IN100446 |
| 2025-10-17 | €725.23 | Hr LJR Batenburg | IN100222 |
| 2025-10-20 | €50.00 | Mw Z C Stuart | IN100394 |
| 2025-10-21 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-10-22 | €150.00 | Mw N Masrour | IN100456 |
| 2025-10-23 | €100.00 | L DOGAN | IN100417 |
| 2025-10-23 | €211.75 | CENTER-TO-EDGE PRODUCTIONS | IN100466 |
| 2025-10-24 | €500.00 | Mw F van Alphen | IN100026 |
| 2025-10-24 | €1,000.00 | GÜNEY ELEKTRO | IN100315 |
| 2025-10-26 | €1,830.30 | HOUTZAGERIJ DAEMEN | IN100109 |
| 2025-10-27 | €141.83 | H.H.E. Henssen | IN100469 |
| 2025-10-28 | €371.98 | Kinderdagverblijf Little Super Star | IN100366 |
| 2025-10-31 | €57.53 | Hr KT Mugne | IN100431 |
| 2025-11-01 | €250.00 | AAFI Solutions B.V. | IN100170 |
| 2025-11-01 | €2,235.00 | Mw S Hofman | IN100012 |
| 2025-11-02 | €528.56 | ACRUZ BRANDPREVENTIE EN | IN100241 |
| 2025-11-04 | €259.15 | N PETROSJAN | IN100210 |
| 2025-11-07 | €1,000.00 | GÜNEY ELEKTRO | IN100315 |
| 2025-11-20 | €150.00 | Mw N Masrour | IN100456 |
| 2025-11-20 | €186.69 | Hr S Ashili | IN100454 |
| 2025-11-21 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-11-26 | €156.74 | Elzet Bouw | IN100296 |
| 2025-11-26 | €1,951.01 | Hr J Roelofs | IN100182 |
| 2025-11-27 | €300.00 | Mw LM Gebremeskel | IN100377 |
| 2025-11-28 | €250.00 | AAFI Solutions B.V. | IN100170 |
| 2025-11-29 | €141.83 | H.H.E. Henssen | IN100469 |
| 2025-11-29 | €399.00 | Veselin Kordov | IN100497 |
| 2025-12-02 | €528.56 | ACRUZ BRANDPREVENTIE EN | IN100241 |
| 2025-12-03 | €487.00 | HWC Personeel B.V. | IN100418 |
| 2025-12-05 | €259.15 | N PETROSJAN | IN100210 |
| 2025-12-17 | €50.00 | H.A.H.M. van Bottenburg | IN100400 |
| 2025-12-17 | €482.99 | Erbengem. Saskia, Liselotte und Juliette | IN100299 |
| 2025-12-19 | €186.69 | Hr S Ashili | IN100454 |
| 2025-12-19 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2025-12-21 | €399.00 | Veselin Kordov | IN100497 |
| 2025-12-22 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-12-22 | €150.00 | Mw N Masrour | IN100456 |
| 2025-12-24 | €550.00 | FUTURE PROJECTS BV | IN100437 |
| 2025-12-24 | €1,302.99 | MA BOS | IN100217 |
| 2025-12-29 | €50.00 | H.A.H.M. van Bottenburg | IN100400 |
| 2025-12-29 | €100.00 | Mw JK Pauw | IN100334 |
| 2025-12-30 | €141.83 | H.H.E. Henssen | IN100469 |
| 2025-12-31 | €500.00 | Mw F van Alphen | IN100026 |
| 2025-12-31 | €1,431.61 | SDV Security | IN100378 |
| 2026-01-01 | €399.00 | Veselin Kordov | IN100497 |
| 2026-01-05 | €259.15 | DönerGo | IN100210 |
| 2026-01-07 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-01-09 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-01-16 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-01-19 | €1,500.00 | Y'S INFRA B.V. | IN100249 |
| 2026-01-20 | €186.69 | Hr S Ashili | IN100454 |
| 2026-01-21 | €100.00 | Mw JK Pauw | IN100334 |
| 2026-01-21 | €399.00 | Veselin Kordov | IN100497 |
| 2026-01-23 | €150.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-01-29 | €141.83 | H.H.E. Henssen | IN100469 |
| 2026-01-29 | €550.00 | FUTURE PROJECTS BV | IN100437 |
| 2026-01-31 | €276.30 | Hr JRCT Jairam | IN100350 |
| 2026-02-02 | €1,512.48 | AERO EXPRESS BV | IN100163 |
| 2026-02-05 | €211.75 | YELK Finance | IN100489 |
| 2026-02-05 | €500.00 | Mw F van Alphen | IN100026 |
| 2026-02-10 | €259.15 | DönerGo | IN100210 |
| 2026-02-17 | €409.55 | MS DOMBEK | IN100446 |
| 2026-02-18 | €399.00 | Veselin Kordov | IN100497 |
| 2026-02-20 | €186.69 | Hr S Ashili | IN100454 |
| 2026-02-23 | €156.74 | LUKASZ ZANIEWICZ | IN100296 |
| 2026-02-26 | €3,754.01 | EMOTIVE B.V. | IN100330 |
| 2026-02-28 | €276.30 | Hr JRCT Jairam | IN100350 |
| 2026-03-02 | €141.83 | H.H.E. Henssen | IN100469 |
| 2026-03-02 | €500.00 | Mw F van Alphen | IN100026 |
| 2026-03-05 | €300.00 | Mw F van Alphen | IN100026 |
| 2026-03-09 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-03-10 | €156.74 | Elzet Bouw | IN100296 |
| 2026-03-10 | €259.15 | N PETROSJAN | IN100210 |
| 2026-03-10 | €641.00 | handelsonderneming jakobs | IN100333 |
| 2026-03-11 | €116.44 | Mw SA Makkinga | IN100506 |
| 2026-03-13 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-03-17 | €200.00 | Ruizendaal Vloeren | IN100019 |
| 2026-03-20 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-03-21 | €186.95 | Hr S Ashili | IN100454 |
| 2026-03-23 | €399.00 | Veselin Kordov | IN100497 |
| 2026-03-28 | €276.30 | Hr JRCT Jairam | IN100350 |
| 2026-03-31 | €141.83 | H.H.E. Henssen | IN100469 |
| 2026-04-01 | €116.44 | Mw SA Makkinga | IN100506 |
| 2026-04-02 | €179.54 | Hr E van der Meer | IN100552 |
| 2026-04-05 | €500.00 | Mw F van Alphen | IN100026 |
| 2026-04-07 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-04-17 | €399.00 | Veselin Kordov | IN100497 |
| 2026-04-20 | €100.00 | Mw JK Pauw | IN100334 |
| 2026-04-20 | €267.80 | Hr N Ouaalit | IN100505 |
| 2026-04-21 | €186.95 | Hr S Ashili | IN100454 |
| 2026-04-24 | €250.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-04-26 | €276.30 | Hr JRCT Jairam | IN100350 |
| 2026-04-29 | €141.83 | H.H.E. Henssen | IN100469 |
| 2026-04-30 | €256.00 | Hr JPGT Janssen | IN100553 |
| 2026-05-02 | €116.44 | Mw SA Makkinga | IN100506 |
| 2026-05-15 | €100.00 | Klijn Afbouw V.O.F. | IN100229 |
| 2026-05-24 | €186.95 | Hr S Ashili | IN100454 |
| 2026-05-24 | €276.30 | Hr JRCT Jairam | IN100350 |
| 2026-05-27 | €393.25 | Toys of your Choice | IN100457 |
| 2026-05-28 | €399.00 | Veselin Kordov | IN100497 |
| 2026-05-30 | €100.00 | Hr JPGT Janssen | IN100553 |

## GROEP A — na 30 mei 2026, echt nieuw — 17 stuks, €8,836.39

| Datum | Bedrag | Tegenpartij | Zaak | Zaakstatus | Herkend via | Uitbetaald aan opdrachtgever? | Omschrijving |
|---|---|---|---|---|---|---|---|
| 2026-06-01 | €50.00 | Mw S Saltik | IN100345 | afgesloten | IN-nr | JA 2026-06-16 | Betalingsregeling dossier IN100345 |
| 2026-06-01 | €116.44 | Mw SA Makkinga | — | ? | geen kenmerk | ? | thuiszorg Sabina 8043VD 481 Zwolle |
| 2026-06-02 | €141.80 | H.H.E. Henssen | IN100469 | afgesloten | IN-nr | JA 2026-07-02 | Henssen's Bizz Benelux / IN100469 |
| 2026-06-09 | €14.52 | Handelsond. Beerens B.V. | IN100547 | afgesloten | IN-nr | JA 2026-07-02 | dossiernr. IN100547 / LegalWork B.V. - factuur LW100882 van 15 okt 2025 |
| 2026-06-10 | €540.69 | Dakrenovatie Mulder | IN100568 | afgesloten | naam | niet gevonden | 100767 |
| 2026-06-10 | €1,026.54 | Vosbouw | IN100532 | afgesloten | IN-nr | JA 2026-07-02 | Kenmerk IN100532 |
| 2026-06-11 | €1,428.62 | Pirnar NL | IN100585 | afgesloten | IN-nr | JA 2026-07-02 | Incassocode: IN100585 |
| 2026-06-11 | €2,817.25 | Studio The Blue Pearl | IN100480 | afgesloten | IN-nr | JA 2026-07-02 | IN100480 |
| 2026-06-16 | €1,036.58 | FOX AANNEMERS KOZIJNEN | IN100494 | afgesloten | IN-nr | JA 2026-07-02 | IN100494 IN100494I70956639 |
| 2026-06-18 | €216.25 | Mw SJL Cuijpers | IN100543 | afgesloten | IN-nr | JA 2026-07-02 | Incassocenter B.V. / Bernard (IN100543) |
| 2026-06-23 | €200.00 | KET D | IN100476 | afgesloten | IN-nr | niet gevonden | Dossiernummer In100476 |
| 2026-06-25 | €276.32 | Hr JRCT Jairam | IN100350 | afgesloten | IN-nr | JA 2026-07-02 | Jairam (IN100350) |
| 2026-06-26 | €300.00 | Hr E Dinc | D100085 | niet in Luxis | los kenmerk | ? | Dossiernummer: D100085 |
| 2026-06-29 | €100.00 | Hr JPGT Janssen | IN100553 | afgesloten | IN-nr | JA 2026-07-02 | in100553 |
| 2026-07-01 | €50.00 | Mw S Saltik | IN100345 | afgesloten | IN-nr | JA 2026-07-02 | Betalingsregeling IN100345 |
| 2026-07-07 | €250.00 | Onderhoudsbedrijf Benjamin Radem | IN100215 | nieuw | IN-nr | niet gevonden | Dossier. IN100215 |
| 2026-07-08 | €271.38 | Stal Sans Souci | IN100197 | afgesloten | IN-nr | niet gevonden | IN100197 I71731124 |

## GROEP B — termijnen van betaalregelingen, zaak deels geboekt — 8 stuks, €3,575.50

| Datum | Bedrag | Tegenpartij | Zaak | Zaakstatus | Herkend via | Uitbetaald aan opdrachtgever? | Omschrijving |
|---|---|---|---|---|---|---|---|
| 2025-07-29 | €948.42 | KINDEROPV IKKE OOK TWEE | IN100172 | afgesloten | IN-nr | niet gevonden | kenmerk IN100172 |
| 2025-08-04 | €1,309.86 | Avetica B.V. | IN100148 | afgesloten | IN-nr | niet gevonden | IN100148-I61187362 |
| 2025-10-28 | €371.98 | KDV Little Super Stars | IN100366 | afgesloten | IN-nr | niet gevonden | INC Zakelijk IN100366 |
| 2025-11-25 | €57.53 | Hr KT Mugne | IN100431 | afgesloten | IN-nr | niet gevonden | IN100431 |
| 2026-02-06 | €528.56 | ACRUZ BRANDPREVENTIE EN | IN100241 | afgesloten | IN-nr | JA 2026-03-09 | dossiernummer: IN100241 A.Cruz Brandpreventie en Utiliteitsbouw |
| 2026-04-01 | €50.00 | Mw S Saltik | IN100345 | afgesloten | IN-nr | JA 2026-05-04 | IN100345 |
| 2026-04-13 | €259.15 | N PETROSJAN | IN100210 | afgesloten | IN-nr | JA 2026-04-16 | IN100210 termijn 10 van de 10 |
| 2026-05-08 | €50.00 | Mw S Saltik | IN100345 | afgesloten | IN-nr | JA 2026-06-16 | IN100345.   Betalingsregeling |

## GROEP C — zaak bekend in Luxis (afgesloten), betaling nooit geboekt — 28 stuks, €44,540.91

| Datum | Bedrag | Tegenpartij | Zaak | Zaakstatus | Herkend via | Uitbetaald aan opdrachtgever? | Omschrijving |
|---|---|---|---|---|---|---|---|
| 2025-07-09 | €1,013.74 | HATENBOER WATER BV | IN100260 | afgesloten | IN-nr | niet gevonden | Dossier IN100260 INC Zakelijk B.V. / Hatenboer-Water |
| 2025-07-11 | €3,778.59 | TPORTAL | IN100279 | afgesloten | IN-nr | niet gevonden | IN100279 |
| 2025-07-24 | €3,072.90 | DOCO INTERNATIONAL BV | IN100272 | afgesloten | IN-nr | niet gevonden | Kenmerk IN100272 I62131263 restant betaling Invorderingsbedrijf-Doco Internation |
| 2025-07-31 | €896.27 | JORDAN . BREEDIJK STYLING | IN100302 | afgesloten | naam | niet gevonden |  |
| 2025-08-07 | €927.98 | KROON VLEESWARENFABRIEK ZWAAGW E | IN100255 | afgesloten | IN-nr | niet gevonden | IN100255 onder protest |
| 2025-08-22 | €811.79 | Maatschap Schouwburgring 563 | IN100250 | afgesloten | IN-nr | niet gevonden | IN100250 |
| 2025-08-22 | €2,299.43 | Wasserij Buis B.V. | IN100195 | afgesloten | IN-nr | niet gevonden | Wasserij Buis (IN100195) |
| 2025-08-22 | €3,233.68 | W&L Beleggingen B.V. | IN100107 | afgesloten | IN-nr | niet gevonden | IN100107 |
| 2025-09-18 | €930.11 | CAFÉ MONTPARNASSE | IN100420 | afgesloten | IN-nr | niet gevonden | incassocode IN100420 |
| 2025-09-19 | €174.64 | Aleman Visuals | IN100429 | afgesloten | IN-nr | niet gevonden | IN100429 |
| 2025-09-22 | €1,734.70 | Q HUANG CJ | IN100440 | afgesloten | IN-nr | niet gevonden | in100440 |
| 2025-09-22 | €2,160.58 | Bartosz Piping + Constructions | IN100428 | afgesloten | IN-nr | niet gevonden | WEDEROM SOMMATIE TOT BETALING / Incassocenter B.V. / Bartosz Piping + Constructi |
| 2025-09-26 | €483.85 | K.E Vloeren | IN100303 | afgesloten | IN-nr | niet gevonden | IN100303 |
| 2025-10-03 | €173.47 | SCOOTMOBIEL + MORE | IN100426 | afgesloten | IN-nr | niet gevonden | IN100426 t.b.v. oplichters Incassocenter |
| 2025-10-06 | €5,851.50 | ZZIIN BREDA | IN100280 | afgesloten | IN-nr | niet gevonden | IN100280 |
| 2025-10-08 | €383.02 | CMS Derks Star Busmann N.V. | IN100158 | afgesloten | IN-nr | niet gevonden | Dossier INC Zakelijk B.V. - CMS Derks Star Busmann N.V. IN100158 - factuur 30011 |
| 2025-10-08 | €488.35 | Hr R J Steins-Hundscheidt en/of  | IN100464 | afgesloten | IN-nr | niet gevonden | Treffen van een regeling (aanbod vaststellingsovereenkomst) / COLLECT 1 B.V. / R |
| 2025-10-14 | €3,470.31 | Van Vliet metaaltechniek | IN100453 | afgesloten | IN-nr | niet gevonden | IN100453 |
| 2025-10-23 | €312.68 | T.S. de Vries | IN100395 | afgesloten | IN-nr | niet gevonden | SOMMATIE TOT BETALING / Incassocenter B.V. / De Vries / IN100395 |
| 2025-11-21 | €912.48 | GÜNEY ELEKTRO | IN100315 | afgesloten | IN-nr | niet gevonden | Incassocenter B.V. / Güney elektro (IN100315) |
| 2025-12-16 | €290.03 | Florusse Busch duurzame installa | IN100356 | afgesloten | IN-nr | niet gevonden | Ref. IN100356 factuurnummer 140059 |
| 2025-12-16 | €798.09 | Fixer Aannemersbedrijf | IN100455 | afgesloten | IN-nr | niet gevonden | IN100455 |
| 2025-12-18 | €1,901.37 | SIMAR AUTOMATISERING BV | IN100174 | afgesloten | IN-nr | niet gevonden | INC Zakelijk B.V. / Simar Automatisering B.V. (IN100174) ONDER PROTEST |
| 2026-01-28 | €893.75 | Mw L Smirnova | IN100436 | afgesloten | IN-nr | JA 2026-02-09 | IN100436-I66242659 Smirnov70 |
| 2026-02-20 | €209.09 | Mw ZC Markelo | IN100394 | afgesloten | IN-nr | JA 2026-05-04 | Fix it Virtual / IN100394 |
| 2026-03-31 | €231.92 | YONA FAILY SPICE FACTORY | IN100548 | afgesloten | IN-nr | niet gevonden | LW100892 IN100548 |
| 2026-04-02 | €5,895.09 | van Essen de vakschilder | IN100544 | afgesloten | IN-nr | JA 2026-05-04 | IN100544 |
| 2026-05-28 | €1,211.50 | Handelsond. Beerens B.V. | IN100547 | afgesloten | IN-nr | JA 2026-06-16 | dossiernr. IN100547 / LegalWork B.V. - factuur LW100882 van 15 okt 2025 |

## GROEP D — zaak onbekend in Luxis — 21 stuks, €39,565.49

| Datum | Bedrag | Tegenpartij | Zaak | Zaakstatus | Herkend via | Uitbetaald aan opdrachtgever? | Omschrijving |
|---|---|---|---|---|---|---|---|
| 2025-07-11 | €5,369.82 | DFREIGHT SHIPPING LLC | — | ? | geen kenmerk | ? | Legal fees Dfreight shipping |
| 2025-08-01 | €17,500.00 | DONKER GROEP BV | — | ? | geen kenmerk | ? | dossier Grave / Donker |
| 2025-08-13 | €929.08 | Braspenning Vloeren | — | ? | geen kenmerk | ? |  |
| 2025-08-21 | €568.77 | Hr JH van Zaanen | — | ? | geen kenmerk | ? | Factuur 140213 |
| 2025-08-21 | €1,198.27 | Richard Yorke Limited | — | ? | geen kenmerk | ? | (BUSINESS EXPENSES)RICHARD YORKE LTD INV 300136852 |
| 2025-08-24 | €1,810.62 | TRUST IT B V | — | ? | geen kenmerk | ? | Fact.nrs: 300136874 en 300141547 + rente en kosten |
| 2025-09-24 | €285.33 | Groenendijk Tech. Dienstverlenin | — | ? | geen kenmerk | ? | betalingsregeling |
| 2025-10-22 | €525.29 | NM VAN DEN BOOM | — | ? | geen kenmerk | ? | factuur 138259 |
| 2025-10-22 | €6,663.73 | MK FLEX BV | D100106 | niet in Luxis | los kenmerk | ? | Kenmerk: D100106 |
| 2025-12-01 | €500.00 | Van der Hem Holding BV | d100060 | niet in Luxis | los kenmerk | ? | d100060 hem/smedes |
| 2025-12-30 | €100.00 | Hr E Dinc | D100085 | niet in Luxis | los kenmerk | ? | Dossiernr.:D100085 |
| 2025-12-31 | €50.00 | H.A.H.M. van Bottenburg | — | ? | geen kenmerk | ? | 3e deel betaling fakt.137158 |
| 2026-01-14 | €711.38 | FayeCare B.V. | — | ? | geen kenmerk | ? | Kenmerk 142162 142163 143298 |
| 2026-01-24 | €45.20 | Mw N Masrour | FN100456 | niet in Luxis | los kenmerk | ? | Collect 1b/ rijschool ainzohra (FN100456) |
| 2026-01-27 | €300.00 | Hr E Dinc | D1000085 | niet in Luxis | los kenmerk | ? | D1000085 |
| 2026-02-23 | €100.00 | Mw JK Pauw | — | ? | geen kenmerk | ? |  |
| 2026-02-26 | €300.00 | Hr E Dinc | D1000085 | niet in Luxis | los kenmerk | ? | Dossiernr.: D1000085 |
| 2026-03-31 | €300.00 | Hr E Dinc | D1000085 | niet in Luxis | los kenmerk | ? | Dossiernummer: D1000085 |
| 2026-04-29 | €300.00 | Hr E Dinc | D1000085 | niet in Luxis | los kenmerk | ? | Dossiernummer: D1000085 |
| 2026-05-19 | €1,708.00 | Hr R K0nigel en Mw M L E Konigel | D100079 | niet in Luxis | los kenmerk | ? | Scholte/Konigel Louwers D100079 |
| 2026-05-27 | €300.00 | Hr E Dinc | D1000085 | niet in Luxis | los kenmerk | ? | Dossiernummer: D1000085 |

## Detail groep B — bewijs per zaak (bank vs. Luxis-boeking op dezelfde dag)

| Zaak | Debiteur | Datum | Bank ontving | Luxis boekte die dag | Verschil |
|---|---|---|---|---|---|
| IN100172 | Kinderopvang Ikke-Ook Twee | 29-07-2025 | €948,42 | €761,06 | €187,36 |
| IN100148 | Avetica B.V. | 04-08-2025 | €1.309,86 | €307,34 | €1.002,52 (22-08 is −€1.309,86 aan Avetica terugbetaald) |
| IN100366 | KDV Little Super Stars | 28-10-2025 | €371,98 | €313,89 (2e regel die dag) | €58,09 |
| IN100431 | KM Eco / Mugne | 25-11-2025 | €57,53 | €40,09 | €17,44 |
| IN100241 | A.Cruz Brandpreventie | 06-02-2026 | €528,56 | €397,78 | €130,78 |
| IN100210 | Petrosjan | 13-04-2026 | €259,15 | €115,76 | €143,39 |

Lezing: dit zijn de slottermijnen — de debiteur betaalde de vaste termijn, de zaak had minder openstaan; BaseNet boekte het restant en de rest werd afgehandeld (doorstorting/terugbetaling staat in de afschrijvingen). **Bijboeken van het volle bankbedrag = dubbel.**

### Saltik IN100345 (regeling loopt gewoon door)
- In afschrift: 01-04 €50, 08-05 €50 (groep B) én 01-06 €50, 01-07 €50 (groep A).
- Uitbetalingen 'incklant IN100345': 04-05, 16-06, 02-07 — het geld wordt maandelijks doorgestort.
- In Luxis: alleen een oude betaling van €150 (jan 2025); de regeling-record bestaat wel.

## Beslislijst (bijgewerkt t.o.v. S194)

1. **138 GEBOEKT** — bij import per stuk afwijzen of vooraf uitsluiten (dubbeltel-valkuil H17 ziet ze niet).
2. **Groep A (17, €8.836,39)** — 11 al doorgestort, 6 vermoedelijk nog op de rekening. Boeken op afgesloten zaak of eerst heropenen? En: doorgestorte bedragen wel/niet als derdengelden-bijschrijving boeken (zonder uitbetaling erbij klopt het saldo niet)?
3. **Groep B** — VERVALLEN op de Saltik-termijnen na: de 6 slottermijnen zijn gecapt geboekt (audit), alleen Saltik IN100345 (2×€50, plus 2×€50 in groep A) is echt onboekt.
4. ~~Groep C bijboeken of laten~~ — VERVALLEN na audit: al geboekt (gecapt), zie correctie bovenaan.
5. **Groep D (21, €39.565,49)** — zaken niet in Luxis (D-/FN-nummers, losse facturen): negeren of dossiers aanmaken?
6. **Derdengelden-ijkpunt** — Luxis-saldo is €0, bank zegt €12.544,99 (8 juli). Voorstel: kies een ijkdatum en boek alleen vanaf daar in+uit volledig; historie reconstrueren = ~370 boekingen handwerk.