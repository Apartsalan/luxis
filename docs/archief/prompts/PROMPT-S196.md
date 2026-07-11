# Sessie-prompt S196 — bouwblok 2 afmaken (termijn-vooruitblik + 3 proefzaken)

> ⚠️ **ACHTERHAALD (11 juli, avond): Taak 1 (C1 bankimport) is in S195 al UITGEVOERD.**
> 17 betalingen geboekt (€14.922,60) incl. Saltik 4×€50, 10 zaken heropend, 12 onverklaarde
> credits per besluit Arsalan niet geboekt (geen incassozaken), derdengelden blijft Lisanne's
> BaseNet-maandproces. Zie SESSION-NOTES S195 + Fable-hercontrole in `S195-1op1-audit.md`.
> **Alleen Taak 2 en Taak 3 zijn nog te doen.**

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** (check met `/model` dat je
NIET op Fable zit; bouwen doen we op Opus). Codex (alleen-lezen tegenlezer) mag meekijken op
bouw-wijzigingen vóór deploy.

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 196 — bouwblok 2 afmaken: C1 bankimport-proef (samen) → B4/A8 termijn-vooruitblik → B11 3 proefzaken

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/sessions/S195-1op1-audit.md` — de grondige betalingsaudit (LEES DIT EERST): alles klopt
  1-op-1, 64 betalingen gecapt (met heropenings-notities al op de dossiers), en de sterk
  ingekorte bankimport-beslislijst.
- `docs/sessions/S195-bankimport-indeling.md` — complete indeling van alle 212 afschrift-credits.
- `docs/plans/PLAN-fase2-bouwblokken.md` — de blokken + besluiten.
- CSV in repo-root: `CSV_A_NL20RABO0388506520_EUR_20250709_20260709.csv`; BaseNet-export:
  `Xml_02-07-2026_2400.zip`.

## Taak 1 — C1 eerste bankimport-proef, SAMEN met Arsalan (KERN)
⚠️ Dit boekt echt geld/derdengelden op prod → **niet blind, per beslissing met Arsalan.**
De audit (S195) heeft de lijst sterk verkleind — B/C uit de oude droogloop waren GEEN gaten
maar al-geboekte (gecapte) betalingen. Resterende echte beslispunten:
- **138 al geboekt** — bij import per stuk afwijzen of vooraf uitsluiten (H17-dedup ziet ze niet;
  ze liepen buiten de import-pijplijn om).
- **17 echt-nieuw (na 30 mei, €8.836,39)** — 11 al doorgestort aan opdrachtgever, 6 nog op de
  rekening (~€1.678,51). Boeken op afgesloten zaak of eerst heropenen? Beslissing Arsalan.
- **Saltik IN100345** — regeling loopt door, 4×€50 ontvangen (apr/mei/jun/jul) niets geboekt,
  telkens doorgestort. Bijboeken of laten?
- **21 onbekende zaken (€39.565,49, D-/FN-nummers)** — negeren of dossiers aanmaken?
- **Derdengelden-ijkpunt** — Luxis-ledger leeg (0 transacties) vs banksaldo €12.544,99 (8 juli).
  Kies een ijkdatum en boek vanaf daar in+uit volledig; historie reconstrueren = handwerk.
- Voer de import uit via de Bankimport-pagina (`/betalingen`) of gericht per transactie; verifieer
  na afloop in de app (matches, derdengeldensaldo, art. 6:44-verdeling).

## Taak 2 — B4/A8 termijn-vooruitblik (bouwen, alleen overzicht over zaken heen)
Op dossierniveau bestaat dit al (Betalingen-tab). Bouw ALLEEN het overzicht óver zaken heen:
één lijst van aankomende regeling-termijnen (welke zaak, welk bedrag, welke datum). Onderzoek
eerst waar dit past (dashboard-blok of eigen pagina), presenteer kort, dan bouwen.

## Taak 3 — B11 stappen voor de 3 proefzaken
Zet de 3 proefzaken een stap verder in de pijplijn (details in `PLAN-fase2-bouwblokken.md`).
Per zaak bevestigen met Arsalan.

## Voorstel dat blijft liggen (alleen bouwen als Arsalan het wil)
Automatisch slot/waarschuwing bij heropening van een zaak met een `[S195-audit]`-notitie
(gecapte betaling) — nu vangen de 64 handmatige notities het af.

## Alternatief — als Arsalan niet beschikbaar is voor de import
Begin met **bouwblok 3**: B3-versimpeling (status volgt pijplijn), A5-pauze, A3 dagstart-lijst,
A7 sjablonen op één plek.

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec backend pytest tests/ -k "<relevant>" -v`
- Lint: `uvx ruff check backend/app/` · Frontend (indien geraakt): `npx tsc --noEmit` + `npm run build`
- Codex-tegenlezer (alleen-lezen) op de diff vóór deploy; verwerk echte vondsten.
- Live doorklikken in de prod-app ná deploy.

## Constraints
- ⚠️ **MAILSLOT:** check `OUTBOUND_MAIL_LOCK` in `/opt/luxis/.env` vóór iets dat mail kan
  versturen; alleen eraf op expliciet verzoek Arsalan (gepland ~13 juli).
- Alleen de blokken uit het plan; extra vondsten = noteren als voorstel, niet bouwen.
- Prod-mutaties (bankimport-boekingen, waarden) alleen ná expliciet akkoord Arsalan.

## Commit
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH (skill
`deploy-regels`), containers healthy checken. Afsluiten met `/sessie-einde` (notities,
roadmap, archiefregels, tag sessie-196).
