# Audit S172 — Code ↔ Roadmap inventaris (5 juli 2026)

**Methode:** goedkope structuur-scan (grep/glob) over de hele codebase + gericht diep lezen
bij vermoede mismatches + verificatie in de productie-database (via SSH). Elke bevinding
hieronder is tegen de code of de prod-DB gecheckt, niet aangenomen.
**Opdracht:** `docs/sessions/PROMPT-AUDIT-code-vs-roadmap.md`.

---

## 1. Feature-inventaris — wat er ÉCHT in de code zit

Harde tellingen (5 juli 2026): **19 backend-modules, 28 routerbestanden, ±287 endpoints,
42 modelklassen, 26 frontend-pagina's, 36 hooks.** (Roadmap zegt "234 endpoints, 25 routers,
35 models, 24 pagina's" — de tellingen in de roadmap-kop lopen structureel achter; niet erg,
maar illustreert de drift.)

| Module (backend) | Wat het kan (één regel) | Frontend |
|---|---|---|
| `auth` (12 endp.) | Login/refresh/logout, reset+wijzig wachtwoord (trekt tokens in), account-lockout, users; JWT 15 min + rotatie | login, reset-password, setup |
| `relations` (19) | Contacten CRUD/zoeken/sorteren, persoon↔bedrijf-links, facturatieprofiel, rente/BIK-defaults per klant, **geversioneerde AV (`ContactTerms`)**, KYC/WWFT (UBO, PEP, risico) | /relaties |
| `cases` (20+) | Dossiers CRUD + wizard, partijen, activiteiten, status-workflow, bestanden, unified tijdlijn, conflict-check, **afwikkelflow (S170)** | /zaken (12 tabs) |
| `collections` (22) | Vorderingen, samengestelde rente 6:119/119a, WIK/BIK, betalingen met 6:44-toerekening, betaalregelingen, griffierecht 2026, verjaring, nakosten | tabs in dossier |
| `incasso` (19) | Pipeline 21 stappen, batch brief+mail, auto-advance, verweer-tracking, staphistorie, AI-concept per stap | /incasso |
| `workflow` (19) | Taken, statussen+transities, scheduler (deadlines, verjaring, overdue, talm-job), agenda-events | /taken, /agenda |
| `invoices` (19) | Facturen + lifecycle, PDF, credit-nota's, BTW per regel, provisie/BIK-regels, voorschotnota, betaal-tracking, verzenden via Outlook | /facturen |
| `time_entries` (7) | Uren CRUD, timer (6-min), onbefactureerd, week/dag | /uren + timer |
| `documents` (25) | DOCX/PDF-generatie, ManagedTemplates (DB + disk-fallback), template-editor, merge fields, preview | /documenten |
| `email` (25) | Outlook/Graph OAuth, 5-min sync, auto-koppeling (dossiernr/thread), bijlagen, branded compose, Ongesorteerd + **suggesties (FEAT-MAIL-01: gebouwd!)**, BaseNet-archief (6393 mails) | /correspondentie |
| `ai_agent` (54!) | Classificatie (8 categorieën), intake-agent, follow-up advisor, betalingsmatching, **3 draft-services**, verweer-bibliotheek (5), slim-leren (131 kandidaten), orchestrator (auto-draft UIT), sentiment, betalingsbelofte, 34 AI-tools | /intake, /followup, /betalingen, AI-leren |
| `trust_funds` (14) | Derdengelden, vier-ogen, storno, verrekening (Voda 6.19), SEPA- en NOvA-exports, ongekoppeld-tab | /derdengelden |
| `notifications` (5) | Meldingen, snooze, tab-context-links | bel-icoon |
| `dashboard` (3+) | KPI's, actie-widget, rapportages met drill-down | /, /rapportages |
| `settings` (2) | Tenant, kantoorgegevens, modules | /instellingen (9 tabs) |
| `exact_online` (9) | OAuth + factuur-sync — gebouwd, **0 actieve connecties** | instellingen-tab |
| `products` (6) | Artikel-catalogus (30 BaseNet-artikelen), grootboek per regel | instellingen-tab |
| `search` (1) | Global search Ctrl+K over zaken/relaties/documenten/facturen/e-mails | palette |
| `calendar` (6) | Agenda-events CRUD + Outlook-agendasync | /agenda |

