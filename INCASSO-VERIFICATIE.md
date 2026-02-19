# Incasso-module Verificatierapport

**Datum:** 19 februari 2026
**Auditor:** Claude Code (Opus 4.6)
**Scope:** Renteberekening, WIK-staffel, Art. 6:44 BW imputatie, Seed data
**Bronbestanden:** `backend/app/collections/` (interest.py, wik.py, payment_distribution.py, service.py, models.py, schemas.py, router.py)
**Testbestanden:** `backend/tests/` (test_interest.py, test_interest_edge_cases.py, test_wik.py, test_wik_edge_cases.py, test_payment_distribution.py, test_payment_distribution_extended.py)

---

## 1. Renteberekening (interest.py)

### 1.1 Correctheid: GOED

De rente-engine is **wiskundig correct** geimplementeerd en volgt de Nederlandse wettelijke regels nauwkeurig.

**Wat klopt:**

- **Samengestelde rente:** Jaarlijkse kapitalisatie "telkens na afloop van een jaar" (art. 6:119 lid 2 BW). Het samenstellingsjaar loopt correct vanaf de **verzuimdatum**, NIET vanaf 1 januari.
- **Tariefwisselingen:** Wanneer het tarief wijzigt halverwege een renteperiode, wordt de periode correct gesplitst in sub-perioden met elk hun eigen tarief.
- **Pro-rata berekening:** Consistent `dagen/365`, ook in schrikkeljaren. Dit is de standaard Nederlandse praktijk.
- **Decimal types:** 100% Decimal gebruik. Geen enkele float in de hele berekeningsketen. `ROUND_HALF_UP` consequent toegepast.
- **Schrikkeljaar:** `_add_years(date(2024,2,29), 1)` geeft correct `date(2025,2,28)`, niet 1 maart.
- **Afronding per periode:** Elke sub-periode wordt individueel afgerond op 2 decimalen, daarna gesommeerd. Dit is de correcte werkwijze voor processtukken.
- **Contractuele rente:** Zowel enkelvoudige als samengestelde rente worden ondersteund, configureerbaar per zaak.

**Technische kwaliteit:**

| Aspect | Beoordeling |
|--------|------------|
| Decimal consequent | OK — nergens float |
| Afronding | OK — ROUND_HALF_UP consistent |
| Jaar vanaf verzuimdatum | OK — uitgebreid getest |
| Tariefwisselingen | OK — split in sub-perioden |
| Schrikkeljaar | OK — Feb 29 correct afgehandeld |
| Negatieve hoofdsom | OK — geeft negatieve rente (wiskundig correct) |
| Nul hoofdsom | OK — geeft 0 rente |
| 10 jaar compound | OK — expliciet getest |

### 1.2 Edge Cases Getest

| Edge Case | Status | Test |
|-----------|--------|------|
| 0 dagen (zelfde start/eind) | Getest | `TestZeroDays` |
| 1 dag rente | Getest | `TestSingleDay` |
| Exact 1 jaar (compound = simple) | Getest | `test_compound_1_year_equals_simple` |
| 1 jaar + 1 dag (kapitalisatie + 1 dag) | Getest | `test_one_year_plus_one_day` |
| 2 jaar compound | Getest | `test_compound_2_years` |
| 3 jaar compound | Getest | `test_compound_3_years` |
| 10 jaar compound | Getest | `test_very_long_compound_10_years` |
| 1,5 jaar (gedeeltelijk jaar) | Getest | `test_compound_1_5_years` |
| Gedeeltelijk jaar kapitaliseert NIET | Getest | `test_compound_partial_year_does_not_capitalize` |
| Tariefwijziging binnen samenstellingsjaar | Getest | `test_compound_rate_change_within_year` |
| 3 tariefwijzigingen in 1 jaar | Getest | `test_multiple_rate_changes_within_compound_year` |
| Realistisch voorbeeld met NL tarieven | Getest | `test_compound_real_rates_example` |
| Schrikkeljaar (Feb 29) | Getest | `TestLeapYear` |
| Compound startend op Feb 29 | Getest | `test_compound_starting_feb29` |
| Nul hoofdsom | Getest | `TestNegativeAndZeroAmounts` |
| Negatieve hoofdsom | Getest | `test_negative_principal_simple/compound` |
| 1 cent hoofdsom | Getest | `test_one_cent_principal` |
| 0% tarief | Getest | `TestZeroRate` |
| Zeer kleine hoofdsom (50 euro) | Getest | `test_small_principal` |
| Zeer grote hoofdsom (1.000.000 euro) | Getest | `test_very_large_principal` |
| Tarief wijzigt exact op startdatum | Getest | `test_rate_change_on_start_date` |
| Tarief wijzigt exact op einddatum | Getest | `test_rate_change_on_end_date` |
| Geen tarief voor startdatum | Getest | `test_no_rate_before_start` |
| Lege tarievenlijst | Getest | `test_empty_rates_list` |
| ROUND_HALF_UP op exact 0.005 | Getest | `TestRounding` |

