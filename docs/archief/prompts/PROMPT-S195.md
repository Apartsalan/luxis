# Sessie-prompt S195 — bouwblok 2 afmaken (bankimport-proef + termijn-vooruitblik + 3 proefzaken)

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** (check met `/model`
dat je NIET op Fable zit; bouwen doen we op Opus). Codex (Sol Ultra, alleen-lezen) mag
als externe tegenlezer meekijken op bouw-wijzigingen vóór deploy.

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 195 — bouwblok 2 afmaken: C1 bankimport-proef (samen) → B4/A8 → B11

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/sessions/S194-bankimport-droogloop.md` — de droogloop + beslislijst 4 groepen (LEES DIT EERST).
- `docs/plans/PLAN-fase2-bouwblokken.md` — de blokken + besluiten.
- CSV staat in de repo-root: `CSV_A_NL20RABO0388506520_EUR_20250709_20260709.csv`.

## Vooraf — 2 kleine losse punten
1. **Kantoorrekening checken:** vraag Arsalan of `NL79KNAB0606569456` klopt (in S194 stond
   1 cijfer te weinig aangeleverd → via IBAN-checksum gereconstrueerd). Zo niet: corrigeren op prod.
2. **2 verweesde verjaringstaken** op afgesloten zaken (IN100015, IN100127) — van vóór de S193-fix.
   Vraag Arsalan of je ze mag afvinken (data-mutatie). Zo ja: op `completed` zetten.

## Taak 1 — C1 eerste bankimport-proef, SAMEN met Arsalan (KERN)
⚠️ Dit boekt echt geld/derdengelden op prod → **niet blind, per beslissing met Arsalan.**
- Neem de beslislijst uit `S194-bankimport-droogloop.md` door (4 groepen):
  - **138 al geboekt** (S179/S180) — MOETEN uitgesloten worden: H17-dubbel-herkenning ziet ze
    NIET (die boekingen liepen buiten de import-pijplijn om). Blind importeren + alles goedkeuren
    = honderden dubbele boekingen. Bepaal samen de veilige route (bv. alleen ná-30-mei importeren,
    of per match afzonderlijk beoordelen/afwijzen).
  - **17 echt-nieuw** (na 30 mei, €8.836) — meeste zaken staan op "afgesloten": boeken op
    afgesloten zaak of eerst heropenen? Beslissing Arsalan.
  - **29 gaten** op bekende maar afgesloten zaken (€43.744) — historie bijboeken of laten?
  - **22 onbekende** zaken (€40.462, D-/FN-nummers) — negeren of dossiers aanmaken?
- Voer de import uit via de bestaande Bankimport-pagina (`/betalingen`) of gericht per transactie;
  verifieer na afloop in de app (matches, derdengeldensaldo, art. 6:44-verdeling).

## Taak 2 — B4/A8 termijn-vooruitblik (bouwen, alleen overzicht over zaken heen)
Op dossierniveau bestaat dit al (Betalingen-tab). Bouw ALLEEN het overzicht óver zaken heen:
één lijst van aankomende regeling-termijnen (welke zaak, welk bedrag, welke datum), zodat
Lisanne in één blik ziet wat er deze/komende weken verwacht wordt. Geen groot status-systeem.
Onderzoek eerst hoe/waar dit past (dashboard-blok of eigen pagina), presenteer kort, dan bouwen.

## Taak 3 — B11 stappen voor de 3 proefzaken
Zet de 3 proefzaken een stap verder in de pijplijn (details in `PLAN-fase2-bouwblokken.md` +
D-C-rapport). Per zaak bevestigen met Arsalan.

## Alternatief — als C2/Arsalan niet beschikbaar is voor de import
Begin met **bouwblok 3**: B3-versimpeling (status volgt pijplijn), A5-pauze (classificatie/
meldingen uit), A3 dagstart-lijst, A7 sjablonen op één plek.

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec backend pytest tests/ -k "<relevant>" -v` (alleen relevante modules)
- Lint: `uvx ruff check backend/app/` · Frontend (indien geraakt): `npx tsc --noEmit` + `npm run build`
- Codex-tegenlezer (alleen-lezen) op de diff vóór deploy; verwerk echte vondsten.
- Live doorklikken in de prod-app ná deploy.

## Constraints
- ⚠️ **MAILSLOT:** stond aan t/m ~13 juli. Check `OUTBOUND_MAIL_LOCK` in `/opt/luxis/.env`
  vóór je iets doet dat mail kan versturen; alleen eraf op expliciet verzoek Arsalan.
- Alleen de blokken uit het plan; extra vondsten = noteren als voorstel, niet bouwen.
- Prod-mutaties (bankimport-boekingen, waarden) alleen ná expliciet akkoord Arsalan.

## Commit
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH (skill
`deploy-regels`), containers healthy checken. Afsluiten met `/sessie-einde` (notities,
roadmap, archiefregels, tag sessie-195).
