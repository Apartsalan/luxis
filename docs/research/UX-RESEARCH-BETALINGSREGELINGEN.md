# UX Research — Betalingsregelingen (Payment Plans)

**Datum:** 16 maart 2026
**Status:** Onderzoek afgerond — wacht op goedkeuring voor implementatie
**Doel:** Hoe behandelen toonaangevende legal PM en incasso-software betalingsregelingen, en wat bouwen we voor Luxis?

---

## 1. Huidige situatie in Luxis

### Wat er al is (backend)

Het `PaymentArrangement` model bestaat al in `backend/app/collections/models.py`:

```python
class PaymentArrangement(TenantBase):
    __tablename__ = "payment_arrangements"

    case_id: UUID
    total_amount: Decimal        # totaal afgesproken bedrag
    installment_amount: Decimal  # bedrag per termijn
    frequency: str               # weekly | monthly | quarterly
    start_date: date
    end_date: date | None
    status: str                  # active | completed | defaulted
    notes: str | None
```

Backend-endpoints aanwezig:
- `GET /api/cases/{case_id}/arrangements` — lijst
- `POST /api/cases/{case_id}/arrangements` — aanmaken
- `PATCH /api/cases/{case_id}/arrangements/{id}` — status bijwerken

### Wat er mist

- **Frontend UI:** nul. Geen component, geen hook, niets.
- **Termijngeneratie:** het model slaat `installment_amount` + `frequency` op, maar genereert geen concrete termijnlijst (datum 1, datum 2, ...) met individuele status per termijn.
- **Koppeling met betalingen:** er is geen link tussen een geregistreerde `Payment` en een specifieke termijn van de regeling.
- **Gemiste-termijn-detectie:** geen automatische signalering als een verwachte termijn niet is binnengekomen.
- **Opzegging/intrekking workflow:** geen formele "wanprestatie" flow.

---

## 2. Concurrentie-analyse

### 2.1 Clio (legal PM, Noord-Amerika, marktleider)

**Payment Plans in Clio Payments:**
Clio heeft payment plans geintegreerd in hun betaalmodule (Clio Payments, powered by Stripe). De kern van hun aanpak:

**Velden die ze bijhouden:**
- Totaalbedrag van de regeling
- Termijnbedrag
- Frequentie (wekelijks, tweewekelijks, maandelijks)
- Startdatum
- Automatische of handmatige incasso (auto-charge via opgeslagen kaart vs. handmatige herinnering)
- Gekoppelde factuur of matter

**Termijnstructuur:**
Clio genereert automatisch een termijnschema. Elke termijn heeft:
- Vervaldatum
- Bedrag
- Status: `scheduled`, `paid`, `failed`, `waived`

**Status tracking:**
- `Active` — loopt nog, volgende termijn gepland
- `Completed` — alle termijnen betaald
- `Defaulted` — termijn gemist, automatisch geflagged
- `Cancelled` — handmatig beëindigd

**Gemiste betalingen:**
- Bij automatische incasso: Clio probeert opnieuw (via Stripe retry logic), na X pogingen wordt status `failed`
- Bij handmatige: Clio stuurt herinneringen per e-mail op vervaldatum
- Advocaat krijgt notificatie bij mislukte betaling

**UI/UX:**
- Payment plan aanmaken vanuit de factuur (niet apart)
- Wizard: 3 stappen — bedrag → schema → bevestiging
- Overzicht op matter-level: lijst van alle termijnen met kleurgecodeerde status
- "Mark as paid" knop per termijn voor handmatige registratie
- Progress bar: X/Y termijnen betaald

**Integratie met facturen:**
- Payment plan vervangt directe factuurbetaling
- Factuur blijft open totdat alle termijnen betaald zijn
- Elke betaalde termijn vermindert de openstaande factuursaldo

---

### 2.2 PracticePanther (legal PM, Noord-Amerika)

