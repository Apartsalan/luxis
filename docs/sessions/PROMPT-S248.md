cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 248 — Arsalan bepaalt de hoofdtaak

## Model
Start op **Fable** (`/effort max`) voor onderzoek/plan/review. Wissel naar
**Opus** zodra er gebouwd/geklikt wordt, en meld die wissel zelf. Bouwen op
Fable en plannen op Opus zijn allebei fout — zie memory `feedback_model_choice`.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door met de
taak die Arsalan bij start kiest.

Extra taak-context (alleen als de gekozen taak dat raakt, `/sessie-start` leest
dit NIET):
- **Kennisregels bouwen** → `docs/plans/ONTWERP-juridische-kennisregels-S247.md`
  (VOORSTEL, nog niet akkoord). Nieuwe feature: eerst ontwerp verfijnen op Fable +
  eerste regels van Lisanne ophalen; pas bouwen na expliciet GO. Aparte tabel +
  RLS in dezelfde migratie; toepasbaarheids-conditie is HARD (art. 6:235 mag niet
  omgekeerd op een consument).
- **Fase-heropening per groep** → `docs/plans/BASENET-STATUS-HERSTEL.md` (406
  dossiers, GO per groep, draaiboek-checks éérst).

## Taak
Arsalan bepaalt de hoofdtaak bij start. Sterke kandidaten uit de roadmap:
1. Juridische kennisregels (demo-punten blok 4, restant S247) — ontwerp→GO→bouw.
2. Fase-heropening volgende groep uit BASENET-STATUS-HERSTEL.
3. Openstaande losse punten (afgeronde-taak-"X dagen te laat", melding mislukte
   geplande mail alleen naar inplanner, DMARC, kostenblokje, sharp-CVE's).

**Signaleren, niet oppakken (rolverdeling S240 — inhoudelijk werk = Lisanne):**
oud IN100606-concept weggooien + opnieuw genereren, IN100592 3e betwisting,
regeling-taken IN100281/IN100537, IN100127, 2 open mails (IN100128/IN100586),
IN100492-vraag, 4 review-mails ongesorteerde bak + intake Ram Charan Sukhdai.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevant>"` (één run tegelijk).
- Lint: `uvx ruff check backend/app/`  ·  Frontend: `cd frontend && npx tsc --noEmit`.
- Kruispunt-check skill `breed-testen` bij elk gedeeld effect (mail/stap/concept/geld/zaak).
- Bij prompt-wijziging: verse AI-output op het echte geval verifiëren (niets versturen), kosten natellen.
- Deploy via SSH; login 200; CI groen natrekken.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testverzendingen alleen op testdossiers
  (2026-00006/…-00015, gmail Arsalan) en netjes terugzetten.
- Kostenbewust testen (ai_usage natellen).
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (Lisanne).
- Nieuwe feature (zoals kennisregels) → eerst plan + goedkeuring, niet autonoom bouwen.
- KvK: niet naar vragen.  ·  Nooit `git add -A` — expliciete paden.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH.
Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S249).
