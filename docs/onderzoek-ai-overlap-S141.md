# Onderzoek demo-feedback Lisanne — Sessie 141

**Datum:** 2026-05-14
**Type:** Onderzoek-only (geen code-wijzigingen)
**Bron:** 7 punten uit Lisanne's demo-feedback sessie 140

---

## Executive Summary

Vier van de zeven punten zijn **één onderliggend probleem**: AI-acties, notificaties, concept-klaar-status en email-updates zijn versnipperd over de UI in plaats van centraal op het dossier. Lisanne wil één plek per dossier waar staat: "Er is een update, dit is de volgende stap, ik kan een concept maken." Dat is er nu niet.

De andere drie punten zijn losse bugs/UX-issues:
- **Tijdstempels** — overal datum-only, helper-functie ontbreekt
- **Mail-sync** — sync draait, maar 60% emails wordt niet auto-gekoppeld (duplicate contact-relaties)
- **Status pipeline** — 45 van 48 dossiers hebben geen `incasso_step_id`, pipeline-advance werkt niet voor de meesten

**Aanbevolen volgorde:**
1. **Eerst:** Punt 4+5+6+7 samenvoegen tot één unified Actie-Feed op dossier (M)
2. **Daarna:** Punt 3 pipeline-advance bug fixen (S-M)
3. **Daarna:** Punt 2 auto-koppeling verbeteren (S)
4. **Tussendoor (parallel):** Punt 1 tijdstempels overal toevoegen (S)

---

## Punt 1 — Tijdstempels (datum + tijd)

**Lisanne:** "Overal alleen datum, ik wil ook HH:MM zien."

### Bevindingen

Helper-bestand: `frontend/src/lib/utils.ts`

| Bestaande functie | Output | Heeft tijd? |
|---|---|---|
| `formatDate` | "17 februari 2026" | Nee |
| `formatDateShort` | "17-02-2026" | Nee |
| `formatRelativeTime` | "5 min geleden" / "17 feb" | Hybride |
| `formatDateTime` | **bestaat niet** | — |

**7 componenten** tonen datum zonder tijd, terwijl het backend-veld (`email_date`, `created_at`, `entered_at`) wél een timestamp bevat:

| Component | File | Veld |
|---|---|---|
| Correspondentie e-maillijst | `CorrespondentieTab.tsx:555` | `email.email_date` |
| Correspondentie e-maildetail | `CorrespondentieTab.tsx:135` | `email.email_date` |
| Dossier-header (geopend) | `DossierHeader.tsx:228` | `zaak.date_opened` |
| Dossier-sidebar | `DossierSidebar.tsx:110` | `zaak.date_opened` |
| Dashboard recente activiteit | `dashboard/page.tsx:402` | `activity.created_at` |
| Details-tab activiteit-feed | `DetailsTab.tsx:875` | `activity.created_at` |
| Staphistorie | `StaphistorieTab.tsx:113,118` | `entered_at`, `exited_at` |

**Curiosum:** `StaphistorieTab` heeft een **lokale** formatter (regel 23-30) met `hour`+`minute` opties die wél tijd toont. Niet hergebruikt elders.

### Voorgestelde fix — **S (1-2u)**

1. Voeg `formatDateTime(date, "short" | "long")` toe aan `utils.ts`
2. Lokale formatter in `StaphistorieTab` vervangen door centrale helper
3. Vervang `formatDate`/`formatDateShort` in 6 andere componenten door `formatDateTime`
4. Visuele check in browser per scherm

**Risico:** laag. Pure UI-wijziging, geen backend-impact.

---

## Punt 2 — Mail-sync werkt niet

**Lisanne:** "Mail-sync doet het niet meer."

### Bevindingen (productie-diagnose)

**Sync DRAAIT** wel — productie-logs tonen elke 5 min een succesvolle run:

