# AI & Automation Inline UX Research — Luxis Incasso

**Datum:** 2026-03-22
**Doel:** Hoe tonen collections/incasso platforms en legal AI tools geautomatiseerde beslissingen, AI-suggesties en confidence levels INLINE in hun workflow — zonder apart AI-scherm?

---

## 1. Collections & Debt Recovery Platforms

### 1.1 TrueAccord — "Heartbeat" ML Engine

**Hoe AI zichtbaar is:**
- Patented ML engine "Heartbeat" beslist automatisch over timing, kanaal (email/SMS/brief) en toon per debiteur
- RPA bots draaien 45 geautomatiseerde processen 24/7 — verwerken 60.000+ betalingen/maand voor een enkele client
- "HumAIn" aanpak: agents worden ondersteund door AI, niet vervangen
- Opt-out requests en accountstatus-updates in real-time (< 90 seconden)

**UI-patroon:** AI draait volledig op de achtergrond. De gebruiker ziet het RESULTAAT (welk bericht verstuurd, wanneer, via welk kanaal) maar niet de beslissing zelf. Geen confidence scores zichtbaar voor agents.

**Relevantie voor Luxis:** Goed model voor "invisible AI" — de agent maakt autonoom keuzes en toont alleen het resultaat in een activity feed.

---

### 1.2 Receeve — Strategy Builder + AI Decisioning

**Hoe AI zichtbaar is:**
- **Drag & Drop Strategy Builder**: no-code visuele flow voor het ontwerpen van incasso-strategieen
- Behavioral scoring per debiteur (AI bepaalt segment en risico)
- A/B testing en zelf-optimalisatie van strategieen, kanalen en timing
- Case Manager: single dashboard met alle klant/claim data

**Pipeline/kanban:** Receeve gebruikt een strategy flow (niet kanban) — visuele nodes die triggers, acties en condities verbinden. De AI optimaliseert BINNEN deze flows.

**Human review:** Agents krijgen een Case Manager workspace met geprioriteerde cases. Complexe cases worden naar agents gerouteerd; routine gaat automatisch.

**Relevantie voor Luxis:** De strategy builder is overkill voor 1 advocaat, maar het PRINCIPE — visuele weergave van welke stap actief is per dossier, met AI die de timing/kanaal optimaliseert — is direct toepasbaar op de incasso pipeline.

---

### 1.3 InDebted — Game Theory AI

**Hoe AI zichtbaar is:**
- ML modellen leren van 1.8 miljard klantinteracties
- "Minimax" logic uit game theory: AI simuleert worst-case scenarios en past strategie automatisch aan
- 80% van debiteuren beheert zelf via de web app — AI stuurt ze daarheen

**UI-patroon:** Debiteur-facing, niet agent-facing. De AI is onzichtbaar voor de eindgebruiker — het stuurt alleen de communicatie.

**Relevantie voor Luxis:** Bevestigt dat voor EENVOUDIGE incasso (herinnering, aanmaning, sommatie) de AI volledig autonoom kan werken. De advocaat hoeft alleen escalaties te zien.

---

### 1.4 HighRadius — AI Worklist Prioritization (BEST PRACTICE)

**Hoe AI zichtbaar is:**
- **Collections Score: 0-100** per debiteur, berekend door ML op 20+ variabelen
- AI-ranked worklist: automatisch gesorteerd op wie het meeste impact heeft
- Smart Account Assignment: accounts worden automatisch toegewezen op basis van beschikbaarheid + verwachte impact
- Voorspelt betalingsvertraging 30 dagen vooruit
- Interactive dashboards met real-time metrics

**Visual indicators:**
- Score badge (0-100) naast elke account
- Kleurcodering op basis van risico/prioriteit
- Suggested actions per account (bel/email/brief)

**Human review:** Collector krijgt een geprioriteerde lijst. Per account staat een suggestie (actie + reden). Collector kan accepteren of eigen actie kiezen.

