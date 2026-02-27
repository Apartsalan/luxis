# UX Research — E5: Slimme Facturatie-flow

> **Datum:** 20 februari 2026
> **Status:** Research afgerond — klaar voor implementatie
> **Prioriteit:** Hoog (E5 in roadmap)
> **Complexiteit:** Groot

---

## 1. Wat er nu is

### Huidige facturatie-flow (`facturen/nieuw/page.tsx`, 597 regels)

De huidige flow is **volledig handmatig**:

1. Gebruiker klikt "Nieuwe factuur" → leeg formulier
2. Zoekt en selecteert een contactpersoon (verplicht)
3. Optioneel: koppelt een dossier
4. Vult datum, vervaldatum, BTW, referentie, notities in
5. Voegt **handmatig** factuurregels toe (omschrijving, aantal, stukprijs)
6. Optioneel: klikt "Importeer uren" om **één voor één** tijdregistraties toe te voegen
7. Optioneel: klikt "Importeer verschotten" om onkosten toe te voegen
8. Slaat op → factuur in "Concept" status

### Problemen met de huidige flow

| Probleem | Impact |
|----------|--------|
| **Geen overzicht van onbefactureerde uren** | Lisanne weet niet welke uren nog open staan — moet zelf bijhouden |
| **Eén-voor-één import** | Bij 20 tijdregistraties = 20 klikken. Geen batch-selectie |
| **Geen `invoiced` vlag op TimeEntry** | Systeem weet niet welke uren al gefactureerd zijn — toont ALLES |
| **Geen "Factureer dit dossier" shortcut** | Altijd via het lege factuurformulier, nooit vanuit de zaak |
| **Expense heeft wél `invoiced` tracking** | Inconsistentie: onkosten worden correct als gefactureerd gemarkeerd, uren niet |

### Technische staat

#### Frontend

| Bestand | Wat | Status |
|---------|-----|--------|
| `facturen/nieuw/page.tsx` | Factuuraanmaak-formulier | Werkt, maar handmatig |
| `hooks/use-invoices.ts` | CRUD hooks + types | Compleet, 458 regels |
| `hooks/use-time-entries.ts` | Tijdregistratie hooks | Mist `uninvoiced` filter |

**Bestaande "Importeer uren" flow** (regels 89-131 in `facturen/nieuw/page.tsx`):
- Haalt ALLE billable uren op voor geselecteerd dossier (`useTimeEntries({ case_id, billable: true })`)
- Toont ze in een dialog
- Importeert **één entry per klik** als nieuwe factuurregel
- Geen filtering op al-gefactureerde uren
- Geen checkboxes of batch-selectie

#### Backend

| Bestand | Wat | Kritieke gap |
|---------|-----|-------------|
| `time_entries/models.py` | TimeEntry model | **GEEN `invoiced` veld** |
| `time_entries/service.py` | CRUD + aggregaties | Geen uninvoiced filtering |
| `time_entries/router.py` | Endpoints | Geen unbilled endpoint |
| `invoices/service.py` | `create_invoice()` | Markeert expenses als invoiced, **maar NIET time entries** |
| `invoices/models.py` | InvoiceLine | Heeft `time_entry_id` FK — link bestaat al |

**Cruciale vondst:** Het `Expense` model heeft al het juiste patroon:
```python
# Expense model (invoices/models.py, regel 89)
invoiced = Column(Boolean, default=False, nullable=False)
billable = Column(Boolean, default=True, nullable=False)
```

En de `create_invoice` service markeert expenses correct:
```python
# invoices/service.py, regels 216-227
if line_data.expense_id:
    expense = await db.get(Expense, line_data.expense_id)
    if expense:
        expense.invoiced = True
```

**Dit patroon moet exact gekopieerd worden naar TimeEntry.**

---

## 2. Wat Lisanne nodig heeft

### De kernbehoefte

> "Toon me welke uren nog niet gefactureerd zijn, laat me selecteren wat ik wil factureren, en maak de factuur."

### Gewenste workflow (3 stappen)

1. **Selecteer** — Overzicht van onbefactureerde uren, gegroepeerd per dossier of contact
2. **Review** — Bekijk de geselecteerde uren, pas eventueel aan (omschrijving, tarief)
3. **Factureer** — Met één klik een factuur genereren

### Use cases

| Scenario | Frequentie | Wat Lisanne wil |
|----------|-----------|-----------------|
| Maandelijkse facturatie per dossier | Wekelijks/maandelijks | Alle uren van dossier X → factuur |
| Factureer na afronding zaak | Bij afsluiting | Alle openstaande uren → eindfactuur |
| Deelfacturatie | Soms | Selectie van specifieke uren → factuur |
| Quick bill vanuit dossierdetail | Vaak | "Factureer uren" knop op dossierpagina |