**Payment Plans:**
PracticePanther heeft een eenvoudigere aanpak dan Clio, maar goed doordacht voor solopraktijken.

**Velden:**
- Totaalbedrag
- Aantal termijnen (ze rekenen zelf het termijnbedrag uit)
- Frequentie
- Startdatum
- Beschrijving/notitie

**Termijnstructuur:**
- Genereert automatisch een lijst van termijndatums
- Elk met status: `pending`, `paid`, `overdue`

**Status tracking:**
- `Active` — regeling loopt
- `Completed` — volledig betaald
- `Paused` — tijdelijk opgeschort (uniek aan PracticePanther)
- `Defaulted` — wanprestatie

**Gemiste betalingen:**
- Automatische statusovergang naar `overdue` als vervaldatum is gepasseerd zonder betaling
- Handmatige actie vereist om te escaleren naar `defaulted`
- Geen automatische retry (geen embedded payments)

**UI/UX:**
- Payment plan aanmaken vanuit contact of matter
- Overzicht per matter: tabel van termijnen
- "Record payment" per termijn
- Eenvoudige notities per regeling
- Geen progress bar — wel kleurcodering op de termijnen (groen/oranje/rood)

**Uniek aan PracticePanther:** "Paused" status — advocaat kan regeling tijdelijk stilzetten bij lopende onderhandeling met debiteur, zonder hem te markeren als wanprestatie.

---

### 2.3 LawPay (legal payment processing, VS)

LawPay is gespecialiseerd in legale betalingen. Ze hebben "Payment Plans" als kernfeature:

**Velden:**
- Plantype: `fixed_amount` (vast bedrag per termijn) of `fixed_installments` (vast aantal termijnen, bedrag berekend)
- Totaalbedrag
- Down payment (aanbetaling)
- Frequentie: wekelijks, tweewekelijks, maandelijks, kwartaal
- Startdatum eerste termijn
- Automatisch incasseren (stored payment method vereist)

**Termijnstructuur:**
Volledig gegenereerd schema. Per termijn:
- Datum
- Bedrag (inclusief eventuele last termijn die afwijkt door afrondingsverschil)
- Status: `scheduled`, `processing`, `paid`, `failed`, `waived`

**Status tracking (plan-level):**
- `Active`
- `Completed`
- `Past due` (separate van "defaulted" — plan loopt maar is achter)
- `Cancelled`

**Gemiste betalingen:**
- Auto-retry na 3 en 5 dagen bij gefaalde incasso
- Na 2 mislukte pogingen: advocaat genotificeerd, status `past due`
- Advocaat kan kiezen: opnieuw proberen, waive (kwijtschelden), of cancel
- Elke mislukte poging wordt gelogd in de audit trail

**UI/UX:**
- Dashboard: "Payment Plans" als aparte sectie
- Per plan: progress indicator (bijv. "3 of 8 payments received")
- Filterable list: alle active, all past due, all completed
- Termijnkalender: kalenderweergave van verwachte termijnen
- Één klik om een termijn als "waived" te markeren

**Uniek aan LawPay:**
- Aanbetaling als afzonderlijk veld (down payment)
- "Waive" actie per termijn — kan termijn kwijtschelden zonder hele regeling te annuleren
- Audit log per termijn (poging 1 gefaald om X reden, poging 2 geslaagd)

---

### 2.4 Smokeball (legal PM, Australie/VS)

Smokeball heeft payment plans als onderdeel van hun billing module:

**Velden:**
- Verband met matter + invoice
- Totaalbedrag
- Termijnen: handmatig of automatisch gegenereerd
- Elke termijn heeft eigen datum + bedrag (volledig vrij)
- Notities

**Termijnstructuur:**
Zowel vast schema (alle termijnen gelijk) als volledig aangepaste termijnen (elke termijn ander bedrag en datum).

**Status tracking:**
- `Active`, `Completed`, `Cancelled`
- Per termijn: `upcoming`, `due`, `overdue`, `paid`

