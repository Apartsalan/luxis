# Sessie-prompt S198 — AUTONOOM bouwblok 3 (klus 1-4) + Fable-review + Codex code-review

Kopieer alles onder de streep in een nieuwe sessie. **Model: Opus** (check met `/model`).
Arsalan is weg en wil bij terugkomst een AFGEROND, gereviewd, uitgerold resultaat.

---

cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 198 — AUTONOOM bouwblok 3: bouw klus 1-4, deploy per klus, daarna Fable-review + Codex code-review

## Werkmodus: AUTONOOM
Arsalan is niet beschikbaar. **Stop NIET om goedkeuring te vragen.** Bouw klus 1 t/m 4,
deploy elk per stuk via SSH (skill `deploy-regels`), en doe daarna de review-ronde. Twijfel je
over een ontwerpkeuze → maak de meest verdedigbare keuze, noteer 'm in de sessie-notities, en
ga door. Laat NOOIT een half-kapotte toestand achter: liever een klus veilig afbakenen +
documenteren wat is uitgesteld dan iets brekends deployen.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- `docs/plans/PLAN-fase2-bouwblokken.md` — besluiten per punt (stapel 3, rij 9-13).
- Werkorder-detail: B3 in `docs/research/audit-DB-kernmotor.md`; A3/A5/A7 in `docs/research/audit-DA-werkschil.md`.
- De S197-entry in SESSION-NOTES.md — daar staat het klus-1-onderzoek + de MET ARSALAN AFGESTEMDE aanpak.

## Taak 1 — B3: status versimpelen tot 4 + "Stap"-filter (aanpak is AFGESTEMD, bouwen)
Onderzoek is al gedaan (S197-entry). Feit: `workflow_statuses/transitions/rules` zijn leeg → élke
statuswijziging faalt, "Volgende stap"-knoppen kapot, statusfilter leeg, auto-"betaald" vuurt nooit,
`date_closed` nooit gezet, de pijplijn→status-koppeling (S166, `incasso/service.py`) checkt het lege
systeem en vuurt dus nooit. **Bouw de afgestemde aanpak:**
- **Status = 4 vaste waarden:** `nieuw` / `in_behandeling` / `betaald` / `afgesloten`. Labels NL in
  de frontend-constanten (`status-constants.ts`, `zaken/[id]/types.tsx`, DossierHeader).
- **Pijplijn stuurt de status:** repareer de DODE koppeling in `incasso/service.py`
  (`STEP_NAME_TO_STATUS` + de `WorkflowStatus`-existence-check die nooit vuurt) → zaak op een stap =
  status `in_behandeling`; eindstappen "Betaald"/"Afgesloten" → die status. Vervang de check tegen de
  lege `workflow_statuses`-tabel door de nieuwe 4-status-logica.
- **Auto-"betaald" repareren:** `app/workflow/hooks.py::on_payment_received` roept nu
  `validate_transition` aan die op de lege tabellen faalt. Zet bij €0-openstaand direct
  `status=betaald` + `date_closed` (BEHOUD de bestaande €0-guard + de import-skip
  `_skip_workflow_hook`). Draai de dode workflow-engine hier NIET meer.
- **Afsluiten/Heropenen** i.p.v. de kapotte `NEXT_STATUSES`-knoppen in `DossierHeader.tsx`:
  Afsluiten → `afgesloten` + `date_closed`; Heropenen → terug naar `nieuw`/`in_behandeling` +
  `date_closed` leeg. Backend-endpoint(s) simpel houden (geen workflow-engine).
- **Statusfilter Dossiers-lijst** = de 4 vaste waarden (nu lege dropdown).
- **NIEUW "Stap"-filter op de Dossiers-lijst** (Arsalans punt: kunnen filteren op alle zaken op
  sommatie/dagvaarding/vonnis = de pijplijn-STAP, niet status). Query-param op de cases-lijst-endpoint
  (`incasso_step_id`) + dropdown gevoed uit `list_pipeline_steps`.
- **Datamigratie:** zaken mét pijplijn-stap en niet-terminaal → `in_behandeling`; `nieuw` zonder stap
  blijft `nieuw`; `afgesloten` (580) onaangeraakt. Idempotent, guarded.
