# S195 — 1-op-1 audit: BaseNet-bron vs Luxis (betalingen + regelingen)

Grondige controle op verzoek Arsalan (11 juli 2026): is alles één-op-één overgezet, bij het juiste dossier, kloppend met het bronbestand (`Xml_02-07-2026_2400.zip`) en het bankafschrift? Alleen-lezen; methode: onafhankelijke herberekening met de echte parser (`scripts/basenet/parse.py` + `mapping.py`) tegen prod-exports.

## Eindoordeel

| Controle | Resultaat |
|---|---|
| 56 losse betaal-records (IncassoBetalingAnders) | ✅ alle 56 in Luxis, juiste dossier, juiste datum; 0 dubbel, 0 ontbrekend |
| 199 bankregel-betalingen (CashBankLine, S180) | ✅ alle 199 in Luxis, juiste dossier (cblpcode), juiste datum; 0 dubbel |
| Bedragen | 191 op de cent exact; **64 bewust lager geboekt (gecapt)** — zie tabel, totaal €6.198,46 |
| 13 betalingsregelingen / 121 termijnen | ✅ allemaal exact: juiste zaak, juiste vervaldatum, juist bedrag; niets mist, niets dubbel |
| Regelingen-scope | Bron heeft 323 termijnen over 37 zaken; bewust alleen de 121 **toekomstige** (vanaf 9 juli 2026) over 13 zaken geïmporteerd — verleden termijnen zeggen niet of ze betaald zijn (S179-afspraak). Geen zaak met toekomstige termijnen ontbreekt. |
| Bankafschrift-kruiscontrole | 138 credits exact geboekt; alle 57 venster-boekingen zonder exacte credit verklaard: gecapt (bank ontving méér) óf 'rechtstreeks aan cliënt' (nooit via de derdengeldenrekening) |
| Verjaringstaken IN100015/IN100127 | ❌ NIET afgevinkt — BaseNet-status was **Lopend** (niet gesloten), voorwaarde Arsalan niet voldaan |

## De 64 gecapte betalingen — wat en waarom

De import boekte een betaling nooit hoger dan wat er volgens Luxis' eigen renteberekening op de betaaldag openstond. Luxis rekent rente juridisch zuiver vanaf de vervaldatum en komt daardoor iets lager uit dan BaseNet; het verschil is destijds bewust gecapt en gerapporteerd (S179: 17×, S180: 47× — deze audit reproduceert exact diezelfde aantallen onafhankelijk).

**Gevolg:** deze 64 zaken staan in Luxis op 'volledig betaald', maar het geregistreerde betaalbedrag is samen **€6.198,46 lager** dan wat de debiteur werkelijk betaalde.

⚠️ **Heropeningsrisico:** wordt zo'n zaak later heropend en opnieuw doorgerekend (bv. met contractuele rente 2%/mnd), dan telt Luxis het te lage betaalbedrag mee → de debiteur zou kunnen worden aangeslagen voor geld dat al betaald is. **Bij heropening van een zaak uit deze lijst: eerst het betaalbedrag corrigeren naar het bronbedrag.** Deze tabel is daarvoor de referentie.

