# Implementatieplan: Smart Document Templates + Incasso Workflow Automation

## Overzicht

Twee features in 7 stappen:
1. **Smart Document Templates** — alle zaakdata beschikbaar als merge fields, DOCX-only
2. **Incasso Workflow Automation** — configureerbare status-engine met fases, taken, deadlines, en automatische acties

---

## Datamodel

### Stap 1: Case model uitbreiden

**Case** — nieuw veld:
```
debtor_type: varchar(10), not null, default 'b2b'
  → enum: 'b2b' | 'b2c'
  → auto-ingevuld bij aanmaken: company → b2b, person → b2c
  → override mogelijk door gebruiker
```

Dit veld stuurt:
- Welk rentetype geldt (handelsrente vs wettelijke rente)
- Of 14-dagenbrief verplicht is
- Of BIK-staffel geldt
- Welke workflow rules van toepassing zijn

---

### Stap 2: Configureerbare status-engine

**WorkflowStatus** — vervangt de hardcoded CASE_STATUSES tuple:
```
id:           uuid (PK)
tenant_id:    uuid (FK → tenants.id)
slug:         varchar(50)     — bijv. 'herinnering', 'aanmaning', '14_dagenbrief'
label:        varchar(100)    — bijv. 'Herinnering', 'Aanmaning', '14-dagenbrief'
phase:        varchar(30)     — enum: 'minnelijk', 'regeling', 'gerechtelijk', 'executie', 'afgerond'
sort_order:   int             — volgorde binnen fase
color:        varchar(20)     — bijv. 'blue', 'amber', 'red' (voor UI badges)
is_terminal:  bool            — true voor 'betaald', 'schikking', 'oninbaar'
is_initial:   bool            — true voor 'nieuw' (startpunt)
is_active:    bool            — soft delete
created_at:   timestamp
updated_at:   timestamp
```

**WorkflowTransition** — vervangt de hardcoded STATUS_TRANSITIONS dict:
```
id:             uuid (PK)
tenant_id:      uuid (FK → tenants.id)
from_status_id: uuid (FK → workflow_statuses.id)
to_status_id:   uuid (FK → workflow_statuses.id)
debtor_type:    varchar(10)   — 'b2b', 'b2c', of 'both'
requires_note:  bool          — moet gebruiker een notitie toevoegen?
is_active:      bool
```

**Default statussen** (seed data bij tenant-aanmaak):

| Fase | Status slug | Label | sort_order |
|------|-------------|-------|------------|
| minnelijk | nieuw | Nieuw | 10 |
| minnelijk | herinnering | Herinnering | 20 |
| minnelijk | aanmaning | Aanmaning | 30 |
| minnelijk | 14_dagenbrief | 14-dagenbrief | 40 |
| minnelijk | sommatie | Sommatie | 50 |
| minnelijk | tweede_sommatie | Tweede sommatie | 60 |
| regeling | betalingsregeling | Betalingsregeling | 70 |
| gerechtelijk | conservatoir_beslag | Conservatoir beslag | 80 |
| gerechtelijk | dagvaarding | Dagvaarding | 90 |
| gerechtelijk | vonnis | Vonnis | 100 |
| executie | executie | Executie | 110 |
| executie | faillissementsaanvraag | Faillissementsaanvraag | 120 |
| afgerond | betaald | Betaald | 130 |
| afgerond | schikking | Schikking | 140 |
| afgerond | oninbaar | Oninbaar | 150 |

**Migratie van bestaande data:**
- Case.status (varchar) blijft als kolom, maar verwijst nu naar WorkflowStatus.slug
- Bestaande cases met oude statussen worden gemapt naar de nieuwe slugs
- De hardcoded STATUS_TRANSITIONS dict in schemas.py wordt vervangen door database lookups

---

### Stap 3: Task/Deadline systeem

