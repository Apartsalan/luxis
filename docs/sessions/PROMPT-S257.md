cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 257 — testdossiers uit Lisannes lijsten (en uit de ochtendmail)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): entry **S256** in
`SESSION-NOTES.md` en `docs/audits/beoordeling-2026-09-04.md` (de beoordeling die deze
klus opleverde).

**Model:** onderzoek/oogst/review = Fable 5.1 (effort **high**, niet max), bouwen/klikwerk
= Opus. Signaleer de wissel zelf vóór je begint.

## Achtergrond (waarom dit nu de eerste klus is)
Sinds S256 krijgt Lisanne elke ochtend om 09:00 NL een samenvattingsmail met wat op haar
wacht. De eerste proefdraai meldde **37 brieven** — maar **14 daarvan zijn testdossiers**
(`2026-00006` t/m `2026-00020`, o.a. "TEST Debiteur Fable-review B.V." en de TEST10-reeks).
Die staan óók in de incassolijst, de follow-up-werklijst en het dashboardcijfer
("62 actieve dossiers" = 48 echt + 14 test). Een werklijst waarin een derde nep is, leert
haar de lijst te wantrouwen — precies wat we net probeerden op te lossen.

## Taak
De testdossiers markeren en uit de lijsten van de dagelijkse werkstroom filteren, **zonder
ze te verwijderen** — ze zijn nodig voor testrondes (zie de constraint over echte
debiteuren hieronder).

Denkrichting (niet dwingend, maar wél eerst meten vóór je bouwt):
1. Een `is_test`-vlag op `cases` (default `false`) is waarschijnlijk het eerlijkst.
   Patroonherkenning op het dossiernummer kan NIET: een écht nieuw dossier in Luxis krijgt
   ook een `2026-000xx`-nummer. Verifieer dat zelf in `generate_case_number`.
2. Filter de gemarkeerde dossiers uit: incasso-pijplijn, follow-up-aanbevelingen,
   dashboard-tellingen én `app/notifications/daily_summary.py` (de ochtendmail).
3. Ze moeten wél vindbaar blijven via zoeken/directe link, anders kun je er niet meer mee
   testen.
4. Nieuwe tabel of kolom → check de RLS-regel in `CLAUDE.md` (migratie + `apply_rls`).

**Wachter éérst, dan pas fixen** (S255/S256-les, drie keer bewezen): draai de nieuwe wachter
tegen de ONgefixte code en kijk of hij rood wordt en de juiste regels aanwijst. Sloop daarna
de regel weer om te zien of hij bijt — in S256 vond die sabotage-proef nog een gat in de
wachter zelf (de blokvorm van een reduce glipte door de eerste regex).

## Daarna (alleen als er tijd over is, en het is een KEUZE van Arsalan)
Arsalans privé-post (Hetzner-facturen, Philips Hue-nieuwsbrieven) staat in de maillijst
omdat `seidony@` als kantoormailbox meesynct; 63 mails staan op "ongesorteerd". Die mailbox
leverde in 30 dagen 4 echte inkomende dossiermails. Opties: ontkoppelen, of bulkpost
automatisch wegzetten. **Eerst voorleggen aan Arsalan — het is zijn mailbox.**

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -v` (of gericht: `-k "test|case"`)
- Lint: `uvx ruff check backend/app/` (ruff zit niet in de container sinds S162)
- Build: `cd frontend && npx tsc --noEmit && npm run build`
- Na uitrol: de ochtendmail één keer proefdraaien naar **alleen** seidony@ en natellen dat
  het aantal brieven met 14 is gedaald:
  `docker compose exec -T backend python -c "import asyncio, app.main; from app.notifications.daily_summary import send_daily_summaries; print(asyncio.run(send_daily_summaries(only_to='seidony@kestinglegal.nl')))"`

## Constraints (wat NIET doen)
- **Testdossiers niet verwijderen of afsluiten** — ze blijven nodig om mee te testen.
- Geen echte debiteuren mailen. Testdossiers netjes terugzetten na gebruik.
- Fase-heropening van de resterende ~395 dossiers: NIET zonder GO per groep.
- Geen kennisregels aanraken.
- Nooit `git add -A` (de hook blokkeert het) — stage expliciete paden.
- `npm audit fix --force` NOOIT op de frontend (zet Next terug naar 14). Zonder `--force`
  mag wél; dat is in S256 gedaan.
- Etiket omzetten (b2c↔b2b) op een dossier: alleen met GO per dossier.

## Bekende valkuilen (kosten je anders een half uur)
- **Eén pytest-run tegelijk.** `docker compose exec -T backend pkill -f pytest` vóór een
  nieuwe run.
- **Testgereedschap in de dev-container is met de hand geïnstalleerd** en verdwijnt zodra de
  container hercreëerd wordt. Herstellen:
  `docker compose exec backend sh -c 'cd /app && uv export --frozen --extra dev --no-emit-project -o /tmp/r.txt && UV_LINK_MODE=copy uv pip install --python $(which python) --target /home/appuser/.local/lib/python3.12/site-packages -r /tmp/r.txt'`
- **Playwright-schermafdrukken direct na `navigate` tonen skeletons.** Eerst ~3 seconden
  wachten via `browser_evaluate`, dán de afdruk maken (S256-les).
- **Visueel controleren zonder wachtwoorden:** haal een token via `POST /api/auth/login`
  (curl) en zet dat met Playwright in `localStorage` (`luxis_access_token` /
  `luxis_refresh_token`). Nooit inloggen als Lisanne.
- Bash-heredocs met Nederlandse tekst en apostrofs breken; schrijf zulke scripts naar een
  bestand in de scratchpad en draai dat (S256-les). Commit-messages via `git commit -F -`.

## Voor Lisanne (inhoudelijk, niet zelf oppakken)
- **IN100515**: de rente staat bevroren op 9 juni terwijl het dossier openstaat (regeling die
  zij op 6 augustus zelf aanmaakte). Als dat niet bewust is, loopt daar geen rente.
- **KvK-nummer 72908475** op de contactkaart van Kaandorp (IN100077) — staat op de bel.
- Horen 'aanmaning' en 'tweede_sommatie' in menugroep 2?
- 143 mail-classificaties, 26 AI-concepten en 3 intakes wachten op haar beoordeling.

## Commit
Commit + push naar main met conventional commit message. Deploy via SSH volgens skill
`deploy-regels` (frontend en/of backend). CI natrekken. `/sessie-einde` (volgende = S258).