| Zaak | Betaaldatum | Werkelijk betaald (bron) | Geboekt in Luxis | Verschil | Type |
|---|---|---|---|---|---|
| IN100148 | 2025-08-04 | €1,309.86 | €307.34 | €1,002.52 | bankregel |
| IN100178 | 2025-06-19 | €4,553.58 | €4,028.43 | €525.15 | bankregel |
| IN100453 | 2025-10-14 | €3,470.31 | €3,140.60 | €329.71 | bankregel |
| IN100146 | 2025-05-20 | €1,732.60 | €1,434.34 | €298.26 | bankregel |
| IN100075 | 2025-07-11 | €5,369.82 | €5,076.09 | €293.73 | betaal-record |
| IN100047 | 2025-01-30 | €296.38 | €75.01 | €221.37 | bankregel |
| IN100003 | 2025-02-09 | €1,245.27 | €1,032.21 | €213.06 | bankregel |
| IN100544 | 2026-04-02 | €5,895.09 | €5,685.16 | €209.93 | bankregel |
| IN100272 | 2025-07-24 | €3,072.90 | €2,865.19 | €207.71 | bankregel |
| IN100172 | 2025-07-29 | €948.42 | €761.06 | €187.36 | bankregel |
| IN100255 | 2025-08-07 | €927.98 | €749.47 | €178.51 | betaal-record |
| IN100174 | 2025-12-18 | €1,901.37 | €1,723.87 | €177.50 | bankregel |
| IN100084 | 2025-04-11 | €4,376.77 | €4,215.50 | €161.27 | bankregel |
| IN100210 | 2026-04-13 | €259.15 | €115.76 | €143.39 | bankregel |
| IN100241 | 2026-02-06 | €528.56 | €397.78 | €130.78 | bankregel |
| IN100165 | 2025-05-28 | €1,479.08 | €1,352.17 | €126.91 | bankregel |
| IN100048 | 2025-02-03 | €2,606.36 | €2,498.87 | €107.49 | bankregel |
| IN100160 | 2025-06-03 | €2,892.35 | €2,785.86 | €106.49 | bankregel |
| IN100279 | 2025-07-11 | €3,778.59 | €3,691.56 | €87.03 | betaal-record |
| IN100195 | 2025-08-22 | €2,299.43 | €2,218.72 | €80.71 | betaal-record |
| IN100547 | 2026-05-28 | €1,211.50 | €1,133.43 | €78.07 | bankregel |
| IN100260 | 2025-07-09 | €1,013.74 | €942.23 | €71.51 | bankregel |
| IN100161 | 2025-05-21 | €1,442.94 | €1,372.31 | €70.63 | bankregel |
| IN100138 | 2025-05-28 | €3,631.52 | €3,562.34 | €69.18 | bankregel |
| IN100440 | 2025-09-22 | €1,734.70 | €1,666.71 | €67.99 | bankregel |
| IN100036 | 2025-01-29 | €5,518.79 | €5,451.46 | €67.33 | bankregel |
| IN100097 | 2025-04-23 | €2,200.92 | €2,137.70 | €63.22 | bankregel |
| IN100366 | 2025-10-28 | €371.98 | €313.89 | €58.09 | bankregel |
| IN100367 | 2025-08-24 | €1,810.62 | €1,755.51 | €55.11 | betaal-record |
| IN100124 | 2025-05-13 | €2,061.19 | €2,007.44 | €53.75 | bankregel |
| IN100144 | 2025-05-16 | €711.07 | €662.10 | €48.97 | betaal-record |
| IN100455 | 2025-12-16 | €798.09 | €749.82 | €48.27 | bankregel |
| IN100115 | 2025-05-16 | €771.45 | €727.19 | €44.26 | bankregel |
| IN100126 | 2025-05-13 | €964.12 | €920.51 | €43.61 | betaal-record |
| IN100456 | 2026-01-24 | €45.20 | €2.24 | €42.96 | bankregel |
| IN100380 | 2025-10-22 | €525.29 | €485.07 | €40.22 | bankregel |
| IN100428 | 2025-09-22 | €2,160.58 | €2,122.08 | €38.50 | bankregel |
| IN100218 | 2025-06-27 | €514.02 | €479.97 | €34.05 | bankregel |
| IN100361 | 2025-08-21 | €1,198.27 | €1,164.64 | €33.63 | betaal-record |
| IN100395 | 2025-10-23 | €312.68 | €280.20 | €32.48 | betaal-record |
| IN100436 | 2026-01-28 | €893.75 | €866.13 | €27.62 | bankregel |
| IN100420 | 2025-09-18 | €930.11 | €904.00 | €26.11 | bankregel |
| IN100322 | 2025-08-13 | €929.08 | €904.29 | €24.79 | betaal-record |
| IN100250 | 2025-08-22 | €811.79 | €788.76 | €23.03 | betaal-record |
| IN100107 | 2025-08-22 | €3,233.68 | €3,210.99 | €22.69 | betaal-record |
| IN100280 | 2025-10-06 | €5,851.50 | €5,830.34 | €21.16 | bankregel |
| IN100464 | 2025-10-08 | €488.35 | €468.72 | €19.63 | bankregel |
| IN100122 | 2025-05-19 | €119.80 | €100.48 | €19.32 | betaal-record |
| IN100010 | 2025-03-31 | €108.33 | €89.40 | €18.93 | bankregel |
| IN100431 | 2025-11-25 | €57.53 | €40.09 | €17.44 | bankregel |
| IN100426 | 2025-10-03 | €173.47 | €157.33 | €16.14 | betaal-record |
| IN100400 | 2025-12-31 | €50.00 | €35.63 | €14.37 | bankregel |
| IN100394 | 2026-02-20 | €209.09 | €196.61 | €12.48 | bankregel |
| IN100303 | 2025-09-26 | €483.85 | €471.60 | €12.25 | bankregel |
| IN100374 | 2025-08-21 | €568.77 | €557.28 | €11.49 | betaal-record |
| IN100334 | 2026-02-23 | €100.00 | €88.88 | €11.12 | bankregel |
| IN100548 | 2026-03-31 | €231.92 | €221.26 | €10.66 | bankregel |
| IN100158 | 2025-10-08 | €383.02 | €374.33 | €8.69 | bankregel |
| IN100429 | 2025-09-19 | €174.64 | €166.29 | €8.35 | bankregel |
| IN100393 | 2025-09-24 | €285.33 | €279.06 | €6.27 | bankregel |
| IN100315 | 2025-11-21 | €912.48 | €907.41 | €5.07 | bankregel |
| IN100491 | 2026-01-14 | €711.38 | €706.43 | €4.95 | bankregel |
| IN100356 | 2025-12-16 | €290.03 | €285.23 | €4.80 | betaal-record |
| IN100302 | 2025-07-31 | €896.27 | €895.88 | €0.39 | betaal-record |
| **Totaal (64)** | | | | **€6,198.46** | |

