cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 233 — Mail-werkplek: antwoorden zonder de mails kwijt te raken

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities, scant modules/pagina's,
laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context: entry S232 in `SESSION-NOTES.md` (deze sessie borduurt daarop voort).
Model: **Opus** voor het bouwwerk; wissel naar Fable voor de review aan het eind
(vaste cyclus — memory `feedback_model_choice`).

## Taak 1 — AI-antwoord als zijpaneel i.p.v. los venster (HOOFDTAAK)

Klik je op een mail van de wederpartij en dan op "AI-antwoord", dan word je nu naar
een ándere pagina gestuurd en klapt daar een venster middenin het scherm open — de
mail waarop je antwoordt is dan weg. Arsalan wil kunnen blijven lezen tijdens het
schrijven.

**Wat er moet gebeuren:**
- Het opstel-/reviewvenster wordt een **zijpaneel** (rechts), zodat links de mails
  leesbaar en aanklikbaar blijven en je op de mailpagina blijft.
- **Onderin het paneel** de mail waarop je antwoordt **uitklapbaar**, met de eerdere
  mailtjes van de draad eronder (mailgeschiedenis).
- Geldt op alle drie de plekken waar het mailvenster leeft: de Mail-pagina, het
  dossier-tabblad Correspondentie én het documenten-tabblad (`EmailComposeDialog` +
  `AiReplyDialog`). Test alle drie door.

**Kruispunt-let-op (skill `breed-testen`):** dit raakt alleen de LEES/UX-kant, geen
verzendregel — maar de AI-antwoordroute (`POST /api/ai/draft`, intent reply_to_email)
blijft ongewijzigd: antwoorden schuiven de pijplijn NOOIT door (huisregel P1). Niet
per ongeluk de S232-doorschuiflogica raken.

## Taak 2 — AI luistert naar "doe de facturen erbij"

In een AI-antwoord vroeg Arsalan om de facturen mee te sturen; dat deed de AI niet.
Oorzaak (gemeten S231/S232): de AI levert alléén tekst — hij kan zelf geen bijlagen
toevoegen, dus de instructie ging verloren.

**Wat er moet gebeuren:** de AI geeft naast de tekst een signaal terug ("facturen
bijvoegen: ja/nee", afgeleid uit de behandelaar-instructie), en het concept opent dan
met de factuur-PDF's al aangevinkt (de gebruiker kan ze weghalen). De factuur-resolver
bestaat al (`AUTO_ATTACH_INVOICE_TYPES` / claims met `invoice_file_id`).

**Randvoorwaarden:** de dagelijkse auto-conceptbatch krijgt geen instructie → blijft
ongewijzigd. De spelregel "instructie van de behandelaar is leidend" (A3) blijft staan.

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail; hotmail werkt via
M365). MAILSLOT OPEN. Elke prod-mutatie: dry-run/telling + GO + natelling. Geen
`git add -A`. Kruispunt-check bij elk gedeeld effect. KvK: niet naar vragen. Deploy via
SSH mét `--force-recreate`. **Nieuwe inlognaam Lisanne: kesting@kestinglegal.nl (S232).**

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "ai or draft or compose" -v`
- Lint: `uvx ruff check backend/app`
- Frontend: `cd frontend && npx tsc --noEmit`
- Visueel: klik de AI-antwoordflow door op Mail + dossier-Correspondentie (Playwright,
  niets echts versturen) — mails moeten zichtbaar blijven naast het paneel.
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie + git tag
sessie-233 + PROMPT-S234; verplaats PROMPT-S231 en ouder naar `docs/archief/prompts/`).

## Vooruitblik (niet deze sessie)
- **S234** — incassostappen kritisch herzien: situatie-stappen i.p.v. platte lijst;
  derde/laatste sommatie een brief koppelen (dan schuiven ze ook door); batch/follow-up
  op dezelfde "volgende stap"-logica als compose/send + AI-route trekken.
- **S235** — betalingsregeling herkennen uit mail (classificatie bestaat al) + flexibel
  termijnschema (2× €200, daarna €1.000 — elke termijn heeft al zijn eigen bedrag/datum).
- Losse punten: BaseNet-delisting melden, derde AI-testronde (± 110 calls → eerst GO),
  Lisanne-steekproef auto-conceptbatch, kostenblokje dashboard, Outlook-route weghalen.