**Relevantie voor Luxis:** **DIT IS HET BESTE MODEL.** Een numerieke score + kleurcodering + gesuggereerde actie per dossier. Direct toepasbaar op de incasso pipeline.

---

### 1.5 Aktos — No-Code Automation + AI Phone Agent

**Hoe AI zichtbaar is:**
- No-code automation builder met templates per jurisdictie
- AI Phone Agent (inbound + outbound) volledig geintegreerd (geen bolt-on)
- Real-time dashboards: call outcomes, account performance, compliance alerts
- In-platform messaging: account-centric, auditable gesprekken

**UI-patroon:** AI Phone Agent is een "team member" in het platform — zijn acties verschijnen in dezelfde activity feed als menselijke acties, met een badge dat het een AI-actie was.

**Relevantie voor Luxis:** AI-acties als "team member" in de activity feed is een elegant patroon. De AI Agent krijgt een avatar/badge en zijn acties staan in dezelfde tijdlijn als Lisanne's acties.

---

### 1.6 CollBox — Automation + Human Specialists

**Hoe AI zichtbaar is:**
- Auto-detectie van achterstallige facturen vanuit boekhoudpakket
- Drempelwaarde instelbaar (1, 15 of 30 dagen achterstallig)
- Dashboard toont: wie benaderd, wat gezegd, welke facturen betaald
- Elke call, email en notitie gelogd in het dashboard

**Human review:** Dedicated AR Specialist doet het daadwerkelijke contact. Dashboard geeft volledig overzicht van alle interacties.

**Relevantie voor Luxis:** Het logging-patroon is belangrijk — elke AI-actie moet gelogd worden met details (wat verstuurd, wanneer, aan wie, resultaat).

---

### 1.7 Collectly — AI Agent "Billie" (Healthcare)

**Hoe AI zichtbaar is:**
- Billie AI Agent handelt 24/7 patientvragen af
- Multi-channel: SMS, email, automated calls, live chat
- Smart AutoPay: AI stelt automatisch betalingsregelingen voor

**UI-patroon:** AI is een chatbot-achtige interface voor de debiteur. Voor de beheerder: analytics dashboard met collection rates en conversion metrics.

**Relevantie voor Luxis:** De "AI stelt betalingsregeling voor" functie is direct relevant. Bij incasso: als debiteur reageert met "ik kan niet alles betalen", kan de AI een betalingsregeling voorstellen aan Lisanne ter goedkeuring.

---

## 2. Nederlandse/Europese Incasso Tools

### 2.1 Payt — Automated Receivables Management

**Hoe AI zichtbaar is:**
- Dashboard met real-time inzicht in betaalstatus van alle facturen
- Geautomatiseerde herinneringen en opvolging
- 65% van achterstallige facturen wordt alsnog betaald via automatisering
- Betaalopties: iDEAL, QR, PayPal, creditcard, automatische incasso

**UI-patroon:** Pipeline-achtig: facturen doorlopen automatisch fases (verzonden > herinnering 1 > herinnering 2 > incasso). Dashboard toont waar elke factuur staat.

**Relevantie voor Luxis:** Bevestigt dat Nederlandse markt gewend is aan fase-gebaseerde flow. De Luxis incasso pipeline past hier perfect bij.

---

### 2.2 Straetus — Centurion Software + Franchise

**Hoe AI zichtbaar is:**
- Eigen software "Centurion" met geautomatiseerde workflows
- Automatische integratie met boekhoudpakketten — geen handmatige acties nodig
- Online portaal voor clients om voortgang te volgen
- Resultaat: tot 15% betere cashflow

**UI-patroon:** Focus op portaal-view voor de klant (schuldeiser), niet zozeer op agent-interface.

**Relevantie voor Luxis:** Client-portaal is een toekomstige feature. Voor nu: bevestigt dat automatisering van de standaard-flow (herinnering > aanmaning > incasso) de norm is in NL.

---

### 2.3 iFlow — Nederlands Incasso Platform

**Kenmerken:** Specifiek voor de Nederlandse incassomarkt. Workflow-gebaseerd met integraties voor boekhoudpakketten.

