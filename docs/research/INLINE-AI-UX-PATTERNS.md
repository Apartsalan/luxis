# Inline AI UX Patterns — Research Report

**Doel:** Hoe tonen de beste SaaS-tools AI-resultaten INLINE binnen de workflow (niet op een aparte AI-pagina)?
**Datum:** 2026-03-22
**Toepassing:** Luxis AI Incasso Agent — AI is onzichtbaar, maar resultaten zijn zichtbaar

---

## TL;DR — De 6 Patronen die Luxis Moet Adopteren

| # | Patroon | Voorbeeld | Luxis Toepassing |
|---|---------|-----------|------------------|
| 1 | **Inline Badges/Labels** | Linear auto-labels, Superhuman auto-labels, Gmail smart labels | AI-classificatie ("betwisting", "betaalbelofte") als badge op emails/dossiers |
| 2 | **Ghost Text in Composer** | Intercom Fin Tab-to-accept, Superhuman Instant Reply | Concept-antwoord in email composer, Tab om te accepteren |
| 3 | **Contextual Sidebar Panel** | Salesforce Einstein, Intercom Copilot, Clio Manage AI | AI-context panel rechts met bronnen + redenering |
| 4 | **Auto-Applied + Hover-to-Review** | Linear Triage Intelligence auto-apply | AI vult velden in, hover toont redenering, klik om te wijzigen |
| 5 | **Ambient Status Cards** | Asana Smart Status, HubSpot audit cards | Dashboard kaarten die AI-acties samenvatten |
| 6 | **Confidence Indicators** | Industry best practice (Smashing Mag, Shape of AI) | Kleur-codering op AI-voorstellen: groen (hoog), amber (medium) |

---

## 1. CRM & Legal Tools met AI

### Clio Manage AI (voorheen Clio Duo)

**Hoe het werkt:**
- AI is ingebouwd in Clio Manage zelf — geen apart product of pagina
- Toegang via een "Ask a Question" chat panel EN via "AI Actions" op het dossier-dashboard
- Deadlines worden geextraheerd uit court documents en getoond in een **side-by-side view** met het brondocument
- Facturen worden als **draft** aangemaakt door AI, met een **approval workflow** voor menselijke review
- Uitgaven worden automatisch gepopuleerd vanuit documenten

**UI Patronen:**
- **Side-by-side document view**: AI-geextraheerde deadlines naast het brondocument, zodat de advocaat kan verifieren
- **Draft-modus**: AI maakt concepten (facturen, events), menselijke review voor het definitief wordt
- **Approval routing**: AI-gemaakte items gaan door een goedkeuringsflow

**Relevantie voor Luxis:**
- Het side-by-side patroon is perfect voor wanneer de AI een email analyseert: links de email, rechts de AI-analyse
- Draft-modus voor AI-gegenereerde antwoorden: AI stelt voor, Lisanne keurt goed
- Approval workflow = de "needs review" status die we nodig hebben

