cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 247 — verse-ogen-review nachtdiff + AI-kennislaag (demo-punten blok 4)

## Model
Start op **Fable** (`/effort max`) voor deel A (review). Daarna **Opus** voor
deel B (bouwen). Meld de wissel zelf — les S246: "bouwen → Opus" in een
sessieprompt slaat op de BOUWfase; plan- en reviewfase zijn altijd Fable.

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S247). Lees entry **S246-nacht** in SESSION-NOTES: eindreview S246 is
gedraaid (4 fixes live) én de lopende band (batch + follow-up) heeft nu ook
"Verstuur later", beide live bewezen op testdossiers. CI van de nacht-commits
natrekken.

## Deel A (Fable) — verse-ogen-review van de NACHTDIFF
De nacht-commits `90aa57f` + `8ef2d88` zijn gebouwd én getest door dezelfde
Fable-instantie — tegen de vaste cyclus in (nachtopdracht Arsalan). Daarom:
één verse tegenlezing van precies die twee commits. Aandachtspunten:
- `_pre_send_blokkade` + `_run_batch_step`/`_run_followup` in
  `email/scheduled_service.py`: sessie-/transactiegrenzen (claim-commit,
  rollback-pad), tenant-context na commits.
- Batch-inplannen: dekt de avondcontrole écht dezelfde gevallen als
  `batch_execute` zelf zou weigeren? (stap, sjabloon, e-mail, poort)
- Follow-up: goedkeuren-nu + uitvoeren-later — klopt de statusmachine in alle
  volgordes (afwijzen ná inplannen, tweede planning, superseded)?
- UI: `verstuur-later-menu.tsx` in batch- en follow-upvenster; "Weghalen" op
  mislukte rijen. Visueel nalopen (screenshots bekijken).
Repareren mag direct (kleine vondsten); grote vondsten eerst voorleggen.

## Deel B (Opus, na de review) — AI-kennislaag
1. **Placeholder-bug IN100606** (demo-vraag Arsalan). Gemeten (S243): de
   placeholder is bewust ontwerp (`backend/app/ai_agent/incasso_email_prompts.py:314-318`
   — onbekend verweer → placeholder i.p.v. verzonnen argument), maar de AI
   kopieerde de mal `<kernverweer letterlijk uit incoming_defense>` LETTERLIJK
   in het concept. Fix de prompt-instructie + wachter op de substitutie. Leg
   Arsalan in gewone taal uit: dit is een vangnet, geen fout.
2. **Juridische kennisregels** (demo-wens IN100458: BV "wil de AV vernietigen"
   — kansloos, art. 6:235 BW, maar Luxis herkent zulke standaard-onzin niet).
   Ontwerp op Fable: curated bibliotheek "veelvoorkomende onjuiste stellingen +
   standaard-weerlegging" als uitbreiding van de verweer-bibliotheek
   (learned_answers, 132 rijen), via DEZELFDE goedkeur-flow — élke regel langs
   Lisanne vóór gebruik. Signaleer ook: de 132 kandidaten wachten al op haar.

## Verificatie
- Kruispunt-check skill `breed-testen`; wachter per foutSOORT.
- Wachters op prompt↔schema-sync (test_kimi_client_structured-patroon).
- Derde AI-testronde na promptwijziging: verse AI-antwoorden op de goud-gevallen
  (`scripts/ai/antwoord_testronde.py`, S238-rapport als vergelijk), niets versturen.
- **Eén pytest-run tegelijk** (S246: twee gelijktijdige runs = 68 spookfouten).
- uvx ruff; tsc; deploy via SSH; login 200.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testverzendingen alleen op testdossiers
  (2026-00006/…-00015, gmail Arsalan) en netjes terugzetten.
- Kostenbewust testen (ai_usage natellen).
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (Lisanne).
- KvK: niet naar vragen.

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S248).