---

## 3. Legal Practice Management met AI

### 3.1 Smokeball — Archie AI Matter Assistant (BEST PRACTICE)

**Hoe AI zichtbaar is:**
- **Archie tab** in elk dossier: chat-interface specifiek voor dat dossier
- Knoppen: Ask, Browse, Compose, Draft
- Document-aware: Archie ziet alle documenten in het dossier
- Bij antwoorden: bronvermelding met klikbare links naar documenten
- Conversation history in linker panel
- Andere teamleden's vragen zichtbaar (initialen-iconen)

**Drafting tools:**
- Quill-icoon voor documenten genereren
- Direct geintegreerd met Outlook en Word
- Kan emails, brieven, clausules en juridische documenten opstellen

**AutoTime:** Automatische tijdregistratie op basis van activiteit — bespaart tot 3 uur/dag

**Relevantie voor Luxis:** **DIRECT TOEPASBAAR.** Een "AI tab" per dossier waar de AI:
- Vragen kan beantwoorden over het dossier
- Correspondentie kan voorstellen
- Documenten kan samenvatten
- Bronvermelding naar dossier-documenten

---

### 3.2 CoCounsel (Thomson Reuters/Casetext) — AI Legal Assistant

**Hoe AI zichtbaar is:**
- Chat-interface voor juridische vragen
- Inline Citations: bronvermelding bij elk antwoord
- Kan brieven, memo's, contracten opstellen via prompt
- Getraind op GPT-4 + Casetext's juridische database

**UI-patroon:** Voornamelijk chat-gebaseerd. De AI leeft in een apart panel/tab, niet inline in het document zelf.

**Relevantie voor Luxis:** Citations-patroon is belangrijk — als de AI een suggestie doet (bijv. "stuur 14-dagenbrief"), moet de bron vermeld worden (bijv. "art. 6:96 lid 6 BW").

---

### 3.3 Harvey AI — Unified Professional AI

**Hoe AI zichtbaar is:**
- Alle drafting in een main Assistant interface (geen aparte tools)
- Word Add-In met context-aware suggesties op basis van documenttype
- Bronvermelding bij elk antwoord
- Conversational flow: vraag > antwoord > follow-up > revisie in een thread

**UI-patroon:** Harvey is het meest "inline" van de legal AI tools — suggesties verschijnen in de context van het document waaraan je werkt.

**Relevantie voor Luxis:** Het principe van "suggesties op basis van context" is waardevol. Als Lisanne een dossier opent in de incasso-fase, toont de AI automatisch relevante suggesties (bijv. "14-dagenbrief is 3 dagen geleden verstuurd, termijn verloopt over 11 dagen").

---

### 3.4 PracticePanther — Workflow Automation

**Hoe AI zichtbaar is:**
- Voornamelijk workflow-automatisering, niet zozeer AI-suggesties
- Task workflows, client intake automation, calendaring
- Integratie met externe AI tools (bijv. AgentZap voor intake)

**Relevantie voor Luxis:** Bevestigt dat legal PM tools voornamelijk workflow-automatisering gebruiken. AI is een laag eroverheen, niet de kern.

---

## 4. Agentic AI UX Design Patterns (Industry Best Practices)

### 4.1 Suggestion Card Component

**Standaard structuur voor een AI-suggestie kaart:**

```
+--------------------------------------------------+
| [AI icon] Suggestie van AI                  [x]   |
|                                                    |
| "Verstuur 14-dagenbrief naar debiteur"            |
|                                                    |
| Reden: Termijn herinnering 2 is verlopen (14d)    |
| Confidence: ████████░░ 82%                        |
|                                                    |
| [Accepteren]  [Aanpassen]  [Afwijzen]             |
+--------------------------------------------------+
```