**Oordeel:** dit is een compleet PMS. De breedte klopt met wat de roadmap claimt; wat NIET
klopt is de samenhang van de AI-laag (zie §4) en een reeks stale roadmap-regels (zie §2/§3).

---

## 2. "Al gebouwd maar vergeten"

| # | Wat | Bewijs | Roadmap zegt |
|---|---|---|---|
| 2.1 | **`ContactTerms` geversioneerde AV** (aanleiding van deze audit) | `relations/models.py`, `automation_service.py:379-416` | Sinds S171 gecorrigeerd ✅ |
| 2.2 | **FEAT-MAIL-01 mail-suggesties** — suggest-endpoint + confidence-sortering bestaan | `email/sync_router.py:162,384` + `sync_service.py:1193` | "🟢 Gepland S148" — **stale, is gebouwd** |
| 2.3 | **Zes 'root-documenten' verplaatst naar `docs/`** — FEATURE-INVENTORY, DECISIONS, UX-REVIEW, UX-VERBETERPLAN, BUGS-EN-VERBETERPUNTEN, PROMPT-TEMPLATES-IN-WORKFLOW | commit `5fbd0cb` | Roadmap §Projectdocumenten + CLAUDE.md `@DECISIONS.md` wijzen naar de root — **dode links**. NB: `docs/FEATURE-INVENTORY.md` is een markt-checklist ("wat zou een PMS moeten kunnen"), géén inventaris van wat er ís — dit document (§1) vult dat gat |
| 2.4 | **KYC/WWFT-module** — volledig (identificatie, UBO, PEP/sanctie, risico, review-scheduling) | `relations/kyc_service.py`, `kyc_router.py` | Alleen in oude lijst; komt in geen enkel actueel plan/flow voor. Dormant maar af |
| 2.5 | **Sentiment-analyse + betalingsbelofte-extractie** (AUDIT-28/18) | `ai_agent/service.py` | Gebouwd; niemand verwijst er nog naar |
| 2.6 | **Exact Online-module** — OAuth + sync compleet | `exact_online/` (9 endpoints) | Bekend, wacht bewust op activatie (FIN-4/CONN-13) |
| 2.7 | **Orchestrator/event-bus** — event-systeem klaar, auto-draft bewust uit | `ai_agent/events.py`, `orchestrator.py:78` | Klopt met AI-AGENT-besluit S160, maar staat nergens als "bestaat, staat uit" |

## 3. "Beloofd maar afwezig / half"

| # | Claim | Werkelijkheid | Bewijs |
|---|---|---|---|
| 3.1 | Tech-stack: **"Queue: Celery + Redis"** (CLAUDE.md + roadmap + DECISIONS) | Celery wordt **nergens** gebruikt; `events.py` zegt letterlijk "no Redis/Celery"; alle scheduling = APScheduler. Celery is een dode dependency in `pyproject.toml` | `events.py:1-5`, `workflow/scheduler.py` |
| 3.2 | Tech-stack: "Nginx + Let's Encrypt", "python-jose", "Sentry (~26/mnd)" | Caddy (niet Nginx), PyJWT (jose vervangen S90), Sentry-DSN nog leeg (S159-actiepunt) | Caddyfile, `pyproject.toml`, prod `.env` |
| 3.3 | **DF122-04 mailsjablonen-editor** ("Sessie 124") | Nooit gebouwd: de ±25 e-mailsjablonen zitten hardcoded in `email/incasso_templates.py` (1734 regels Python). Lisanne kan ze niet zelf aanpassen | `incasso_templates.py` |
| 3.4 | **AUDIT-H25 modules_enabled server-side** | Nog steeds alleen validatie bij opslaan; geen endpoint-enforcement. Correct als "open" gemarkeerd — maar het is de laatste open HIGH uit juni | `settings/service.py:35-37` |
| 3.5 | **K1-plan (nieuw `knowledge_documents`-systeem)** in roadmap-kennisbanksectie | Achterhaald door S171 (ContactTerms) — sectie zelf zegt dat al, maar het K1/K2/K3-plan eronder staat er nog volledig in en leest als actueel plan | roadmap r.1348-1358 |
| 3.6 | "AI raadpleegt volledige dossiercontext" (AI-UX-13 ✅) | Waar voor het **verweer-pad**; NIET waar voor `/api/ai/draft` (unified) — die leest géén AV, géén geleerde voorbeelden, géén verweer-bibliotheek (zie §4.1) | `unified_draft_service.py` |