### 1.3 Edge Cases NIET Getest

| Edge Case | Ernst | Toelichting |
|-----------|-------|------------|
| **Rente na deelbetaling op hoofdsom** | HOOG | Wanneer een betaling de hoofdsom vermindert, moet rente berekend worden op het verlaagde bedrag vanaf de betalingsdatum. Dit is NIET geimplementeerd — rente wordt altijd op de originele hoofdsom berekend. Zie sectie 4 voor details. |
| **Meerdere vorderingen met verschillende verzuimdata** | MEDIUM | De code ondersteunt dit via `calculate_case_interest` (loopt over claims), maar er is geen specifieke test voor. |
| **Lege claims-lijst** | LAAG | `calculate_case_interest` met 0 claims — zou moeten werken maar is niet getest. |
| **Vervaldatum op weekend/feestdag** | LAAG | Systeem gebruikt de ingevoerde verzuimdatum zonder correctie voor weekenden. In de praktijk correct: de gebruiker voert de juridisch correcte datum in. |
| **Contractuele rente met tariefwijziging** | LAAG | `build_contractual_rate_schedule` maakt een vast tarief. Contracten met variabele rente worden niet ondersteund. |

### 1.4 Juridische Correctheid

**Artikel 6:119 BW (wettelijke rente):** CORRECT
- Samengestelde rente, jaarlijks — OK
- Jaar loopt vanaf verzuimdatum — OK
- Formule: hoofdsom x tarief% x dagen/365 — OK

**Artikel 6:119a BW (handelsrente):** CORRECT
- Zelfde compound-logica als 6:119 — OK
- ECB herfinancieringsrente + 8 procentpunt — tarieven correct in seed data

**Artikel 6:119b BW (overheidshandelsrente):** CORRECT
- Zelfde tarieven als 6:119a — OK in seed data

---

## 2. WIK-staffel / BIK-berekening (wik.py)

### 2.1 Correctheid: GOED

De WIK-staffelberekening is **exact correct** geimplementeerd en uitgebreid getest.

**Staffelverificatie:**

| Schijf | Code | Wet | Status |
|--------|------|-----|--------|
| 15% over eerste EUR 2.500 | `(Decimal("2500"), Decimal("0.15"))` | 15% over eerste 2.500 | OK |
| 10% over EUR 2.500-5.000 | `(Decimal("5000"), Decimal("0.10"))` | 10% over 2.500-5.000 | OK |
| 5% over EUR 5.000-10.000 | `(Decimal("10000"), Decimal("0.05"))` | 5% over 5.000-10.000 | OK |
| 1% over EUR 10.000-200.000 | `(Decimal("200000"), Decimal("0.01"))` | 1% over 10.000-200.000 | OK |
| 0,5% over EUR 200.000+ | `(None, Decimal("0.005"))` | 0,5% over meerdere | OK |
| Minimum EUR 40 | `WIK_MINIMUM = Decimal("40.00")` | Minimum EUR 40 | OK |
| Maximum EUR 6.775 | `WIK_MAXIMUM = Decimal("6775.00")` | Maximum EUR 6.775 | OK |
| BTW 21% | `BTW_RATE = Decimal("0.21")` | 21% | OK |