**WorkflowTask** — taken die automatisch of handmatig ontstaan:
```
id:               uuid (PK)
tenant_id:        uuid (FK → tenants.id)
case_id:          uuid (FK → cases.id)
assigned_to_id:   uuid (FK → users.id, nullable)

task_type:        varchar(50)
  → 'generate_document'   — genereer een document
  → 'send_letter'         — stuur brief (handmatig: print/mail)
  → 'check_payment'       — controleer of betaling is ontvangen
  → 'escalate_status'     — status automatisch naar volgende stap
  → 'manual_review'       — advocaat moet handmatig beoordelen
  → 'set_deadline'        — zet een deadline (bijv. reactietermijn wederpartij)
  → 'custom'              — vrije taak

title:            varchar(255)  — bijv. "Genereer 14-dagenbrief voor zaak 2026-00012"
description:      text (nullable)
due_date:         date          — wanneer moet dit uitgevoerd zijn
completed_at:     timestamp (nullable)

status:           varchar(20)
  → 'pending'     — nog niet aan de beurt (due_date in toekomst)
  → 'due'         — due_date bereikt, moet uitgevoerd worden
  → 'completed'   — afgerond
  → 'skipped'     — overgeslagen (handmatige override)
  → 'overdue'     — niet op tijd uitgevoerd

auto_execute:     bool          — true = systeem voert uit, false = wachten op gebruiker
action_config:    jsonb         — configuratie per task_type, bijv:
  → generate_document: {"template_type": "14_dagenbrief"}
  → escalate_status:   {"target_status_slug": "sommatie"}
  → check_payment:     {"expected_amount": "5000.00"}

created_by_rule_id: uuid (FK → workflow_rules.id, nullable) — welke regel maakte deze taak
is_active:        bool
created_at:       timestamp
updated_at:       timestamp
```

---

### Stap 4: Workflow Rules (automation)

**WorkflowRule** — configureerbare regels per kantoor:
```
id:               uuid (PK)
tenant_id:        uuid (FK → tenants.id)

name:             varchar(255)  — bijv. "Na aanmaning → wacht 14 dagen → 14-dagenbrief"
description:      text (nullable)

trigger_status_id: uuid (FK → workflow_statuses.id) — bij welke status-transitie
debtor_type:      varchar(10)   — 'b2b', 'b2c', 'both'

days_delay:       int           — wacht X dagen na status-transitie
action_type:      varchar(50)   — zelfde types als WorkflowTask.task_type
action_config:    jsonb         — zelfde structuur als WorkflowTask.action_config

auto_execute:     bool          — taak direct uitvoeren of wachten op gebruiker
assign_to_case_owner: bool      — taak toewijzen aan zaakeigenaar

sort_order:       int           — volgorde als meerdere rules op zelfde trigger
is_active:        bool
created_at:       timestamp
updated_at:       timestamp
```

**Default rules** (seed data bij tenant-aanmaak):

| Trigger status | Delay | Actie | B2B/B2C | Auto |
|----------------|-------|-------|---------|------|
| nieuw | 0 | create task: "Beoordeel nieuwe zaak" | both | nee |
| herinnering | 14 | create task: "Check betaling na herinnering" | both | nee |
| aanmaning | 14 | create task: "Stuur 14-dagenbrief" | b2c | nee |
| aanmaning | 14 | create task: "Stuur sommatie" | b2b | nee |
| 14_dagenbrief | 15 | create task: "Check betaling na 14-dagenbrief" | b2c | nee |
| sommatie | 14 | create task: "Check betaling na sommatie" | both | nee |
| vonnis | 0 | create task: "Plan executie" | both | nee |
| betalingsregeling | 30 | create task: "Controleer termijnbetaling" | both | nee |

> **Let op:** default rules zijn bewust `auto_execute: false`. Het systeem maakt taken aan, maar de advocaat beslist. In een latere fase kan het kantoor regels op auto zetten als ze vertrouwen hebben in het systeem.

**Wettelijke constraints** (hardcoded, NIET configureerbaar):
```python
LEGAL_CONSTRAINTS = {
    "14_dagenbrief_min_wait": 14,      # Art. 6:96 lid 6 BW: min 14 dagen wachttijd
    "14_dagenbrief_required_b2c": True, # 14-dagenbrief is verplicht voor B2C
    "verjaring_years": 5,              # Art. 3:307 BW: 5 jaar verjaring
}
```