## 4. Parallelle / dubbele systemen

### 4.1 DRIE AI-conceptservices met drie verschillende geheugens (KERNBEVINDING)

| Pad | Trigger | AV (voorwaarden) | Geleerde voorbeelden | Verweer-bibliotheek |
|---|---|---|---|---|
| `incasso/automation_service.py` | Pipeline-stap "Concept genereren" + verweer-flow | ✅ geversioneerd (`ContactTerms`, fallback legacy) | ✅ | ✅ |
| `ai_agent/draft_service.py` | Orchestrator/classificatie-hook, client-update | ⚠️ **alleen legacy `Contact.terms_file_path` (leeg sinds S168-wipe)** | ✅ | ✅ |
| `ai_agent/unified_draft_service.py` | `/api/ai/draft` — de compose-dialog (next_step / reply / free) | ❌ **geen** | ❌ **geen** | ❌ **geen** |

Gevolg: **welke kennis de AI heeft hangt af van welke knop Lisanne toevallig klikt.**
De kennisbank (K0/K1) waar alles op wacht, voedt maar één van de drie paden volledig.
Dit is waarom "bouwen en bouwen" niet als béter voelt: de nieuwe kennis-laag klikt niet
in alle bestaande paden. Fix-richting: één gedeelde context-bouwer (AV + geleerde
voorbeelden + bibliotheek) die alle drie de services aanroepen — daarna is consolidatie
naar minder services een aparte, latere opruimklus.

### 4.2 Vier sjabloon-opslagplaatsen
1. `email/incasso_templates.py` — ±25 hardcoded Python/HTML e-mailsjablonen (BaseNet-stijl);
2. `managed_templates` (DB + disk-fallback) — DOCX-sjablonen met editor-UI;
3. `response_templates` (DB, 6 rijen) — antwoordsjablonen van de classificatie-flow;
4. `incasso_pipeline_steps.email_subject/body_template(_html)` — sjabloontekst per pipeline-stap.

Vier plekken met deels overlappende inhoud (de disclaimer-bug DF138-15 moest al in 3 plekken
tegelijk gefixt worden). Eén bron per sjabloonsoort is de richting (DF122-04 zou 1+4 naar DB brengen).

### 4.3 Twee workflow-systemen (bekend, half gekoppeld)
`case.status` (workflow-statussen + transities) naast `incasso_step_id` (pipeline). Bewuste
keuze (H11-follow-up), maar de koppeling is nog steeds eenrichting/handmatig. Blijft de
grootste bron van "waarom staat dit dossier nog open"-verwarring.

### 4.4 Klein spul
- `kimi_client.py` heet nog zo maar is 100% Claude (S159) — hernoemen bij gelegenheid (`ai_client.py`), scheelt elke sessie een verwarrings-moment.
- `Contact.terms_file_path`-kolom + het dode pad in `draft_service` — verwijderen na 4.1-fix.
- Roadmap-doc-tabel + CLAUDE.md `@DECISIONS.md`-verwijzing wijzen naar verplaatste bestanden.