**Componenten:**
1. **AI indicator** (icoon/badge dat dit van AI komt)
2. **Suggestie content** (wat de AI voorstelt)
3. **Reden/uitleg** (waarom, eventueel inklapbaar)
4. **Confidence indicator** (score, kleur, of tekstueel)
5. **Actieknoppen** (accepteer / pas aan / wijs af)
6. **Feedback mechanisme** (was dit nuttig?)

---

### 4.2 Confidence Visualization Patterns

**Opties voor het tonen van confidence:**

| Methode | Wanneer gebruiken | Voorbeeld |
|---------|-------------------|-----------|
| Percentage | Technische gebruikers | "82% zeker" |
| Kleurintensiteit | Subtiel, niet storend | Groene/gele/rode rand |
| Tekstlabel | Niet-technische gebruikers | "Zeer waarschijnlijk" / "Mogelijk" / "Onzeker" |
| Progress bar | Visueel duidelijk | ████████░░ |
| Icoon | Minimaal | Checkmark (hoog) / Vraagteken (laag) |

**Best practice:** Gebruik TEKSTLABELS voor Lisanne (geen techneut), niet percentages. Drie niveaus:
- **Zeker** (groen) — AI is confident, actie kan automatisch
- **Waarschijnlijk** (geel/oranje) — AI denkt dat dit klopt, maar check gewenst
- **Onzeker** (rood/grijs) — AI weet het niet, menselijke beoordeling nodig

---

### 4.3 Human-in-the-Loop Checkpoints

**Autonomie-spectrum** (van Smashing Magazine / Agentic Design patterns):

| Level | Beschrijving | Luxis voorbeeld |
|-------|-------------|-----------------|
| Volledig autonoom | AI handelt zonder tussenkomst | Rente herberekenen bij betaling |
| Notify after | AI handelt, meldt achteraf | Herinnering verstuurd (in activity feed) |
| Suggest & wait | AI stelt voor, wacht op goedkeuring | "Verstuur 14-dagenbrief?" [Ja/Nee] |
| Assist | AI bereidt voor, mens voert uit | Brief is opgesteld, Lisanne moet versturen |
| Manual + AI info | Mens doet het, AI geeft context | Dagvaarding: AI toont relevante info maar Lisanne doet alles |

**Best practice:** Begin met "Suggest & wait" voor alles. Na verloop van tijd kan Lisanne per actietype het autonomieniveau verhogen.

---

### 4.4 Inline Action Patterns

**Hoe AI-suggesties in de bestaande UI te integreren (zonder apart scherm):**

1. **Activity Feed Badge** — AI-acties in dezelfde tijdlijn als menselijke acties, met een AI-badge/avatar
2. **Inline Suggestion Card** — Bovenaan een tab/pagina: "AI suggereert: [actie]" met accept/reject knoppen
3. **Status Badge op Pipeline** — In de kanban/pipeline: kleur/icoon dat aangeeft of de AI een actie voorstelt
4. **Contextual Tooltip** — Hover over een dossier in de lijst: "AI: 14-dagenbrief termijn verloopt morgen"
5. **Notification Dot** — Badge op het dossier dat er een AI-suggestie klaarstaat

---

## 5. Concrete Aanbevelingen voor Luxis Incasso

### 5.1 Pipeline View — AI Integratie

De bestaande incasso pipeline (kanban met fasen) krijgt AI-indicatoren:

```
Pipeline kolom: "14-dagenbrief"
+--------------------------------+
| Dossier 2026-00042             |
| Bakkerij de Groot              |
| EUR 3.450,00                   |
| [AI] Termijn verloopt morgen   |  <-- inline AI indicator
| [Actie voorgesteld]            |  <-- badge
+--------------------------------+
```

**Per kaart in de pipeline:**
- **AI badge** als er een suggestie klaarstaat (bijv. paars/blauw sterretje)
- **Termijn indicator** met kleur (groen = op schema, oranje = bijna, rood = verlopen)
- **Volgende stap suggestie** in kleine tekst onder de kaart

---

### 5.2 Dossier Detail — AI Sidebar/Tab

Twee opties (gebaseerd op Smokeball Archie + Harvey):

