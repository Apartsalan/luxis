cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 234 — Incassostappen kritisch herzien

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities, scant modules/pagina's,
laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context: entries S232 + S233 + S233b in `SESSION-NOTES.md` (deze sessie
borduurt daarop voort). Model: **Fable** voor het onderzoek/ontwerp (breed, in de bron
meten), **Opus** voor het bouwwerk; Fable weer voor de review aan het eind (vaste
cyclus — memory `feedback_model_choice`; wissel ACTIEF signaleren).

Sinds S233b (21 juli, tussen S233 en deze sessie in): uitgaande mails dragen nu een
draad-kenmerk (provider_thread_id via `write_outbound_log`), de Outlook-antwoordroute
is gerepareerd (RFC-/basenet-ids en bijlagen via sendMail, alleen echt Graph-id kaal
via /reply — wachter `test_outlook_reply_routing`), en het compose-paneel waarschuwt
als de AI facturen wil bijsluiten die het dossier niet heeft. Raak je verzendroutes
aan, weet dat deze er net liggen.

## Achtergrond (waarom deze sessie)
S232 liet de sjabloon-verzendknop (compose/send) doorschuiven naar de volgende stap,
op dezelfde regel als de AI-conceptroute (advance-after-send). Twee dingen bleven staan:
1. **Derde/laatste sommatie hebben géén brief gekoppeld** → die stappen schuiven daarom
   NOG NIET door (mechaniek dekt het zodra er een brief aan hangt — S232-grens).
2. **Batch- en follow-up-route** houden nog hun eigen "volgende in de lijst"-logica,
   los van de gedeelde `advance_after_step_send()`-helper.
Bovendien wil Arsalan de incassostappen zelf herzien: een platte lijst voelt te rigide;
hij denkt aan situatie-stappen (de vervolgstap hangt af van wat er gebeurt: betaling,
verweer, betalingsregeling, stilte).

## Taak 1 — HOOFDTAAK: stappen-model kritisch herzien (ONDERZOEK EERST)
**Meet in de bron** (skill `fable-diepte` + `breed-testen`): welke pijplijnstappen
bestaan er nu echt in prod (`incasso_pipeline_steps`), welke dragen een brief/sjabloon,
welke niet, en welke "volgende stap"-logica's leven er (compose/send + AI-route via
`advance_after_step_send`, batch, follow-up). Breng in kaart vóór je iets voorstelt.
Presenteer daarna een ontwerp (Plan Mode): situatie-stappen i.p.v. platte lijst.
NIET bouwen vóór akkoord op het ontwerp — dit raakt de kern van de pijplijn.

## Taak 2 — derde/laatste sommatie een brief koppelen
Zodra het ontwerp staat: koppel een brief/sjabloon aan de derde en laatste sommatie zodat
die stappen ook doorschuiven na verzending (de S232-mechaniek dekt het dan zonder
codewijziging — bewijs dat met een wachter).

## Taak 3 — batch + follow-up op dezelfde doorschuif-logica
Trek de batch- en follow-up-verzendroute op dezelfde gedeelde helper
(`advance_after_step_send`) als compose/send + AI-route. Wachter over de HELE
route-matrix (skill `breed-testen`): elke stap-brief-route schuift door, elke
antwoord/vrij/herverzending doet dat NIET.

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail; hotmail via M365).
MAILSLOT OPEN. Elke prod-mutatie: dry-run/telling + GO + natelling. Geen `git add -A`.
Kruispunt-check bij elk gedeeld effect. KvK: niet naar vragen. Deploy via SSH mét
`--force-recreate`. Inlognaam Lisanne: kesting@kestinglegal.nl.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "incasso or advance or step or send" -v`
- Lint: `uvx ruff check backend/app`
- Frontend: `cd frontend && npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-234 + PROMPT-S235; verplaats PROMPT-S232 en ouder naar `docs/archief/prompts/`).

## Vooruitblik (niet deze sessie)
- **S235** — betalingsregeling herkennen uit mail (classificatie bestaat al) + flexibel
  termijnschema (2× €200, daarna €1.000 — elke termijn heeft al zijn eigen bedrag/datum).
- Losse punten: BaseNet-delisting melden, derde AI-testronde (± 110 calls → eerst GO),
  Lisanne-steekproef auto-conceptbatch, kostenblokje dashboard, Outlook-route weghalen,
  AI-antwoord-generatieflow van S233 op een fysieke telefoon natrekken (zijpaneel + draad
  + factuur-voorselectie).
