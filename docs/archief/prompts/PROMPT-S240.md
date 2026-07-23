cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 240 — twee functies bouwen (bak-melding + belofte-bewaking), daarna testronde 2

## Model
Deze sessie is BOUWWERK → **Opus**. Check bij start welk model actief is (statusregel of
`/model`); staat er Fable, wissel dan eerst naar Opus. De testronde-2-analyse aan het eind
mag op Opus blijven (klikwerk); alleen als er een groot ontwerpvraagstuk opduikt →
signaleren en Arsalan laten wisselen naar Fable (memory `feedback_model_choice`).

## Start
Lees `SESSION-NOTES.md` entry S239 + het logboek `docs/sessions/S239-SCENARIOS.md`
(daar staan de vondsten, de voorstel-lijst en de eindstand per scenario). De
verbindingskaart (`docs/ARCHITECTUUR-KAART.md`) laadt automatisch.

**Vraag bij start éérst:** zijn de 2 gevonden mails al beantwoord? (IN100128
update-verzoek Invorderingsbedrijf 13-7, IN100586 uithanden-mail 17-6 — beide staan
sinds S239 op hun dossier.) Zo nee: aanbieden om concepten klaar te zetten (NIET
versturen zonder GO).

## Hoofdtaak 1 — melding/teller ongesorteerde mailbak (GO Arsalan 23-7)
Een inkomende mail die nérgens aan koppelt valt nu stil in de ongesorteerde bak
(Mail-pagina): 44 stuks totaal, 2 échte zakelijke mails bleven er 9 dagen / 5 weken
hangen (S239-meting). Bouw:
- Melding bij elke nieuwe ongesorteerde inbound-mail (zelfde recept als
  `case_closed_invoice` in `notifications/service.py`: alle actieve gebruikers,
  `create_notification_if_not_exists`-dedupe). Doorklik → Mail-pagina, ongesorteerd-filter.
- Badge-teller "ongesorteerd" op de Mail-pagina (aantal open, niet-dismissed).
- Kruispunt-check: de eigen-afzender-poort (S236) en dismissed-mails mogen NOOIT
  melden; BaseNet-importaccount uitsluiten. Wachter voor de melding-route.

## Hoofdtaak 2 — betaalbelofte-bewaking (GO Arsalan 23-7)
De mail-beoordeling herkent een betaalbelofte al perfect (categorie
`belofte_tot_betaling`, `promise_date` + `promise_amount` op de classificatie — live
bewezen in S239), maar níets kijkt ooit naar die datum. Bouw:
- Taak "Betaalbelofte controleren — {zaaknummer}" met due = promise_date, aangemaakt
  bij de classificatie (zelfde recept als `ensure_arrangement_request_task` uit S235:
  direct bij herkennen, dedupe op open taak, geen taak bij gesloten/betaalde zaak).
- Sluit de taak automatisch als de zaak vóór/op de beloofde datum volledig betaald
  raakt (haak aan `on_payment_received` of check bij taak-weergave — kies de
  eenvoudigste route en documenteer de keuze).
- Wachters: taak bij belofte-classificatie; geen taak bij gesloten zaak; geen dubbele
  taak bij tweede belofte-mail; taak dicht na volledige betaling.

## Daarna (als beide LIVE + nageteld zijn) — testronde 2, brillen van Arsalan:
1. **Slordige gebruiker:** tikfouten, dubbelklikken, rare invoer (0, negatief, komma's,
   te lange teksten), halverwege stoppen, terug-knop, twee tabs. Vooral op: dossier
   aanmaken, vordering/betaling invoeren, regeling-formulier, compose-venster.
2. **Klik-ronde als Lisanne:** met Playwright (of Chrome-extensie) als
   seidony@kestinglegal.nl door de echte schermen: ochtendronde (dashboard → taken →
   mail), dossier openen, concept reviewen, betaling boeken — desktop én mobiel formaat.
   NIETS versturen zonder GO; testkanaal 2026-00006.
Zelfde discipline als S239: verwacht resultaat vooraf per scenario, vondsten in drie
bakken (fout → fixen met rode test eerst; ergernis → fixen; gemis → voorstel-lijst),
elke prod-mutatie terugdraaien + natellen, logboek bijhouden
(`docs/sessions/S240-SCENARIOS.md`).

## Constraints
Geen echte debiteuren/cliënten mailen zonder expliciete GO per verzending; testkanaal
2026-00006. Geen `git add -A`. Deploy via SSH mét `--force-recreate`. Eén testrun
tegelijk. KvK: niet naar vragen. Prod-datamutaties: dry-run + natelling + GO (de
opruimronde — spooktaken, oude testdossier-taken — is van Arsalan+Lisanne samen, NIET
zelfstandig doen). S238-huisregel: prompt-JSON-instructie gewijzigd → schema mee
(wachters in `tests/test_kimi_client_structured.py`).

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v`
- Lint: `uvx ruff check backend/app` | Frontend geraakt → `npx tsc --noEmit`
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde`-recept: SESSION-NOTES max 10 entries + roadmap één prioriteit-sectie +
git tag sessie-240 + PROMPT-S241; verplaats PROMPT-S239 en ouder naar
`docs/archief/prompts/`.

## Losse punten (niet deze sessie tenzij tijd over)
Voorstel-lijst 3-7 uit S239 (meldingen bundelen, categorie 'onduidelijk',
overbetaling-knop, cascade dossier-verwijderen, weekend-logica), Lisanne-antwoorden
(IN100592/IN100606/IN100492), BaseNet-delisting, derde AI-testronde (± 110 calls →
eerst GO), kostenblokje dashboard, opmaak-restpunt S227, S221b-rest, DMARC, testdata
opruimen, 4 cosmetische restjes S235, sharp/libvips-CVE's.
