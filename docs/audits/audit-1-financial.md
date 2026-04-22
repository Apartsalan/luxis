# Audit 1 — Financial Calculations (Luxis)

**Audit datum:** 2026-04-22
**Auditor:** Domain-expert review (Dutch collections law lens)
**Scope:** backend/app/collections/ (interest, WIK, payment distribution, griffierechten) plus integratie in services (cases, invoices, compliance).

---

## Samenvatting — kritische bevindingen

| Nr | Ernst | Bevinding | Module |
|----|-------|-----------|--------|
| 1 | Critical | Rente blijft lopen op oorspronkelijke hoofdsom na deelbetaling (schendt art. 6:44 BW) | collections/interest.py, service.py |
| 2 | Critical | BTW-op-BIK niet configureerbaar per client/case, default overal include_btw=False | collections/wik.py + alle aanroepen |
| 3 | Critical | Handelsrente (6:119a) wordt NIET automatisch gekozen bij B2B — default is statutory | cases/service.py lijn 399-405 |
| 4 | High | bik_override_percentage wordt genegeerd bij betalingsverdeling + financial summary | collections/service.py lijnen 237, 867 |
| 5 | High | Nakosten (EUR 189 / EUR 287) ontbreken volledig — geen berekening mogelijk | geen bestand |
| 6 | High | Wachttijd 14-dagenbrief is 14 in workflow, 15 in compliance — workflow te kort | workflow/service.py lijn 334 |
| 7 | Medium | Compound anniversary drift bij Feb 29 verzuim (verliest 1 dag per schrikkeljaar-cyclus) | collections/interest.py lijn 184-232 |
| 8 | Medium | Griffierechten-tabel 2026 heeft duplicaat-rijen — tarieven moeten geverifieerd | collections/griffierechten.py |
| 9 | Medium | 14-dagenbrief compliance telt vanaf created_at (verzending), niet ontvangst | collections/compliance.py lijn 71-77 |
| 10 | Low | interest_rates tabel is globaal (geen tenant) — acceptabel, geen mutatie-API | collections/models.py |

**Totalen:** Critical: 3 / High: 3 / Medium: 3 / Low: 1

---

## Hand-gecalculeerde scenarios vs code

| Scenario | Beschrijving | Hand-calc (NL recht) | Code-output | Verschil | Beoordeling |
|---|---|---|---|---|---|
| S1 | Consument EUR 3.500, verzuim 2025-03-15, calc 2026-04-22, wettelijke rente compound | EUR 211,39 | EUR 211,39 | 0,00 | CORRECT |
| S2 | Consument EUR 5.000, verzuim 2024-06-01, deelbetaling EUR 1.000 op 2024-10-01. Rente tot 2025-04-01 | EUR 270,82 | EUR 279,18 | +8,36 te veel | INCORRECT - art. 6:44 BW |
| S3a | B2C EUR 2.500,00 (tier boundary) | EUR 375,00 | EUR 375,00 | 0,00 | CORRECT |
| S3b | B2C EUR 5.000,00 | EUR 625,00 | EUR 625,00 | 0,00 | CORRECT |
| S3c | B2C EUR 10.000,00 | EUR 875,00 | EUR 875,00 | 0,00 | CORRECT |
| S3d | B2C EUR 200.000,00 | EUR 2.775,00 | EUR 2.775,00 | 0,00 | CORRECT |
| S3e | B2C EUR 1.005.000 (WIK max) | EUR 6.775,00 | EUR 6.775,00 | 0,00 | CORRECT |
| S3f | B2C EUR 1,00 (WIK min) | EUR 40,00 | EUR 40,00 | 0,00 | CORRECT |
| S4 | B2B EUR 12.000, verzuim 2024-03-01, calc 2026-04-22, handelsrente compound | EUR 3.084,76 | EUR 3.084,76 | 0,00 | CORRECT (math). B2B-default is statutory - zie bevinding 3 |
| S5 | B2C EUR 10.000, verzuim 2024-02-29, 4 jaar compound @ 6% | 4 volle jaren tot 2028-02-29 | anniversary drift op Feb 28 | ~EUR 1,60 drift | MEDIUM - bevinding 7 |
| S6 | Client niet BTW-plichtig (VvE), B2C EUR 3.500, BIK incl. BTW | EUR 574,75 | EUR 475,00 | -99,75 te weinig | CRITICAL - bevinding 2 |
| S7 | Compound anniversary exact: EUR 10.000, 1 jaar na verzuim | EUR 600,00 | EUR 600,00 | 0,00 | CORRECT |
| S8 | Compound anniversary + 1 dag | EUR 601,74 | EUR 601,74 | 0,00 | CORRECT |

---


## Bevindingen in detail

### 1. [CRITICAL] Rente accumuleert op oorspronkelijke hoofdsom na deelbetaling

**Locatie:**
- backend/app/collections/interest.py:310-351 (calculate_case_interest)
- backend/app/collections/service.py:206-251 (create_payment)

