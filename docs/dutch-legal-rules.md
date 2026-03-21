# Dutch Legal Rules — Luxis Reference

## Interest Rates (Wettelijke Rente)

### Art. 6:119 BW — Statutory Interest (Wettelijke Rente)
- For consumer debts
- Set by AMvB, changes per half-year (1 jan, 1 jul)
- Current rates in `scripts/seed_interest_rates.py`

### Art. 6:119a BW — Commercial Interest (Handelsrente)
- For B2B transactions
- Higher than statutory rate
- ECB refinancing rate + 8 percentage points

### Art. 6:119b BW — Government Interest
- For transactions with government entities

### Compound Interest
- Year runs from **verzuimdatum** (default date), NOT from January 1
- Each anniversary of the verzuimdatum, accrued interest capitalizes

## WIK-staffel (Art. 6:96 BW — Buitengerechtelijke Incassokosten)

Tiered calculation on principal:
| Over bedrag | Percentage |
|-------------|-----------|
| Eerste EUR 2.500 | 15% |
| EUR 2.500 - 5.000 | 10% |
| EUR 5.000 - 10.000 | 5% |
| EUR 10.000 - 200.000 | 1% |
| Boven EUR 200.000 | 0.5% |

- **Minimum:** EUR 40
- **Maximum:** EUR 6.775
- **BTW:** 21% bovenop BIK als schuldeiser NIET BTW-plichtig is (en BTW dus niet kan verrekenen)

## Payment Distribution (Art. 6:44 BW)

Volgorde van toerekening bij deelbetaling:
1. **Kosten** (BIK, proceskosten, etc.)
2. **Rente** (vervallen rente)
3. **Hoofdsom** (principal)

## 14-dagenbrief (Art. 6:96 lid 6 BW)

- Verplicht voor consumenten (B2C)
- Termijn: 14 dagen na ontvangst (niet na verzending)
- Moet exacte bedrag BIK vermelden
- Zonder correcte 14-dagenbrief: geen BIK verschuldigd

## Dagvaarding

- Termijn: minimaal 7 dagen voor zitting
- Griffierecht: afhankelijk van vorderingsbedrag
- Nakosten: EUR 189 (zonder betekening) / EUR 287 (met betekening) — per 1 februari 2026 liquidatietarief
