# AI Agent Layer — Luxis Masterplan

**Status:** DRAFT — wacht op goedkeuring
**Datum:** 6 maart 2026
**Sessie:** 38

---

## Samenvatting

Een AI agent die het volledige incassowerk kan afhandelen, van intake tot afronding. De agent werkt met alles wat Luxis al kan (dossiers, facturatie, documenten, email, betalingen) en voegt intelligentie toe.

**Kernprincipe:** De advocaat blijft altijd eindverantwoordelijk (NOvA). De agent bereidt voor, de advocaat keurt goed.

---

## Concurrentie-analyse

### Legal AI (internationaal)

| Bedrijf | Product | Wat het doet | Autonomie |
|---------|---------|-------------|-----------|
| Harvey AI | Platform ($8B) | Multi-step workflows, contract review 80x sneller | Hoog |
| Thomson Reuters | CoCounsel Legal (1M users) | Deep Research, guided workflows | Medium-Hoog |
| Luminance | Autopilot | Autonome NDA-onderhandeling | Zeer hoog |
| Clio | Manage AI | Deadline extractie, factuur generatie | Medium |
| Smokeball | AutoTime + Archie | Auto tijdregistratie, AI drafting | Laag-Medium |
| Anthropic | Claude Cowork Legal (feb 2026) | Contract review, NDA triage | Medium |

### Incasso/Collections AI

| Bedrijf | Wat het doet | Markt |
|---------|-------------|-------|
| Kolleno | 3 autonomieniveaus (insights/copilot/execute), DSO -67% | Internationaal B2B |
| Prodigal AI | 24/7 voice + digital agent | US consumer debt |
| Intrum/Ophelos | AI-native in 8 EU-markten incl. NL, innovatieprijs 2025 | Enterprise consumer |
| Flanderijn | ML voorspelt succes in 83% | NL deurwaarders |
| Payt | ML betaalgedrag-predictie, 65% recovery | NL debiteurenbeheer |
| POM | AI optimaliseert contactmoment, 52% minder escalaties | NL debiteurenbeheer |

### De gap die Luxis vult

**Niemand** combineert:
1. Nederlandse wetskennis (WIK-staffel, art. 6:44 BW, compound interest, 14-dagenbrief)
2. Advocatenkantoor-workflow (NOvA-compliant)
3. AI agent voor de hele pipeline (intake tot dagvaarding)
4. Toegankelijk voor kleine kantoren (1-5 advocaten)

---

## NOvA Regels (dec 2025)

- Advocaat blijft **altijd eindverantwoordelijk**
- AI-output is altijd een **concept** dat verificatie nodig heeft
- Geen client data naar tools die trainen op input
- Transparant over AI-gebruik

---

## Wat Luxis NU al kan (bestaande API's)

De AI agent hoeft niet alles zelf te bouwen — Luxis heeft al een complete API:

### Dossiers & Incasso
- Dossier CRUD + pipeline stappen + status transitions
- Vorderingen (claims) CRUD met verzuimdatum
- Compound interest berekening (art. 6:119/6:119a BW)
- BIK/WIK berekening (art. 6:96 BW, 15/10/5/1/0.5% staffel)
- Payment distribution (art. 6:44 BW: kosten → rente → hoofdsom)
- Betalingsregelingen CRUD
- Derdengelden (trust funds) met goedkeuringsflow
- Pipeline overview + batch acties + queue counts
- Conflict check

### Documenten & Email
- DOCX template rendering (herinnering, aanmaning, 14-dagenbrief, sommatie)
- Custom managed templates (upload eigen .docx)
- Document verzenden als PDF per email
- Email sync via Gmail/Outlook provider
- Email auto-linking aan dossiers (contact/referentie/dossiernummer matching)
- Compose via provider (verschijnt in Verzonden map)
- Ongelinkte emails queue met suggesties
- Bijlagen downloaden + opslaan bij dossier

### Facturatie & Financieel
- Factuur CRUD met regels (concept → goedgekeurd → verzonden → betaald)
- Credit notes
- Factuurbetalingen registreren + payment summary
- Debiteurenoverzicht (aging receivables)
- Onkosten CRUD (declarabel, nog niet gefactureerd)
- Onbefactureerde uren ophalen per dossier
- Tijdregistratie CRUD + samenvatting

### Workflow & Planning
- Taken CRUD met toewijzing + deadline + status
- Agenda events CRUD
- Verjaringscheck (alle actieve dossiers)
- Automatiseringsregels
- Dashboard KPI's + recente activiteit

### Overig
- KYC/WWFT compliance checks
- Global search (dossiers, relaties, documenten)
- Relaties CRUD met koppelingen (persoon ↔ bedrijf)

---

## Architectuur

### 3 Lagen

```
┌─────────────────────────────────────────────────────┐
│                   LAAG 3: AI AGENT                  │
│  Orchestrator + gespecialiseerde sub-agents          │
│  Claude API + tool use                               │
├─────────────────────────────────────────────────────┤
│                   LAAG 2: MCP TOOLS                 │
│  Luxis-interne tools (wrappen bestaande API's)       │
│  Externe tools (KvK API, bank feed)                  │
├─────────────────────────────────────────────────────┤
│                   LAAG 1: LUXIS CORE                │
│  Bestaande API's (alles hierboven)                   │
└─────────────────────────────────────────────────────┘
```

