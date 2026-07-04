# Onderzoek: Knowledge Base & Learning Loop (S169 — 4 juli 2026, Fable 5)

**Vraag uit de roadmap:** de AI-assistent heeft een kennisbank nodig (algemene voorwaarden,
wettelijke regels, richtlijnen) en een feedback-loop zodat hij leert van Lisanne's
correcties. Vereist: onderzoekssessie (hoe doen Harvey AI, CoCounsel, Clio dit?) →
architectuurkeuze (RAG vs structured prompting) → kennisbank-UI → feedback-mechanisme.

---

## 1. Hoe doen de grote spelers het?

### Harvey AI (BigLaw, enterprise)
- **Grounding:** agentic RAG over 150+ juridische bronnen + kantoor-documenten (Vault,
  iManage); elke zin gedekt door een citeerbare bron. Redeneer-gestuurde retrieval
  (ReAct-loop), multi-model met een "partner"-model dat werk delegeert.
- **Leren:** géén model-hertraining op feedback. De loop = mens-evaluatie (juristen
  beoordelen zij-aan-zij op 7-puntsschaal), eigen benchmarks/rubrics per taak, en
  **iteratieve prompt-verbetering**. Juristen zitten ín het bouwteam.
- Bron: [ZenML: Harvey RAG](https://www.zenml.io/llmops-database/enterprise-grade-rag-systems-for-legal-ai-platform) ·
  [ZenML: Harvey evaluatie](https://www.zenml.io/llmops-database/building-and-evaluating-legal-ai-at-scale-with-domain-expert-integration) ·
  [OpenAI over Harvey](https://openai.com/index/harvey/) ·
  [Harvey agentic search](https://www.harvey.ai/blog/how-agentic-search-unlocks-legal-research-intelligence)

### CoCounsel (Thomson Reuters)
- **Grounding:** redeneert vanuit Westlaw/Practical Law + de eigen kennis van het kantoor,
  met **dezelfde taxonomie-, citatie- en metadata-discipline** op klantcontent als op
  autoritatieve bronnen, binnen een duidelijk begrensde governance-omgeving.
- Bron: [CoCounsel Legal](https://legal.thomsonreuters.com/en/products/cocounsel-legal) ·
  [TR Institute: reimagined](https://www.thomsonreuters.com/en-us/posts/innovation/cocounsel-legal-reimagined/) ·
  [TR: drafting](https://legal.thomsonreuters.com/blog/from-assistance-to-orchestration-how-cocounsel-legal-is-changing-the-drafting-game/)

### Clio Manage AI (vh. Clio Duo) — dichtstbijzijnde analogie voor Luxis
- AI **ingebouwd in het praktijkmanagementsysteem**, gebruikt **uitsluitend de eigen
  kantoordata**, en houdt de gebruiker in controle: elke actie is review + approval.
  Deadline-extractie toont bron-document zij-aan-zij ter verificatie. $39/gebruiker/mnd.
- Geen publiek bewijs van een "lerende" loop verder dan menselijke goedkeuring.
- Bron: [Clio Manage AI](https://www.clio.com/blog/manage-ai/) ·
  [Clio AI features](https://www.clio.com/features/legal-ai-software/) ·
  [Lawyerist review](https://lawyerist.com/reviews/artificial-intelligence-in-law-firms/clio-duo-review-artificial-intelligence-for-lawyers/)

### Architectuur-consensus (klein, begrensd corpus)
- Kennisbank die past in honderden pagina's en niet dagelijks wijzigt → **gestructureerde
  prompt-injectie, géén vector-database**. RAG wordt pas structureel nodig bij een
  feitelijk onbegrensde datalake.
  Bron: [Regal: context engineering](https://www.regal.ai/blog/context-engineering-for-ai-agents) ·
  [Ahoi Kapptn: long prompt → RAG](https://ahoikapptn.com/en/blog/from-long-prompt-to-rag-how-to-build-robust-ai-agents-with-your-knowledge-base) ·
  [arXiv 2502.12462](https://arxiv.org/html/2502.12462v1)
- **3–5 zorgvuldig gekozen voorbeelden geven 80–90% van de waarde van fine-tuning**;
  feedback-als-voorbeelden-in-de-prompt ("memory-assisted prompting") is een gevalideerd
  productiepatroon.
  Bron: [Few-shot i.p.v. fine-tuning](https://dev.to/superorange0707/stop-fine-tuning-everything-inject-knowledge-with-few-shot-in-context-learning-40gb) ·
  [arXiv 2201.06009: memory-assisted prompt editing](https://arxiv.org/pdf/2201.06009)

## 2. Hoofdconclusie

**Niemand — ook Harvey niet — laat het model "vanzelf leren" van correcties.** De
industrie-standaard is overal dezelfde vorm: (1) grounding in gecureerde eigen bronnen,
(2) een mens die goedkeurt, (3) gecureerde voorbeelden in de prompt, (4) meten.
**Luxis doet die vorm al**: defense_library (few-shot), verweer-bibliotheek (door Lisanne
goedgekeurde, geanonimiseerde voorbeelden), edit-rate-dashboard (mens-evaluatie), besluit
S160 (assistent, geen autonomie). Het besluit van S160/S167 wordt door dit onderzoek dus
**gevalideerd, niet vervangen.**

Wat ontbreekt is niet "slimmer leren", maar **gegronde bronkennis**: de AI kent de échte
algemene voorwaarden van de 7 vaste opdrachtgevers niet (art. 9.3, art. 20.4, NCNP — de
verweer-typen verwijzen er nú al naar zonder de tekst te hebben).

## 3. Architectuurkeuze

**Deterministische selectieve prompt-injectie. Geen RAG, geen vector-database, geen
embeddings.**

Waarom:
- Het corpus is klein en begrensd (7 opdrachtgevers × voorwaarden + richtlijnen).
- De selectiesleutels zijn **structureel, niet semantisch**: dossier → opdrachtgever →
  diens voorwaarden; classificatie-categorie/verweer-type → relevant artikel. Daar is
  geen zoekmachine voor nodig.
- AVG: geen externe verwerking; voorwaarden zijn bovendien contractteksten, geen
  persoonsgegevens.
- Zelfde patroon als de bestaande `build_learned_examples_text` (alleen verweer-stap,
  begrensd aantal tekens) — klein diff, bewezen injectiepunt.
- **Upgrade-pad** als het corpus ooit echt groeit: pgvector (lokaal in Postgres, AVG-oké).
  Nu niet bouwen.

## 4. Premortem (verplicht bij architectuurkeuze) — uitkomst

Volledig rapport: `docs/research/premortem-report-2026-07-04.html` (+ transcript `.md`).
7 faalscenario's geanalyseerd. Kern:

- **Meest waarschijnlijke faal:** de menselijke bottleneck. Twee scenario's (kennisbank
  blijft leeg; review-loop verstopt) delen dezelfde wortel: het plan hangt op werk van
  Lisanne zonder deadline — en het signaal staat nú al op rood (130 kandidaten wachten
  ±3 weken).
- **Gevaarlijkste faal:** verouderde/verkeerde voorwaarden in de kennisbank → AI citeert
  het verkeerde artikel in een echte zaak → vertrouwensbreuk die álle AI-features raakt.
- **Verborgen aanname:** "als wij het bouwen, komen content en review vanzelf" + "meer
  juridische context = betere concepten" (terwijl het kwaliteitsanker Lisanne's eigen
  stijl-voorbeelden zijn).
- **Belangrijkste planwijzigingen:** content- en engagement-gate vóór de bouw (K0),
  versie-metadata verplicht, injectie-cap in code, met/zonder-flag voor meting,
  **per-voorbeeld attributie geschrapt** (statistisch betekenisloos op deze schaal),
  autonomie-grendel als test.

## 5. Gefaseerd plan (herzien ná premortem)

### K0 — Gate: content + engagement (geen bouwwerk)
1. **Voorwaarden verzamelen:** eerst zoeken in de geïmporteerde BaseNet-mails/bijlagen
   (6.393 mails); wat ontbreekt vraagt Arsalan bij Lisanne op als PDF (één mail).
   Per document vastleggen: opdrachtgever, versiedatum, welke artikelen relevant.
   Lisanne's rol beperkt tot valideren (minuten, geen uren).
2. **Lisanne's eerste review-ronde gebeurt** (gepland: deze week, dashboard is er klaar
   voor sinds S169).
**K1 start pas als beide er zijn.** Staat één van beide na 14 dagen op nul → eerst dát
gesprek, niet bouwen.

### K1 — Kennisbank (1 bouwsessie, Opus)
- Tabel `knowledge_documents`: tenant, optioneel contact/opdrachtgever-koppeling,
  verweer-type/categorie-koppeling, titel, tekst, **versiedatum + geldig-vanaf**, bron,
  actief-vlag.
- Beheer-UI in Instellingen (nieuw tabblad "Kennisbank"): toevoegen/bewerken/deactiveren.
- Injectie in de verweer-prompt: zelfde patroon als learned examples; **harde cap
  (~1.500 tekens) in code**; citaat altijd mét versiedatum.
- **Meting vanaf dag één:** vlag per draft "met/zonder kennisbank-injectie" + log van
  injectiegrootte, zodat de edit-rate vóór/ná en mét/zónder vergelijkbaar is.

### K2 — Leer-loop verbreden + meten (na Lisanne's eerste ronde, Opus)
- `LEARNABLE_CATEGORIES` uitbreiden (kandidaat: betalingsregeling-reacties) — pas na
  haar kalibratie-oordeel.
- Meting: **geaggregeerde** edit-rate-trend + wachtrij-gezondheid (instroom vs beoordeeld
  per week). GEEN per-voorbeeld attributie (premortem: schijnverbanden bij deze n).
- F7 backfill-perf hoort hier (cutoff voor al-verwerkte mails).
- **Autonomie-grendel:** test/assert dat geen verzendpad bestaat zonder gebruikersklik
  (S160 in code verankerd).

### K3 — Patroonherkenning per debiteur-type
**Geparkeerd.** Te weinig data (n = tientallen/maand), en het duwt richting de autonome
agent (S160). Herzien op z'n vroegst bij kantoor 2+ of >500 verzonden concepten.

### Product-noot (generalisatie)
Kesting-specifieke begrippen (verweer-typen, artikelnummers) horen in **data**, niet
dieper in code/prompts. K1 modelleert ze daarom aan de kennisbank-kant als tenant-data.
Heuristieken blijven bewust Kesting-afgesteld tot er een tweede kantoor is (YAGNI), maar
de teller "hardcoded Kesting-begrippen in code" mag tijdens K1 niet stijgen.

## 6. Open vragen voor Arsalan/Lisanne
1. Zijn de actuele algemene voorwaarden van de 7 vaste opdrachtgevers beschikbaar
   (PDF/mail)? Wie levert wat ontbreekt?
2. Wil Lisanne per voorwaarden-document 5 minuten valideren (versiedatum + relevante
   artikelen), als wij alles voorbereiden?
3. Akkoord met schrappen van per-voorbeeld attributie uit de roadmap-ambitie
   "meetbaarheid" (vervangen door geaggregeerde trend + wachtrij-gezondheid)?
