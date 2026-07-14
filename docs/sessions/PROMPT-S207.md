cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 207 — vervolg: M4 afmaken + uitrollen (blok 0 en L4/L5/L6 zijn al KLAAR)

## ✅ AFGEROND 14 juli (S211-sessie, Fable) — dit spoor is DICHT
- **Blok 0 KLAAR** (13 juli, Sonnet) — rapport `docs/sessions/S207-review-S205.md`; 3 must-fixes
  gebouwd, gecommit (`543789c`, `50f98fa`, `452f995`) én gedeployd.
- **L4/L5/L6 KLAAR + LIVE** — commit `584b63c` bleek al mee-uitgerold met de S210-deploy
  (VPS-controle 14 juli: staat op `4025d43`, waar `584b63c` een voorouder van is).
- **M4 AF** (14 juli): de twee halve bouwers uit de werkmap (`incasso_templates.py` escape-laag,
  `invoices/service.py`) afgemaakt met de ontbrekende derde (`ai_agent/followup_service.py`
  DOCX-route) én een VIERDE die de audit miste: `incasso/service.py::_build_step_email`
  (batch-pad, autoescape=False → gesplitst: onderwerp plat, body autoescape). Regressietests
  in `test_followup.py`, `test_incasso_templates.py`, `test_invoice_send_email.py`,
  `test_incasso_pipeline.py`. Gecommit op tak `s211-wik-rentebijlage` (aparte commits);
  gaat mee naar prod met de S211-merge na akkoord Arsalan.
- **Mini-checklist GROEN** (14 juli): alle 5 dagelijkse jobs + 7 overige in `scheduler_heartbeat`
  met verse `last_run_at` en lege `last_error`.
- **Nog open uit de oorspronkelijke lijst:** M5 (ontvangers-parser + 39-velden-opschoning,
  vergt apart akkoord) en sporen B/C — nieuw spoor, niet dit document heropenen.
Rest van dit document = oorspronkelijke opdracht (historie).

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): `docs/security/S202-delta-audit.md`
(bevindingen M4/M5/L4/L5/L6 met locaties + fix-recept per punt).

## Blok 0 — VERPLICHT eerst: Fable-review van de S205-fixes (besluit Arsalan, 13 juli)
Het S205-werk (7 commits `d440081`…`ee465b9`: 14-dagenbrief-gate op alle 3 verzendwegen +
verstuurd-proxy + "toch versturen"-noodknop + dagenbrief-sjabloon + mailsync-sessie-per-postbus +
heartbeat-last_error) is **nooit onafhankelijk gereviewd** — S204 reviewde S203, de S206-review
dekte alleen de S206-commits. Het is wél het juridisch gevoeligste stuk (art. 6:96 lid 6 BW,
Lisanne's beroepsrisico) en S205 noteerde zelf: gate niet live end-to-end getest (mailslot dicht,
beide actieve B2C-zaken stap-loos), frontend-noodknop alleen build/tsc.
Werkvorm zoals S206: adversariële Fable-subagent (model=fable, read-only) op de volledige diff
`d440081^..ee465b9` + het S204-review-rapport (`docs/sessions/S204-review.md` §Beslislijst als
toetssteen: dekt elke fix het punt écht?). Bevindingen ZELF verifiëren in de bron; must-fixes
direct bouwen (rood→groen→commit→push→deploy). Speciale aandacht: kan een sommatie nog langs één
van de drie wegen zónder gate? Telt de verstuurd-proxy echt alleen échte sends? Laat de override
altijd een spoor achter?