---

## 3. Hoe concurrenten dit doen

### Clio — "Quick Bill"

Clio is de industriestandaard voor advocatuur-facturatie:

- **"Quick Bill" knop** op elke zaak — genereert direct een factuur met alle onbefactureerde uren
- Bills trekken automatisch alle **unbilled time entries** per matter
- Gebruiker **reviewt en bewerkt** voor verzending (omschrijving aanpassen, uren verwijderen)
- Non-billable entries worden via checkbox uitgesloten en verschijnen niet op facturen
- **Batch-benadering**: alle uren in één keer, niet één voor één
- Invoice preview toont subtotaal, BTW, totaal
- Directe koppeling vanuit de zaak — niet via een los factuurformulier

**Wat Clio goed doet:**
- Nul-stappen facturatie ("Quick Bill" = 1 klik)
- Review-stap voorkomt fouten
- Duidelijk onderscheid billable vs. non-billable

### Harvest — Uninvoiced Hours

Harvest is de standaard voor time tracking + invoicing:

- **Filter voor uninvoiced uren** in gedetailleerde tijdrapporten
- Facturatie in **2 klikken** vanuit getrackte tijd
- Uren worden **automatisch als gefactureerd gemarkeerd** na het aanmaken van de factuur
- Beheerders kunnen uren handmatig markeren als gefactureerd/ongefactureerd
- Duidelijke visuele scheiding: gefactureerd (grijs) vs. ongefactureerd (actief)

**Wat Harvest goed doet:**
- Automatische tracking van invoiced-status
- Visuele feedback (gefactureerd = grijs/gedempt)
- Undo-mogelijkheid (handmatig un-invoicen)

### Synthese — Wat wij overnemen

| Feature | Bron | Toepassing in Luxis |
|---------|------|---------------------|
| Quick Bill vanuit dossier | Clio | "Factureer uren" knop op dossierdetail |
| Batch-selectie met checkboxes | Clio + Harvest | Selecteer welke uren je wilt factureren |
| Auto-markering als gefactureerd | Harvest | `invoiced = True` op TimeEntry bij factuurcreatie |
| Review-stap voor verzending | Clio | Preview met alle geselecteerde uren + totalen |
| Uninvoiced filter | Harvest | Backend endpoint + frontend filter |

---

## 4. Backend plan

### Stap 1: `invoiced` veld toevoegen aan TimeEntry

**Bestand:** `backend/app/time_entries/models.py`

```python
# Toevoegen aan TimeEntry model:
invoiced = Column(Boolean, default=False, nullable=False, index=True)
```

**Alembic migratie:**
```python
# Nieuwe kolom + default voor bestaande records
op.add_column('time_entries', sa.Column('invoiced', sa.Boolean(), nullable=False, server_default='false'))
op.create_index('ix_time_entries_invoiced', 'time_entries', ['invoiced'])
```

### Stap 2: Uninvoiced time entries endpoint

**Bestand:** `backend/app/time_entries/router.py`

Nieuw endpoint:
```
GET /api/time-entries/unbilled?case_id=&contact_id=
```

Returns: alle tijdregistraties waar `billable = True AND invoiced = False`

Optioneel grouperen per dossier (voor overzichtspagina).

**Bestand:** `backend/app/time_entries/service.py`

Nieuwe functie:
```python
async def list_unbilled_time_entries(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    case_id: uuid.UUID | None = None,
    contact_id: uuid.UUID | None = None,
) -> list[TimeEntry]:
    """Get all billable, uninvoiced time entries."""
    stmt = (
        select(TimeEntry)
        .where(
            TimeEntry.tenant_id == tenant_id,
            TimeEntry.billable == True,
            TimeEntry.invoiced == False,
            TimeEntry.is_active == True,
        )
        .order_by(TimeEntry.date.desc())
    )
    if case_id:
        stmt = stmt.where(TimeEntry.case_id == case_id)
    # contact_id filter via join op Case.contact_id
    ...
```

### Stap 3: `create_invoice` aanpassen — time entries markeren

**Bestand:** `backend/app/invoices/service.py`

In de `create_invoice` functie, na het aanmaken van regels, time entries markeren als gefactureerd (identiek patroon als expenses):

```python
# Na bestaande expense-markering (regels 216-227), toevoegen:
if line_data.time_entry_id:
    time_entry = await db.get(TimeEntry, line_data.time_entry_id)
    if time_entry and time_entry.tenant_id == tenant_id:
        time_entry.invoiced = True
```

### Stap 4: `remove_line` aanpassen — time entries un-markeren

**Bestand:** `backend/app/invoices/service.py`