### Autonomieniveaus (per stap configureerbaar)

| Niveau | Naam | Wat de agent doet | Lawyer actie |
|--------|------|-------------------|--------------|
| 1 | **Inzicht** | Analyseert, signaleert, adviseert | Lawyer doet alles zelf |
| 2 | **Copilot** | Bereidt alles voor, drafts klaar | Lawyer reviewt + 1-click approve |
| 3 | **Autonoom** | Voert uit binnen regels | Lawyer ziet achteraf in audit log |

---

## Fases

### Fase A1: MCP Tool Layer (2-3 sessies)

Wrap alle bestaande Luxis API's als MCP tools zodat de AI agent ze kan aanroepen:

| Tool | Wrapt | Voorbeeld |
|------|-------|-----------|
| `dossier_create` | POST /api/cases | Maak dossier van intake-email |
| `dossier_get` / `dossier_list` | GET /api/cases | Haal dossierinfo op |
| `dossier_update` | PUT /api/cases/{id} | Update status/velden |
| `contact_lookup` | GET /api/relations + conflict-check | Zoek bestaande relatie |
| `contact_create` | POST /api/relations | Nieuwe debiteur aanmaken |
| `interest_calculate` | GET /api/cases/{id}/interest | Rente berekenen |
| `wik_calculate` | GET /api/cases/{id}/bik | BIK berekenen |
| `payment_register` | POST /api/cases/{id}/payments | Betaling met art. 6:44 verdeling |
| `payment_summary` | GET /api/cases/{id}/financial-summary | Totaaloverzicht |
| `document_generate` | POST /api/documents/docx/cases/{id}/generate | Template renderen |
| `document_send` | POST /api/documents/{id}/send | PDF per email versturen |
| `email_send` | POST /api/email/compose/cases/{id} | Email via provider |
| `email_read` | GET /api/email/messages/{id} | Email inhoud lezen |
| `email_unlinked` | GET /api/email/unlinked | Ongelinkte emails ophalen |
| `pipeline_overview` | GET /api/incasso/pipeline | Alle dossiers per stap |
| `pipeline_advance` | POST /api/incasso/batch | Batch pipeline actie |
| `invoice_create` | POST /api/invoices | Factuur aanmaken |
| `invoice_add_line` | POST /api/invoices/{id}/lines | Factuurregel toevoegen |
| `invoice_approve` | POST /api/invoices/{id}/approve | Factuur goedkeuren |
| `invoice_send` | POST /api/invoices/{id}/send | Factuur markeren als verzonden |
| `invoice_mark_paid` | POST /api/invoices/{id}/mark-paid | Factuur betaald markeren |
| `unbilled_hours` | GET /api/time-entries/unbilled | Onbefactureerde uren |
| `receivables` | GET /api/invoices/receivables | Openstaande facturen |
| `time_entry_create` | POST /api/time-entries | Tijdregistratie loggen |
| `task_create` | POST /api/workflow/tasks | Taak voor Lisanne |
| `task_list` | GET /api/workflow/tasks | Openstaande taken |
| `calendar_create` | POST /api/calendar/events | Agenda-event |
| `trust_fund_balance` | GET /api/trust-funds/cases/{id}/balance | Derdengelden saldo |
| `trust_fund_create` | POST /api/trust-funds/cases/{id}/transactions | Storting/uitkering |
| `dashboard_summary` | GET /api/dashboard/summary | KPI's ophalen |
| `search` | GET /api/search | Global zoeken |

### Fase A2: Incasso Copilot (3-4 sessies)

De eerste AI-functionaliteit — niveau 2 (copilot):

#### A2.1 — Dossier Intake Agent
- Client stuurt email met factuur + debiteurgegevens
- Agent parsed email, extraheert: debiteur, factuurnummer, bedrag, vervaldatum
- Agent verrijkt via KvK API
- Agent maakt concept-dossier aan → lawyer reviewt + approve met 1 klik
- **Tijdsbesparing:** 10-15 min → 30 sec review

#### A2.2 — Workflow Advisor
- Agent monitort alle dossiers continu
- Signaleert: "Dossier 2026-00045 staat 16 dagen zonder reactie → aanbeveling: 14-dagenbrief"
- Genereert brief met correcte berekeningen
- Lawyer klikt: approve → verstuurd
- Logt automatisch tijdregistratie voor de actie

#### A2.3 — Payment Matcher
- Betaling binnenkomend → agent matcht op bedrag/referentie/debiteur
- Past art. 6:44 BW toe automatisch (niveau 3)
- Updatet dossier + berekent nieuw saldo

#### A2.4 — Debtor Response Classifier
- Inkomende email van debiteur
- Agent classificeert: betwisting / betalingsregeling / betaald-bewering / adreswijziging
- Stelt vervolgactie voor per categorie
- Standaard: concept-antwoord klaar. Complex: escalatie naar lawyer

