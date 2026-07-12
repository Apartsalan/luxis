# S201 — Overdracht naar Sol (Codex/ultra) — 12 juli 2026

**Waarom deze hand-off:** Fable begon S201 (read-only onderzoek facturatie-migratie),
mat de veldsemantiek volledig door, maar raakte door de tokens heen vóór de prod-
match-query, het uren-advies, het Donker/Dinc-spoor en de twee output-documenten.
Alles hieronder is **gemeten in deze sessie** (script/telling) tenzij expliciet
"NIET geverifieerd". Sol kan hierop verder zonder opnieuw te meten.

**Opdracht + constraints:** zie `docs/sessions/PROMPT-S201-onderzoek-facturatie.md`.
100% read-only, geen prod-mutatie, geen import-uitvoering, geen mail. Output-doelen:
`docs/research/S201-facturatie-recept.md` + `docs/research/S201-volledigheidsmatrix.md`.
**Commit NIETS tussendoor** — S200 draait parallel; pas op het allerlaatst `git pull` + `/sessie-einde`.

---

## 0. Werkomgeving (opnieuw opzetten — scratchpad is weg per sessie)

- Bron-zip: `C:\Users\arsal\Documents\luxis\Xml_02-07-2026_2400.zip` (137 XML-bestanden).
- Uitpakken naar een tijdelijke map, bv.:
  ```bash
  python -c "import zipfile; zipfile.ZipFile('Xml_02-07-2026_2400.zip').extractall(r'<EXPORT_DIR>')"
  ```
  **Let op:** gebruik een ABSOLUUT Windows-pad als `<EXPORT_DIR>`. Fable's eerste poging
  gebruikte per ongeluk een letterlijk `$HOME` → maakte een map `C:\c\Users\...` aan in de repo.
  Die is intussen opgeruimd, maar controleer `git status` op rare `c/`-paden.
- Parser: `scripts/basenet/parse.py` → `parse_entity(EXPORT_DIR, "OutgoingInvoice")` etc.
  Samenvatting van alle bestanden: `python -m scripts.basenet.parse <EXPORT_DIR>`.
