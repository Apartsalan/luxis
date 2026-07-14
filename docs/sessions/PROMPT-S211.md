cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 211 — WIK-rentebijlage bij eerste sommatie (bouwen tegen KvK-testomgeving)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): **`docs/plans/PLAN-wik-rentebijlage.md`**
— dat is de volledige, goedgekeurde spec (gemeten uitgangspunten, besluiten A–D, bouwstappen,
premortem, KvK-testgegevens). Lees dat plan eerst.

## Model
Dit is **bouwen → Opus**. (Onderzoek + plan zijn in S210 op Fable gedaan en goedgekeurd.)

## Taak
Bouw de WIK-rentebijlage volgens `PLAN-wik-rentebijlage.md`, bouwstappen 1–7, **tegen de KvK-
testomgeving** (test-key + endpoints staan in het plan, §Technisch). Kern:
- Nieuw veld `legal_form` (+ herkomst) op de relatie; auto-vullen uit KvK bij aanmaak met KvK-nummer.
- Eén beslisregel `should_attach_rente_bijlage` die **alleen het opgeslagen veld** leest (nooit live
  KvK in het verzendpad) — besluiten A/B/C uit het plan.
- Renteoverzicht als PDF-bijlage aan de e-mailroute van stap `sort_order` 0 (14-dagenbrief) + 1
  (eerste sommatie); ook opslaan als GeneratedDocument. Eén gedeelde helper, gebruikt door zowel
  `ai_agent/followup_service.py` als `incasso/service.py`.
- Backfill-script (droogloop-modus) klaarzetten, maar **NIET draaien** — dat wacht op de echte
  productie-sleutel (Arsalan meldt binnenkomst; testdata = nepbedrijven).

## Verificatie
- Backend: `docker compose exec -T backend python -m pytest tests/ -k "kvk or legal_form or bijlage or compliance or contact" -q`
- Lint: `uvx ruff check backend/app/` (lokaal vóór push)
- Frontend geraakt? `cd frontend && npx tsc --noEmit`
- KvK-client end-to-end tegen de testomgeving bewijzen (rechtsvorm komt terug); verzendpad-test:
  faalt NIET als KvK onbereikbaar is.
- Visuele controle (Opus, niet Fable): relatiekaart toont het rechtsvorm-veld; een testsommatie
  op een particuliere/eenmanszaak-zaak krijgt de PDF-bijlage, een BV-zaak niet.

## Constraints (wat NIET doen)
- **Backfill NIET draaien** vóór de echte sleutel er is (besluit D wacht).
- KvK **nooit** in het live verzendpad aanroepen — beslissing leest het opgeslagen veld.
- Mailslot blijft DICHT; niets echt versturen (bijlage-test via preview/render, niet via echte mail).
- Geen `git add -A` (expliciete paden). Parallelle S207-track (5 ongecommitte bestanden in de
  werkkopie) niet aanraken.
- Landregel op dagvaarding/faillissementsverzoek = apart, buiten scope.

## Commit
Commit + push naar main per afgerond onderdeel. Deploy via SSH (skill `deploy-regels`);
migratie-volgorde: build backend → migrate → up. `KVK_API_KEY`/`KVK_API_BASE` als env op de VPS
(testwaarden nu; productiewaarden zodra de sleutel binnen is). Werk af met `/sessie-einde`.