De status-engine valideert:
- B2C zaak kan niet naar 'sommatie' zonder eerst '14_dagenbrief' gehad te hebben
- Na '14_dagenbrief' moeten minimaal 14 dagen gewacht worden
- Systeem waarschuwt bij naderen verjaring (5 jaar na verzuimdatum)

---

### Stap 5: Document systeem unificeren

**Bestaand HTML systeem verwijderen:**
- `DocumentTemplate` model → verwijderen (content was HTML/Jinja2)
- `documents/service.py` (HTML renderer) → verwijderen

**DOCX systeem uitbreiden:**

`GeneratedDocument` model aanpassen:
```
+ template_type:    varchar(50)       — welk type template is gebruikt
+ template_snapshot: bytea (nullable)  — kopie van de template DOCX op moment van generatie
- content_html:     (verwijderen)      — was voor HTML systeem
```

**Uitgebreide merge fields** (alle zaakdata):

```python
MERGE_FIELDS = {
    # Zaak
    "zaak.zaaknummer": "2026-00012",
    "zaak.type": "incasso",
    "zaak.status": "Sommatie",
    "zaak.debtor_type": "b2c",
    "zaak.referentie": "Uw kenmerk: REF-123",
    "zaak.datum_geopend": "15 januari 2026",
    "zaak.omschrijving": "...",

    # Client (opdrachtgever)
    "client.naam": "Jansen B.V.",
    "client.adres": "Keizersgracht 123",
    "client.postcode_stad": "1015 CJ Amsterdam",
    "client.email": "info@jansen.nl",
    "client.telefoon": "+31 20 123 4567",
    "client.kvk": "12345678",
    "client.btw": "NL123456789B01",

    # Wederpartij (debiteur)
    "wederpartij.naam": "De Vries",
    "wederpartij.adres": "...",
    "wederpartij.postcode_stad": "...",
    "wederpartij.email": "...",
    "wederpartij.telefoon": "...",
    "wederpartij.kvk": "...",

    # Kantoor (tenant)
    "kantoor.naam": "Kesting Legal",
    "kantoor.adres": "...",
    "kantoor.postcode_stad": "...",
    "kantoor.kvk": "...",
    "kantoor.btw": "...",
    "kantoor.iban": "...",

    # Financieel
    "financieel.totaal_hoofdsom": "EUR 5.000,00",
    "financieel.totaal_rente": "EUR 312,50",
    "financieel.bik_bedrag": "EUR 625,00",
    "financieel.btw_bik": "EUR 131,25",
    "financieel.totaal_bik": "EUR 756,25",
    "financieel.totaal_verschuldigd": "EUR 6.068,75",
    "financieel.totaal_betaald": "EUR 0,00",
    "financieel.totaal_openstaand": "EUR 6.068,75",

    # Datum
    "vandaag": "18 februari 2026",
    "termijn_14_dagen": "4 maart 2026",
    "termijn_30_dagen": "20 maart 2026",

    # Loops (voor tabellen in templates)
    "vorderingen[]": [
        {"beschrijving": "...", "factuurnummer": "...", "hoofdsom": "EUR 5.000,00", "verzuimdatum": "..."},
    ],
    "betalingen[]": [
        {"datum": "...", "bedrag": "EUR 1.000,00", "beschrijving": "..."},
    ],
    "rente_regels[]": [
        {"van": "...", "tot": "...", "tarief": "6,00%", "hoofdsom": "...", "rente": "..."},
    ],
}
```

**Nieuw: Tenant.iban veld** — IBAN van het kantoor (nodig voor 14-dagenbrief):
```
Tenant model uitbreiden:
+ iban: varchar(34), nullable
+ phone: varchar(50), nullable
+ email: varchar(320), nullable
```

---

## Bouwvolgorde

### Stap 1: Database migraties (migration 008)
- Case.debtor_type toevoegen
- Tenant.iban, Tenant.phone, Tenant.email toevoegen
- WorkflowStatus tabel aanmaken
- WorkflowTransition tabel aanmaken
- WorkflowTask tabel aanmaken
- WorkflowRule tabel aanmaken
- Seed data: default statussen, transities, en rules
- DocumentTemplate tabel: content_html nullable maken (deprecation stap 1)
- GeneratedDocument: template_type en template_snapshot toevoegen, content_html nullable maken

