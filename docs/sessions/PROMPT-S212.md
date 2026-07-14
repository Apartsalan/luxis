cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 212 — WIK-rentebijlage LIVE + bijlage op de resterende verzendpaden + terug-navigatie

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): `docs/plans/PLAN-wik-rentebijlage.md`
(besluiten A–D) + SESSION-NOTES entry S211 (§Bekende issues = de precieze restpunten).

## Model
Dit is **uitvoeren → Opus** (merge/deploy, klein bouwwerk, veel visueel klikwerk).

## Blok 1 — GO + merge + deploy (eerst, met Arsalan erbij)
Tak `s211-wik-rentebijlage` (5 commits: WIK-rentebijlage + Fable-review-fixes + S207-M4) staat
groen (volledige suite 1338) en wacht op GO van Arsalan.
1. Vraag expliciet GO. ⚠️ Benoem het bewuste besluit: het **mailslot staat OPEN** en tot de
   rechtsvorm-backfill draait heeft élke zakelijke wederpartij `legal_form` leeg → besluit B →
   **iedere** 14-dagenbrief/eerste sommatie krijgt de rentebijlage, ook naar BV's. Afgesproken
   veilige kant, maar het begint bij deploy.
2. Na GO: merge naar main → push → deploy backend+frontend **mét migratie** (deploy-regels:
   build → migrate → up). Rooktest + korte visuele prod-check (relatiekaart toont rechtsvorm).
3. `PROMPT-S207.md` + `PROMPT-S210.md` en ouder → `docs/archief/prompts/` (kon niet vóór de
   merge — S207-status stond op de tak).

## Blok 2 — Rente-bijlage op de resterende verzendpaden (Fable-review bevinding 3)
De bijlage zit op het batch- en followup-pad, maar dezelfde brieven gaan óók via:
- het **compose/AI-concept-pad** (`email/compose_router.py` — hangt voor exact
  `14_dagenbrief`/`sommatie_drukte` al factuur-PDF's aan: zelfde plek de gedeelde helper
  `documents/rente_bijlage.py` aanhaken);
- het **document-verzendpad** (`documents/router.py`, send-route).
Dit is de meest gebruikte route van Lisanne — een eenmanszaak die via een AI-concept een
sommatie krijgt, mist nu de bijlage (de schadelijke richting). Plus klein: het preview-zinnetje
in de followup-frontend zegt "De brief gaat als PDF-bijlage mee" → moet "renteoverzicht als
bijlage" worden. Tests: zelfde patroon als `test_followup.py` (bijlage wél/BV niet).

## Blok 3 — Terug-navigatie heel Luxis (wens Arsalan, 14 juli)
Het terug-pijltje in Luxis brengt je niet terug naar waar je vandaan kwam (voorbeeld: vanaf een
dossier naar Facturen → terug-pijltje → NIET terug op het dossier; opnieuw zoeken). Dat moet
werken zoals in elke normale tool: terug = naar de pagina van herkomst.
1. Inventariseer ALLE plekken: grep in `frontend/src` op terug-pijltjes/ArrowLeft, vaste
   `<Link href=...>`-terugknoppen en kruimelpaden; noteer per plek waar hij nu heen gaat.
2. Fix overal naar "terug naar herkomst" (router.back met nette fallback naar de vaste
   ouderpagina als er geen historie is — direct-bezochte URL mag niet breken).
3. Bewijs met doorklikken (Playwright): minstens dossier→facturen→terug, dossier→relatie→terug,
   incasso→dossier→terug, en 2 eigen gevonden gevallen.

## Los moment — zodra de echte KvK-sleutel binnen is (~16 juli, Arsalan meldt)
`KVK_API_KEY` (+ `KVK_API_BASE=https://api.kvk.nl/api`) als env op de VPS → herstart backend →
`scripts/kvk_backfill_legal_form.py --dry-run` → akkoord Arsalan → echt draaien → natelling
(±438 relaties, ±€9). Daarna meten hoeveel zaken géén bijlage meer krijgen (BV's).

## Verificatie
- Backend: `docker compose exec -T backend python -m pytest tests/ -k "kvk or bijlage or compose or followup or document" -q`
- Lint: `uvx ruff check backend/app/` · Frontend: `cd frontend && npx tsc --noEmit`
- Visueel doorklikken op de terug-navigatie is verplicht bewijs (blok 3).

## Constraints (wat NIET doen)
- **Mailslot staat OPEN** — niets echt versturen; bijlage-tests via preview/render/mocks.
- Backfill NIET draaien vóór de echte sleutel er is.
- Geen `git add -A`; expliciete paden.
- S209-backfills (notities/alerts/land/provisie) zijn AF (S209+S210) — NIET heropenen.
- Buiten scope: ontvangers-opschoning (M5), facturatie-import (S201), S203-restpunten —
  alleen op expliciete vraag.

## Commit
Blok 1 = merge (geen nieuwe commits nodig). Blok 2/3: commit + push naar main per afgerond
onderdeel, deploy via SSH (deploy-regels). Werk af met `/sessie-einde`.
