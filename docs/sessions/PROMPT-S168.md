# Sessieprompt S168 — BaseNet-import UITVOEREN (schone lei → fase 1 + 1b + 2 + 3)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

De documenten-backup is **binnen**: `160174.zip … 160192.zip` (~8 GB, 11 bestanden) in de luxis-hoofdmap, plus `Xml_02-07-2026_2400.zip` (metadata). Beide zijn PII → `.gitignore` dekt nu blanket `*.zip`. **NOOIT een zip committen of naar buiten sturen.**

---

## ⚡ Model + effort per stap — ZEG DE GEBRUIKER LETTERLIJK WAT TE ZETTEN

De assistent kan het sessie-model niet zelf wisselen. Regel (memory `feedback_model_choice`, bevestigd in S167): **onderzoek/ontwerp/oordeel → Fable 5; bouwen/uitvoeren/deployen/security/destructief → Opus 4.8.** De sandwich (Fable plant → Opus bouwt → Fable reviewt) bewees zich in S167 twee keer.

| Stap | Model + effort | Waarom |
|------|----------------|--------|
| A. Documenten-formaat kraken (zips uitpakken, .eml-structuur, koppeling aan dossier) | **Fable 5 · high** | Onbekend formaat reverse-engineeren = uitzoekwerk |
| B. Schone-lei-wipe prod-testdata | **Opus 4.8 · high** | Destructief op productie — Fable weigert dit soms |
| C. Import fase 1 uitvoeren | **Opus 4.8 · high** | Destructief/uitvoerend op prod |
| D. Fase 1b + 2 bouwen + uitvoeren | **Opus 4.8 · high** | Code bouwen + prod-write |
| E. Fase 3 (classificatie + backfill) | **Opus 4.8 · high** (kostenraming-oordeel mag Fable) | Uitvoeren + kosten |
| F. Eindreview | **Fable 5 · high** | Frisse blik op bugs + ontwerp |

**Begin met:** "Zet model op **Fable 5** + effort **high** voor het uitzoeken van het documentformaat; ik zeg wanneer we naar **Opus 4.8** omslaan voor de wipe + import." Herhaal de omslag bij elke overgang denken↔uitvoeren.

## Deploy/uitvoeren: ZELF via SSH — en dit keer GOED (harde eis Arsalan)
SSH `root@46.225.115.216`, key `~/.ssh/luxis_deploy`, app `/opt/luxis`. Skill `deploy-regels` (in S167 gecorrigeerd). **Deploy-valkuilen uit S167 — vermijd ze:**
1. **BUILD VÓÓR MIGRATIE.** Prod bakt code ín de image (geen source-mount) → `alembic upgrade` vóór `build` draait op de oude image en slaat de migratie STIL over. Volgorde: `git pull && build && run --rm backend alembic upgrade head && up -d`.
2. **CHECK CI + DEPLOY NA ELKE PUSH** met `gh run list` — de CI-auto-deploy (`deploy.yml`) rolt vanzelf uit (build → up → migrate) en doet het goed; ga NIET vanuit dat het klaar is, verifieer CI groen + Deploy success + `docker inspect luxis-backend --format '{{.State.StartedAt}}'` vers.
3. **Import-scripts draaien in de prod-container** — `scripts/` zit NIET in de prod-image → `docker cp scripts/basenet luxis-backend:/tmp/` (zie hoe S166 dit deed). Dry-run (`--dry-run`) altijd eerst; pas dan `--execute`.

## Context laden bij start
luxis-researcher: "Lees SESSION-NOTES.md (sessie 167) + `docs/research/basenet-import-ontwerp.md` (volledig, incl. §4b wipe-plan)." Plus memory `project_basenet_import` + `project_shadow_learning`.

---

## Taak (in deze volgorde, mét Arsalan)

### A. Documenten-formaat kraken (Fable)
Pak (één zip eerst) uit naar scratchpad; structuur in kaart. Verwacht: bestanden per dossier(map), `.eml` voor mail. Koppeling aan Luxis-dossier: BaseNet `lepcode` (= inccode, IN-nummer) → case. **Let op:** fase-1-cases hebben id `uuid5("basenet:case:{incasso_systemid}")`; letters verwijzen via **inccode** → bouw `inccode → systemid → case_id` uit de Incasso-export. Richting uit `leinout` (3=uitgaand, 4=inkomend — ontwerpdoc §1). Alleen IN-dossiers.

