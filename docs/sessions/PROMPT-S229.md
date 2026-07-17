cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 229 — Mobiel-restpunten van de fysieke-telefoon-check + vervolg

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules/pagina's, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Extra taak-context: `docs/sessions/PLAN-S228-MOBIEL.md` (status-blok bovenaan =
wat er al ligt; §7 = bekende beperkingen).
Model: **Opus** voor klein fixwerk; wissel naar Fable bij onderzoek/review
(vaste cyclus — memory `feedback_model_choice`).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? Check `KVK_API_KEY` in `/opt/luxis/.env`
op de VPS. JA → eerst de rechtsvorm-backfill (`docs/archief/prompts/PROMPT-S217.md`
+ STAND in `docs/archief/prompts/PROMPT-S215.md`), dán de rest. NEE → direct door.

## Taak 1 — Mobiel-restpunten (EERST, kort)
S228 heeft Luxis volledig mobiel gemaakt en alles is bewezen in een nagebootst
telefoonscherm — maar NIET op een fysiek toestel. Arsalan klikt op zijn eigen
telefoon door (app-icoon via "Zet op beginscherm", inzoomen bij typen, randen
rond de notch, onderbalk, mail lezen/beantwoorden op 2026-00006, incasso-kaarten).
→ Vraag welke punten hij tegenkwam (één AskUser-vraag; screenshots welkom) en fix
gericht per punt. Niets tegengekomen → door naar Taak 2.

## Taak 2 — Vervolg (in deze volgorde, zover de tijd reikt)
1. **Opmaak-restpunt S227 uitvragen** — zijn oordeel over de opmaaktest-mail was
   "niet goed maar prima, laat maar"; wat er schort is nog steeds niet
   gespecificeerd (S228 werd mobiel-sessie). Eén vraag + gerichte fix
   (maten staan centraal in `backend/app/email/incasso_templates.py`).
2. **S221b-UX-restant:** review-scherm classificatie+concept naast elkaar;
   voortgangsindicator bij concept-genereren (~30-40 s zonder feedback);
   tijdlijn-mailregel klikbaar (id-betekenis eerst verifiëren); follow-up
   sorteerbare koppen (server-side sortering); intake-detectie dempen; échte
   HTML-tabellen in AI-mails (injectie-oppervlak — apart afwegen); Blok
   6-beslismemo b2b/b2c (alleen memo).
3. Optioneel klein (mobiel-polish, alleen als Taak 1 leeg is): snelle-actie-
   dialogen (notitie/taak/uren/filters) omzetten naar het Drawer-onderschuifpaneel
   (`components/ui/responsive-dialog.tsx` staat klaar).

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail). MAILSLOT
OPEN. Prod-mutaties: dry-run/telling + GO. Geen `git add -A`. Bayar IN100613 niet
aanraken. Testdata 2026-00007 t/m -00019 opruimen alleen ná GO (natelling).
Desktopweergave mag niet zichtbaar veranderen bij mobiel-fixes (steekproef 1440).
Let op de deploy-race: handmatige SSH-deploy mét `--force-recreate`, en een rode
GitHub-"Deploy"-run door een container-naamconflict ≠ kapotte app (zie memory
`feedback_deploy_via_ssh`).

## Verificatie
- Frontend: `npx tsc --noEmit`; mobiel-wachter lokaal:
  `npx playwright test mobile-overflow --project=mobile` (of handmatig scrollWidth
  meten op 390/820 zoals S228).
- Backend (alleen bij backend-werk): relevante `pytest`, `uvx ruff check app/`.
- Kruispunt-check (skill `breed-testen`) bij elk gedeeld effect.
- CI groen na push (`gh run list`) — vaste afsluitcheck.
- Live doorklikken op 2026-00006.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag
sessie-229 + PROMPT-S230).

## Nog open na S228
- DMARC ontbreekt op kestinglegal.nl → Arsalan/BaseNet publiceert record (SPF+DKIM OK).
- Auto-concept-gate: menselijke steekproef Lisanne (~10 concepten) vóór activering.
- Klant-update-endpoint UI-dood (S224-klasse beslispunt: opruimen of knop geven).
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