**Wat de wet zegt:** Art. 6:44 BW + art. 6:119/6:119a BW samen - rente loopt over de uitstaande hoofdsom. Na een deelbetaling die (na kosten en rente) hoofdsom aflost, moet rente vanaf dat moment over de lagere hoofdsom lopen.

**Wat de code doet:** calculate_case_interest gebruikt altijd claim.principal_amount. In create_payment wordt total_interest op die onverminderde hoofdsom berekend, waarna reeds toegerekende rente van eerdere betalingen wordt afgetrokken. Het verschil is te hoog.

**Bewijs (scenario S2):**
- Principal EUR 5.000, verzuim 2024-06-01, rente 7% in 2024, 6% per 2025-01-01.
- Deelbetaling EUR 1.000 op 2024-10-01: 625 BIK + 116,99 rente + 258,01 hoofdsom, rest 4.741,99.
- Rente tot 2025-04-01: Code EUR 279,18 / Wet EUR 270,82 / Te veel EUR 8,36.

Bij grotere bedragen en meerdere deelbetalingen loopt dit snel op. Een debiteur kan dit bij de rechter aanvechten.

**Fix-aanbeveling:** Schrijf eerst rode test (S2). Herschrijf calculate_case_interest zodat het per-claim een lijst van (datum, nieuwe_principal) accepteert, of integreer payment-history in de compound-loop.

---

### 2. [CRITICAL] BTW-op-BIK niet configureerbaar; default include_btw=False overal

**Locatie:**
- backend/app/collections/wik.py:47-51 (default include_btw=False)
- backend/app/collections/service.py:240, 867
- backend/app/collections/compliance.py:81
- backend/app/documents/service.py:238, docx_service.py:366, 495
- backend/app/invoices/service.py:1103

**Wat de wet zegt:** Als schuldeiser NIET BTW-plichtig is (consument, VvE, kerk, stichting zonder BTW-ondernemerschap), mag 21% BTW over BIK worden gevorderd. Is schuldeiser wel BTW-plichtig (BV, advocaat), dan mag dat niet.

**Wat de code doet:** calculate_bik ondersteunt de flag, maar geen enkele interne aanroep zet include_btw=True. Alleen de losse API endpoint honoreert een query-parameter. Geen veld op Contact dat client-BTW-status registreert.

**Gevolg:** Voor Kesting Legal (BV, BTW-plichtig) toevallig correct. Maar bij incasso voor niet-BTW-plichtige client wordt 21% BTW over BIK niet meegevorderd - direct geldverlies.

**Scenario S6 bewijs:** Principal EUR 3.500 voor niet-BTW-plichtige client. WIK = 375 + 100 = EUR 475. Met BTW zou EUR 574,75 moeten zijn. Verschil: EUR 99,75 per dossier.

**Fix-aanbeveling:**
1. Veld is_btw_plichtig: bool op Contact (client), default True.
2. Alle calculate_bik(total_principal) vervangen door calculate_bik(total_principal, include_btw=not case.client.is_btw_plichtig).
3. UI-toggle in dossier- en clientinstellingen.

---

### 3. [CRITICAL] Handelsrente (6:119a) wordt niet auto-geselecteerd bij B2B

**Locatie:** backend/app/cases/service.py:399-405

**Wat de wet zegt:** Art. 6:119a BW - bij B2B handelsovereenkomst geldt dwingend de handelsrente. Partijen kunnen niet kiezen.

**Wat de code doet:** debtor_type b2b wordt nergens meegenomen in de interest_type keuze. Default zonder client-default = statutory (consument).

**Scenario S4 impact:** B2B EUR 12.000, verzuim 2024-03-01, 25 maanden open. Handelsrente EUR 3.084,76. Wettelijke rente ~EUR 1.950. Verschil: EUR 1.134 per dossier dat ten onrechte niet wordt gevorderd.

**Fix-aanbeveling:** Voeg elif debtor_type == b2b: interest_type = commercial toe. Plus UI-waarschuwing.

---


### 4. [HIGH] bik_override_percentage genegeerd in payment distribution + financial summary

**Locatie:**
- backend/app/collections/service.py:237-238 (alleen fixed bik_override)
- backend/app/collections/service.py:867-875 (idem)

**Wat er gebeurt:** DF117-04 voegde bik_override_percentage toe. invoices/service.py:1091 respecteert dit, collections/service.py niet. Bedragen op dossieroverzicht en factuur lopen uit elkaar.

**Fix-aanbeveling:** Percentage-tak toevoegen in beide plekken. Veld als parameter doorgeven vanuit de router.

---

### 5. [HIGH] Nakosten (EUR 189 / EUR 287) ontbreken volledig

**Locatie:** Geen code. Grep op nakost, betekening, 189, 287 in app/: 0 resultaten.

**Wat de wet zegt:** Bij vonnis worden nakosten toegekend:
- EUR 189 zonder betekening exploot
- EUR 287 met betekening exploot (per 1 februari 2026)

