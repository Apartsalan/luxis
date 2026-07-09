# Luxis — Verbindingskaart

> **Doel:** in 2 pagina's zien hoe alles aan elkaar hangt, zodat elke sessie ("nieuwe
> medewerker") binnen 5 minuten het complete plaatje heeft. **LEES DIT ALS EERSTE.**
> **Onderhoudsregel:** wijzig je een koppeling tussen systemen → werk deze kaart bij in
> dezelfde sessie (hoort bij `/sessie-einde`). Wordt hij langer dan 2 pagina's → inkorten.
> Feitelijke detail-inventaris: `docs/audits/inventaris-2026-07-05.md`.

**Laatst bijgewerkt:** 6 juli 2026 (S174, verbind-sprint 2: staleness-gate, audience-gate, 13-types-woordenschat + type-matching).

---

## Het product in één zin
Praktijkmanagement voor NL-advocatenkantoren; dossiers → vorderingen (rente/WIK/6:44) →
brieven & mail → betalingen & derdengelden → facturen, met een AI-assistent die concepten
schrijft en Lisanne die beslist.

## De hoofdstromen (wie voedt wie)

```
BaseNet-archief (import, 6393 mails, passief)
        │
Outlook/M365 ──Graph sync (5 min)──► synced_emails ──AI-classificatie (8 cat.)──┐
                                          │                                     │
                                          ▼                                     ▼
dossiers (cases) ◄── intake-agent ◄── inkomende mail            verweer-flow: auto-switch stap
   │        │                                                   "Verweer beantwoorden" + AI-concept
   │        ├── vorderingen/rente/WIK/6:44 ..... collections/
   │        ├── pipeline 21 stappen ............ incasso/  ──batch brief+mail──► Outlook
   │        ├── taken/deadlines ................ workflow/ (APScheduler; GEEN Celery)
   │        ├── uren ──► facturen ──PDF/mail──► invoices/
   │        └── derdengelden (vier-ogen, storno, afwikkelflow S170) ... trust_funds/
   │
   └── betalingen: bankimport CSV ──matcher──► trust-deposit + 6:44-betaling (FIN-1 helper)
```

## De AI-laag — drie conceptservices, gedeeld geheugen via één resolver + één type-loop

| Pad | Trigger (knop) | Voorwaarden (AV) | Geleerde vb. | Bibliotheek |
|---|---|---|---|---|
| `incasso/automation_service.py` | Pipeline "Concept genereren" + verweer-flow | ✅ `ContactTerms` (geversioneerd) | ✅ (type-voorrang) | ✅ |
| `ai_agent/draft_service.py` | Orchestrator/classificatie-hook, client-update | ✅ `ContactTerms` (gedeelde resolver, S173) | ✅ (type-voorrang) | ✅ |
| `ai_agent/unified_draft_service.py` | Compose-dialog `/api/ai/draft` | ✅ bij verweer (resolver, S173) | ✅ bij verweer (type-voorrang) | ✅ bij verweer |

**Gedaan (S173):** gedeelde AV-resolver `ai_agent/knowledge_context.resolve_case_terms`,
gebruikt door alle drie de paden. Automation-gedrag byte-identiek (bibliotheek-injectie zit
in `incasso_email_prompts`, ongewijzigd). unified injecteert kennis **alleen bij een
verweer-categorie** (S164-les: minder losse tekst = minder afdwalen).

**Gedaan (S174):**
- **Staleness-gate** — gedeelde helper `knowledge_context.last_inbound_defense` bepaalt
  categorie + verweer-type van de ALLERNIEUWSTE inkomende mail (op `email_date`, niet
  `created_at`); nieuwste inbound niet geclassificeerd → geen kennis injecteren. Fixte de
  `created_at`-bug in draft_service én automation_service.
- **Audience-gate** — client-updates (`generate_client_update`) slaan de debiteur-gerichte
  bibliotheek + geleerde voorbeelden over; AV + financiële context blijven.
- **13-types-woordenschat + type-matching** — de classificatie kiest een `defense_type`,
  en `get_learned_examples` geeft goedgekeurde voorbeelden van datzelfde type voorrang.
  De twee verweer-categorieën vormen daarbij ÉÉN pool.

Consolidatie 3→minder services blijft een latere opruimklus.

**AI-kennisbronnen:**
- `ContactTerms` (relations) — geversioneerde AV per opdrachtgever, selectie op factuurdatum.
- `learned_answers` (slim leren) — kandidaten uit verstuurde antwoorden → Lisanne keurt →
  pas dan prompt-voeding. Type-toekenning nu via `defense_types.prelabel_defense_type`
  (deterministische trefwoord-regels, 13 types; difflib = alleen nog duplicaat-filter).
- `defense_types.py` — de 13-types-woordenschat (key EN / label NL) + pre-labeler + aliassen.
- `defense_library.py` — 5 statische voorbeeldantwoorden (8 apr 2026).
- AI-client: `ai_agent/kimi_client.py` — **naam is legacy, is 100% Claude** (Sonnet=alle concepten incl. compose-dialog/verweer sinds S173, Haiku=classificatie/intake/invoice).
- Orchestrator (`events.py` + `orchestrator.py`): event-bus bestaat, **auto-draft bewust UIT** (S160-besluit: assistent, geen autonomie).

## Sjablonen — vier opslagplaatsen (bekende schuld)
1. `email/incasso_templates.py` — ±25 hardcoded HTML-mails (BaseNet-huisstijl) ← bron van waarheid voor mail-opmaak
2. `managed_templates` (DB+disk) — DOCX-brieven, editor in Instellingen
3. `response_templates` (DB, 6) — antwoorden classificatie-flow
4. `incasso_pipeline_steps.email_*_template` — sjabloontekst per stap

Wijzig je een standaardtekst (disclaimer, handtekening): **check alle vier**.

## Twee workflow-systemen (bewust, half gekoppeld)
- `case.status` — algemene dossier-workflow (statussen + transities).
- `case.incasso_step_id` — incasso-pipeline (21 stappen, eigen historie `CaseStepHistory`).
- Koppeling: alleen guards (bijv. `requires_settled` op "Afgesloten"); status volgt de
  pipeline NIET automatisch. Verwarring over "waarom staat dit open" begint meestal hier.

## Slapend maar af (niet opnieuw bouwen!)
KYC/WWFT (relations) · Exact Online (OAuth+sync, 0 connecties) · sentiment + betalings-
belofte-extractie (ai_agent) · orchestrator-events · mail-suggesties (FEAT-MAIL-01, gebouwd).

## Vaste valkuilen (kaart-niveau)
- Prod = image-baked (S170): code wijzigen ⇒ rebuild; `templates/` is wél live gemount.
- Geld = `Decimal` overal; API serialiseert Decimal als **string** (frontend: `Number()`).
- RLS FORCE + `SET LOCAL ROLE luxis_app`; alles tenant-scoped behalve `interest_rates`.
- Kesting-specifieke kennis hoort in **data** (DB/ContactTerms), niet in code.

## Waar staat wat (documenten)
- `LUXIS-ROADMAP.md` — status/prioriteit (source of truth, maar kop-tellingen ijlen na)
- `docs/audits/inventaris-2026-07-05.md` — feitelijke feature-inventaris + dubbele systemen
- `docs/FEATURE-INVENTORY.md` — markt-checklist ("wat zou een PMS kunnen"), geen inventaris
- `SESSION-NOTES.md` — per sessie wat er gebeurd is · `docs/sessions/PROMPT-S17x.md` — volgende taak
- Skills: `deploy-regels`, `bekende-fouten`, `incasso-workflow`, `template-systeem`