**Optie A: AI Tab in dossier** (zoals Smokeball)
- Aparte tab "AI Assistent" naast Overzicht, Vorderingen, etc.
- Chat-interface specifiek voor dit dossier
- Suggesties op basis van dossier-context
- Bronvermelding naar documenten en wetsartikelen

**Optie B: AI Suggestion Banner** (inline, geen aparte tab)
- Bovenaan het dossier-detail: een inklapbare kaart met de huidige AI-suggestie
- Altijd zichtbaar, niet verstopt in een tab
- Drie knoppen: Uitvoeren / Aanpassen / Later

**Aanbeveling:** Begin met **Optie B** (suggestion banner) — het is simpeler en Lisanne hoeft niet naar een aparte tab te navigeren. Voeg later Optie A toe voor complexere interacties.

---

### 5.3 Activity Feed — AI als Team Member

Gebaseerd op Aktos en CollBox:

```
Tijdlijn in dossier:
------------------------------------------
[Lisanne] 10:32 — Factuur toegevoegd (EUR 2.100)
[AI]      10:33 — Rente berekend: EUR 42,50 (6:119a BW, 10,5%)
[AI]      10:33 — BIK berekend: EUR 315,00 (WIK-staffel)
[AI]      10:33 — Suggestie: verstuur herinnering per email
[Lisanne] 10:45 — Herinnering verstuurd per email
[AI]      10:45 — Volgende stap: wacht 14 dagen, dan aanmaning
------------------------------------------
```

**Visueel onderscheid:**
- AI-acties: andere avatar (robot/sterretje icoon), subtielere kleur (bijv. paars/blauw)
- Menselijke acties: gebruikers-avatar, standaard kleur
- Autonome AI-acties: gewoon gelogd (bijv. rente berekening)
- AI-suggesties: met actieknoppen (accepteer/wijs af)

---

### 5.4 Dashboard — AI Summary Widget

Gebaseerd op HighRadius dashboards:

```
+------------------------------------------+
| AI Overzicht                        [>]  |
|                                          |
| 3 dossiers vereisen actie                |
| 2 termijnen verlopen vandaag            |
| 1 betalingsbelofte niet nagekomen        |
|                                          |
| Suggesties:                              |
| - Dossier 042: verstuur sommatie   [>]   |
| - Dossier 038: dagvaarding overwegen [>] |
| - Dossier 051: betaling ontvangen  [>]   |
+------------------------------------------+
```

---

### 5.5 Confidence Levels — Nederlandse Labels

Voor Lisanne (niet-technisch):

| AI Confidence | Label (NL) | Kleur | Icoon | Gedrag |
|--------------|-----------|-------|-------|--------|
| > 90% | "Automatisch" | Groen | Checkmark | AI voert uit, meldt achteraf |
| 70-90% | "Aanbevolen" | Blauw | Duim omhoog | AI stelt voor, wacht op klik |
| 50-70% | "Mogelijk" | Oranje | Vraagteken | AI toont optie, Lisanne beslist |
| < 50% | "Onzeker" | Grijs | Waarschuwing | AI geeft info, geen suggestie |

---

## 6. Anti-patterns — Wat NIET Doen

| Anti-pattern | Waarom niet | Beter alternatief |
|-------------|------------|-------------------|
| Aparte "AI pagina" | Niemand navigeert ernaartoe | Inline in bestaande views |
| Technische confidence percentages | Lisanne is geen data scientist | Tekstlabels: "Aanbevolen" / "Mogelijk" |
| AI die zonder melding handelt | Geen vertrouwen, geen controle | Altijd loggen, bij twijfel vragen |
| Overmatige notificaties | Alert fatigue | Batch suggesties, 1x per dag of bij opening dossier |
| AI-jargon in de UI | Verwarrend | Gewoon Nederlands: "Volgende stap: ..." |

---

## 7. Implementatie Prioriteiten (Fasering)