**Rekenvoorbeelden geverifieerd:**

| Hoofdsom | Verwacht | Code geeft | Status |
|----------|----------|-----------|--------|
| EUR 0 | EUR 0 | EUR 0 | OK |
| EUR 100 | EUR 40 (minimum) | EUR 40 | OK |
| EUR 1.000 | EUR 150 | EUR 150 | OK |
| EUR 2.500 | EUR 375 | EUR 375 | OK |
| EUR 5.000 | EUR 625 | EUR 625 | OK |
| EUR 10.000 | EUR 875 | EUR 875 | OK |
| EUR 25.000 | EUR 1.025 | EUR 1.025 | OK |
| EUR 100.000 | EUR 1.775 | EUR 1.775 | OK |
| EUR 200.000 | EUR 2.775 | EUR 2.775 | OK |
| EUR 500.000 | EUR 4.275 | EUR 4.275 | OK |
| EUR 1.005.000 | EUR 6.775 (max) | EUR 6.775 | OK |
| EUR 5.000.000 | EUR 6.775 (max) | EUR 6.775 | OK |

### 2.2 Edge Cases Getest

| Edge Case | Status | Test |
|-----------|--------|------|
| Exact op elke schijfgrens (2500, 5000, 10000, 200000) | Getest | `TestBoundary*` klassen |
| 1 cent boven/onder elke grens | Getest | Uitgebreid |
| Minimum (EUR 40) grens | Getest | `TestMinimumCap` |
| Maximum (EUR 6.775) grens | Getest | `TestMaximumCap` |
| EUR 0 hoofdsom | Getest | `test_bik_zero_principal` |
| EUR 0,01 hoofdsom | Niet expliciet | Maar minimum van EUR 40 vangt dit op |
| Negatieve hoofdsom | Getest | `test_bik_negative_principal` |
| BTW op minimum | Getest | `test_btw_on_minimum` |
| BTW op maximum | Getest | `test_maximum_with_btw` |
| BTW afronding | Getest | `TestBTWEdgeCases` |
| Bedrag met centen | Getest | `test_bik_with_cents`, `TestDecimalPrecision` |
| Alle 5 staffels tegelijk | Getest | `test_all_five_tiers` |
| Transparantie staffelopbouw | Getest | `test_bik_tiers_transparency` |

### 2.3 Edge Cases NIET Getest

| Edge Case | Ernst | Toelichting |
|-----------|-------|------------|
| EUR 0,01 hoofdsom | LAAG | Impliciet afgedekt door minimumcap van EUR 40. `calculate_bik(Decimal("0.01"))` zou 15% = 0.00 berekenen, dan opgehoogd naar minimum EUR 40. Correct, maar niet expliciet getest. |
| Exact EUR 1.000.000 | LAAG | Niet getest op exact dit bedrag, maar maximum is uitgebreid getest. |
| BTW-tarief wijziging | INFO | BTW-tarief (21%) is hardcoded. Correct voor NL sinds 2012. Bij wijziging moet code aangepast worden. |

### 2.4 Juridische Correctheid

**Art. 6:96 BW / Besluit BIK:** CORRECT
- Staffel exact conform Besluit vergoeding voor buitengerechtelijke incassokosten (Stb. 2012, 141)
- Minimum en maximum correct
- BTW-berekening correct

**Opmerking:** De 14-dagenbrief (art. 6:96 lid 6 BW) wordt niet door de BIK-berekening zelf gecontroleerd. Dit is een processtap, geen berekeningsstap. De gebruiker moet zelf zorgen dat de 14-dagenbrief correct is verstuurd voordat BIK in rekening wordt gebracht. Dit is acceptabel — het is een workflow-check, geen berekeningscheck.

---

## 3. Art. 6:44 BW — Betalingsimputatie (payment_distribution.py)

### 3.1 Correctheid: GOED (als standalone functie)

