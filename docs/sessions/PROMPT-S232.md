cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 232 — Doorschuiven op de sjabloon-verzendroute (kruispunt-fix)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities, scant modules/pagina's,
laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context: `docs/sessions/S230-werkorders.md` (S230/S231-verslag).
Model: **Opus** voor het bouwwerk; wissel naar Fable voor de review aan het eind
(vaste cyclus — memory `feedback_model_choice`).

## Taak 1 — Sjabloon-verzendroute moet doorschuiven (HOOFDTAAK)

Arsalan verstuurde in de demo een eerste sommatie via de mail-dialoog met sjabloon.
De mail ging goed de deur uit, maar het dossier bleef op "Eerste sommatie" staan.
Zijn verwachting is terecht: **een eerste sommatie stuur je met een sjabloon, niet
met AI** — dus juist die route moet doorschuiven.

**Hoe het nu is (gemeten S231):** alleen `POST /api/incasso/cases/{id}/advance-after-send`
(`backend/app/incasso/router.py`, ~r360) schuift door, en die wordt aangeroepen vanuit
de AI-conceptflow. De gate is `is_step_draft = draft.intent in (None, "next_step")` —
antwoorden en vrije berichten bewegen de pijplijn bewust nooit (huisregel P1). De
compose-route (`backend/app/email/compose_router.py::send_email`) doet dit niet.

**Wat er moet gebeuren:** als een verse dossier-mail aan de debiteur wordt verstuurd
met een `template_type` dat hoort bij de HUIDIGE pijplijnstap, dan na succesvolle
verzending doorschuiven volgens dezelfde `advance_to_step`-regel. De bouwstenen zijn er:
- `_derive_step_template_type(case, recipients)` in compose_router leidt het brieftype
  al af (wordt gebruikt voor het renteoverzicht);
- `move_case_to_step` in `incasso/service.py` is de enige juiste manier om te bewegen
  (legt CaseStepHistory + pijplijn-activiteit vast).

**Randvoorwaarden (niet onderhandelbaar):**
- Antwoorden (`reply_to_message_id`), doorsturen en vrije berichten schuiven NOOIT door
  (huisregel P1) — ook niet als er toevallig een sjabloon is gekozen.
- Herverzenden mag niet dubbel doorschuiven: is het dossier al verder, dan hoort het
  sjabloon niet meer bij de huidige stap → niets doen.
- Alleen bij `status == "sent"`; een mislukte verzending beweegt niets.
- Log de verzending op de HUIDIGE stap vóór het doorschuiven (zelfde volgorde als
  `advance_after_send`), anders verdwijnt het bewijs uit de staphistorie.

**Wachter (skill `breed-testen`, de SOORT):** één test die ALLE verzendroutes afloopt
en toetst: stap-brief → schuift door; antwoord/vrij bericht → schuift niet door. Niet
één test voor het ene gefixte geval. Patroon: `test_office_channel_guard.py` /
`test_send_route_drift_guard.py`.

**Daarna, met GO:** IN100605 handmatig naar "Tweede sommatie" (de sommatie ging op
20-7 succesvol de deur uit, dossier bleef staan).

## Taak 2 — Kleine open punten (zover de tijd reikt)
- **BaseNet-delisting melden.** Hun uitgaande relay 194.180.216.120 staat op Microsofts
  blokkadelijst (550 5.7.1, S3150). Wij omzeilen het via M365, maar het raakt ook mail
  buiten Luxis om. Conceptmail: zie SESSION-NOTES entry S230/S231.
- **Derde AI-testronde** (`scripts/ai/antwoord_testronde.py`, via `docker compose run`
  met `/opt/luxis/scripts` gemount — zie skill `deploy-regels`, valkuil docker cp).
  Meet het effect van de twee laatste ingrepen. Kost ± 110 AI-aanroepen → EERST GO
  vragen i.v.m. het kostenpunt.
- **Lisanne-steekproef** op de eerste echte auto-conceptbatch (draait dagelijks 08:00 UTC).
- **Kostenblokje op het dashboard** (voorstel, niet gebouwd): `SELECT purpose, count(*),
  sum(cost_usd) FROM ai_usage GROUP BY 1` — vraag eerst of Arsalan het wil.

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail; hotmail werkt nu
ook via M365). MAILSLOT OPEN. Elke prod-mutatie: dry-run/telling + GO + natelling. Geen
`git add -A`. Bayar IN100613 niet aanraken. Kruispunt-check bij elk gedeeld effect. KvK:
niet naar vragen. Deploy via SSH mét `--force-recreate`.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "incasso or send or compose" -v`
- Lint: `uvx ruff check backend/app`
- Frontend (bij UI-wijziging): `cd frontend && npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.
- Live natelling in de prod-DB (read-only) dat het doorschuiven écht klopt.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-232 + PROMPT-S233; verplaats PROMPT-S230 en ouder naar `docs/archief/prompts/`).