Deze bedragen horen in beslispassages van vonnissen plus executiebrieven.

**Fix-aanbeveling:** Nieuw bestand collections/nakosten.py met constanten plus calculate_nakosten(betekend: bool); checkbox betekend op Case; opname in get_financial_summary.

---

### 6. [HIGH] 14-dagenbrief termijn inconsistent: 14 in workflow, 15 in compliance

**Locatie:**
- backend/app/workflow/service.py:334 (min_wait=14, strict <)
- backend/app/collections/compliance.py:73 (< 15)

**Wat de wet zegt:** Art. 6:96 lid 6 BW - 14 dagen na ontvangst. Rechtspraak rekent effectief >=15 dagen na verzending.

**Wat de code doet:** Compliance correct (>=15). Workflow laat al op dag 14 door. Via status-transitie kan 1 dag te vroeg worden overgesprongen, maar compliance blokkeert bij send - inconsistente UX.

**Fix-aanbeveling:** Harmoniseer op >=15 in beide plekken.

---

### 7. [MEDIUM] Compound anniversary drift bij Feb 29 verzuim

**Locatie:** backend/app/collections/interest.py:184-218 plus _add_years lijn 223-232

**Wat gebeurt:** _add_years(date(2024,2,29), 1) = date(2025,2,28). year_start wordt daarna 2025-02-28 en blijft vastzitten - in schrikkeljaar 2028 keert niet terug naar 29 feb. Code verliest 1 dag per 4-jarige cyclus.

**Impact:** EUR 100.000 over 4 jaar @ 6% = ~EUR 49 drift. Principieel onjuist, niet urgent.

**Fix-aanbeveling:** Gebruik in de loop altijd _add_years(original_default_date, i).

---

### 8. [MEDIUM] Griffierechten-tabel 2026 duplicaten plus verificatie nodig

**Locatie:** backend/app/collections/griffierechten.py:14-22

**Wat er staat:** Meerdere rijen met identieke bedragen binnen kanton (500 en 1500 beide 92/132; 2500, 5000, 12500 alle 244/530). Duplicaten suggereren dat grenzen of tarieven niet kloppen met 2026 Wgbz.

**Fix-aanbeveling:**
1. Verifieer met rechtspraak.nl/griffierechten (2026).
2. Verplaats naar geversioneerde tabel met effective_from.

---

### 9. [MEDIUM] 14-dagenbrief compliance telt vanaf created_at, niet ontvangst

**Locatie:** backend/app/collections/compliance.py:71-77

**Wat de wet zegt:** 14 dagen beginnen de dag NA ontvangst. Bij papier 1-2 dagen postduur.

**Wat de code doet:** days_since = today - created_at.date() (generatie/verzending).

**Fix-aanbeveling:** Veld received_at toevoegen op GeneratedDocument.

---

### 10. [LOW] interest_rates globaal (geen tenant) - minimaal risico

**Locatie:** backend/app/collections/models.py - InterestRate erft Base + TimestampMixin.

**Commentaar:** Bewust zo. Rijksoverheidstarieven universeel. Mitigatie: geen mutatie-endpoint; router heeft geen POST/PUT op rates.

---

## Afwezige verificatie-tests

Unit-tests vangen deze scenarios NIET:

1. Integratie deelbetaling + rente-voortloop (S2).
2. BTW-configuratie per client.
3. B2B auto-select handelsrente.
4. bik_override_percentage in payment flow.
5. Nakosten.
6. Griffierechten 2026 waardes.

---

## Fix-prioriteit

**Deze week (Critical):**
1. Rode test S2 schrijven, calculate_case_interest aanpassen voor principal-segmenten.
2. is_btw_plichtig veld op Contact plus propagatie in alle calculate_bik calls.
3. B2B auto-select commercial in create_case.

**Volgende sprint (High):**
4. bik_override_percentage in payment-distribution + financial summary.
5. nakosten.py module + betekend toggle.
6. 14-dagenbrief termijn op >=15 harmoniseren.

**Later (Medium):**
7. Feb 29 anniversary drift fix.
8. Griffierechten tabel 2026 verifieren + versioneren.
9. received_at veld voor 14-dagenbrief.

---

## Code-references

- Interest engine: backend/app/collections/interest.py:62-232
- calculate_case_interest: backend/app/collections/interest.py:254-360
- WIK staffel: backend/app/collections/wik.py:47-123
- Payment distribution: backend/app/collections/payment_distribution.py:29-82
- create_payment: backend/app/collections/service.py:185-299
- get_financial_summary: backend/app/collections/service.py:821-912
- Case create + interest_type default: backend/app/cases/service.py:378-488
- Griffierechten: backend/app/collections/griffierechten.py
- Compliance: backend/app/collections/compliance.py
- Workflow 14-dagen: backend/app/workflow/service.py:317-340
- Seed rates: scripts/seed_interest_rates.py