### B. Schone lei (Opus — DESTRUCTIEF, verse backup eerst)
Besluit Arsalan (S166): alle prod-data is testdata en mag weg. **Herbevestig scope live** vóór uitvoeren. (1) Verse backup (`docs/runbooks/restore.md`), bewezen restore. (2) Wipe testdata (ontwerpdoc §4b): cases/claims/payments/contacts/synced_emails/classifications/ai_drafts/intake_requests/invoices/time_entries/trust/workflow_tasks/notifications/**learned_answers**. **Behoud:** tenants, users, pipeline-steps, templates, tenant-settings, interest_rates, email_accounts (Outlook). Verifieer counts = 0 (business) + config intact.

### C. Fase 1 uitvoeren (Opus)
`scripts/basenet/import_basenet.py --execute` in de prod-container (dry-run eerst — na wipe 0 overlap). Verwacht 1168 relaties / 607 dossiers / 1563 vorderingen. Steekproef (IN100000 = Incassocenter/Bliksem, cliënt-kenmerk IN121388).

### D. Fase 1b + 2 bouwen + uitvoeren (Opus)
- **1b:** betalingen (`Payment`/`IncassoBetaling*`) + persoon↔bedrijf `ContactLink` (via `account`). Betaling↔incasso-koppeling eerst decoderen (`entityid`/`entitysysid`).
- **2:** `.eml` parsen (Python `email`) → `synced_emails` (direction uit leinout, body_html/text uit .eml, dedup op `basenet:{systemid}`, case via inccode→case_id). `email_account_id` NOT NULL → apart import-account of Lisanne's account; **verifieer dat de 5-min-sync deze mails niet opnieuw ophaalt/verwerkt**. Alleen IN-dossier-mails.

### E. Fase 3 — verweer-bibliotheek voeden (Opus) — LET OP: gewijzigd sinds S167
Shadow-learning is in S167 omgebouwd naar de **verweer-antwoord-bibliotheek mét goedkeuring** (`app/ai_agent/learned_answers.py`). De backfill maakt nu **kandidaten** die Lisanne beoordeelt in "Slim leren" — hij voedt de AI niet automatisch. Fase 3 wordt daarmee:
1. Gerichte AI-classificatie: filter uitgaande mails (de nieuwe `_looks_like_rebuttal` + substantie-filter doen dit al), classificeer alléén de voorafgaande inkomende mails zodat `_category_for_outbound` een verweer-categorie vindt (≤3.115, verwacht veel minder). **Kostenraming vooraf + go Arsalan** (memory cost-vs-kwaliteit).
2. `backfill_learned_answers` per tenant → vult de kandidaat-wachtrij. **Steekproef in de DB/UI**: kandidaten moeten schone weerleggingen zijn (geen sommatie-staart, geen PII, geen duplicaten). De S167-fixes (extractie-staart, ISO-datum/factuurnr-anonimisering, dedup, substantie-filter) zijn hierop afgestemd — met véél meer data kunnen de drempels (`_LIBRARY_DUPLICATE_RATIO=0.85`, `_LIBRARY_TYPE_RATIO=0.45`, tail-markers) bijstelling vragen. **Fable-review op een steekproef vóór je het "af" noemt.**

## Verificatie
- Tests: `docker exec luxis-backend python -m pytest tests/test_basenet_import.py tests/test_shadow_learning.py -v`. Ruff: `uvx ruff check scripts/basenet/ app/ai_agent/`.
- Na import: counts + steekproeven; "Slim leren"-dashboard toont echte kandidaten per categorie zonder PII/duplicaten.
- **CI groen + Deploy success bevestigd via `gh run list` na élke push.**

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Verweer-bibliotheek = assistent; Lisanne beslist wat een standaard wordt.
- Dossiers als **passief archief** (status `afgesloten`, geen pipeline-stap). Alleen **IN**-dossiers (D overslaan). Boekhouding blijft Exact-leidend.
- Wipe = destructief → ALTIJD verse backup eerst + scope live herbevestigen.
- **Nooit een zip committen** (PII). `.gitignore` dekt `*.zip`.

## Backlog na de import
#1 cliënt-kenmerk bij factuur-upload (BaseNet `inckenmerkclient` → `case.reference` bestaat al; UI-kant) · #5 verweer-escalatie (2 reacties → ultimatum → volgende fase) · #7 H25 (`modules_enabled` server-side, hele taak **Opus**).

## Commit + Sessie-einde
Commit + push per stap (conventional commits), deploy + verifieer per keer. Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP + git tag `sessie-168` + PROMPT-S169.