### Fase 1: Foundation (bij lancering AI Agent)
- Activity feed met AI-acties (AI als team member)
- Inline suggestion banner bovenaan dossier-detail
- Pipeline kaarten met AI-badge en termijn-indicator

### Fase 2: Intelligence (na eerste feedback)
- Dashboard AI summary widget
- Confidence labels per suggestie
- Betalingsbelofte tracking (debiteur zegt "ik betaal vrijdag")

### Fase 3: Autonomie (na vertrouwen is opgebouwd)
- Configureerbaar autonomieniveau per actietype
- AI verstuurt routine-berichten automatisch (herinnering, aanmaning)
- Lisanne reviewt alleen escalaties en dagvaardingen

---

## Bronnen

### Collections Platforms
- [TrueAccord — RPA & Heartbeat ML Engine](https://blog.trueaccord.com/2025/04/leading-the-way-with-rpa-bots/)
- [Receeve — AI-native Collections Platform](https://www.receeve.com/platform/data-ai)
- [Receeve — Strategy Builder](https://www.receeve.com/collections-strategy-automation)
- [InDebted — AI Collections](https://www.indebted.co/en-us/solution/receeve/)
- [HighRadius — AI Worklist Prioritization](https://www.highradius.com/software/order-to-cash/collections-management/ai-based-worklist-prioritization/)
- [Aktos — Modern Debt Collection Software](https://www.aktos.ai/)
- [Aktos — AI for Debt Collections](https://www.aktos.ai/blog/scale-faster-with-ai-for-debt-collections)
- [CollBox — Automated Collections](https://www.getapp.com/finance-accounting-software/a/collbox/)
- [Collectly — AI Patient Collections](https://collectly.co/)

### Nederlandse/Europese Tools
- [Payt — Debiteurenbeheer](https://paytsoftware.com/)
- [Straetus — Incasso Software Centurion](https://www.straetus.nl/)
- [iFlow — Incasso Software](https://www.iflow.nl/)
- [Cash2Collect — Toekomst van Incasso](https://cash2collect.nl/toekomst-incasso-automatisering-ai/)

### Legal AI
- [Smokeball — Archie AI Matter Assistant](https://www.smokeball.com/features/archie-ai-matter-assistant)
- [Smokeball — Getting Started with Archie](https://support.smokeball.com/hc/en-us/articles/24407844681751-Getting-Started-with-Archie-the-Smokeball-AI-Assistant)
- [Harvey AI — Unified Experience](https://www.harvey.ai/blog/a-more-unified-harvey-experience)
- [CoCounsel — AI Legal Assistant](https://topaitools.com/tools/casetext)
- [PracticePanther — Legal Software](https://www.practicepanther.com/)

### UX Design Patterns
- [Agentic Design — Confidence Visualization Patterns](https://agentic-design.ai/patterns/ui-ux-patterns/confidence-visualization-patterns)
- [AI UX Playground — Confidence Score Pattern](https://www.aiuxplayground.com/pattern/confidence-score)
- [Smashing Magazine — Designing for Agentic AI](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)
- [ShapeofAI — Inline Action Pattern](https://www.shapeof.ai/patterns/inline-action)
- [UX Magazine — Agentic UX Patterns](https://uxmag.medium.com/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents-f7682bff44af)
- [Spyro Soft — Online Debt Collector UX Case Study](https://spyro-soft.com/blog/fintech/online-debt-collector-designing-better-ux-for-financial-products)
- [AI UX Patterns for Design Systems](https://thedesignsystem.guide/blog/ai-ux-patterns-for-design-systems-(part-1))
- [GenAI UX Patterns (20+)](https://uxdesign.cc/20-genai-ux-patterns-examples-and-implementation-tactics-5b1868b7d4a1)

### Market Data
- [AI Debt Collection Market — Expected to reach $15.9B by 2034](https://www.sedric.ai/arm-resources/ai-in-collections-transforming-debt-recovery-in-2025)
- [Debt Collection Software Market — $4.8B in 2025, $11.3B by 2033](https://www.aktos.ai/blog/best-debt-collection-software-for-2025)