**Gemiste betalingen:**
- Automatische overgang naar `overdue` na vervaldatum
- Smokeball Pro stuurt herinneringen per e-mail aan de cliënt

**Uniek aan Smokeball:**
- Vrije termijnindeling: advocaat kan per termijn een ander bedrag invullen
- Dit is handig als eerste termijn groter is (aanbetaling) of laatste termijn kleiner is door afrondingsverschil

---

### 2.5 Payt (Nederlands debiteurenbeheer SaaS)

Payt is de meest relevante referentie voor Luxis: Nederlands, gericht op debiteurenbeheer (niet advocatuur).

**Betalingsregeling in Payt:**
Payt behandelt betalingsregelingen als een formeel object op dossier/factuur-niveau.

**Velden:**
- Dossiernummer (koppeling aan openstaande vordering)
- Totaalbedrag regeling (kan lager zijn dan oorspronkelijke vordering als er wordt afgeboekt)
- Termijnen: aantal + bedrag per termijn
- Frequentie
- Startdatum
- Einddatum (automatisch berekend)
- Status
- Notities / reden betalingsregeling
- Geaccordeerd door (naam medewerker)

**Termijnstructuur:**
Payt genereert een termijnschema. Per termijn:
- Verwachte datum
- Verwacht bedrag
- Werkelijk ontvangen bedrag (kan gedeeltelijk zijn)
- Betalingsdatum
- Status: `verwacht`, `ontvangen`, `gedeeltelijk`, `gemist`, `kwijtgescholden`

**Status tracking (regeling-level):**
- `Actief` — loopt, volgende termijn verwacht
- `Afgerond` — volledig betaald
- `Geschonden` (wanprestatie) — termijn gemist, incasso hervat
- `Opgezegd` — handmatig beëindigd door medewerker
- `In onderhandeling` — tijdelijk on hold

**Gemiste betalingen / wanprestatie-flow:**
Dit is waar Payt het sterkst is voor incasso-context:

1. Vervaldatum passeert zonder betaling → termijn krijgt status `gemist`
2. Medewerker ontvangt signaal (dashboard alert)
3. Medewerker kiest:
   a. **Herinnering sturen** — termijn nog in onderhandeling
   b. **Wanprestatie constateren** — regeling wordt `geschonden`, incassoprocedure hervat
   c. **Uitstel geven** — termijndatum wordt verschoven
4. Bij wanprestatie: de regeling wordt gesloten, het dossier gaat terug in de incasso-pipeline

**UI/UX (Payt):**
- Betalingsregeling aanmaken via knop in dossieroverzicht
- Wizard: 3 stappen — voorwaarden → schema → bevestiging
- Termijnoverzicht als tabel met kleurcodering
- Dashboard widget: "Betalingsregelingen" met aantallen per status
- Alert bij gemiste termijn
- PDF-export van de betalingsregeling (document voor debiteur)
- Correspondentieknoppeling: herinneringsmail direct versturen vanuit de termijn

**Integratie met vordering:**
- Betalingsregeling "bevriest" de actieve incassoprocedure
- Rente loopt door tenzij expliciet gestopt in de regeling
- Elke ontvangen termijn wordt geboekt als deelbetaling (met art. 6:44 BW-toerekening)

---

### 2.6 Basenet (Nederlands legal PM, huidig systeem Lisanne)

Basenet heeft betalingsregelingen als losse functionaliteit:

**Velden (zo goed als bekend):**
- Koppeling aan dossier
- Termijnen (aantal + bedrag)
- Vervaldatums
- Status per termijn
- Opmerkingen

Basenet heeft geen fancy UI voor dit — het is een tamelijk eenvoudige lijst van termijnen met handmatige statusbeheer. Geen automatische detectie van gemiste betalingen, geen wanprestatie-workflow. Alles handmatig.

Dit is precies de reden waarom Luxis hier beter kan zijn.

