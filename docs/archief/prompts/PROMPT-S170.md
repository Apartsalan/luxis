# Sessieprompt S170 — Kennisbank (K0-gate → K1) voor de AI-verweerassistent

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Context laden bij start
Lees zelf (geen agent — die timen uit bij onderzoek):
- `docs/research/kennisbank-learning-loop-onderzoek-2026-07-04.md` — onderzoek + gefaseerd plan K0–K3 (S169, Fable).
- `docs/research/premortem-report-2026-07-04.html` — 7 faalscenario's + herzien plan.
- SESSION-NOTES.md (S169-entry) voor de laatste stand.

**Stand na S169:** het "Slim leren"-dashboard is geschaald naar 130 kandidaten en LIVE. Architectuur + plan voor de kennisbank zijn onderzocht en door Arsalan goedgekeurd. **Kernbesluit: deterministische selectieve prompt-injectie, GEEN RAG/vector-DB.** Bibliotheek blijft een assistent (S160): Lisanne beslist, niets gaat autonoom de deur uit.

## De K0-gate (VERPLICHT vóór er iets gebouwd wordt)
De grootste faalreden uit de premortem is de menselijke bottleneck. Bouw K1 **alleen** als beide waar zijn:
1. **Lisanne's eerste review-ronde** van de 130 kandidaten is (grotendeels) gedaan — check in "Slim leren" (Instellingen → Slim leren, of `?tab=ai-leren`): staat de teller flink onder 130 en zijn er goedgekeurde voorbeelden?
2. **Lisanne's actuele algemene voorwaarden** van de 7 vaste opdrachtgevers zijn aangeleverd (zij heeft ze). Per document nodig: opdrachtgever, **versiedatum/geldig-vanaf**, relevante artikelen. Háár actuele set is leidend — géén oude versies uit de BaseNet-import gebruiken (premortem-risico #2).

**Staat de gate na 14 dagen nog op nul → eerst dát gesprek met Arsalan, niet bouwen.** Meld dit expliciet i.p.v. een lege kast op te leveren.

## Hoofdtaak (als de gate gehaald is): K1 — Kennisbank (bouwen = Opus)
1. Tabel `knowledge_documents` (per tenant; optionele koppeling aan contact/opdrachtgever + verweer-type/categorie; titel, tekst, **versiedatum + geldig-vanaf**, bron, actief-vlag). Alembic-migratie.
2. Beheer-UI: nieuw tabblad "Kennisbank" in Instellingen (toevoegen/bewerken/deactiveren) — zelfde stijl als de andere tabs.
3. Injectie in de verweer-prompt: zelfde patroon als `build_learned_examples_text` (alleen verweer-stap), **harde cap ~1.500 tekens in code**, citaat altijd mét versiedatum. Selectie op (opdrachtgever, verweer-type/categorie) — deterministisch, geen embeddings.
4. **Meting vanaf dag één**: vlag per draft "met/zonder kennisbank-injectie" + log injectiegrootte, en **baseline edit-rate vastklikken** (datum + cijfers noteren) zodat effect vóór/ná en mét/zónder vergelijkbaar is.
5. Kesting-specifieke begrippen (art. 9.3 etc.) horen in **data**, niet dieper in code/prompts — de teller "hardcoded Kesting-begrippen buiten de DB" mag niet stijgen.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "learned or knowledge" -v` (relevante modules)
- Lint lokaal: `cd backend && uvx ruff check app/` (ruff zit niet in de runtime-container — CI-lint faalt anders stil)
- Frontend: `cd frontend && npx tsc --noEmit` én `npm run build` (build MOET slagen vóór commit)

## Constraints (NIET doen)
- **Geen RAG/vector-database/embeddings** — deterministische injectie (besluit S169).
- **Geen autonome AI-agent** (S160): niets wordt zonder Lisanne's klik verstuurd. Voeg desnoods een test/assert toe die dit bewaakt.
- **K2 (leer-loop verbreden + meten) en K3 (patroonherkenning) NIET nu** — K2 pas ná Lisanne's kalibratie-oordeel; per-voorbeeld attributie is geschrapt (schijnverbanden). K3 geparkeerd.
- Kennisbank niet vullen met oude voorwaarden uit de import — alleen Lisanne's actuele set.
- CLAUDE.md + `.claude/commands/*.md` staan ongecommit gewijzigd (niet van mij) — met rust laten.
- Nooit een zip committen (PII); tijdelijke extracties opruimen.

## Deploy/uitvoeren: ZELF via SSH — mét de S168-les
SSH `root@46.225.115.216`, key `~/.ssh/luxis_deploy`, app `/opt/luxis`. Backend + migratie: `git pull && docker compose build backend && docker compose run --rm backend python -m alembic upgrade head && docker compose up -d backend && docker image prune -f`. **Na de deploy: verifieer `docker inspect luxis-backend --format '{{.State.StartedAt}}'` ligt ná je push** (source-mount + uvicorn-zonder-reload → oude code kan blijven draaien); zo niet `docker restart luxis-backend`. CI groen checken via `gh run list`.

## Optioneel/backlog (na K1)
- Source-mount-vraag uitzoeken (is de prod bind-mount bedoeld of dev-override? bekende-fouten #28).
- F7 backfill-perf (cutoff voor al-verwerkte mails) — pas ná Lisanne's oordeel.
- Permanente "vaste-opdrachtgever"-filter op de leerstroom.

## Commit + Sessie-einde
Commit + push per stap, deploy + verifieer per keer. Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP + git tag `sessie-170` + PROMPT-S171.