In de `remove_line` functie, time entry un-markeren (identiek patroon als expenses):

```python
# Na bestaande expense-un-markering, toevoegen:
if line.time_entry_id:
    time_entry = await db.get(TimeEntry, line.time_entry_id)
    if time_entry:
        time_entry.invoiced = False
```

### Stap 5: Schemas aanpassen

**Bestand:** `backend/app/time_entries/schemas.py`

- `TimeEntryResponse`: voeg `invoiced: bool` toe
- Optioneel: `UnbilledTimeEntrySummary` schema voor gegroepeerd overzicht

### Stap 6: Bestaande data migreren

Alle time entries die al op een factuurregel staan moeten `invoiced = True` krijgen:

```python
# In de Alembic migratie (data migration):
op.execute("""
    UPDATE time_entries
    SET invoiced = true
    WHERE id IN (
        SELECT DISTINCT time_entry_id
        FROM invoice_lines
        WHERE time_entry_id IS NOT NULL
    )
""")
```

---

## 5. Frontend plan

### Flow 1: "Factureer uren" vanuit dossierdetail (Quick Bill)

**Locatie:** Dossierdetail pagina → Quick Actions bar (al aanwezig: B2)

Nieuwe knop: **"Factureer uren"** (naast bestaande "Factuur" knop)

**Stap 1 — Selectie:**
- Dialog/sheet opent met alle onbefactureerde uren voor dit dossier
- Tabel met kolommen: ☑ | Datum | Omschrijving | Duur | Tarief | Bedrag
- "Alles selecteren" checkbox bovenaan
- Subtotaal onderaan dat meebeweegt met selectie
- Lege state: "Geen onbefactureerde uren voor dit dossier"

**Stap 2 — Preview:**
- Na klik "Factureer geselecteerde uren" → preview
- Toont: contactpersoon (van dossier), factuurdatum (vandaag), vervaldatum (+30d)
- Tabel met geselecteerde uren als factuurregels
- Subtotaal, BTW (21%), Totaal
- Mogelijkheid om omschrijving per regel aan te passen

**Stap 3 — Bevestiging:**
- "Factuur aanmaken" knop → POST /api/invoices met alle geselecteerde time_entry_ids
- Succes: redirect naar factuurdetail, toast "Factuur aangemaakt"
- Time entries automatisch gemarkeerd als `invoiced = True`

### Flow 2: Verbeterde "Importeer uren" op factuurformulier

**Locatie:** `facturen/nieuw/page.tsx` — bestaande "Importeer uren" knop

Huidige flow verbeteren:
- Toon alleen **onbefactureerde** uren (filter op `invoiced = false`)
- Voeg **checkboxes** toe voor batch-selectie
- "Alles selecteren" toggle
- "Importeer geselecteerde" knop (i.p.v. één-voor-één)
- Visueel: al-geïmporteerde uren gedempt weergeven

### Flow 3: Overzicht onbefactureerde uren (optioneel, fase 2)

**Locatie:** Eventueel als tab op de facturen-pagina of als aparte subpagina

- Overzicht van ALLE onbefactureerde uren, gegroepeerd per dossier
- Per dossier: aantal uren, totaalbedrag, laatste activiteit
- "Factureer" knop per dossier → Quick Bill flow

### Componenten

| Component | Doel | Nieuw? |
|-----------|------|--------|
| `UnbilledTimeSelector` | Tabel met checkboxes voor urenselectie | Nieuw |
| `InvoicePreview` | Preview van factuur voor bevestiging | Nieuw |
| `QuickBillDialog` | Combined selector + preview in dialog/sheet | Nieuw |

### Hooks

| Hook | Doel | Wijziging |
|------|------|-----------|
| `useTimeEntries` | Bestaande hook | Parameter `invoiced?: boolean` toevoegen |
| `useUnbilledTimeEntries` | Onbefactureerde uren per dossier/contact | Nieuw |
| `useQuickBillInvoice` | Factuur aanmaken vanuit selectie | Nieuw (wrapper rond `useCreateInvoice`) |

---

## 6. Bouwstappen

### Fase 1: Backend — `invoiced` tracking (1-2 uur)

1. Voeg `invoiced: bool` toe aan `TimeEntry` model
2. Maak Alembic migratie (incl. data migration voor bestaande records)
3. Pas `TimeEntryResponse` schema aan
4. Voeg `uninvoiced_only` filter toe aan `list_time_entries` service
5. Maak `GET /api/time-entries/unbilled` endpoint
6. Pas `create_invoice` aan: markeer time entries als invoiced
7. Pas `remove_line` aan: un-markeer time entries
8. Tests schrijven:
   - Test: unbilled endpoint retourneert alleen uninvoiced + billable
   - Test: create_invoice markeert time entries als invoiced
   - Test: remove_line un-markeert time entry
   - Test: data migration correctheid