## Eerst: mini-checklist (klein, read-only)
Staan de 5 dagelijkse-job-rijen nu in `scheduler_heartbeat` op prod (ná 06:35 UTC)? Verwacht:
`daily_task_status_update`, `daily_verjaring_check`, `daily_deadline_notifications`,
`daily_installment_overdue_check`, `daily_invoice_overdue_check`. Read-only via SSH:
`docker compose exec -T db psql -U luxis -d luxis -c "SELECT job_id, last_run_at, last_error FROM scheduler_heartbeat ORDER BY job_id;"`
In S206 bewezen: alle 5 zijn geregistreerd + ingepland (opstartlog); ze verschijnen na de eerste
ochtendrun. Zo nee ná 06:35 UTC → uitzoeken waarom de dagelijkse jobs niet vuren.

## Taak — kies één spoor (leg de keuze kort aan Arsalan voor, met aanbeveling)

### A. Mail-verstevigingen (S202-restant) — AANBEVOLEN vervolg van S206
Werk per fix rood→groen→commit→push→deploy. **Mailslot blijft DICHT** — al deze fixes zijn
test-baar zónder mail te versturen (render-probe / schema-probe / unit).
- **M4 (MIDDEL) — HTML-injectie in systeemmails.** Dossierdata (omschrijving, factuurnummer, naam)
  gaat ongeëscapet via f-strings de mail-HTML in; `_render_branded` markeert alles als vertrouwd
  (`Markup`). Escape data-afkomstige tekst op de rendergrens, laat alleen eigen vaste HTML als
  `Markup`. Builders: `email/incasso_templates.py` (`_claims_table`, `_summary_row`, e.a.),
  `invoices/service.py:615-620`, `ai_agent/followup_service.py:476-495`. Regressietest met naam/
  kenmerk/omschrijving/factuurnummer met HTML-tekens (audit beschrijft de render-probe). ⚠️ Raakt
  de opmaak van júridische brieven — verifieer dat legitieme content niet breekt (bestaande
  `test_email_branding.py` + nieuwe test).
- **L6 (LAAG)** — CR/LF/NUL uit mailheaders/bestandsnaam strippen vóór loggen (`email/sync_service.py`
  onderwerp/message-id/bestandsnaam-logregels). Klein + regressietest.
- **L4 (LAAG)** — base64-bijlagecap vóór decoderen afdwingen (`compose_router.py:83-86,207-228`).
- **L5 (LAAG)** — mailslot-cache pas na succesvolle commit wijzigen (`email/service.py:73-86`).
- **M5 (MIDDEL) — ontvangers.** Code-kant: één centrale parser/validator + recipient-cap + route-
  rate-limit vóór elk transport. **De 39 bestaande adresvelden opschonen = aparte prod-data-migratie
  → EERST expliciet akkoord Arsalan, droogloop eerst.**

### B. S201 facturatie-import
439 conflict-vrije facturen; recept + droogloop-poorten in `docs/research/S201-facturatie-recept.md`.
Naar-buiten-gerichte schrijfactie op prod → **apart akkoord vereist**, droogloop eerst.

### C. S203-restpunten
35-route backend-sloop (eigen per-route-verificatie), #7 document-audittrail, #15 regeling-badge,
log-persistentie VPS.

## Verificatie
- Backend: `docker compose exec -T backend python -m pytest tests/ -k "<relevant>" -v` (relevante modules).
  Volledige suite alleen bij gedeelde-functie-wijziging — **detached draaien** (S206-les: achtergrond-
  taken worden gekild; `docker compose exec -d backend sh -c '... > /tmp/run.log 2>&1; echo done'` +
  pollen op het logbestand).
- Lint: `uvx ruff check backend/app/`
- Frontend geraakt? `cd frontend && npx tsc --noEmit && npm run build`.

## Constraints (wat NIET doen)
- Mailslot blijft DICHT; niets versturen.
- Geen prod-instellingen/data wijzigen zonder apart akkoord (m.n. M5's 39-velden-opschoning).
- Nooit `git add -A` — alleen expliciete paden stagen.
- Sporen niet mengen — kies er één.

## Commit
Commit + push naar main per afgeronde taak. Deploy via SSH (deploy-regels). Werk af met /sessie-einde.