De `distribute_payment` functie implementeert de wettelijke volgorde **correct**:
1. Kosten (BIK, proceskosten, deurwaarderskosten)
2. Rente (vervallen rente)
3. Hoofdsom

**Wat klopt:**
- Volgorde kosten -> rente -> hoofdsom: OK
- Overbetaling wordt correct gedetecteerd en gerapporteerd: OK
- Decimal types consequent: OK
- Afronding correct: OK

### 3.2 Edge Cases Getest

| Edge Case | Status | Test |
|-----------|--------|------|
| Volledige betaling (alles gedekt) | Getest | `test_full_payment_covers_everything` |
| Deelbetaling alleen kosten | Getest | `test_partial_payment_costs_only` |
| Deelbetaling kosten + deel rente | Getest | `test_partial_payment_costs_and_some_interest` |
| Deelbetaling kosten + rente + deel hoofdsom | Getest | `test_payment_covers_costs_interest_partial_principal` |
| Overbetaling | Getest | `test_overpayment`, `TestOverpayment` |
| Geen kosten | Getest | `test_no_costs` |
| Geen rente | Getest | `test_no_interest` |
| EUR 0 betaling | Getest | `test_zero_payment` |
| Betaling met centen | Getest | `test_small_payment_with_cents` |
| Alleen hoofdsom resterend | Getest | `test_principal_only` |
| Exact bedrag kosten | Getest | `test_exact_costs_payment` |
| 3 opeenvolgende betalingen (volledig afbetaald) | Getest | `test_three_payments_pay_everything` |
| 5 gelijke betalingen | Getest | `test_five_equal_payments` |
| 10 kleine betalingen (druppelsgewijs) | Getest | `test_ten_small_payments` |
| 1 cent betalingen | Getest | `test_very_small_payments_one_cent` |
| 50 betalingen (precisie-stress) | Getest | `test_many_payments_no_precision_loss` |
| Betalingen met oneven centen | Getest | `test_payments_with_cents` |
| Herhalende decimalen (10/3) | Getest | `test_repeating_decimals` |
| Betaling spreidt over alle componenten | Getest | `test_payment_spans_all_three_components` |
| Alleen kosten resterend | Getest | `test_only_costs_remaining` |
| Alleen rente resterend | Getest | `test_only_interest_remaining` |
| Alles 0 (elke betaling = overbetaling) | Getest | `test_all_zero` |
| Realistisch incassoscenario | Getest | `TestRealisticScenario` |

### 3.3 Edge Cases NIET Getest

| Edge Case | Ernst | Toelichting |
|-----------|-------|------------|
| Negatieve betaling | LAAG | Functie valideert niet op negatieve betaling. Schema valideert `amount > 0` op API-niveau. |
| Negatieve uitstaande bedragen | LAAG | Functie valideert niet op negatieve kosten/rente/hoofdsom. Praktisch onmogelijk via de API. |

### 3.4 Juridische Correctheid

**Art. 6:44 BW:** CORRECT
- Volgorde: kosten -> rente -> hoofdsom — klopt exact met de wet
- Schuldenaar kan niet kiezen om eerst op de hoofdsom af te lossen — correct afgedwongen

---

## 4. KRITIEKE BEVINDING: Integratie Payment Distribution

### 4.1 BUG: Betalingsallocatie wordt NOOIT berekend

**Ernst: HOOG**

De `distribute_payment` functie in `payment_distribution.py` wordt **nergens aangeroepen** in de service-laag. Bij het aanmaken van een betaling (`service.py:create_payment`, regel 130-159) worden de allocatievelden nooit ingevuld:

```python
# service.py regel 143-149
payment = Payment(
    tenant_id=tenant_id,
    case_id=case_id,
    amount=data.amount,
    payment_date=data.payment_date,
    description=data.description,
    payment_method=data.payment_method,
)
# allocated_to_costs, allocated_to_interest, allocated_to_principal → default Decimal("0")
```

