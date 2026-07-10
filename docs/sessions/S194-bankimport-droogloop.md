# S194 — Droogloop bankimport derdengeldenrekening (niets weggeschreven)

**Bestand:** CSV_A_NL20RABO0388506520 (9 juli 2025 t/m 9 juli 2026, 368 regels)
**Methode:** echte parser + echte matcher van de app, alleen-lezen tegen prod (10 juli 2026).

## Parser-fix vooraf (gecommit + live)
De echte Rabobank-export gebruikt een komma als decimaalteken (+1013,74). De parser
stripte komma's, waardoor élk bedrag 100× te hoog binnenkwam (som €17,7 mln i.p.v.
€176.905,81). Gefixt in `_parse_amount` (komma/punt/duizendtallen), 3 nieuwe tests
met een letterlijke rij uit dit afschrift. 53 tests groen. Encoding (Latin-1) ving
de upload-route al af.

## Cijfers na de fix
| Categorie | Aantal | Som |
|---|---|---|
| Bijschrijvingen (credits) totaal | 212 | €176.905,81 |
| Al geboekt in Luxis (datum+bedrag exact, S179/S180) | 138 | €80.387,52 |
| **A. Ná 30 mei 2026 — echt nieuw venster** | **17** | **€8.836,39** |
| B. Latere termijnen van deels geboekte regelingen | 6 | €3.475,50 |
| C. Gat: zaak bestaat (afgesloten), betaling nooit geboekt | 29 | €43.744,64 |
| D. Zaak onbekend in Luxis (D-/FN-nummers, losse facturen) | 22 | €40.461,76 |
| Afschrijvingen (uitgaand, worden nooit geïmporteerd) | 156 | — |

⚠️ **Dubbeltel-valkuil:** de 255 bestaande betalingen (S179/S180) zijn destijds
direct geboekt, búiten de import-pijplijn om. De ingebouwde dubbel-herkenning
(H17) kijkt alleen naar eerder geïmporteerde bankregels en herkent ze dus NIET.
Dit CSV blind importeren + alles goedkeuren = honderden dubbele boekingen.
De 138 "al geboekt" moeten bij de echte import per stuk afgewezen of vooraf
uitgesloten worden.

⚠️ **Matcher-bereik:** de automatische matcher kijkt alleen naar actieve
incassozaken (18 stuks op prod). Vrijwel alle historische credits horen bij
afgesloten zaken → handmatig koppelen of zaak heropenen. Van venster A matchte
alleen IN100215 (€250, 7 juli) automatisch.

## Beslislijst voor de importproef (C1, samen met Arsalan)
1. Venster A (17 credits, €8.836,39): importeren? Meeste zaken staan op
   "afgesloten" — boeken op afgesloten zaak of eerst heropenen?
2. Categorie C (€43,7k op bekende maar afgesloten zaken): historie bijboeken of
   bewust laten (BaseNet-tijdperk)?
3. Categorie D (€40,5k, zaken die niet in Luxis zitten): negeren of alsnog
   dossiers aanmaken?
4. Categorie B (6 termijnen): horen bij lopende regelingen — bijboeken ligt voor
   de hand, per stuk bevestigen.

## Rekening-scheiding in de code (vraag Arsalan, S194)
Wanneer welke rekening — zo zit het in de code, en het klopt:
- **Factuur van Lisanne aan haar opdrachtgever** → kantoorrekening
  (factuur-sjabloon toont `kantoor.iban`, 2 plekken).
- **Debiteur betaalt (sommatie/aanmaning/regeling)** → derdengeldenrekening
  (alle brieftexten gebruiken de derdengelden-helper; bij leeg veld een luide
  placeholder, nooit stil de verkeerde rekening — audit #61, Voda 6.19 lid 1).
- **Uitbetalingen derdengelden (SEPA)** → derdengeldenrekening.

**Prod-datafout:** het véld kantoorrekening bevat op prod de derdengelden-IBAN
(NL20 RABO 0388 5065 20). Elke factuur aan een opdrachtgever vraagt dus nu om
betaling op de derdengeldenrekening. Fix = juiste eigen Kesting-rekening
invullen (waarde bij Arsalan/Lisanne opvragen; zelfde punt als D-C-audit).

**Bijvangst (niet aangeraakt):** drie oude briefsjablonen in de map
`backend/templates/` (sommatie, 14-dagenbrief, renteberekening) worden door geen
enkele code meer gebruikt — opruimkandidaat voor de veegsessie.