```
10:10:48 Sync klaar voor seidony@kestinglegal.nl: 45 opgehaald, 0 nieuw, 0 gekoppeld, 45 overgeslagen
10:10:49 Sync klaar voor seidony@kestinglegal.nl: 21 opgehaald, 0 nieuw, 0 gekoppeld, 21 overgeslagen
10:10:49 Scheduler: email auto-sync klaar — 2 accounts, 0 nieuw, 0 gekoppeld
```

**Token-status:** OK
- Outlook-account `seidony@kestinglegal.nl`: token expiry `2026-05-14 10:16` (auto-refresh werkt)
- IMAP-account: expiry `2099-01-01` (geen issue)
- Last sync: 4 min geleden — nog steeds actief

**Database-stand `synced_emails`:**
- 143 totaal
- 87 unlinked (**60%**)
- 98 inbound
- Latest mail: vandaag 09:49

**Echte oorzaak — auto-koppeling faalt:**

Productie-logs herhalen tientallen keren:
```
INFO: Meerdere dossiers (3) gevonden voor ['kesting@kestinglegal.nl'] — niet auto-gekoppeld
INFO: Dossiernummer ['2026-00007'] gevonden in email maar dossier bestaat niet — niet doorvallen
```

**Wat er gebeurt:**
1. Sync haalt emails op ✅
2. Auto-koppeling probeert match op:
   - Dossiernummer in onderwerp/body → faalt als dossier niet bestaat
   - Email-adres → `kesting@kestinglegal.nl` zit aan **3 dossiers** gekoppeld → ambiguïteit → niet auto-gekoppeld
3. Email belandt in "Ongesorteerd" wachtrij (M6)
4. Lisanne ziet niks nieuws onder haar dossiers en denkt: "sync werkt niet"

### Voorgestelde fix

**Optie A — Surface "Ongesorteerd" prominenter — S (2-4u)**
- Badge in sidebar tonen met aantal ongesorteerde mails
- Eerste landing-actie na inlog: ongesorteerd reviewen
- Lisanne ziet sync wél, maar onder de juiste plek

**Optie B — Slimmere auto-koppeling — M (4-8u)**
- Bij meerdere kandidaat-dossiers: niet weigeren, maar gokken op meest-recente of meest-actieve
- Tonen als "voorgestelde koppeling" met 1-klik confirm/reject
- Vermijdt false-positives, maakt 60% unlinked → minder dan 10%

**Optie C — Beide combineren — M (1 sessie)**

**Aanbevolen:** Optie C. Optie A is een quick-win, B lost echte probleem op.

**Risico:** Optie B kan false-positives veroorzaken → klant ziet email van wederpartij A onder dossier van klant B. Mitigatie: alleen suggereren, niet auto-koppelen.

---

## Punt 3 — Status blijft op 1e sommatie

**Lisanne:** "Na versturen 1e sommatie blijft status hangen op 1e sommatie. Pop-up komt wel, maar status verandert niet."

### Bevindingen

**Database-stand (productie):**

| Metric | Waarde |
|---|---|
| Totaal dossiers | 48 |
| Met `incasso_step_id` (= pipeline-stap ingesteld) | **3** |
| Zonder pipeline-stap | **45 (94%)** |
| Status `active` | 0 |

**Conclusie:** Het probleem is dieper dan "status update faalt" — bij 94% van de dossiers is de pipeline-stap überhaupt nooit ingesteld of weer leeggemaakt.

### Code-analyse

**Pop-up flow:**
1. `frontend/src/app/(dashboard)/incasso/page.tsx:1083-1114` — `handleExecuteBatch()` toont preview-dialog
2. Pop-up roept `useBatchExecute()` → `POST /api/incasso/batch` met `action="generate_document"`, `send_email=true`
3. Backend `backend/app/incasso/service.py:980-1234` — `batch_execute()` doet 3 dingen: document genereren, email versturen, `_try_auto_advance()` aanroepen