9. `pytest` — alle tests groen
10. Commit: `feat(invoices): add invoiced tracking to time entries`

### Fase 2: Frontend — Verbeterde import op factuurformulier (1 uur)

1. Pas `use-time-entries.ts` aan: voeg `invoiced` filter parameter toe
2. Verander "Importeer uren" dialog in `facturen/nieuw/page.tsx`:
   - Filter op `invoiced = false`
   - Voeg checkboxes toe
   - "Alles selecteren" toggle
   - "Importeer geselecteerde" batch-knop
3. `npm run build` — check
4. Commit: `feat(invoices): batch import unbilled time entries`

### Fase 3: Frontend — Quick Bill vanuit dossierdetail (1-2 uur)

1. Maak `UnbilledTimeSelector` component (tabel + checkboxes)
2. Maak `InvoicePreview` component (preview + totalen)
3. Maak `QuickBillDialog` component (combineert selector + preview)
4. Voeg "Factureer uren" knop toe aan dossierdetail Quick Actions
5. Implementeer de 3-stappen flow (selectie → preview → bevestiging)
6. `npm run build` — check
7. Commit: `feat(invoices): quick bill flow from case detail`

### Fase 4: Polish & edge cases (30 min)

1. Empty states (geen onbefactureerde uren)
2. Loading states bij ophalen uren
3. Error handling bij mislukte factuurcreatie
4. Toast notificaties bij succes
5. Invalidate queries na factuurcreatie (uren lijst verversen)
6. Test de complete flow end-to-end
7. Commit: `fix(invoices): polish smart invoicing flow`

---

## 7. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| Bestaande time entries niet correct gemigreerd | Hoog | Data migration in Alembic: UPDATE time_entries SET invoiced = true WHERE id IN (SELECT time_entry_id FROM invoice_lines) |
| Dubbel factureren van dezelfde uren | Hoog | `invoiced` vlag + frontend filter. Backend validatie: weiger time_entry_id als al invoiced |
| Performance bij veel onbefactureerde uren | Laag | Index op `invoiced` kolom. Paginatie op endpoint |
| Invoice line verwijderen maar time entry niet un-markeren | Midden | Bestaand patroon volgen (expense un-markering werkt al correct) |
| Factuur annuleren maar uren blijven "invoiced" | Midden | Bij `cancel_invoice`: alle gekoppelde time entries + expenses un-markeren |
| BTW-berekening bij batch import | Laag | Bestaande BTW-logica hergebruiken (werkt al correct) |
| `delete_invoice` markeert uren niet terug | Midden | Toevoegen aan `delete_invoice` service: un-markeer alle gekoppelde time entries |

---

## 8. Database-impact

### Nieuwe kolom

```sql
ALTER TABLE time_entries ADD COLUMN invoiced BOOLEAN NOT NULL DEFAULT false;
CREATE INDEX ix_time_entries_invoiced ON time_entries (invoiced);
```

### Data migration

```sql
UPDATE time_entries
SET invoiced = true
WHERE id IN (
    SELECT DISTINCT time_entry_id
    FROM invoice_lines
    WHERE time_entry_id IS NOT NULL
);
```

### Geschatte impact

- Kolom toevoegen: instant (PostgreSQL ADD COLUMN met DEFAULT is O(1))
- Index aanmaken: snel (tabel is klein, <10.000 rijen verwacht)
- Data migration: snel (JOIN op bestaande FK)

---

## 9. Samenvatting

**Kernprobleem:** De huidige facturatie-flow is volledig handmatig. Lisanne moet zelf bijhouden welke uren al gefactureerd zijn en ze één voor één importeren. Er is geen systeem-tracking van de facturatiestatus van tijdregistraties.

**Oplossing:**
1. **Backend:** `invoiced` boolean op TimeEntry (kopie van het Expense-patroon), unbilled endpoint, auto-markering bij factuurcreatie
2. **Frontend:** Batch-selectie met checkboxes, "Quick Bill" vanuit dossierdetail, preview voor bevestiging

**Benchmark:** Clio's "Quick Bill" (1-klik facturatie per zaak) + Harvest's automatische invoiced-tracking

**Omvang:** Groot. Backend: nieuw veld + migratie + 3 service-wijzigingen + nieuw endpoint. Frontend: 3 nieuwe componenten + 2 bestaande pagina's aanpassen.

**Geschatte bouwtijd:** 4-6 uur (backend 1-2, frontend 2-3, polish 1)

---

*Dit document is het onderzoek en plan voor E5. De implementatie volgt de standaard werkwijze: plan → bouw → check → commit.*