---

## 3. Gemeenschappelijke patronen (cross-product)

### 3.1 Twee termijnmodellen

Alle producten ondersteunen een van twee modellen:

**Model A — Vaste termijnen (meest gebruikt):**
- Advocaat vult in: totaalbedrag + termijnbedrag + frequentie
- Systeem genereert automatisch het schema
- Laatste termijn kan afwijken (afrondingsverschil)

**Model B — Vrije termijnen (Smokeball, minder gebruikelijk):**
- Advocaat vult per termijn datum + bedrag handmatig in
- Meer flexibel maar meer werk
- Handig voor: aanbetaling + gelijke termijnen, of onregelmatige termijnen

### 3.2 Status op twee niveaus

**Regeling-niveau:**
`actief` → `afgerond` (automatisch) of `geschonden` (handmatig) of `opgezegd` (handmatig)

**Termijn-niveau:**
`verwacht` → `ontvangen` (handmatig registreren) of `gemist` (automatisch na vervaldatum)
Extra: `gedeeltelijk` (deelbetaling ontvangen), `kwijtgescholden` (handmatig)

### 3.3 Workflow bij wanprestatie

Geen enkel product scheldt automatisch kwijt of escaleert automatisch. De advocaat beslist altijd:
1. Gemiste termijn detecteren (automatisch)
2. Advocaat wordt gesignaleerd (dashboard/notification)
3. Advocaat kiest actie: herinnering / uitstel / wanprestatie constateren
4. Bij wanprestatie: incasso hervat

### 3.4 Koppeling aan betalingen

Alle producten koppelen termijnontvangsten aan de bestaande betalingsregistratie. Een ontvangen termijn is gewoon een betaling, geboekt op het dossier. Dit is compatibel met Luxis' bestaande `Payment` model en art. 6:44 BW-toerekening.

### 3.5 Niet-automatische rente

Bij betalingsregelingen in incasso-context: rente loopt normaal door op de openstaande vordering, tenzij expliciet anders afgesproken. Geen van de producten stopt rente automatisch bij het instellen van een regeling.

---

## 4. Aanbevolen aanpak voor Luxis

### 4.1 Wat we bouwen

Luxis combineert de beste elementen:
- **Clio:** twee termijnmodellen (vast + vrij), progress indicator
- **Payt:** wanprestatie-workflow, gemiste termijn detectie, koppeling aan incasso-pipeline
- **LawPay:** "waive" per termijn, audit trail, aanbetaling als optie
- **PracticePanther:** "paused" status voor tijdelijke opschorting

### 4.2 Datamodel uitbreidingen

Het bestaande `PaymentArrangement` model moet uitgebreid worden met een `PaymentArrangementInstallment` tabel voor concrete termijnen:

```python
class PaymentArrangementInstallment(TenantBase):
    __tablename__ = "payment_arrangement_installments"

    arrangement_id: UUID  # FK naar payment_arrangements
    case_id: UUID         # denormalized voor snelheid
    installment_number: int  # 1, 2, 3, ...
    due_date: date
    amount: Decimal       # NUMERIC(15,2)
    paid_amount: Decimal  # 0 tot bedrag (deelbetaling mogelijk)
    paid_date: date | None
    payment_id: UUID | None  # FK naar payments (bij registratie)
    status: str           # verwacht | ontvangen | gedeeltelijk | gemist | kwijtgescholden
    notes: str | None
```

En het bestaande `PaymentArrangement` model moet uitgebreid worden:

```python
# Toevoegen aan PaymentArrangement:
arrangement_type: str    # "fixed" | "custom" — vast schema of vrije termijnen
down_payment: Decimal    # optionele aanbetaling (standaard 0)
interest_suspended: bool # rente opgeschort tijdens regeling (standaard False)
created_by_user_id: UUID # wie heeft de regeling gemaakt
```

De status-enum uitbreiden:
```
active | completed | defaulted | paused | cancelled
```