**Auto-advance logica:**
- `_try_auto_advance()` (service.py:893-975) checkt **completed `WorkflowTask` records**, niet of email succesvol is verzonden
- AIDraft-status wordt alleen op `'sent'` gezet via `POST /api/incasso/cases/{id}/advance-after-send` (router.py:359-442)
- Maar de **batch-flow roept dit endpoint NIET aan**

**Root cause:** Twee aparte verzendpaden:
- **Batch-flow** (incasso-pagina): mail verzonden, géén AIDraft `sent`-update, géén pipeline-advance trigger
- **Single-flow** (advance-after-send): mail verzonden, AIDraft `sent`, pipeline-advance OK

**Bijkomend:** `case.status` legacy veld vs `case.incasso_step_id` leidend veld — frontend toont mogelijk verkeerd veld in status-badge.

### Voorgestelde fix — **M (4-6u)**

1. Batch-flow `batch_execute()` aanvullen: na succesvolle email-verzending de AIDraft-status op `'sent'` zetten (zelfde logica als `advance_after_send`)
2. Status-advance gebeurt dan automatisch via `_try_auto_advance()`
3. Verifiëren dat status-badge op frontend leest van `case.incasso_step_id` → `pipeline_step.name`, niet `case.status`
4. **Eerst:** bestaande 45 dossiers zonder step migreren — alle "active" dossiers krijgen step 1 toegewezen of expliciet markeren als afgerond/concept

**Risico:** medium. Bestaande data herstel is risicovol — eerst dry-run, dan migratie.

---

## Punt 4 — Geen meldingen meer

**Lisanne:** "Bel-icoon is leeg, ik krijg geen meldingen meer."

### Bevindingen (productie-diagnose)

**Database `notifications` tabel:**

```
total | unread | latest
------+--------+-------
  403 |    403 | 2026-05-14 06:20 (vanochtend)
```

**Per type:**
```
type             | count
-----------------+------
deadline_overdue |   403
```