### Stap 2: Backend — status-engine refactoren
- Nieuw: `app/workflow/` module met models, schemas, service, router
- WorkflowStatus CRUD (admin only)
- WorkflowTransition CRUD (admin only)
- `cases/service.py` → status-transitie logica refactoren om WorkflowTransition te gebruiken
- Wettelijke constraints validatie (14-dagen regel, B2C verplichtingen)
- Verjaring waarschuwing logica
- Backward compatible: Case.status blijft een string (slug), maar wordt nu gevalideerd tegen WorkflowStatus

### Stap 3: Backend — task/deadline systeem
- WorkflowTask CRUD endpoints
- WorkflowRule CRUD endpoints (admin only)
- Task engine: bij status-transitie → check matching rules → create tasks
- Scheduler setup (APScheduler of Celery Beat):
  - Dagelijkse job: check due tasks, markeer als 'due' of 'overdue'
  - Dagelijkse job: check verjaring (waarschuwing 90 en 30 dagen van tevoren)
  - Auto-execute tasks die dat vlag hebben
- Dashboard integratie: openstaande taken als actielijst

### Stap 4: Backend — document systeem unificeren
- Alle merge fields implementeren (zaak, client, wederpartij, kantoor, financieel, datum, loops)
- Template field picker endpoint: GET /api/documents/merge-fields → lijst van beschikbare velden per zaak
- HTML template systeem deprecaten (DocumentTemplate model behouden maar niet meer gebruiken)
- GeneratedDocument.template_snapshot vullen bij generatie
- Nieuwe template types toevoegen: herinnering, aanmaning, tweede_sommatie, dagvaarding

### Stap 5: Backend — workflow automation engine
- Status-transitie hook: na elke status change → evaluate rules → create tasks
- Payment hook: na elke betaling → check of zaak volledig betaald → auto-status naar 'betaald'
- Derdengelden hook: deposit → check of dit een betaling is die doorgestort moet worden
- Audit trail: elke automatische actie wordt gelogd in CaseActivity

### Stap 6: Frontend — workflow configuratie
- Instellingen pagina → nieuw tabblad "Workflow"
- Status beheer (toevoegen, verwijderen, herordenen, kleur wijzigen)
- Transitie matrix editor (welke status → welke status mag)
- Workflow rules editor (trigger, delay, actie, debtor type filter)
- Template beheer (DOCX upload, merge field preview)

### Stap 7: Frontend — zaakdetail + takenlijst
- Pipeline stepper herwerken: toon fases, klikbaar, huidige status highlighted
- Takenlijst paneel in zaakdetail: openstaande en recente taken
- Task acties: markeer als afgerond, overslaan, handmatig taak toevoegen
- Debtor type selector bij zaak aanmaken (auto-invullen, override mogelijk)
- Verjaring indicator (warning badge als < 90 dagen)
- Dashboard: "Mijn taken" widget met openstaande taken

---

## Wat NIET in scope is (bewust)

- **Email integratie**: automatisch brieven mailen. Komt later.
- **Deurwaarder koppeling**: API naar deurwaarderskantoor. Komt later.
- **OCR/document scanning**: inkomende brieven digitaliseren. Komt later.
- **Meerdere workflows per case_type**: nu één workflow voor incasso. Later eventueel voor insolventie, advies.
- **Rollen en rechten per taak**: nu kan iedereen alles. Later fijnmazig.

---

## Risico's en mitigatie

| Risico | Mitigatie |
|--------|----------|
| Bestaande cases verliezen status na migratie | Migratie script mapt oude statussen 1-op-1 naar nieuwe WorkflowStatus slugs |
| Performance bij veel workflow rules | Rules worden gecached per tenant (invalidate bij wijziging) |
| Scheduler mist een taak | Retry mechanisme + dagelijks catch-up check |
| Template rendering faalt | Foutmelding met specifiek ontbrekend veld, niet generieke error |
| Kantoor verwijdert kritieke status | Soft delete + validatie: status in gebruik kan niet verwijderd worden |