### 4.3 Business logic

**Bij aanmaken van regeling (type=fixed):**
1. Bereken aantal termijnen: `ceil(total_amount / installment_amount)`
2. Genereer termijndatums op basis van `start_date` + `frequency`
3. Pas laatste termijn aan voor afrondingsverschil
4. Sla alle termijnen op als `status=verwacht`

**Dagelijkse job (Celery beat):**
1. Check alle actieve regelingen
2. Termijnen waarvan `due_date < today` en `status=verwacht` → `status=gemist`
3. Maak notificatie aan voor advocaat

**Bij registreren van termijnbetaling:**
1. Termijn-status → `ontvangen` (of `gedeeltelijk` als bedrag lager)
2. Maak automatisch een `Payment` record aan (linked aan de termijn)
3. Art. 6:44 BW-toerekening loopt via bestaande `create_payment()` service
4. Check of alle termijnen `ontvangen` zijn → regeling naar `completed`

**Bij wanprestatie constateren:**
1. Regeling-status → `defaulted`
2. Alle `verwacht`-termijnen worden `kwijtgescholden` of `gemist` (advocaat kiest)
3. Incasso-pipeline hervat (case kan terug naar vorige stap)

### 4.4 UI/UX plan

**Locatie:** Tab "Financieel" op het dossierscherm (incasso-module)

```
┌─────────────────────────────────────────────────────────┐
│  Financieel                                             │
│  [Vorderingen]  [Betalingen]  [Betalingsregeling]  [BIK]│
├─────────────────────────────────────────────────────────┤
```

**Tab "Betalingsregeling" — leeg state:**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Geen betalingsregeling                               │
│   Stel een regeling in als de debiteur in termijnen    │
│   wil betalen.                                         │
│                                                         │
│              [+ Betalingsregeling instellen]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Tab "Betalingsregeling" — actieve regeling:**
```
┌─────────────────────────────────────────────────────────┐
│  Betalingsregeling                          [Acties ▼]  │
│                                                         │
│  ████████████░░░░░░░░  3 van 6 termijnen betaald        │
│  € 1.800 ontvangen van € 3.600 totaal                  │
│                                                         │
│  Status: Actief    Frequentie: Maandelijks              │
│  Start: 1 jan 2026   Einde: 1 jun 2026                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Termijn  Vervaldatum   Bedrag    Status     Actie      │
│  1        1 jan 2026    € 600    ✓ Ontvangen            │
│  2        1 feb 2026    € 600    ✓ Ontvangen            │
│  3        1 mrt 2026    € 600    ✓ Ontvangen            │
│  4        1 apr 2026    € 600    ⏰ Verwacht  [Registreer]│
│  5        1 mei 2026    € 600    ⏰ Verwacht            │
│  6        1 jun 2026    € 600    ⏰ Verwacht            │
└─────────────────────────────────────────────────────────┘
```

**Wizard — aanmaken (3 stappen):**

Stap 1 — Bedrag en schema:
```
Totaalbedrag:       [€ 3.600,00]
Termijnbedrag:      [€   600,00]   (berekend: 6 termijnen)
Frequentie:         [Maandelijks ▼]
Eerste termijn:     [1 april 2026]
Aanbetaling:        [€ 0,00]  (optioneel)
```

Stap 2 — Preview termijnschema:
```
Gegenereerd schema (6 termijnen):
  #1  1 apr 2026   € 600,00
  #2  1 mei 2026   € 600,00
  ...
  #6  1 sep 2026   € 600,00
  ─────────────────────────
  Totaal: € 3.600,00
```

Stap 3 — Bevestiging + notities

**Acties-menu (dropdown op actieve regeling):**
- Termijn registreren → opent dialog
- Regeling pauzeren
- Wanprestatie constateren → bevestigingsdialog
- Regeling annuleren → bevestigingsdialog
- Afdrukken (PDF-overzicht)