**Per user:** alle 403 → `seidony@kestinglegal.nl` (Lisanne's login).

**Conclusie:** notifications worden **wél** aangemaakt en zijn allemaal **ongelezen**, maar Lisanne ziet ze niet in de UI.

### Mogelijke oorzaken (gesorteerd op waarschijnlijkheid)

**Hypothese 1 (waarschijnlijkste) — Frontend bell-icon polling kapot of cached**
- `useNotifications(15)` + `useUnreadCount()` met `refetchInterval: 30_000`
- Controleren: opent Lisanne devtools → ziet ze de calls naar `/api/notifications/unread-count`? Geeft die 403 of een fout?

**Hypothese 2 — Tenant-isolation faalt**
- RLS-policy `(tenant_id = current_setting('app.current_tenant'))` — als middleware tenant niet zet bij de notifications-call → 0 resultaten

**Hypothese 3 — Eénzijdig notification-type**
- Alle 403 zijn `deadline_overdue` ("Taak te laat: ...")
- Geen `email_received`, geen `draft_ready`, geen `classification_done`
- Lisanne ervaart het als "geen meldingen" omdat de relevante events niet getriggerd worden
- Inbound email + classify + draft-ready genereren géén notification (orchestrator auto-draft is `DISABLED`, regel 80 in `orchestrator.py`)

### Voorgestelde fix

**Stap 1 — Verifiëren — XS (15 min)**
- Lisanne laten inloggen → devtools → ziet ze `GET /api/notifications/unread-count` → response?
- Als response = 403 → frontend-bug (badge update)
- Als response = 0 → backend/RLS-bug

**Stap 2 — Notification-types uitbreiden — M (4-6u)**
- Trigger `Notification.create()` toevoegen aan:
  - Sync_service: bij **nieuwe inbound email** gekoppeld aan dossier
  - Classify-service: bij **classificatie klaar** ("Belofte", "Betwisting" etc.)
  - Draft-service: bij **AI-draft gegenereerd** (`status='generated'`)
- Frontend bell-icon groeperen op type

**Risico:** medium. Notification-spam vermijden — Lisanne wil niet 50 notificaties per dag. Throttle/group per case.

---

## Punt 5 — Concept-klaar niet zichtbaar

**Lisanne:** "Ik zie niet wanneer een concept klaar is, geen tijd hoe lang het duurde."

### Bevindingen (productie-diagnose)

**Database `ai_drafts`:**

```
status     | count
-----------+------
generated  |   18
sent       |    1
```

19 drafts in totaal, 18 zijn `generated` (= klaar voor review), 1 verzonden. Latest = vandaag 09:52.

**Workflow tasks `review_ai_draft`:**

```
status     | count
-----------+------
overdue    |    9
skipped    |    7
completed  |    1
pending    |    1
```

**Concept-tijd:** AIDraft heeft `created_at` (start) maar geen `completed_at` of `generation_duration_seconds`. Concept-tijd is niet bijgehouden.

### Root cause

Concepts worden gegenereerd, taken worden gemaakt, maar:
1. **Geen notification** bij `draft generated` event
2. **Geen prominent widget** op dossier-overzicht
3. **9 review-tasks zijn overdue**, 7 skipped — Lisanne zag ze nooit
4. **`onOpenDraft(draftId)`** callback in `TijdregistratieTab` is correct gewired, maar tab niet zichtbaar zonder klik

### Voorgestelde fix — **M, samen met punt 6 en 7**

Zie punt 6 hieronder — Concept-klaar moet in de unified Actie-Feed verschijnen met:
- "Concept klaar voor verweer beantwoorden — 2 min geleden — [Bekijk concept]"
- Concept-tijd: backend extra veld `generation_duration_seconds` (XS, 30 min)

---

## Punt 6 — Niks komt naar voren op dossier

**Lisanne (volledige quote):** "Voorheen kregen we 'hey er is een antwoord of betwisting, genereer hier je volgende stap'. Nu krijgen we niks meer. Ik moet in taken kijken of bij correspondentie. Het moet gewoon op één plek zijn, en dat kan in het dossier zijn — 'hey er is een update, dit is aan de hand, ik kan een bericht voor je maken'. Niet op allemaal verschillende plekken."

### Bevindingen — versnippering

**AI-suggesties zitten nu op 3 plekken (geen daarvan is primair):**

| # | Plek | Component | Wat | Lifespan |
|---|---|---|---|---|
| 1 | `DossierHeader` banner (boven dossier) | `DossierHeader.tsx:382-395` | "Status gewijzigd naar X. Template Y klaarzetten?" | 30s auto-hide |
| 2 | Taken-tab inline | `TijdregistratieTab.tsx` | `review_ai_draft` tasks met `onOpenDraft` callback | Permanent |
| 3 | Correspondentie-tab classifications | `CorrespondentieTab.tsx:19-35` | Smart-reply suggesties (mild/zakelijk/streng) | Permanent |

**Dossier-detailpagina heeft 11 tabs:** Overzicht / Taken / Uren / Vorderingen / Betalingen / Staphistorie / Facturen / Documenten / Correspondentie / Activiteiten / Partijen.

**Op Overzicht-tab (de hoofdpagina) staat NIETS over AI-acties of "wat moet er nu gebeuren".**

### Voorgestelde fix — **M-L (1-2 sessies) — HOOFDPUNT**

**Nieuw component:** `CaseActionFeed` op Overzicht-tab, bovenaan na de header.

Toont een verticale tijdlijn met **actiekaarten** in 3 typen:

```
┌─ Dossier 2026-00062 ─ Verweer beantwoorden ───────┐
│                                                    │
│ 🤖 Concept klaar voor review                       │
│    Verweer beantwoorden — 2 min geleden            │
│    Gegenereerd in 4.3s                             │
│    [Bekijk concept] [Verstuur direct]              │
│                                                    │
│ 📧 Nieuw antwoord van wederpartij                  │
│    "Wij betwisten de vordering omdat..."           │
│    Geclassificeerd als: Betwisting (78%)           │
│    [Smart reply: Mild / Zakelijk / Streng]         │
│                                                    │
│ ⏰ Volgende stap: Stap 5 — Dagvaarding             │
│    Deadline: 21 mei 2026 (over 7 dagen)            │
│    Actie nodig: handmatige beoordeling             │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Data-bronnen die samenkomen:**
1. `useAiDrafts(caseId)` — status `generated` → concept-kaart
2. `useClassifications(caseId)` — recent → reply-kaart
3. `useWorkflowTasks(caseId)` — pending/overdue → actie-kaart
4. `useNextStep(caseId)` — pipeline → vervolg-kaart

**Wat verdwijnt na bouw:**
- `DossierHeader` status-banner (30s auto-hide is foute UX)
- Smart-reply alleen-op-correspondentie-tab → ook in feed
- Review-task alleen-op-taken-tab → ook in feed

**Wat blijft als drilldown:**
- Correspondentie-tab voor email-archief
- Taken-tab voor uitgebreide task-management

**Risico:** medium. Te veel kaarten = nieuwe versnippering. Begrenzen tot top 3 acties + "alles tonen" link.

---

## Punt 7 — AI-overlap: concept-genereren vs correspondentie-antwoord

**Lisanne:** "Bij correspondentie kan je een mail maken, maar ook in het begin naast de 1e sommatie. Het moet op één plek."

### Huidige architectuur — 3 aparte AI-flows

```
┌─────────────────────────────────────────────────────────────────┐
│                      HUIDIGE STAAT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌────────────────────┐  ┌───────────────────┐  ┌────────────┐ │
│ │ 1. INCASSO-STAP    │  │ 2. CONTEXT-DRAFT  │  │ 3. SMART   │ │
│ │    (sjabloontrouw) │  │    (vrij)         │  │    REPLY   │ │
│ ├────────────────────┤  ├───────────────────┤  ├────────────┤ │
│ │ Endpoint:          │  │ Endpoint:         │  │ Endpoint:  │ │
│ │ /api/incasso/      │  │ /api/ai-agent/    │  │ /api/ai-   │ │
│ │ cases/{id}/        │  │ draft/{case_id}   │  │ agent/     │ │
│ │ generate-draft     │  │                   │  │ classific- │ │
│ │                    │  │                   │  │ ations/{}/ │ │
│ │ Hook:              │  │ Hook:             │  │ smart-     │ │
│ │ useGenerate-       │  │ useGenerate-      │  │ replies    │ │
│ │ DraftForCase       │  │ Draft             │  │            │ │
│ │                    │  │                   │  │ UI: 3 toon │ │
│ │ Prompt:            │  │ Prompt:           │  │ varianten  │ │
│ │ incasso_email_     │  │ DRAFT_SYSTEM_     │  │ mild/zake- │ │
│ │ prompts.SYSTEM_    │  │ PROMPT (hard-     │  │ lijk/      │ │
│ │ PROMPT             │  │ coded Python)     │  │ streng     │ │
│ │ (hardcoded)        │  │                   │  │            │ │
│ │                    │  │ Sjabloon:         │  │ Prompt:    │ │
│ │ Sjabloon:          │  │ GEEN — vrije      │  │ SMART_     │ │
│ │ IncassoPipeline-   │  │ generatie op      │  │ REPLY_     │ │
│ │ Step.email_body_   │  │ basis van         │  │ SYSTEM_    │ │
│ │ template (DB)      │  │ case-context      │  │ PROMPT     │ │
│ │                    │  │                   │  │            │ │
│ │ Verweer-bib?       │  │ Verweer-bib?      │  │ Sjabloon:  │ │
│ │ ✓ bij verweer-stap │  │ ✓ altijd          │  │ GEEN       │ │
│ │                    │  │                   │  │            │ │
│ │ STATUS:            │  │ STATUS:           │  │ STATUS:    │ │
│ │ ⚠ NIET AANGE-     │  │ ✓ WERKEND         │  │ ✓ WERKEND  │ │
│ │ SLOTEN op engine   │  │ (correspondentie- │  │ (classifi- │ │
│ │ (zie module-       │  │  tab knop)        │  │ cation-    │ │
│ │ docstring)         │  │                   │  │ card)      │ │
│ └────────────────────┘  └───────────────────┘  └────────────┘ │
│                                                                 │
│ Sjablonen op 3 plekken:                                        │
│ - IncassoPipelineStep.email_body_template (DB)                 │
│ - DRAFT_SYSTEM_PROMPT (Python hardcode)                        │
│ - SMART_REPLY_SYSTEM_PROMPT (Python hardcode)                  │
│ - DEFENSE_EXAMPLES (Python hardcode dict)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Voorgestelde unified architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                      UNIFIED FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ÉÉN endpoint: POST /api/ai/draft            │  │
│  │              body: { case_id, intent, tone? }             │  │
│  │                                                           │  │
│  │  intent: "next_step" | "reply_to_email" | "free_compose" │  │
│  │  tone:   "mild" | "zakelijk" | "streng" (optioneel)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │     DraftService (één service, drie strategieën)         │  │
│  │                                                           │  │
│  │     intent="next_step":                                  │  │
│  │       → kijkt naar case.incasso_step                     │  │
│  │       → laadt managed_template voor die stap             │  │
│  │       → vult variabelen via AI op basis van dossier      │  │
│  │                                                           │  │
│  │     intent="reply_to_email":                             │  │
│  │       → kijkt naar laatste classified email              │  │
│  │       → past tone toe (mild/zakelijk/streng)             │  │
│  │       → laadt verweer-bibliotheek als classification     │  │
│  │         == "betwisting"                                  │  │
│  │                                                           │  │
│  │     intent="free_compose":                               │  │
│  │       → vrije generatie op case-context                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            managed_templates tabel (DB)                  │  │
│  │     (één bron voor alle sjablonen, met variabelen)       │  │
│  │                                                           │  │
│  │     Kolommen: id, name, channel (email/letter),          │  │
│  │     intent_match (next_step/reply/...), step_id?,        │  │
│  │     subject_template, body_template, ai_prompt_extra     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Frontend: ÉÉN component CaseActionFeed roept hetzelfde        │
│  endpoint aan met de juiste intent, krijgt drafts terug.       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Verschillen huidig → unified

| Aspect | Huidig | Unified |
|---|---|---|
| Endpoints | 3 | 1 |
| Hooks | `useGenerateDraft`, `useGenerateDraftForCase`, `useSmartReplies` | `useDraft({intent, tone})` |
| Prompt-bron | 3× hardcoded Python | 1× hardcoded systeem + sjablonen uit DB |
| Sjabloon-bron | `IncassoPipelineStep.email_body_template` + 2× geen | `managed_templates` tabel |
| Verweer-bibliotheek | Hardcoded Python dict | `managed_templates` met `intent_match='reply_dispute'` |
| Niet-aangesloten code | `incasso_email_prompts.py` | — |

### Voorgestelde fix — **L (2-3 sessies)**

**Sessie 1 — Schema + service**
1. Migratie `managed_templates` tabel uitbreiden met `intent_match`, `step_id` (nullable), `tone`
2. Bestaande `IncassoPipelineStep.email_subject_template`/`email_body_template` migreren naar `managed_templates`
3. Hardcoded `DRAFT_SYSTEM_PROMPT` + `SMART_REPLY_SYSTEM_PROMPT` opsplitsen in: vaste systeem-prompt + per-intent variabel deel uit DB
4. Hardcoded `DEFENSE_EXAMPLES` migreren naar `managed_templates` met `intent_match='reply_dispute'`
5. Nieuwe service `app/ai_agent/unified_draft_service.py` die alle 3 strategieën dekt
6. Nieuw endpoint `POST /api/ai/draft` met `{case_id, intent, tone?}`

**Sessie 2 — Frontend consolidatie**
1. Nieuw hook `useDraft({intent, tone})`
2. `CaseActionFeed` component bouwt op nieuw endpoint
3. Bestaande 3 hooks → deprecate, niet meteen verwijderen
4. Smart-reply card op correspondentie-tab → roept nieuw endpoint met `intent='reply_to_email'`

**Sessie 3 — Cleanup**
1. Verwijder `useGenerateDraft`, `useGenerateDraftForCase`, `useSmartReplies` na verificatie
2. Verwijder oude endpoints `/api/incasso/cases/{id}/generate-draft`, `/api/ai-agent/draft/{case_id}`, `/api/ai-agent/classifications/{}/smart-replies`
3. Verwijder `incasso_email_prompts.py` (nooit aangesloten)
4. Verwijder hardcoded `DEFENSE_EXAMPLES` Python dict

**Sjabloon-editor (bestaande TODO uit memory `project_unified_template_editor`):**
- Eén UI om alle sjablonen te beheren (brief + email + pipeline)
- Wijzigen in sjabloon-editor → werkt overal door
- Past perfect bij deze refactor: `managed_templates` wordt single source of truth

**Risico:** L. Migratie raakt 4 modules + bestaande data. Mitigatie:
- Eerst nieuwe service parallel naast oude (feature-flag)
- Per scherm overzetten, niet big-bang
- Bestaande templates eerst CSV-exporten als backup

---

## Aanbevolen sessievolgorde

| Sessie | Punten | Grootte | Waarom eerst |
|---|---|---|---|
| **S142** | Punt 1 (tijdstempels) + Punt 4 verificatie (devtools-check Lisanne) | S | Quick wins. Tijdstempel is 1-2u, notification-diagnose is 15 min — beide opleveren snel. |
| **S143** | Punt 3 (status pipeline bug + 45-dossier-migratie) | M | Lost direct ervaren bug op. Eerst data-state herstellen. |
| **S144** | Punt 2 (auto-koppeling slimmer + Ongesorteerd badge) | M | Voor Lisanne het meest zichtbare effect. |
| **S145-S147** | Punten 4+5+6+7 samen — Unified DraftService + CaseActionFeed | L (3 sessies) | Hoofdpunt. Lost versnippering definitief op. |

**Strategische opmerking:** Niet beginnen met punt 7 direct. Lisanne ziet eerst betere quick wins (tijdstempels, status-fix, auto-koppeling), dan de grote consolidatie. Anders frustreert ze van trage progress.

---

## Memory-aandacht — wat te onthouden

Te bewaren na akkoord op dit rapport:

- **`project_demo_feedback_S140.md`** (project) — 7 punten van Lisanne + status per sessie
- **`feedback_ui_versnippering.md`** (feedback) — Bij elke nieuwe AI-feature: vraag eerst of het in `CaseActionFeed` past, niet als losse tab/banner
- **`reference_managed_templates_consolidatie.md`** (reference) — Bij elke wijziging in `IncassoPipelineStep.email_*`, `DRAFT_SYSTEM_PROMPT`, `SMART_REPLY_SYSTEM_PROMPT`, `DEFENSE_EXAMPLES`: pas op dat consolidatie-plan in S145+ niet wordt gefrustreerd door nieuwe hardcoded paden.

**Niet bewaren:** dit rapport zelf is in `docs/onderzoek-ai-overlap-S141.md`, geen memory nodig.

---

## Wat dit rapport NIET doet

- **Geen code-wijzigingen** — alleen onderzoek
- **Geen impliciete goedkeuring** — wacht op Arsalan-akkoord op aanpak per punt
- **Geen automatische sessieplanning** — Arsalan beslist welke sessie eerst en in welke volgorde

**Volgende stap:** Arsalan reviewt, geeft per punt akkoord (en eventueel scope-aanpassingen), daarna pas bouw in S142+.
