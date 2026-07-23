cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 243 — Arsalan bepaalt de hoofdtaak bij start

## Model
Vraag bij start welk model actief is en of dat past bij de taak die Arsalan
kiest (onderzoek/review = Fable, bouwen/klikwerk = Opus — memory
`feedback_model_choice`). Signaleer een wissel ACTIEF vóór je begint.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Vraag daarna aan Arsalan wat de hoofdtaak
van deze sessie is. Extra taak-context: geen (S242 was een afgeronde veegsessie).

**Administratie-check bij start:**
1. CI natrekken van de laatste S242-commits (`gh run list`) — de drie fix-runs
   (`cd4c70a`, `024eb6b`, `ec10221`) waren bij het S242-einde net binnen of
   liepen nog; de docs-commit daarna ook.
2. **Signaleer aan Arsalan (niet zelf oppakken — rolverdeling S240):** de
   IN100015-verjaringsmelding is ONTERECHT (S242-onderzoek: meermaals gestuit,
   deurwaarder betekende verzoekschrift, dossier 13-7 afgesloten — melding mag
   weggeklikt; Luxis kent geen stuiting, voorstel staat in entry S242). De
   IN100127-waarschuwing (23-3-2026) komt uit hetzelfde kale rekensommetje —
   Lisanne weet of er gestuit is. De 2 open mails (IN100128, IN100586) wachten
   nog op antwoord van Arsalan/Lisanne.

## Kandidaat-hoofdtaken (keuze Arsalan — dit is context, geen opdracht)
- **Opruimronde mét Lisanne/Arsalan (sterkste kandidaat, S241-werklastmeting):**
  39 test-taken, 14 test-adviezen, 81 oude ongesorteerde mails, 16 oude
  aanvragen verdrinken het echte werk (26 taken + 7 adviezen). Claude kan de
  lijsten klaarzetten + na GO opruimen met dry-run + natelling.
- **Verweer-parkeerstap-terugkeer (richting akkoord Arsalan, S242-demo):**
  `docs/plans/VOORSTEL-verweer-parkeerstap-terugkeer.md` — na verstuurd
  verweer-antwoord + stilte automatisch terug de sommatie-keten in. Lees de
  3 controlepunten in het voorstel vóór de bouw.
- Rest voorstel-lijst (S239): categorie 'onduidelijk', overbetaling-knop,
  cascade bij dossier-verwijderen, weekend-logica, kostenblokje.
- Fable-tegenlezing van S242 (wens Arsalan tijdens de demo).
- Iets anders dat Arsalan aandraagt.

## Verificatie (bij bouwwerk)
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevante modules>" -v` (één run tegelijk)
- Lint: `uvx ruff check backend/app` | Frontend geraakt → `npx tsc --noEmit`
- Kruispunt-check: skill `breed-testen` bij elk gedeeld effect.
- Na push: CI groen (`gh run list`), deploy via SSH met `--force-recreate`.

## Constraints
- Geen echte debiteuren/cliënten mailen zonder expliciete GO per geval.
- IN100128/IN100586/IN100592-verweer niet aanraken; KvK: niet naar vragen.
- Prod-mutaties: dry-run + GO + natelling (S239-discipline).
- S238-huisregel: prompt-JSON gewijzigd → schema mee.
- Derde AI-testronde alleen bij wijzigingen aan prompts/schema's/antwoord-logica.

## Commit
Per taak een eigen conventional commit + push naar main; deploy automatisch via
SSH (skill `deploy-regels`). Afsluiten met `/sessie-einde`.