**Bron:** [Clio Manage AI](https://www.clio.com/features/legal-ai-software/), [Clio Help: Manage AI](https://help.clio.com/hc/en-us/articles/29657814904475)

---

### HubSpot Breeze AI

**Hoe het werkt:**
- Drie lagen: **Breeze Copilot** (dagelijkse hulp), **Breeze Agents** (automatisering), **Breeze Intelligence** (data verrijking)
- Agents kunnen direct getriggerd worden vanuit HubSpot workflows
- **Audit cards** tonen exact welke acties de agent heeft uitgevoerd

**UI Patronen:**
- **Audit cards**: Kaarten die laten zien WAT de AI heeft gedaan, WANNEER, en met welk resultaat — bouwt vertrouwen op
- **Inline workflow triggers**: AI-acties als stappen binnen bestaande workflows, niet als aparte pagina
- **Context-aware output**: AI-resultaten voeden terug in het CRM-ecosysteem voor vervolgacties

**Relevantie voor Luxis:**
- Audit cards zijn het perfecte patroon voor het "AI activiteiten" overzicht — niet een aparte pagina, maar kaarten IN het dossier
- AI-acties als onderdeel van de bestaande incasso-pipeline flow

**Bron:** [HubSpot Breeze](https://www.hubspot.com/products/artificial-intelligence/breeze-ai-assistant), [HubSpot Breeze Guide](https://www.fastslowmotion.com/complete-guide-hubspot-breeze/)

---

### Salesforce Einstein (Agentforce)

**Hoe het werkt:**
- Einstein icon rechtsboven in de UI
- Klikken opent een **sidebar** die de pagina naar links verschuift
- Suggesties verschijnen als multi-step action plans die je kunt accepteren/verwijderen
- Prompt Builder voor custom AI-prompts "in the flow of work"

**UI Patronen:**
- **Persistent icon + collapsible sidebar**: De AI is altijd bereikbaar via een vast icoon, maar neemt geen ruimte in tot je het nodig hebt
- **Action plans**: Niet een enkele suggestie maar een gestructureerd plan met meerdere stappen — gebruiker kan individuele stappen verwijderen
- **"Next best action" suggestions**: AI stelt de volgende logische actie voor op basis van context

**Relevantie voor Luxis:**
- Het action plan patroon past perfect bij incasso: AI stelt voor "1. Stuur herinnering, 2. Bereken rente, 3. Update status" — Lisanne kan stappen accepteren/verwijderen
- Sidebar voor AI-context is minder invasief dan een apart scherm

**Bron:** [Salesforce Agentforce](https://www.salesforce.com/agentforce/einstein-copilot/), [Einstein AI Guide](https://www.eesel.ai/blog/salesforce-einstein-ai-features)

---

### Intercom Fin AI Copilot

**Hoe het werkt:**
- AI zit in een **tab in de rechter sidebar** van elke conversatie/ticket
- Suggesties verschijnen **in de reply composer** als ghost text — **Tab om te accepteren, Esc om te weigeren**
- Bronnen worden getoond in de sidebar met **gele highlighting** van gebruikte informatie
- "Add to composer" knop met optie "Add to composer & modify"

**UI Patronen:**
- **Tab-to-accept ghost text**: De krachtigste inline AI pattern — suggestie verschijnt als grijze tekst in het invoerveld, Tab accepteert, Esc verwijdert
- **Source highlighting**: Geel gemarkeerde tekst in de bronnen zodat de agent kan verifieren WAAROM de AI dit antwoord gaf
- **Preview in sidebar**: Bronnen direct in de inbox previewen zonder te navigeren
- **Suggested macros**: Automatische macro-suggesties voor veelvoorkomende vragen

**Relevantie voor Luxis:**
- Tab-to-accept is DE pattern voor AI-gegenereerde email antwoorden in de incasso workflow
- Source highlighting = perfect voor wanneer de AI een email classificeert: markeer de zinnen die tot de classificatie leiden
- "Add to composer & modify" = precies de workflow die Lisanne nodig heeft

**Bron:** [Intercom Copilot](https://www.intercom.com/help/en/articles/8587194-how-to-use-copilot), [Fin AI Copilot Blog](https://www.intercom.com/blog/announcing-fin-ai-copilot/)

---

### Freshdesk Freddy AI

**Hoe het werkt:**
- Context-aware assistentie direct IN het ticket
- Suggested replies, thread summaries, real-time vertaling
- Pre-built "agentic workflows" voor veelvoorkomende scenario's
- No-code builder voor configuratie

**UI Patronen:**
- **In-ticket suggestions**: Concept-antwoorden verschijnen direct in het ticket, niet in een apart venster
- **Thread summary**: Lange conversaties worden samengevat bovenaan het ticket
- **Pre-built workflows**: Kant-en-klare flows die de agent kan activeren met een klik

**Relevantie voor Luxis:**
- Thread summary = nuttig voor lange email-threads in incassodossiers
- Pre-built workflows = de vaste incasso-stappen (herinnering, aanmaning, sommatie) als activeerbare flows

**Bron:** [Freshdesk Freddy AI](https://support.freshdesk.com/support/solutions/articles/50000010359), [Freddy AI Copilot](https://www.freshworks.com/freshdesk/omni/freddy-ai-copilot/)

---

## 2. Email Tools met AI Classificatie

### Superhuman AI

**Hoe het werkt:**
- **Auto Summarize**: Elke email/thread krijgt een 1-regel samenvatting boven de conversatie
- **Auto Labels**: Gebruikers maken labels met korte AI-prompts, inbox wordt gesplitst in tabs per label
- **Instant Reply**: Meerdere AI-concept-antwoorden bij elke email, matcht stem en toon van de gebruiker
- AI is verweven in de kern van het product — geen apart "AI menu"

**UI Patronen:**
- **1-line summary above every conversation**: Altijd zichtbaar, update automatisch bij nieuwe berichten — geen klik nodig
- **Custom AI labels als tabs**: Inbox gesplitst in categorietabs (bijv. "Betwistingen", "Betaalbeloftes", "Nieuwe zaken") — elk automatisch geclassificeerd
- **Multiple draft responses**: Niet een suggestie maar meerdere opties om uit te kiezen
- **Voice matching**: AI leert de schrijfstijl van de gebruiker

**Relevantie voor Luxis:**
- 1-line summary boven elke email in de correspondentie tab = instant context zonder te lezen
- Custom AI labels als tabs in de email inbox = perfect voor incasso email triage
- Multiple draft responses = Lisanne kiest het beste antwoord in plaats van helemaal zelf te schrijven

**Bron:** [Superhuman AI](https://superhuman.com/products/mail/ai), [Superhuman Auto Labels](https://help.superhuman.com/hc/en-us/articles/40127432866323-Auto-Labels)

---

### Gmail Smart Labels / AI Classification

**Hoe het werkt:**
- Native: DLP labels met badged opties (2-7 waarden per label)
- Third-party add-ons (AI Label Assistant) voor automatische tagging
- Labels verschijnen als gekleurde badges naast de email in de inbox

**UI Patronen:**
- **Colored badge labels**: Kleine gekleurde tags naast de email-regel in de inbox
- **Multiple simultaneous labels**: Een email kan meerdere AI-labels krijgen
- **Integrated settings panel**: Configuratie zonder de inbox te verlaten

**Relevantie voor Luxis:**
- Gekleurde badge labels = het basispatroon voor AI-classificatie in de email lijst

**Bron:** [Gmail DLP Classification](https://support.google.com/a/answer/15517856)

---

### Front AI (Intelligent Triage)

**Hoe het werkt:**
- Automatisch routeren van conversaties naar de juiste persoon/team
- AI Compose voor concept-antwoorden op veelvoorkomende vragen
- Classificatie gebeurt op de achtergrond

**UI Patronen:**
- **Auto-routing met labels**: Inkomende berichten krijgen automatisch team/categorie labels
- **AI Compose in-context**: Concept-antwoorden direct in de composer

**Beperking:** Geen manier om AI-accuracy te testen voordat je het live zet — dit willen we beter doen in Luxis

**Bron:** [Front AI](https://www.eesel.ai/blog/front-ai)

---

## 3. Project Management met AI

### Linear Triage Intelligence

**Hoe het werkt:**
- AI analyseert nieuwe issues en stelt voor: **team, project, assignee, labels**
- Suggesties worden getoond met een **korte uitleg** zodat teams snel en consistent kunnen triagen
- **Auto-apply modus**: Bepaalde properties (bijv. "bug" label) worden automatisch toegepast
- **Hover-to-review**: Automatisch toegepaste properties zijn duidelijk gemarkeerd, hover toont de redenering

**UI Patronen (het beste voorbeeld voor Luxis):**
- **Auto-apply + clearly marked**: AI past labels/assignees toe maar markeert ze duidelijk als "AI-applied"
- **Hover for reasoning**: Hover over een AI-applied property toont WAAROM de AI dit koos — transparant en vertrouwenwekkend
- **Configurable per property**: Per eigenschap kiezen: toon suggestie, verberg, of auto-apply
- **Duplicate detection**: AI flagged duplicaten en linkt gerelateerde issues

**Relevantie voor Luxis (HOOG):**
- Dit is het exacte patroon dat we nodig hebben voor AI email classificatie:
  - Email komt binnen → AI classificeert als "betwisting" (auto-applied badge)
  - Hover over badge → "Gebaseerd op: 'ik ben het niet eens met de factuur' in regel 3"
  - Configureerbaar: welke classificaties auto-apply, welke "needs review"
- Duplicate/related detection = herkennen wanneer een email bij een bestaand dossier hoort

**Bron:** [Linear Triage Intelligence](https://linear.app/docs/triage-intelligence), [Linear Auto-Apply Changelog](https://linear.app/changelog/2025-09-19-auto-apply-triage-suggestions)

---

### Notion AI Inline

**Hoe het werkt:**
- AI-bewerkingen direct in de tekst (inline overlay)
- Suggestions mode met tracked changes (zoals Google Docs)
- Page-level summaries
- Notion 3.0 (sept 2025): autonome AI Agents voor multi-step workflows

**UI Patronen:**
- **Inline overlay prompts**: Context-sensitieve suggesties verschijnen direct in de tekst
- **Suggestions mode**: Wijzigingen worden getoond als tracked changes die je kunt accepteren/verwijderen
- **Unified answers met citations**: Antwoorden trekken uit meerdere bronnen met bronvermelding

**Relevantie voor Luxis:**
- Suggestions mode = goed patroon voor AI-gegenereerde concepten die Lisanne reviewt
- Citations = altijd tonen waar de AI zijn conclusie op baseert

**Bron:** [Notion AI Inline Guide](https://www.eesel.ai/blog/notion-ai-inline)

---

### Asana Smart Status / Smart Fields

**Hoe het werkt:**
- **Smart Status**: AI genereert statusupdates op basis van real-time projectdata
- **Smart Fields**: AI stelt custom fields voor bij nieuwe projecten op basis van context
- **AI Studio**: No-code builder voor AI-powered workflows met intelligente regels

**UI Patronen:**
- **Auto-generated status cards**: Statusupdates verschijnen automatisch op het project-dashboard
- **Suggested metadata**: Bij het aanmaken van items stelt AI relevante velden voor
- **No-code workflow builder**: Visueel configureren welke AI-acties wanneer triggeren

**Relevantie voor Luxis:**
- Auto-generated status = AI kan dossier-status updates genereren ("Geen reactie na 14 dagen, tijd voor aanmaning")
- Suggested metadata = AI kan bij nieuw dossier velden voorstellen op basis van de aangeleverde documenten

**Bron:** [Asana Smart Status](https://help.asana.com/s/article/smart-status), [Asana Smart Fields](https://help.asana.com/s/article/smart-fields)

---

## 4. Overkoepelende UX Patronen & Best Practices

### Waar Moet AI Zitten in de UI?

Gebaseerd op UX Collective en Smashing Magazine research zijn er 5 hoofdpatronen:

| Patroon | Beschrijving | Wanneer Gebruiken | Voorbeeld |
|---------|-------------|-------------------|-----------|
| **Inline Overlay** | AI verschijnt direct in de content/tekst | Bewerkingen, suggesties, classificatie | Notion, Grammarly |
| **Right Sidebar Panel** | Collapsible panel rechts | Context, bronnen, gedetailleerde uitleg | Salesforce, Intercom, Clio |
| **Ghost Text / Autocomplete** | Grijze tekst in invoerveld | Concept-antwoorden, form completion | Intercom, Superhuman |
| **Ambient Intelligence** | UI past zich aan zonder dat gebruiker iets doet | Auto-labels, auto-routing, status updates | Linear, Gmail, Superhuman |
| **Action Cards** | Kaarten met voorgestelde acties + accept/reject | Multi-step workflows, goedkeuringsflows | Salesforce, HubSpot, Asana |

### Confidence Indicators (Best Practice 2025-2026)

De belangrijkste nieuwe pattern is de **visuele confidence indicator**:

| Confidence Level | Visuele Weergave | Actie |
|-----------------|-------------------|-------|
| **Hoog** (>90%) | Groene rand/badge | Auto-apply, hover voor uitleg |
| **Medium** (70-90%) | Amber/oranje rand/badge | Toon als suggestie, wacht op bevestiging |
| **Laag** (<70%) | Rode rand/badge of helemaal verbergen | Markeer als "needs review" of niet tonen |

### Anti-Patterns (Wat NIET Doen)

1. **Aparte AI-pagina**: Gebruikers navigeren er niet naartoe. AI moet IN de workflow zitten.
2. **Sparkles/AI iconen die niet begrepen worden**: Onderzoek toont dat "sparkle" iconen vaak worden genegeerd of niet begrepen.
3. **Prominente AI-assistenten die worden genegeerd**: Hoe prominenter de AI-assistentie, hoe vaker het genegeerd wordt.
4. **AI zonder bronnen/redenering**: Gebruikers vertrouwen AI niet als ze niet kunnen zien WAAROM een beslissing is genomen.
5. **Niet-reversibele AI-acties**: Elke AI-actie moet omkeerbaar zijn met een klik.

### De "Explainable Rationale" Pattern

Het meest effectieve trust-building patroon: de AI toont een **beknopte uitleg** van zijn beslissing, gebaseerd op de context van de gebruiker zelf. Niet technisch ("confidence 0.87") maar menselijk ("Geclassificeerd als betwisting omdat de debiteur schrijft: 'ik ben het niet eens met het bedrag'").

---

## 5. Concrete Aanbevelingen voor Luxis AI Agent

### Patroon 1: Email Classificatie (Ambient + Inline Badges)

**Gebaseerd op:** Linear Triage Intelligence + Superhuman Auto Labels

```
Inbox / Correspondentie tab:
┌─────────────────────────────────────────────────────┐
│ Van: debiteur@bedrijf.nl                            │
│ Onderwerp: Re: Factuur 2026-00042                   │
│ [🟡 Betwisting]  [📎 2 bijlagen]   14:32            │
│ "Ik ben het niet eens met het gefactureerde bedrag" │
└─────────────────────────────────────────────────────┘

Hover over [🟡 Betwisting]:
┌─────────────────────────────────────────────────┐
│ AI Classificatie: Betwisting                     │
│ Confidence: 94%                                  │
│ Reden: "ik ben het niet eens met het bedrag"     │
│ Bron: Email body, regel 2                        │
│                                                   │
│ [✓ Correct]  [✗ Wijzig classificatie]            │
└─────────────────────────────────────────────────┘
```

**Configuratie (Linear-stijl):**
- Per classificatie-type kiezen: auto-apply / suggestie / verbergen
- Hoge confidence (>90%) → auto-apply badge
- Lage confidence (<70%) → markeer als "🔍 Review nodig"

---

### Patroon 2: AI Concept-Antwoord (Ghost Text + Sidebar)

**Gebaseerd op:** Intercom Fin Tab-to-accept + Clio side-by-side

```
Email Reply Composer:
┌─────────────────────────────────────────────────────┐
│ Aan: debiteur@bedrijf.nl                            │
│ Onderwerp: Re: Factuur 2026-00042                   │
│                                                      │
│ Geachte heer/mevrouw,                               │ ← AI ghost text (grijs)
│                                                      │
│ Wij hebben uw bericht ontvangen. Het gefactureerde  │
│ bedrag van EUR 3.450,00 is conform de overeenkomst  │
│ d.d. 15 januari 2026. Wij verwijzen u naar...       │
│                                                      │
│ [Tab ↹ Accepteren]  [Esc Verwijderen]  [✏ Bewerken] │
└─────────────────────────────────────────────────────┘

Rechter sidebar (optioneel, click om te openen):
┌─────────────────────────────────────┐
│ 🤖 AI Context                       │
│                                      │
│ Classificatie: Betwisting            │
│ Dossier: 2026-00042                  │
│ Debiteur: ABC Holding B.V.           │
│                                      │
│ Gebruikte bronnen:                   │
│ • Overeenkomst d.d. 15-01-2026      │
│ • Algemene voorwaarden art. 5       │
│ • Eerdere correspondentie (3 mails) │
│                                      │
│ Voorgestelde vervolgactie:           │
│ • Status → "Betwisting ontvangen"   │
│ • Termijn: 14 dagen reactie         │
└─────────────────────────────────────┘
```

---

### Patroon 3: Dossier AI Status Cards (Ambient Intelligence)

**Gebaseerd op:** Asana Smart Status + HubSpot Audit Cards

```
Dossier Detail — Overzicht tab:
┌─────────────────────────────────────────────────────┐
│ Dossier 2026-00042 — ABC Holding B.V.               │
│                                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 🤖 AI Update (vandaag 14:35)                     │ │
│ │                                                   │ │
│ │ • Email ontvangen: betwisting van debiteur        │ │
│ │ • Concept-antwoord opgesteld (wacht op review)    │ │
│ │ • Rente herberekend: EUR 142,50 → EUR 156,80     │ │
│ │                                                   │ │
│ │ [Bekijk details]  [Markeer als gezien ✓]          │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Status: In behandeling                               │
│ Hoofdsom: EUR 3.450,00                              │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
```

---

### Patroon 4: Dashboard AI Samenvatting (Ambient)

**Gebaseerd op:** Superhuman 1-line summaries + Asana Smart Status

```
Dashboard:
┌─────────────────────────────────────────────────────┐
│ 🤖 AI Overzicht (vandaag)                           │
│                                                      │
│ ✅ 3 emails verwerkt en aan dossiers gekoppeld       │
│ 📝 2 concept-antwoorden wachten op review            │
│ ⚠️ 1 email kon niet geclassificeerd worden          │
│ 💰 Rente herberekend voor 5 dossiers                │
│                                                      │
│ [Bekijk wachtrij (2)]                               │
└─────────────────────────────────────────────────────┘
```

---

### Patroon 5: Action Plans bij Escalaties (Salesforce-stijl)

**Gebaseerd op:** Salesforce Einstein action plans

```
Bij een email die escalatie vereist:
┌─────────────────────────────────────────────────────┐
│ 🤖 Voorgesteld Actieplan                             │
│                                                      │
│ De debiteur meldt betalingsonmacht. Voorgestelde     │
│ vervolgstappen:                                      │
│                                                      │
│ ☑ 1. Status wijzigen naar "Betalingsregeling"       │
│ ☑ 2. Betalingsvoorstel template versturen            │
│ ☐ 3. Incasso tijdelijk pauzeren (14 dagen)          │
│ ☑ 4. Herinnering instellen: follow-up over 14 dagen │
│                                                      │
│ [Uitvoeren (3 van 4)]  [Alles accepteren]  [Annuleer]│
└─────────────────────────────────────────────────────┘
```

---

## 6. Implementatie Prioriteit voor Luxis

### Fase 1 — Basis (bij lancering AI Agent)
1. **Inline badges** op emails (classificatie + confidence kleur)
2. **Hover-to-review** met redenering
3. **Dashboard AI samenvatting** kaart

### Fase 2 — Compose & Response
4. **Ghost text** concept-antwoorden in email composer
5. **Tab-to-accept** interactie
6. **AI context sidebar** met bronnen

### Fase 3 — Autonomie
7. **Auto-apply** voor hoge-confidence classificaties
8. **Action plans** voor complexe scenario's
9. **Audit trail** kaarten in dossier activiteiten

### Design Principes (door alle fases heen)
- **AI is onzichtbaar, resultaten zijn zichtbaar** — geen "AI pagina", geen sparkle-iconen
- **Altijd reversibel** — elke AI-actie kan ongedaan gemaakt worden
- **Altijd uitlegbaar** — hover/klik toont WAAROM
- **Configurable confidence drempels** — Lisanne bepaalt wat auto-apply is en wat review nodig heeft
- **Menselijke taal** — geen "confidence 0.87" maar "Waarschijnlijk een betwisting omdat..."

---

## Bronnen

### CRM & Legal
- [Clio Manage AI](https://www.clio.com/features/legal-ai-software/)
- [Clio Help: Get Started with Manage AI](https://help.clio.com/hc/en-us/articles/29657814904475)
- [HubSpot Breeze AI](https://www.hubspot.com/products/artificial-intelligence/breeze-ai-assistant)
- [Salesforce Agentforce](https://www.salesforce.com/agentforce/einstein-copilot/)
- [Intercom Fin AI Copilot](https://www.intercom.com/help/en/articles/8587194-how-to-use-copilot)
- [Freshdesk Freddy AI](https://support.freshdesk.com/support/solutions/articles/50000010359)

### Email
- [Superhuman AI](https://superhuman.com/products/mail/ai)
- [Superhuman Auto Labels](https://help.superhuman.com/hc/en-us/articles/40127432866323-Auto-Labels)
- [Superhuman Instant Reply](https://blog.superhuman.com/superhuman-ai-instant-reply/)
- [Front AI](https://www.eesel.ai/blog/front-ai)

### Project Management
- [Linear Triage Intelligence](https://linear.app/docs/triage-intelligence)
- [Linear Auto-Apply Triage](https://linear.app/changelog/2025-09-19-auto-apply-triage-suggestions)
- [Notion AI Inline Guide](https://www.eesel.ai/blog/notion-ai-inline)
- [Asana Smart Status](https://help.asana.com/s/article/smart-status)
- [Asana Smart Fields](https://help.asana.com/s/article/smart-fields)

### UX Patterns & Design Theory
- [Where Should AI Sit in Your UI? — UX Collective](https://uxdesign.cc/where-should-ai-sit-in-your-ui-1710a258390e)
- [Design Patterns for AI Interfaces — Smashing Magazine](https://www.smashingmagazine.com/2025/07/design-patterns-ai-interfaces/)
- [The Shape of AI — UX Patterns](https://www.shapeof.ai)
- [AI UX Patterns](https://www.aiuxpatterns.com/)
- [7 UX Patterns for Ambient AI Agents](https://www.bprigent.com/article/7-ux-patterns-for-human-oversight-in-ambient-ai-agents)
- [Designing for Agentic AI — Smashing Magazine](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)
- [AI UX Design for SaaS — Userpilot](https://userpilot.com/blog/ai-ux-design/)
- [AI Design Patterns in SaaS — UX Studio](https://www.uxstudioteam.com/ux-blog/ai-design-patterns-in-saas-products)
