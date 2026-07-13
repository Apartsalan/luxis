cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 209 — import-gaten dichten (na S208-veldaudit)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context: `docs/research/S208-veldaudit-basenet.md` (de veldaudit — vooral §2, §3,
§4 en §8).

## Taak
De S208-audit vond concrete gaten in de BaseNet-overzetting. Dicht ze, **elk onderdeel als
losse stap met dry-run + akkoord Arsalan vóór schrijven op prod** (het zijn prod-datamutaties):

1. **Dossiernotities + waarschuwingen** (grootste winst, vóór de fase-heropening):
   99 `pmemo`-werknotities + 13 `palert`-waarschuwingen uit de export → toevoegen aan
   `Case.debtor_notes` (alert bovenaan, herkenbaar gemarkeerd, idempotent via de bestaande
   BaseNet-marker). Export staat in de projectmap: `Xml_02-07-2026_2400.zip`; parser:
   `scripts/basenet/parse.py`.
2. **Land bij adressen:** kolommen `visit_country`/`postal_country` op contacts (migratie —
   let op RLS-regel geldt niet, contacts heeft al RLS; gewone kolom-toevoeging) + backfill
   uit de export (52 niet-NL-relaties) + tonen in relatie-detail alleen indien gevuld +
   meenemen in briefadressering.
3. **Kleine backfills:** `provisie_percentage` (39 zaken, 15%, veld bestaat al op Case) en
   `date_of_birth` (28 personen, veld bestaat al op Contact).
4. **Mapping structureel** (voor de volgende verse export): `incinteresttype`,
   `incssamengesteld`, `pmemo`, `palert`, landen, provisie, geboortedatum opnemen in
   `scripts/basenet/mapping.py` — zie rapport §8.5.

## Verificatie
- Relevante tests: `docker compose exec backend python -m pytest tests/ -k "basenet or contact" -q`
  (géén full suite; container-aanroep is `python -m pytest`)
- Lint: `uvx ruff check backend/app/` (lokaal, vóór push)
- Frontend geraakt? `cd frontend && npx tsc --noEmit`
- Elke prod-mutatie: dry-run-rapport tonen → akkoord → uitvoeren → tel-verificatie achteraf

## Constraints (wat NIET doen)
- GEEN rente-wijzigingen: de rente is in S208 eind-geverifieerd (607/607 conform, ijk op de
  cent) — rapport §7b. Niet opnieuw openen.
- BSN's (3 in de export) bewust NIET importeren (AVG/dataminimalisatie).
- Mailslot blijft DICHT. Geen `git add -A` (expliciete paden). Parallelle S207-track
  (PROMPT-S207.md, ander venster) niet mengen.
- WIK-rentebijlage alleen oppakken als Arsalan meldt dat de KvK-API-sleutel er is.

## Commit
Commit + push naar main met conventional commit message per afgerond onderdeel.
Deploy automatisch via SSH (skill `deploy-regels`); migratie-volgorde: build → migrate → up.
