# Sessie-prompt S197 — bouwblok 3 (B3-versimpeling + A5-pauze + A3 dagstart + A7 sjablonen)

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** (check met `/model`).

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 197 — bouwblok 3: B3 status volgt pijplijn → A5 classificatie-pauze → A3 dagstart-lijst → A7 sjablonen op één plek

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/plans/PLAN-fase2-bouwblokken.md` — de besluiten per punt (stapel 3, rij 9-13).
- Werkorder-details: B3 in `docs/research/audit-DB-kernmotor.md`; A3/A5/A7 in
  `docs/research/audit-DA-werkschil.md`.

## Taak 1 — B3: status versimpelen, volgt de pijplijn (besluit Arsalan S191)
NIET het grote status-systeem optuigen. Status reduceren tot iets dat de incasso-pijplijn
volgt; kapotte "Volgende stap"-knoppen en de lege statusfilter op de Dossiers-lijst meteen mee.
Onderzoek eerst kort de huidige koppeling status↔stap, presenteer aanpak, dan bouwen.

## Taak 2 — A5: classificatielijn op pauze, meldingen/badges uit (besluit S191, ook B6/A11/C9)
Meldingen van classificaties uit; "AI-suggestie"-badges/actieblok ontkoppelen van
pending-classificaties. De 473 wachtende classificaties niet verwerken — lijn staat op pauze.

## Taak 3 — A3: Mijn Taken → dagstart-lijst (besluit S191: "dagstart, ná blok 1")
Herontwerp Mijn Taken tot een bruikbare dagstart (of ontdubbel tot pure takenlijst).
Kort voorstel presenteren vóór de bouw (het is Lisanne's dagelijkse startpunt).

## Taak 4 — A7: sjabloonbeheer alleen in Instellingen (besluit S191)
Documenten-pagina: sjabloonbeheer verhuist naar/blijft in Instellingen; documentenbibliotheek
is LATER (niet bouwen). HTML-tab weg, slug-titels fixen.

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevant>" -v`
  (let op: `python -m pytest`, kaal `pytest` bestaat niet in de container)
- Lint: `uvx ruff check backend/app/` · Frontend: `npx tsc --noEmit` + `npm run build`
- Live doorklikken in de prod-app ná deploy.
- Codex-tegenlezer: timede in S194 én S196 uit (10 min) — eerst werkvorm fixen of
  overslaan met vermelding; niet blind opnieuw proberen.

## Constraints
- ⚠️ **MAILSLOT:** check `OUTBOUND_MAIL_LOCK` in `/opt/luxis/.env` vóór iets dat mail kan
  versturen; alleen eraf op expliciet verzoek Arsalan.
- Alleen de blokken uit het plan; extra vondsten = noteren als voorstel, niet bouwen.
- Verwijderen (data/pagina's) nooit autonoom — per stuk akkoord Arsalan.

## Commit
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH (skill
`deploy-regels`), containers healthy checken. Afsluiten met `/sessie-einde` (notities,
roadmap, archiefregels, tag sessie-197).