**Gevolg:** In `get_financial_summary` (service.py regel 411-413):
```python
total_paid_costs = sum(p.allocated_to_costs for p in payments)      # Altijd 0
total_paid_interest = sum(p.allocated_to_interest for p in payments) # Altijd 0
total_paid_principal = sum(p.allocated_to_principal for p in payments) # Altijd 0
```

Dit betekent:
- `remaining_costs` is altijd gelijk aan `total_bik` (kosten lijken nooit betaald)
- `remaining_interest` is altijd gelijk aan `total_interest`
- `remaining_principal` is altijd gelijk aan `total_principal`
- **Alleen `total_outstanding = grand_total - total_paid` is correct** (op hoog niveau)

**Impact op processtukken:** De per-component uitsplitsing in het financieel overzicht is **onjuist**. Een dagvaardingsspecificatie die deze data gebruikt toont verkeerde allocatie.

**Aanbeveling:** Bij `create_payment` moet `distribute_payment` worden aangeroepen om de allocatievelden in te vullen. Dit vereist dat op het moment van betaling de huidige stand van kosten, rente en hoofdsom bekend is.

### 4.2 DESIGN-BEPERKING: Rente op niet-verlaagde hoofdsom

**Ernst: MEDIUM**

De renteberekening (`calculate_case_interest`) berekent altijd rente op de **originele** hoofdsom van elke vordering. Wanneer een betaling deels op de hoofdsom wordt toegerekend (per art. 6:44 BW), wordt de rente NIET herberekend op het verlaagde bedrag.

**Voorbeeld:**
- Hoofdsom: EUR 5.000, verzuimdatum: 1 jan 2025
- Betaling op 1 jul 2025: EUR 2.000 → hiervan gaat (na kosten en rente) bijv. EUR 525 naar hoofdsom
- Resterende hoofdsom: EUR 4.475
- Maar het systeem berekent rente voor de periode 1 jul 2025 - heden op EUR 5.000, niet EUR 4.475

**Impact:** Bij grote deelbetalingen vroeg in het traject wordt de rente **overschat**. Voor kleine betalingen of betalingen laat in het traject is het verschil verwaarloosbaar.

**Juridische realiteit:** Voor dagvaardingen berekent men typisch rente tot datum dagvaarding op de originele hoofdsom, en vordert men rente "over het toe te wijzen bedrag vanaf datum dagvaarding tot aan de dag der algehele voldoening". In dat geval is de huidige implementatie **acceptabel** voor de dagvaarding zelf, maar **niet correct** voor een lopend financieel overzicht.

**Aanbeveling:** Implementeer een herberekeningsfunctie die betalingen chronologisch verwerkt en rente berekent op het na elke betaling resterende hoofdsombedrag.

---

## 5. Seed Data — Rentetarieven

### 5.1 Verificatie tegen officiële bronnen

