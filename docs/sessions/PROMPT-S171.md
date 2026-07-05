# Sessieprompt S171 — Kennisbank (K0-gate → K1) voor de AI-verweerassistent

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model-keuze bij start
K1 = **bouwen → Opus**. De K0-gate-check + eventuele herplanning = kort redeneren (Opus prima).
Alleen bij een nieuwe brede afweging/onderzoek → Fable. Noem je keuze + reden (memory-regel).

## Context laden bij start (zelf lezen, geen agent — die timen uit)
- `docs/research/kennisbank-learning-loop-onderzoek-2026-07-04.md` — onderzoek + plan K0–K3 (S169, Fable).
- `docs/research/premortem-report-2026-07-04.html` — 7 faalscenario's + herzien plan.
- SESSION-NOTES.md (S170-entry) voor de laatste stand.

**Stand na S170:** doorlichting van Luxis gedaan; **FIN-2 dossier-afwikkelflow gebouwd + LIVE + Fable-gereviewd** (NIET opnieuw bouwen — zie roadmap FIN-2). Source-mount-lek gefixt (prod draait nu image-baked code; deploy hercreëert gegarandeerd). **Kennisbank (K1) is nog NIET gebouwd** — die hing en hangt op de K0-gate. Kernbesluit blijft: **deterministische selectieve prompt-injectie, GEEN RAG/vector-DB.** Bibliotheek = assistent (S160): Lisanne beslist.

## De K0-gate (VERPLICHT vóór er iets aan K1 gebouwd wordt)
Bouw K1 **alleen** als beide waar zijn:
1. **Lisanne's review-ronde** van de 130 kandidaten is (grotendeels) gedaan — check in "Slim leren"
   (Instellingen → Slim leren, of `?tab=ai-leren`), of direct in de DB:
   `SELECT status, count(*) FROM learned_answers GROUP BY status;` — staat `goedgekeurd` flink > 0 en
   `kandidaat` flink onder 130? (S170-meting: 0 goedgekeurd / 130 kandidaat / 1 afgewezen.)
2. **Lisanne's actuele algemene voorwaarden** van de 7 vaste opdrachtgevers zijn aangeleverd. Per document:
   opdrachtgever, **versiedatum/geldig-vanaf**, relevante artikelen. Háár actuele set is leidend —
   géén oude versies uit de BaseNet-import (premortem-risico #2).

**Staat de gate nog op nul → eerst dát gesprek met Arsalan, niet bouwen.** Meld het expliciet.
Arsalan verwachtte de voorwaarden + review ~6 juli aan te leveren.

## Hoofdtaak (als de gate gehaald is): K1 — Kennisbank (bouwen = Opus)
1. Tabel `knowledge_documents` (per tenant; optionele koppeling aan contact/opdrachtgever + verweer-type/
   categorie; titel, tekst, **versiedatum + geldig-vanaf**, bron, actief-vlag). Alembic-migratie.
2. Beheer-UI: nieuw tabblad "Kennisbank" in Instellingen (toevoegen/bewerken/deactiveren) — zelfde stijl.
3. Injectie in de verweer-prompt: zelfde patroon als `build_learned_examples_text` (alleen verweer-stap),
   **harde cap ~1.500 tekens in code**, citaat altijd mét versiedatum. Selectie op (opdrachtgever,
   verweer-type/categorie) — deterministisch, geen embeddings.
4. **Meting vanaf dag één**: vlag per draft "met/zonder kennisbank-injectie" + log injectiegrootte, en
   **baseline edit-rate vastklikken** (datum + cijfers noteren) zodat vóór/ná en mét/zónder vergelijkbaar is.
5. Kesting-specifieke begrippen (art. 9.3 etc.) horen in **data**, niet dieper in code/prompts.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "learned or knowledge" -v`
- Lint lokaal: `cd backend && uvx ruff check app/` (ruff zit niet in de runtime-container)
- Frontend: `cd frontend && npx tsc --noEmit` én `npm run build` (build MOET slagen vóór commit)

## Constraints (NIET doen)
- **Geen RAG/vector-database/embeddings** — deterministische injectie (besluit S169).
- **Geen autonome AI-agent** (S160): niets zonder Lisanne's klik. Voeg desnoods een test/assert toe die dit bewaakt.
- **K2/K3 NIET nu** — K2 pas ná Lisanne's kalibratie-oordeel; per-voorbeeld attributie geschrapt. K3 geparkeerd.
- Kennisbank niet vullen met oude voorwaarden uit de import — alleen Lisanne's actuele set.
- CLAUDE.md + `.claude/commands/*.md` staan ongecommit gewijzigd (niet van mij) — met rust laten.
- Nooit een zip committen (PII); tijdelijke extracties opruimen.

## Deploy/uitvoeren: ZELF via SSH — **nieuw sinds S170: prod draait image-baked code**
SSH `root@46.225.115.216`, key `~/.ssh/luxis_deploy`, app `/opt/luxis`. Backend + migratie:
`git pull && docker compose build backend && docker compose run --rm backend python -m alembic upgrade head && docker compose up -d backend && docker image prune -f`.
De app/alembic source-mount is in S170 verwijderd → **`git pull` alleen ververst de code NIET meer**
(rebuild is verplicht, dat doen de commando's al) en **`up -d` hercreëert nu gegarandeerd** bij een
image-wijziging (de handmatige `docker restart`-dans is niet meer nodig). Verifieer `StartedAt` nog als
goedkope check. CI groen via `gh run list`.

## Optioneel/backlog (na K1, of als de gate nog niet rond is)
- **H6 14-dagenbrief** (na Lisanne's akkoord op de 4 beslispunten — advies + tekst liggen klaar in
  `docs/research/14-dagenbrief-advies.md`; incl. termijn +15 → +16 dagen). Bouwen = Opus, ½ sessie.
- Lisanne-beslissingen ophalen: verdienmodel/BTW (FIN-5, paneel-defaults), 2e stichtingsbestuurder.
- FIN-4 (Exact payment-sync strippen) — pas bij Exact-activatie bundelen (bijt nu niet; 0 connecties).
- F7 backfill-perf (cutoff voor al-verwerkte mails) — pas ná Lisanne's oordeel.
- Permanente "vaste-opdrachtgever"-filter op de leerstroom.

## Commit + Sessie-einde
Commit + push per stap, deploy + verifieer per keer. Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP +
git tag `sessie-171` + PROMPT-S172.