---

## 5. Verweer-type-woordenschat — analyse van de 110 "Overig"

**Bron:** alle 110 `overig`-kandidaten uit de prod-DB gedumpt en gelezen (5 juli 2026).

### 5.a Waarom 93% in "Overig" valt (mechanisme, niet inhoud)
Het type wordt toegekend via **tekst-gelijkenis (difflib) met de 5 statische bibliotheek-teksten**
(`learned_answers.py:501`, drempel 0.45). Dat kan principieel niet werken:
1. Een nieuw verweer-type heeft per definitie geen voorbeeldtekst om op te lijken.
2. Zelfs bestáánde types missen: de art. 9.3-tekst verschilt per opdrachtgever
   (Incassocenter/Invorderingsbedrijf/Collect 1-varianten) → gelijkenis zakt onder 0.45 en
   tientallen zuivere 9.3-afwikkelingen belanden in "Overig".

### 5.b Vervuiling in de wachtrij (±20 van de 110 zijn geen leerbare antwoorden)
- **±10 kandidaten zijn tekst van de DEBITEUR, niet van Lisanne** — bij Re:/Fwd:-mails knipt
  `extract_rebuttal` soms de geciteerde debiteur-tekst eruit (geverifieerd in prod: alle 8
  gecheckte gevallen zijn outbound van incasso@kestinglegal.nl met Fwd:/Re:-subject; de
  citaat-markers ontbreken in BaseNet-.eml-platte tekst). Voorbeelden: `f37aa219`
  ("...wil ik een betalingsregeling aanvragen"), `ff8bb5a8`, `87b26cde`, `5885d6db`,
  `f28d815a`, `32e79764`, `71de1e00`, `e0076e1e`, `a9dd1b36`, `ae7d45c9`.
  **Risico:** keurt Lisanne er per ongeluk één goed, dan leert de AI het argument van de
  tegenpartij als modelantwoord.