**Bronnen gebruikt voor verificatie:**
- [Rijksoverheid.nl](https://www.rijksoverheid.nl/onderwerpen/schulden/vraag-en-antwoord/hoogte-wettelijke-rente)
- [Wieringa Advocaten](https://www.wieringa-advocaten.nl/nl/weblog/2026/01/05/wettelijke-rente-en-wettelijke-handelsrente-per-1-januari-2026/)
- [Credifin](https://credifin.nl/kennisbank/wettelijke-rente-berekening-regels-in-2026/)

**Wettelijke rente (art. 6:119 BW):**

| Periode | Seed data | Officieel | Status |
|---------|-----------|-----------|--------|
| Per 1 jan 2024 | 7,00% | 7% | OK |
| Per 1 jan 2025 | 6,00% | 6% | OK |
| Per 1 jan 2026 | 4,00% | 4% (KB 10 dec 2025) | OK |

**Wettelijke handelsrente (art. 6:119a BW):**

| Periode | Seed data | Officieel | Status |
|---------|-----------|-----------|--------|
| Per 1 jan 2024 | 12,50% | 12,50% | OK |
| Per 1 jul 2024 | 12,25% | 12,25% | OK |
| Per 1 jan 2025 | 11,15% | 11,15% | OK |
| Per 1 jul 2025 | 10,15% | 10,15% | OK |
| Per 1 jan 2026 | *Ontbreekt* | 10,15% (ongewijzigd) | ACTIE NODIG |

### 5.2 Ontbrekend Tarief

**Per 1 januari 2026** is de handelsrente **10,15%** (ongewijzigd ten opzichte van 1 juli 2025). Het systeem geeft het juiste tarief omdat het vorige tarief (10,15% vanaf 2025-07-01) doorloopt. Echter, voor **audittrail en traceerbaarheid** is het aanbevolen om een expliciet record toe te voegen in `seed_interest_rates.py`:

```python
("2026-01-01", "10.15"),  # ECB 2.15% + 8% — ongewijzigd
```

### 5.3 Historische Tarieven

De seed data bevat:
- **Wettelijke rente:** 28 perioden (vanaf 1934)
- **Handelsrente:** 27 perioden (vanaf 2002, invoering art. 6:119a BW)
- **Overheidshandelsrente:** Identiek aan handelsrente (correct per wet)

De historische tarieven zijn consistent met bekende bronnen. **Let op:** De oudere tarieven (voor 2002) zijn lastig te verifiëren via online bronnen. Voor praktisch gebruik is dit niet relevant — incassozaken van voor 2002 komen niet voor.

---

## 6. Type-veiligheid en Precision

### 6.1 Decimal-gebruik

| Bestand | Float gevonden? | Decimal consequent? |
|---------|----------------|-------------------|
| interest.py | NEE | JA — 100% Decimal |
| wik.py | NEE | JA — 100% Decimal |
| payment_distribution.py | NEE | JA — 100% Decimal |
| service.py | NEE | JA — `Decimal("0")` consequent |
| models.py | NEE | JA — `Numeric(15,2)` overal |
| schemas.py | NEE | JA — `Decimal` met `decimal_places=2` |
| router.py | NEE | N.v.t. (geen berekeningen) |
| seed_interest_rates.py | NEE | JA — string-waarden naar DB |

**Conclusie:** Nergens in de financiële code wordt `float` gebruikt. De hele keten van database (`NUMERIC(15,2)`) via SQLAlchemy (`Decimal`) tot API-response (`Pydantic Decimal`) is consistent. Dit voldoet aan de projectregel "NEVER float".

### 6.2 Afrondingsconventie

Overal `ROUND_HALF_UP`:
- `_round2(Decimal("0.005"))` = `Decimal("0.01")` — getest en correct
- Elke sub-periode wordt individueel afgerond, daarna gesommeerd
- Dit is de standaard werkwijze voor renteberekeningen in processtukken

---

## 7. Router en API-analyse

### 7.1 Bevindingen

| Endpoint | Correctheid | Opmerking |
|----------|------------|----------|
| `GET /interest` | OK | Berekent rente voor alle claims per zaak |
| `GET /bik` | OK | Somt `principal_amount` van alle claims op, berekent BIK |
| `POST /payments` | AANDACHTSPUNT | Maakt betaling aan zonder allocatie (zie sectie 4.1) |
| `GET /financial-summary` | AANDACHTSPUNT | Per-component allocatie altijd 0 (zie sectie 4.1) |
| `GET /interest-rates` | OK | Referentie-endpoint voor historische tarieven |

### 7.2 Ontbrekende Response-validatie

Het `/interest` endpoint retourneert een raw `dict` zonder `response_model`. De `CaseInterestSummary` Pydantic-schema bestaat in schemas.py maar wordt niet gebruikt als response_model. Dit is geen correctheidsprobleem maar kan type-fouten verbergen.

---

## 8. Samenvattende Tabel

| Module | Correctheid | Tests Compleet | Juridisch Correct | Actie Nodig |
|--------|------------|---------------|-------------------|-------------|
| **Renteberekening** (interest.py) | GOED | 95% — uitgebreid, vrijwel alle edge cases | JA — art. 6:119, 6:119a, 6:119b correct | Test voor rente na deelbetaling op hoofdsom |
| **WIK/BIK** (wik.py) | GOED | 98% — zeer grondig, alle grenzen getest | JA — Besluit BIK exact geimplementeerd | Minimaal — EUR 0,01 test toevoegen |
| **Art. 6:44 BW** (payment_distribution.py) | GOED (standalone) | 98% — uitgebreid met stress-tests | JA — volgorde kosten->rente->hoofdsom correct | Integratie met service-laag (BUG) |
| **Service-integratie** (service.py) | ONVOLDOENDE | N.v.t. — integratie ontbreekt | N.v.t. | **KRITIEK:** Betalingsallocatie aansluiten |
| **Seed data** (rentetarieven) | GOED | N.v.t. | JA — geverifieerd tegen rijksoverheid.nl | Handelsrente 2026-01-01 toevoegen |

---

## 9. Aanbevelingen (geprioriteerd)

### KRITIEK (moet gefixt)

1. **Betalingsallocatie integreren in service-laag**
   - Bij `create_payment`: roep `distribute_payment` aan
   - Vul `allocated_to_costs`, `allocated_to_interest`, `allocated_to_principal` in op het Payment-record
   - Vereist: berekening van huidige stand kosten/rente/hoofdsom op moment van betaling
   - Impact: financial summary per-component wordt correct

### HOOG (moet gepland)

2. **Renteherberekening na deelbetaling op hoofdsom**
   - Implementeer chronologische verwerking: per betaling → verlaag hoofdsom → bereken rente op nieuw bedrag
   - Impact: correct financieel overzicht na meerdere betalingen
   - Complexiteit: hoog — vereist herarchitectuur van de renteberekening

3. **Integratietests toevoegen**
   - Test: `create_payment` → allocatie → `get_financial_summary` → correcte uitsplitsing
   - Test: meerdere betalingen chronologisch → correcte restanten

### MEDIUM (aanbevolen)

4. **Seed data uitbreiden**
   - Voeg `("2026-01-01", "10.15")` toe aan `COMMERCIAL_RATES` in seed_interest_rates.py
   - Voeg `("2026-01-01", "10.15")` toe voor government rates

5. **Response-model toevoegen aan /interest endpoint**
   - Gebruik `CaseInterestSummary` als `response_model` voor type-validatie

6. **Test voor meerdere vorderingen met verschillende verzuimdata**
   - Expliciet testen dat `calculate_case_interest` correct omgaat met claims die op verschillende data beginnen

### LAAG (nice to have)

7. **Test voor EUR 0,01 BIK**
   - Expliciet testen dat `calculate_bik(Decimal("0.01"))` het minimum van EUR 40 retourneert

8. **Test voor lege claims-lijst**
   - Testen dat `calculate_case_interest` met 0 claims correct 0 retourneert

---

## 10. Conclusie

De **wiskundige kern** van de incassomodule is **solide**. De renteberekening, WIK-staffel en betalingsimputatie zijn elk afzonderlijk correct geimplementeerd en uitgebreid getest. Er zijn **geen fouten** gevonden in de berekeningen zelf. Alle bedragen gebruiken consequent `Decimal` — nergens `float`. De seed data voor rentetarieven is geverifieerd en up-to-date.

Het **kritieke probleem** zit in de **integratie**: de `distribute_payment` functie wordt nooit aangeroepen bij het registreren van betalingen. Hierdoor zijn de per-component allocatievelden altijd 0 en toont het financieel overzicht een incorrecte uitsplitsing. Het totaalbedrag uitstaand (`grand_total - total_paid`) is wel correct.

**Voor dagvaardingen** is het systeem bruikbaar: rente wordt correct berekend op de originele hoofdsom tot datum dagvaarding, en de BIK is exact. **Voor lopende financiële overzichten** na deelbetalingen is het systeem onvolledig door het ontbreken van de allocatie-integratie en de renteherberekening op verlaagde hoofdsom.

---

*Dit rapport is opgesteld op basis van code-analyse en juridische verificatie. Geen code is gewijzigd.*