- **Traceer ALLE callers** van `execute_transition`/`validate_transition`/`get_status_by_slug` en van
  `cases.status` vóór je iets vervangt (grep). Controleer dat blijft werken: verjaring-monitor
  (filtert op terminale status), incasso-wachtrijen (`status.notin_(['betaald','afgesloten'])`),
  sjabloon-suggesties per status (`STATUS_TEMPLATE_MAP`).
- **NIET slopen:** de lege `workflow_statuses/transitions/rules`-tabellen laten staan (veegsessie-
  voorstel). Alleen de code die erop leunt omleiden naar de 4-status-logica.

## Taak 2 — A5: classificatielijn op pauze, meldingen/badges uit (besluit S191)
Meldingen van classificaties uit; "AI-suggestie"-badges/actieblok ontkoppelen van pending-
classificaties. **De 473 wachtende classificaties NIET verwerken en NIET verwijderen** — lijn staat
op pauze. Detail: A5/B6/A11/C9 in de audits.

## Taak 3 — A3: Mijn Taken → dagstart-lijst (ontwerp autonoom)
Herontwerp de Taken-pagina tot een bruikbare dagstart (Lisanne's dagelijkse startpunt), of ontdubbel
tot pure takenlijst. Arsalan is er niet om een voorstel goed te keuren → **maak de meest verdedigbare
keuze, documenteer 'm in de notities, bouw 'm**. Houd 't simpel en Lisanne-proof. Detail: A3 in
`audit-DA-werkschil.md` (o.a. de dubbeltel-badge 19-vs-"Alles gedaan").

## Taak 4 — A7: sjabloonbeheer alleen in Instellingen (besluit S191)
Sjabloonbeheer blijft/hoort in Instellingen; **documentenbibliotheek = LATER, niet bouwen**. HTML-tab
weg (UI, geen data), slug-titels fixen. Detail: A7 in `audit-DA-werkschil.md`.

## Review-ronde (ná klus 1-4 gebouwd + gedeployd)
1. **Fable-review** (subagent, want jij draait op Opus): `Agent`-tool met `model: "fable"` op de
   volledige S198-diff (`git diff` sinds tag `sessie-197`). Focus: financial precision (Decimal),
   multi-tenant/RLS, async, en vooral de **status-migratie-correctheid** (geen zaak in verkeerde
   status/ongewenst gesloten).
2. **Codex code-review:** `scripts/codex-review.sh <promptfile> <outfile> ultra` op de achtergrond
   (geen tijdslimiet — hartslag-bewaker). Prompt = review dezelfde diff, read-only.
3. **In gesprek:** speel Codex' bevindingen aan de Fable-subagent en andersom; verifieer elke
   bevinding ZELF in de code vóór je fixt (neem niks blind over); fix bevestigde punten.
4. Fixes committen + pushen + deployen; live doorklikken op prod (seidony@ / Playwright).

## Verificatie (per werkorder, niet pas aan het eind)
- Backend: `docker compose exec -T backend python -m pytest tests/ -k "<relevant>" -v`
- Lint: `uvx ruff check backend/app/` · Frontend: `npx tsc --noEmit` + `npm run build`
- Deploy via SSH (skill `deploy-regels`), containers healthy checken, live doorklikken.

## Constraints
- ⚠️ **MAIL BLIJFT UIT.** De mailslot-knop staat op UIT (env-noodslot is er in S197 afgehaald). NIET
  openzetten, niets doen wat mail verstuurt. Bouwen raakt de mailslot niet.
- Alleen de blokken uit het plan; extra vondsten = noteren als voorstel, niet bouwen.
- **Geen autonome verwijdering van DATA** (de 473 classificaties, testdossiers, test-aanvragen blijven
  staan — dat is veegsessie mét akkoord). UI-verwijdering (HTML-tab in klus 4) mag wel.
- Financial precision (Decimal), RLS bij nieuwe tenant-tabel in dezelfde migratie — zie CLAUDE.md.

## Commit
Per werkorder committen + pushen (conventional commits); deploy zelf via SSH; containers healthy
checken. Afsluiten met `/sessie-einde` (notities, roadmap, archiefregels, tag sessie-198).