#### A2.5 — Facturatie Agent (NIEUW)
Dit is wat de agent doet met facturatie:

**Eigen facturen (aan cliënten):**
- Agent checkt periodiek onbefactureerde uren per dossier
- Bij voldoende uren/afronding: maakt concept-factuur aan met alle regels
- Voegt tijdregistraties + onkosten automatisch toe als factuurregels
- Lawyer reviewt → 1-click approve → factuur wordt verstuurd
- Agent monitort openstaande facturen en signaleert overdue

**Doorstorten aan cliënt (na incasso-ontvangst):**
- Betaling van debiteur binnenkomt → agent registreert op dossier
- Agent berekent: hoeveel gaat naar cliënt (hoofdsom + rente), hoeveel is kantoorkosten (BIK)
- Agent maakt concept-afrekening klaar: "Dossier 2026-00045: ontvangen €5.240, door te storten aan cliënt: €4.200 (hoofdsom €4.000 + rente €200), kantoorkosten: €1.040 (BIK €860 + BTW €180)"
- Bij derdengelden: maakt uitkeringstransactie klaar ter goedkeuring
- Lawyer keurt goed → geld wordt overgemaakt + cliënt ontvangt specificatie

**Incasso-afrekening:**
- Bij afsluiting dossier: agent genereert complete afrekening
- Overzicht: oorspronkelijke vordering, ontvangen betalingen, verdeling per art. 6:44, rente, BIK, BTW
- Factuur voor kantoorkosten (als die apart gefactureerd worden)
- Alles klaar in 1 approval-stap

### Fase A3: Intelligent Dashboard (2 sessies)

**Het "commandocentrum" voor Lisanne:**

- **Agent Activity Feed**: wat heeft de agent gedaan
- **Approval Queue**: items die goedkeuring nodig hebben, gesorteerd op urgentie
- **Portfolio Insights**: recovery rate, gemiddelde doorlooptijd, voorspelling inkomsten
- **Risico-alerts**: dossiers die afwijken van normaal patroon
- **Audit Trail**: volledige log van elke agent-actie met undo-mogelijkheid
- **Ochtend-briefing**: "Goedemorgen Lisanne. 3 betalingen ontvangen (€12.400), 5 dossiers klaar voor 14-dagenbrief, 2 reacties van debiteuren om te beoordelen."

### Fase A4: Autonoom niveau (2-3 sessies)

Na bewezen copilot-fase, upgrade naar niveau 3 voor routine-taken:

- Auto-herinnering na X dagen zonder betaling
- Auto-aanmaning na X dagen na herinnering
- Auto-rente-update bij elke actie
- Auto-client-rapportage (wekelijks statusupdate per dossier)
- Auto-tijdregistratie bij elke agent-actie
- Smart scheduling (optimaal contactmoment)
- Auto-facturatie concept voor terugkerende dossiers

**Altijd met kill-switch**: per dossier of globaal uitschakelen.

---

## Technische Stack

| Component | Technologie | Waarom |
|-----------|------------|--------|
| LLM | Claude API (Sonnet routine, Opus complex) | Best-in-class tool use, MCP native |
| Agent framework | Claude Agent SDK / custom orchestrator | Orchestrator-worker pattern |
| Tool interface | MCP servers (per Luxis module) | Standaard, toekomstbestendig |
| Approval flow | WebSocket push + queue tabel | Real-time notificaties |
| Audit trail | `agent_actions` tabel | Elke actie gelogd |
| Cost control | Token tracking per dossier/maand | Voorkom onverwachte kosten |

## Kostenschatting

- ~5-10 Claude API calls per dossier/maand
- ~$0.10-0.30 per dossier/maand met Sonnet
- Bij 200 actieve dossiers: ~$20-60/maand
- **ROI**: 1 intake kost 15 min (€15). Agent doet het in 30 sec.

---

## Roadmap

| Fase | Wat | Dependency | Sessies |
|------|-----|-----------|---------|
| A1 | MCP Tool Layer | Geen | 2-3 |
| A2 | Incasso Copilot (intake, workflow, payments, email, facturatie) | A1, M365 voor A2.4 | 3-4 |
| A3 | Intelligent Dashboard | A2 | 2 |
| A4 | Autonoom niveau | A3 + bewezen copilot | 2-3 |

**A2.1-A2.3 en A2.5 kunnen zonder M365 email.** Alleen A2.4 (debtor response) heeft email sync nodig.

---

## Open vragen voor review

1. Wil je dat de agent ook **dagvaardingen** kan voorbereiden (concept), of blijft dat 100% handmatig?
2. Moet de agent **betalingsregelingen** kunnen voorstellen aan debiteuren, of alleen signaleren?
3. Wil je een **cliëntportaal** waar cliënten real-time de status van hun dossiers zien (door de agent bijgehouden)?
4. Moeten er **limieten** zijn op wat de agent autonoom mag doen? (bijv. max bedrag, max aantal acties per dag)
5. Wil je dat de agent ook **niet-incasso** dossiers kan ondersteunen (bijv. insolventiemappen)?
