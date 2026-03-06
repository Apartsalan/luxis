# AI Agent Layer — Luxis Masterplan

**Status:** DRAFT — wacht op goedkeuring
**Datum:** 6 maart 2026
**Sessie:** 38

---

## Samenvatting

Een AI agent die het volledige incassowerk kan afhandelen, van intake tot afronding. De agent werkt met alles wat Luxis al kan (dossiers, facturatie, documenten, email, betalingen) en voegt intelligentie toe.

**Kernprincipe:** De advocaat blijft altijd eindverantwoordelijk (NOvA). De agent bereidt voor, de advocaat keurt goed.

**Kostenprincipe:** De agent is een **taakuitvoerder**, geen chatbot. Geen open-ended conversatie — alleen patroonherkenning + standaardacties. Dit houdt de kosten laag en de output voorspelbaar.

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
| Agent framework | Claude Agent SDK / custom orchestrator | Orchestrator-worker pattern |
| Tool interface | MCP servers (per Luxis module) | Standaard, toekomstbestendig |
| Approval flow | WebSocket push + queue tabel | Real-time notificaties |
| Audit trail | `agent_actions` tabel | Elke actie gelogd |
| Cost control | Token tracking per dossier/maand | Voorkom onverwachte kosten |

## Multi-Model Strategie (kostenoptimalisatie)

**Principe:** De agent is een taakuitvoerder, geen chatbot. Harvey AI biedt een LLM-chat voor juridisch advies — dat is duur. Luxis' agent doet iets fundamenteel anders: hij herkent patronen en voert standaardacties uit. Dit maakt goedkope modellen mogelijk voor 90%+ van het werk.

### Model-selectie per taaktype

| Taak | Model | Kosten/call | Waarom |
|------|-------|-------------|--------|
| Email classificatie (5-6 categorieën) | **Kimi 2.5** | ~$0.001 | Simpele classificatie, goedkoopste optie |
| Data extractie (bedrag, debiteur, datum) | **Kimi 2.5** | ~$0.001 | Gestructureerde extractie |
| Standaard-antwoord selectie | **Kimi 2.5** | ~$0.001 | Template kiezen uit ~10 opties |
| Factuur-regels samenstellen | **Kimi 2.5** | ~$0.001 | Data mapping, geen creativiteit nodig |
| Onbekende email / twijfelgeval | **Claude Haiku** | ~$0.005 | Fallback bij lage confidence |
| Complexe classificatie / escalatie-beslissing | **Claude Sonnet** | ~$0.02 | Alleen als goedkope modellen twijfelen |
| Dagvaarding-drafting (optioneel) | **Claude Opus** | ~$0.10 | Zeldzaam, hoge kwaliteit nodig |

### Decision tree

```
Inkomende taak
  │
  ├─ Standaard patroon? (rule-based check)
  │   ├─ JA → Geen LLM nodig, direct uitvoeren
  │   └─ NEE ↓
  │
  ├─ Classificatie/extractie nodig?
  │   ├─ JA → Kimi 2.5 (goedkoopst)
  │   │        ├─ Confidence > 90%? → Uitvoeren
  │   │        └─ Confidence < 90%? → Haiku retry
  │   │             ├─ Confidence > 90%? → Uitvoeren
  │   │             └─ Confidence < 90%? → Escaleer naar lawyer
  │   └─ NEE ↓
  │
  └─ Complexe taak (drafting, analyse)?
      └─ Sonnet (of Opus voor juridische documenten)
```

### Template-based responses (voorspelbare kosten)

De agent genereert GEEN vrije tekst voor debiteur-communicatie. In plaats daarvan:

1. **Classificeer** de situatie (Kimi 2.5: ~$0.001)
2. **Selecteer** het juiste template uit een vaste set:
   - "Betwisting ontvangen — wij handhaven vordering"
   - "Betalingsregeling — voorstel voorwaarden"
   - "Betaling ontvangen — restant mededeling"
   - "Geen reactie — escalatie waarschuwing"
   - etc. (~10-15 templates)
3. **Vul** de template met dossierdata (geen LLM nodig)
4. **Presenteer** aan lawyer voor goedkeuring

**Resultaat:** Voorspelbare output, voorspelbare kosten, geen hallucinatie-risico.

### Rule-based first, LLM second

Waar mogelijk gebruikt de agent **geen LLM**:

| Actie | Methode | LLM nodig? |
|-------|---------|-------------|
| Rente berekenen | Python Decimal berekening | Nee |
| BIK berekenen | WIK-staffel Python | Nee |
| Betaling verdelen (art. 6:44) | Python logica | Nee |
| Deadline checken | Datum-vergelijking | Nee |
| Verjaring checken | 5-jaar berekening | Nee |
| Pipeline stap bepalen | Status + dagen regel | Nee |
| Email classificeren | LLM classificatie | Ja (Kimi 2.5) |
| Factuur samenstellen uit uren | Data mapping + LLM | Minimaal |
| Debiteur-email beantwoorden | Template selectie | Ja (Kimi 2.5) |

## Kostenschatting (bijgewerkt met multi-model)

### Per dossier per maand
- ~5-10 agent-acties
- ~3-7 Kimi 2.5 calls ($0.001 per stuk) = **$0.003 - $0.007**
- ~1-2 Haiku fallback calls ($0.005 per stuk) = **$0.005 - $0.010**
- ~0-1 Sonnet calls ($0.02 per stuk) = **$0.00 - $0.02**
- **Totaal: ~$0.01 - $0.04 per dossier/maand**

### Bij 200 actieve dossiers
- **$2 - $8 per maand** (was $20-60 met alleen Claude)
- **~85% kostenbesparing** vs. single-model approach

### ROI
- 1 dossier-intake handmatig: 15 min = ~€15 aan tijd
- 1 dossier-intake met agent: 30 sec review = ~€0.50 aan tijd + $0.01 API
- **Break-even bij 1 dossier per maand**

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