- Windows-console kan Unicode (∩, €) niet printen → zet `PYTHONIOENCODING=utf-8` vóór het script.
- Prod read-only query: sla `.sql` op, `scp` naar VPS `/tmp/`, dan
  `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose exec -T db psql -U luxis -d luxis < /tmp/x.sql"`.
  (Fable's laatste query werd door de user afgebroken vóór uitvoering — nog te doen, zie §2.)

---

## 1. GEMETEN veldsemantiek — facturen (deel 1.1 KLAAR)

Bestanden: `admin.outgoinginvoice` (**567** koppen), `admin.outgoinginvoiceline` (**773** regels).

### Factuurkop (OutgoingInvoice)
| Veld | Betekenis (gemeten) | Bewijs |
|---|---|---|
| `invnr` | Factuurnummer, **uniek** 100000–100566 (567/567) | telling |
| `invdatinv` | Factuurdatum. Jaren: 2024=9, 2025=307, 2026=251 | telling |
| `invtobepaid` | **Bruto factuurtotaal incl. BTW.** = som van regel-`inlpricetot` (542 exact gelijk, 0 afwijkend, 25 koppen zonder regels) | steekproef = hele populatie |
| `invopenamount` | Openstaand bedrag (bruto). | zie afleiding onder |
| `invpaid` | **ALTIJD 0.00** in alle 567 records — NIET bruikbaar als "betaald bedrag". Betaald = `invtobepaid − invopenamount`. | `paid>0: 0` in elke status |
| `invpaidstatus` | **1 = betaald** (388 recs, allemaal open==0) · **0 = openstaand** (176, allemaal open≠0) · **9 = 3 recs** (open==0, afwijkend — waarsch. afgeboekt/kwijtgescholden). | kruistabel |
| `invstatus` | **1 = concept** (17, geen senddate) · **5 = verzonden/recent** (78, állemaal senddate, vnl. 2026-04..06, bkyear 2026) · **6 = geboekt/definitief** (457, állemaal senddate, 2024–2026) · **9 = correctie/bijzonder** (14, meest geen senddate, veel €0) · **2 = 1 record** (€0, randgeval). | kruistabellen |
| `invdebcred` | **1 = debetfactuur** (537) · **2 = creditnota** (30). | telling |
| `invcredinv` | Staat op de **originele** factuur en wijst naar het **invnr van de bijbehorende creditnota** (27 gevuld; 27/27 matchen een invnr, 0 op systemid). Vb: factuur 100001 (+1873,08) → credinv 100007 (−1873,08). | telling |
| `invsenddate` | Verzenddatum (leeg bij concepten). | telling |
| `invduedate` | Vervaldatum (537 gevuld). | telling |
| `invrcode` | Debiteur (relatiecode). **58 unieke debiteuren**, állemaal met naam in de export (Company óf Person). | telling |
| `invbetwijze` | 0 (540) / 6 (27). Niet ontcijferd — vermoedelijk betaalwijze/incasso. NIET geverifieerd. | telling |

**Bedragrelatie:** `invtobepaid − invpaid == invopenamount` klopt maar bij 198/567 —
omdat `invpaid` altijd 0 is. De juiste relatie is: **betaald = invtobepaid − invopenamount**,
en `invpaidstatus` is de betrouwbare betaald-vlag.

### ⚠️ Kritieke nuance — negatieve "facturen" die géén creditnota's zijn
- **109 records met `invtobepaid < 0`.** Daarvan:
  - **30 zijn echte creditnota's** (`invdebcred=2`; 25 daarvan tbp<0). Netjes gekoppeld via `invcredinv`.
  - **84 hebben `invdebcred=1` (debet) én tbp<0** — vnl. 2026 (81 stuks), som **−€94.444,83**.
    Omschrijvingen: *"Voor u ontvangen gelden"*, *"Verrekening voorschot"*, *"Voor u ontvangen gelden (januari 2026)"*.
    → Dit zijn **derdengelden-afrekeningen / verrekenstaten**, GEEN verkoopfacturen.
    **Advies voor het recept:** deze 84 NIET als negatieve `invoices` importeren — dat vervuilt de
    omzet. Overweeg: apart afhandelen (matcht wsl. de derdengelden-module) of bewust overslaan.
    Dit moet een expliciet beslispunt worden.

### Factuurregel (OutgoingInvoiceLine)
| Veld | Betekenis (gemeten) |
|---|---|
| `inlinv` | Koppeling naar kop-`invnr` (742/773 match). **31 lege = losse conceptregels** (állemaal `inlstatus=1`, nog niet op een factuur). |
| `inlpcode` | Dossier/projectcode `D######`. Matcht **100% (283/283)** met `rela.project.pcode`; 146/283 ook naar een incassodossier. Project → relatie via `prcode`. |
| `inlprice` | Stukprijs **excl. BTW**. |
| `inlaantal` | Aantal. |
| `inlvatcode` | **`1a` = 21%** (528 regels) · **`0` = NVT/0%** (245). Enige twee codes in gebruik. |
| `inlpricetot` | Regeltotaal. **Formule 773/773 exact:** `ROUND_HALF_UP(inlaantal × inlprice × (1.21 als vatcode 1a, anders 1))`. Dus `inlpricetot` is **incl. BTW** voor 1a-regels. |
| `inldescinv` | Regelomschrijving. |

**BTW-tabel** (`admin.vatpercentage`): alleen `1a`=21% en `0`=0% relevant voor deze regels.
Er bestaan ook 9%/EU-codes maar die komen niet voor op Lisannes facturen.

---

## 2. NOG TE DOEN — deel 1.2 mapping + prod match-query

Luxis-schema is al gelezen (`backend/app/invoices/models.py`):
- `Invoice`: invoice_number (uniek, format `F{jaar}-{seq:05d}` / `CN...` voor credit),
  invoice_type (`invoice`/`credit_note`/`voorschotnota`), status (concept/approved/sent/
  partially_paid/paid/overdue/cancelled), linked_invoice_id (voor creditnota),
  contact_id (verplicht), case_id (optioneel), invoice_date, due_date, paid_date,
  subtotal, btw_percentage, btw_amount, total, reference, notes.
- `InvoiceLine`: line_number, description, quantity, unit_price, line_total,
  btw_percentage (per regel!), product_id/time_entry_id/expense_id (optioneel), gl_account_code.
- `InvoicePayment`: amount, payment_date, payment_method (bank/ideal/cash/verrekening),
  reference, created_by. → **Betaald-info bestaat alleen als saldo in BaseNet** (invopenamount),
  niet als losse betaalregels. Dus per betaalde factuur hooguit 1 synthetische InvoicePayment
  (amount = invtobepaid − invopenamount, method = onbekend) óf gewoon status=paid + paid_date zetten.

**Voorgestelde mapping (Fable's voorstel, Sol toetst):**
- invtobepaid → `total`; leid `subtotal`/`btw_amount` af uit de regels (som excl. BTW / som BTW).
- `btw_percentage` op kop = 21 als er 1a-regels zijn, anders 0; per regel exact uit `inlvatcode`.
- invnr → bewaar als `reference` of in een apart herkomst-veld; **Luxis-nummerreeks NIET hergebruiken**
  (Luxis begint blanco met F2026-…). Alternatief: invoice_number = `BN-{invnr}` om uniekheid te borgen
  zonder de F-reeks te vervuilen. **Beslispunt.**
- Status-mapping: paidstatus 1 → `paid` (+paid_date onbekend → invduedate of invsenddate?);
  paidstatus 0 + invstatus 5/6 → `sent`/`overdue` (o.b.v. invduedate vs vandaag);
  invstatus 1 → `concept`; debcred 2 → `credit_note` + linked_invoice_id via invcredinv.
- Debiteur: rcode → bestaand contact. **Contacts uit S168 dragen `[BaseNet-import] rcode=X systemid=Y`
  in `notes`** → match op rcode. **Match-rate nog te METEN** (query hieronder, was klaar maar afgebroken).

**Kant-en-klare prod-query** (Fable genereerde 'm al; opnieuw bouwen met dit script):
```python
# genereert /tmp match_query.sql: rcode→contacts.notes match + case_number-formaat + IN-code→cases
# rcodes = distinct invrcode; incodes = via project D-code → Incasso.inccode (IN######)
# 3 tellingen: (1) hoeveel van 58 rcodes matchen een contact, (1b) welke niet, (2/3) case-koppeling
```
Verwacht knelpunt: `case_id` koppelen. Factuurregels dragen `inlpcode = D######` (projectcode),
niet het incassonummer. Project→Incasso is 146/283; de rest zijn niet-incasso projecten
(advies, algemene voorwaarden, faillissement). Luxis `cases` bevat alleen de geïmporteerde
incassodossiers → **veel facturen kunnen niet aan een case, wél aan een contact.** Meet dit.

---

## 3. NOG TE DOEN — deel 1.3 uren (NIET gestart)

Data: `rela.hour` **1.320**, `admin.hour_to_invlines` **2.742**, `rela.hour_activity` 864,
`rela.hourprojectemployeeprice` 607, `rela.hourtype` 70. Luxis heeft `time_entries` + urenscherm (leeg).
Te meten: hoeveel Hour-records hangen via `hour_to_invlines` aan een factuurregel vs los;
som uren gefactureerd vs niet. Advies (alles / alleen-gefactureerd / niets) met de historie-vs-
vervuiling-afweging. Let op: `hour_to_invlines` (2742) > Hour (1320) → uren splitsen over meerdere regels.

---

## 4. NOG TE DOEN — deel 1.4 Donker/Dinc-spoor (NIET gestart)

Context S195: 12 onverklaarde bankcredits ±€21,7k, besluit "vervallen".
**Belangrijke meting van Fable:** het "openstaand €21.670,52" is een **NETTO** getal:
som `invopenamount` per status = 5:+47.307,30 · 6:−37.149,85 · 1:+5.264,48 · 9:+6.248,59 ≈ **21.670,52**.
Dus het mengt positieve vorderingen mét de negatieve "ontvangen gelden"-staten. De numerieke
gelijkenis met de 12 credits is dáárdoor waarschijnlijk **toeval** — toets het alsnog hard:
match de 12 bankbedragen/-data op individuele `invtobepaid`/`invopenamount`/`invnr`, niet op het totaal.
Donker Groep (100316) en Donkers (100737) zijn relaties **zonder facturen** (vooronderzoek) → hypothese wankel.

---

## 5. NOG TE DOEN — deel 2 volledigheidsmatrix (records al geteld)

Volledige entiteitstelling (uit `python -m scripts.basenet.parse`, 65.761 records totaal):
grote/relevante posten voor de matrix:

| Entiteit | Records | Geïmporteerd (S168/1b)? | Eerste inschatting relevantie |
|---|---|---|---|
| rela.company | 815 | ✅ contacts | kern |
| rela.person | 208 | ✅ contacts | kern |
| rela.contact | 145 | deels (fase 1b) | contactpersonen |
| advocatuur.incasso | 607 | ✅ cases | kern |
| advocatuur.incassoline | 1.563 | ✅ claims | kern |
| advocatuur.dossier | 187 | ? | check overlap met incasso |
| advocatuur.incassobetaling | 56 | ? betalingen | check vs S194-bankimport |
| advocatuur.incassobetalingsregeling | 323 | ? | betalingsregelingen — mogelijk relevant |
| **admin.outgoinginvoice** | **567** | ❌ | **deze sessie — importeren** |
| **admin.outgoinginvoiceline** | **773** | ❌ | idem |
| admin.payment | 237 | ? | factuurbetalingen? check |
| admin.molliepayment | 237 | ❌ | iDEAL-betalingen — relevant? |
| **rela.hour** | **1.320** | ❌ | uren — deel 1.3 |
| admin.hour_to_invlines | 2.742 | ❌ | uren↔factuur-koppeling |
| **rela.letter** | **17.928** | ❌ | correspondentie — vgl. 6.393 mails; grootste open vraag |
| **admin.journal** | **2.954** | ❌ | boekhouding — raakt rapportages/Exact? |
| admin.memorialline | 777 | ❌ | boekhoudmemoriaal |
| admin.dcinfo | 1.027 | ❌ | debiteuren/open posten |
| **rela.task** | **1.613** | ❌ | taken — lopend werk? → Luxis-taken? |
| rela.task_activity | 1.513 | ❌ | taakhistorie |
| rela.taskhistory | 1.364 | ❌ | idem |
| **rela.project** | **794** | ❌ | projecten (uren + facturen hangen hieraan) |
| rela.workflowevent | 1.436 | ❌ | workflow-historie — waarsch. niet relevant |
| rela.label_link | 1.375 | ❌ | labels |
| rela.email_address | 940 | deels | e-mailadressen relaties |
| rela.relationtag | 729 | ❌ | tags |
| crm.batch_job_record | 4.073 | ❌ | systeem-jobs — niet relevant |
| email.mailsubjectparams | 9.268 | n.v.t. | mail-metadata, systeem |

Per entiteit met records moet de matrix: **geïmporteerd (ja/nee/deels) → relevant (ja/nee + 1 zin) → actie**.
De volledige lijst van 137 bestanden staat in de parser-output; draai die opnieuw voor de complete tabel.

---

## 6. Beslislijst-skelet voor Arsalan (deel 1.5 — invullen na meten)

Per groep importeren ja/nee + aantallen/euro's:
- **Betaalde facturen** (paidstatus=1, 388 recs) — historie/omzet.
- **Openstaande facturen** (paidstatus=0, 176 recs) — actief debiteurenbeheer.
- **Creditnota's** (debcred=2, 30 recs) — koppelen aan origineel.
- **Negatieve "ontvangen gelden"-staten** (debcred=1 & tbp<0, 84 recs, −€94.444,83) — **apart besluit**, waarsch. NIET als factuur.
- **Concepten** (invstatus=1, 17 recs) + **31 losse conceptregels** — meenemen of overslaan?
- **Uren** (1.320) — alles / alleen-gefactureerd / niets.

Som "te betalen" ≈ €235.899,91 en netto-openstaand ≈ €21.670,52 (vooronderzoek; door Fable's
statustellingen bevestigd op het openstaand-getal).

---

## Statusoverzicht taken
- [x] Setup + prod-toegang (invoices=0, contacts=1169 bevestigd)
- [x] 1.1 veldsemantiek facturen — **volledig gemeten** (§1)
- [~] 1.2 mapping + prod match-query — schema gelezen, query klaar, **uitvoering afgebroken** (§2)
- [ ] 1.3 uren-advies (§3)
- [ ] 1.4 Donker/Dinc (§4)
- [ ] 1.5 recept schrijven → `docs/research/S201-facturatie-recept.md`
- [ ] 2 volledigheidsmatrix → `docs/research/S201-volledigheidsmatrix.md` (§5)
- [ ] sessie-einde: `git pull origin main` (S200 parallel!), dan `/sessie-einde`