## Gevolg voor de bankimport-beslislijst (correctie op S194 én op de eerdere S195-indeling)

De groepen B en C uit de afschrift-indeling (samen 36 rijen, ~€48k) zijn **geen gaten**: 34 van de 36 zijn gewoon geboekt, alleen op het gecapte (lagere) bedrag — de datum+bedrag-vergelijking zag ze daardoor ten onrechte als 'nooit geboekt'. Echt onboekt uit B+C zijn alleen de 2 Saltik-termijnen (IN100345, 2×€50).

Resterende echte beslispunten:
1. **Groep A (17 na 30 mei, €8.836,39)** — echt nieuw; 11 al doorgestort aan opdrachtgever, 6 nog op de rekening (~€1.678,51).
2. **Saltik IN100345** — regeling loopt door (apr/mei/juni/juli 4×€50 ontvangen, niets geboekt; telkens doorgestort).
3. **Groep D (21, €39.565,49)** — zaken niet in Luxis (D-/FN-nummers): negeren of dossiers aanmaken.
4. **Derdengelden-ijkpunt** — Luxis-administratie leeg (0 transacties), bank zegt €12.544,99 (8 juli).

## Verjaringstaken — bevinding
IN100015 en IN100127 stonden in BaseNet op **Lopend** (geen finish-reason, geen afrondingsdatum). Arsalans voorwaarde was: alleen afvinken als ze óók in BaseNet gesloten waren → niet voldaan, taken blijven staan. (Dat ze in Luxis 'afgesloten' zijn komt door de generieke werkvoorraad-sluiting bij de import; deze twee zijn kandidaten voor de heropeningsbatches.)

---

## Fable-hercontrole (zelfde avond, na de C1-uitvoering op Opus)

Op verzoek Arsalan is al het niet-op-Fable gedane werk (de C1-boekingen + afsluitdocs)
onafhankelijk herbeoordeeld. Verse reconciliatie van alle 212 afschrift-credits tegen de
prod-stand ná het boeken, nu met bron-gebaseerde herkenning (BaseNet-record op datum+bedrag
i.p.v. alleen naam):

| Categorie | Aantal | Som |
|---|---|---|
| Exact geboekt (historisch) | 138 | €80.387,52 |
| S195-geboekt (11 juli, vol bedrag) | 14 | €9.896,75 |
| Gecapt geboekt (zelfde zaak+datum, lager bedrag — incl. 3 van 11 juli) | 48 | €64.882,58 |
| Onverklaard | 12 | €21.738,96 |

**Bevindingen + herstel:**
1. ✅ **Geen dubbele boekingen** — alle maandreeksen (o.a. IN100350/IN100469/IN100553) lopen
   aansluitend door; de 17 nieuwe boekingen overlappen nergens met bestaande.
2. 🔧 **Gefixt: termijn-koppeling IN100215** — de €250 (07-07) was niet aan de regeling-termijn
   van 12-07 (€1.049,21) gekoppeld → regeling-alarm zou "niets betaald" melden. Nu gekoppeld
   als deelbetaling (paid_amount 250, status partial, payment_id gezet). Saltik-termijnen
   (apr–jul) bestaan niet in Luxis (import nam alleen toekomst) → daar viel niets te koppelen.
3. 🔧 **Gefixt: 3 nieuwe gecapte zaken kregen dezelfde heropen-notitie** als de 64
   (IN100480 €98,22 · IN100532 €87,17 · IN100585 €61,17 verschil). Totaal nu 67 notities.
4. ✏️ **Correctie op het eerdere "16 onbekende betalingen ~€23k":** 8 daarvan waren de bankkant
   van gecapte boekingen (o.a. Braspenning→IN100322, Van Zaanen→IN100374, FayeCare→IN100491,
   Van den Boom→IN100380, Groenendijk→IN100393, Masrour→IN100456, Pauw→IN100334,
   Bottenburg→IN100400) — geld is gewoon geadministreerd. Echt onverklaard: **12 rijen,
   €21.738,96** — Donker €17.500 ("Grave/Donker"), Dinc 6×€300+1×€100, Königel €1.708,
   Makkinga €116,44, Van der Hem €500 (géén BaseNet-record gevonden; naam lijkt op IN100097
   maar bedrag past niet in diens betaal-cache) — per besluit Arsalan géén incassozaken, niet
   geboekt.
5. ✅ **Cap-verschil droogloop vs uitvoering verklaard** — droogloop rekende openstaand per
   vandaag, de boeking capt (correct) op openstaand per betaaldag; restant €0,66 op IN100480
   is hetzelfde bekende recompute-artefact als bij de 64 (notitie dekt het).