**Gemiste termijn — alert in dashboard:**
```
⚠️  Betalingsregeling — Dossier KL-2026-003
    Termijn 2 (1 feb 2026, € 600) is niet ontvangen.
    [Herinnering sturen]  [Wanprestatie constateren]  [Uitstel]
```

### 4.5 Integratie met bestaande code

- Elke geregistreerde termijn maakt een `Payment` aan via `create_payment()` — art. 6:44 BW-toerekening loopt automatisch
- Regeling-status `completed` wordt automatisch gezet zodra alle termijnen `ontvangen` zijn
- Gemiste-termijn-detectie via Celery beat job (dagelijks)
- Notificatie via bestaande `notifications` module

### 4.6 Wat we NIET bouwen (nu)

- Automatische incasso (geen iDEAL/Mollie integratie)
- E-mail herinneringen vanuit de termijn (wel wenselijk, maar dependency op M365-email)
- PDF-export van de regeling (wenselijk, maar apart te bouwen)
- Renteberekening exclusief voor looptijd regeling (rente loopt gewoon door — standaard)

---

## 5. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| Complexe wizard maakt aanmaken traag | Middel | Defaults slim zetten (bedrag = openstaand, datum = vandaag + 1 maand) |
| Deelbetaling op termijn: hoe registreren? | Laag | `paid_amount` veld per termijn, status wordt `gedeeltelijk` |
| Rente loopt door tijdens regeling | Laag | Niet het systeem's probleem — is juridisch standaard. Uitleggen in UI. |
| Celery job mist gemiste termijnen (downtime) | Laag | Bij herstel job: detecteert alsnog alle gemiste termijnen |
| Meerdere regelingen op één dossier | Laag | Toegestaan, maar alleen één `active` tegelijk (validatie in service) |

---

## 6. Bouwstappen (geschat)

| # | Component | Omvang | Details |
|---|-----------|--------|---------|
| 1 | DB migratie: `PaymentArrangementInstallment` tabel + extra velden op `PaymentArrangement` | Klein | Alembic revision |
| 2 | Backend service: termijngeneratie bij aanmaken | Midden | Bereken datums, maak installment records aan |
| 3 | Backend service: termijn registreren (koppelt aan Payment) | Midden | create_payment() aanroepen, status bijwerken |
| 4 | Backend service: wanprestatie-flow | Klein | Status updates, validaties |
| 5 | Celery beat job: gemiste termijnen detecteren | Klein | Dagelijkse check + notificaties |
| 6 | Backend endpoints uitbreiden | Midden | GET/POST/PATCH voor installments |
| 7 | Frontend hook `use-collections.ts` uitbreiden | Klein | Queries + mutations voor regelingen + termijnen |
| 8 | Frontend: tab "Betalingsregeling" in IncassoTab | Groot | Wizard + termijnoverzicht + actiedialogs |
| 9 | Frontend: dashboard alert voor gemiste termijnen | Klein | Notification card op dashboard |
| 10 | Tests (backend) | Midden | Termijngeneratie, registratie, wanprestatie |

**Totaal geschat:** 2-3 sessies (backend-heavy in sessie 1, frontend in sessie 2-3)

---

## 7. Referenties en bronnen

- Clio Payments documentatie (eigen kennis van product tot aug 2025)
- PracticePanther billing docs (eigen kennis)
- LawPay payment plans feature page (eigen kennis)
- Smokeball billing module (eigen kennis)
- Payt.nl debiteurenbeheer (eigen kennis, Nederlandse markt)
- Basenet (Lisanne's huidig systeem — functioneel gat vastgesteld)
- Luxis `backend/app/collections/models.py` — bestaand datamodel
- Dutch legal rules: art. 6:44 BW (toerekening), art. 6:96 BW (BIK)

---

*Dit document is het onderzoeksresultaat. Wacht op goedkeuring voordat implementatie begint.*