- **±10 zijn lege intro-fragmenten** ("Naar aanleiding van uw laatste bericht bericht ik u
  als volgt.") — extractie knipte de inhoud weg. Voorbeelden: `3f9cd561`, `bcb32fa7`,
  `56a53f26`, `a94c5f8e`, `860cb526`.
- **Advies:** deze ±20 bulk-afwijzen (knop bestaat) vóór Lisanne verder beoordeelt, en twee
  kleine extractie-guards toevoegen (Fwd:-subject → skip; substantie-check strenger).

### 5.c Voorgestelde woordenschat (13 types, uit de echte data)
Indicatieve aantallen over de ±90 échte weerleggingen:

| Type (key) | Betekenis | ± |
|---|---|---|
| `afwikkeling_intrekking` | Art. 9.3/20.4-afwikkeling na intrekken/zelf regelen/frustreren van de opdracht (alle opdrachtgever-varianten; vervangt de 2 bestaande 9.3/20.4-keys) | 28 |
| `verlenging_opzegging` | Stilzwijgende verlenging; opzegging te laat / niet aangetoond / niet aangetekend | 14 |
| `betwisting_ongemotiveerd` | Kale of AI-gegenereerde betwisting; stelplicht/bewijslast bij debiteur teruggelegd | 12 |
| `reeds_betaald_verrekening` | "Al betaald / gecrediteerd / verrekend" → reconstructie facturenhistorie | 10 |
| `consumentenbescherming_b2b` | Beroep op herroeping/bedenktijd/14-dagenbrief/reflexwerking → afgewezen want zakelijk | 8 |
| `betalingsregeling_schikking` | Regelingsverzoek, tegenvoorstel, VSO, finale kwijting (uitkomst-cluster, geen verweer) | 7 |
| `derde_partij` | Advocaat/verzekeraar/rechtsbijstand neemt over; doorverwijzing | 7 |
| `klacht_dienstverlening` | "Geen resultaat/slechte service" → inspanningsverplichting, klacht ≠ opschorting | 6 |
| `ncnp_gerechtelijke_fase` | NCNP vervalt in gerechtelijke fase (bestaand type, blijft) | 5 |
| `vertegenwoordiging` | "Medewerker was niet bevoegd" → art. 3:61 lid 2 BW / gewekt vertrouwen | 4 |
| `opschorting_tegenvordering` | Opschorting/wanprestatie/6:74 BW/schuldeisersverzuim | 4 |
| `av_toepasselijkheid` | "Voorwaarden nooit ontvangen" → terhandstelling 6:233/234 BW, getekend akkoord | 3 |
| `kosten_rente_hoogte` | Hoogte BIK/rente/commissie betwist → staffel/contract uitgelegd | 3 |
| `overig` | Restbak (hoort na dit alles < 10% te zijn) | rest |

Opvallend afwezig in de data: **verjaring** (0×) — niet toevoegen tot hij echt voorkomt.

### 5.d Toewijzings-mechanisme (het echte werk, klein)
1. Woordenschat als constante lijst in code (labels NL, keys EN) + dropdown bij goedkeuren
   (backend accepteert `defense_type` al — alleen UI-lijst nodig).
2. Deterministische keyword-pre-labeling voor de wachtrij-groepering (bijv. "9.3"/"20.4" →
   afwikkeling; "stilzwijgende verlenging"/"opzegtermijn" → verlenging; "herroeping"/
   "bedenktijd"/"consument" → consumentenbescherming_b2b; "3:61"/"bevoegd" →
   vertegenwoordiging; enz.). Geen AI-kosten, transparant, past bij de geen-RAG-keuze.
3. Eenmalige her-labeling van de 110 met die regels (data-only script).
4. `get_learned_examples` spreidt al over types — werkt daarna vanzelf beter.

---

## 6. Herziene roadmap — voorstel (wijzigingen, geen herschrijving)

1. **Kop-tellingen** actualiseren of vaag maken ("~19 modules, ~290 endpoints") — exacte
   getallen in de kop verouderen per sessie en wekken schijnprecisie.
2. **Tech-stack-blok fixen** (roadmap + CLAUDE.md + DECISIONS): Celery eruit (+ dependency
   verwijderen), Nginx→Caddy, python-jose→PyJWT, Sentry = "nog niet actief".
3. **Projectdocumenten-tabel**: paden naar `docs/…` corrigeren; noteren dat
   `FEATURE-INVENTORY.md` de markt-checklist is en `docs/audit/inventaris-2026-07-05.md`
   de feitelijke inventaris.
4. **FEAT-MAIL-01** op ✅ zetten (gebouwd; regel zegt "Gepland S148").
5. **Kennisbank-sectie**: het oude K1-bouwplan (knowledge_documents) inkorten tot één regel
   "achterhaald, zie S171"; K2-meting blijft.
6. **Nieuwe prioriteitenlijst AI-samenhang** (vervangt losse geparkeerde items):
   a. Gedeelde context-bouwer voor de 3 draft-services (AV + geleerd + bibliotheek) —
      lost ook het geparkeerde "draft_service op ContactTerms" op;
   b. Verweer-woordenschat + pre-labeling + wachtrij-schoonmaak (§5);
   c. Daarna pas consolidatie 3→minder draft-services / sjablonen naar DB (DF122-04).
7. **H25** expliciet als "laatste open audit-HIGH" markeren (of bewust naar backlog bij
   1-tenant-realiteit).
8. Klein: `kimi_client.py` hernoemen, `Contact.terms_file_path` deprecatie-pad noteren.

---

*Auditor: Fable (S172). Elke rij hierboven is geverifieerd tegen code (bestand:regel) of
prod-DB (query 5 juli 2026). Geen code gewijzigd in deze sessie.*
