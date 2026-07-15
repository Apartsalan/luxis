cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 222 — VERPLICHTE Fable-review S220+S221 + AI-antwoord-testronde (Fable, read-only waar kan)

## Start
Draai eerst `/sessie-start`. Zet `/model` op **Fable** (review/onderzoek = Fable, niet Opus).
Context staat in SESSION-NOTES (entries S220 + S221) — NIET opnieuw uitzoeken wat daar al staat;
deze sessie TOETST het. Mailslot staat OPEN → géén echte debiteuren mailen (testdossier
2026-00006 = Arsalans gmail).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md`), daarna deze review. NEE → direct door.

## Doel: bewijs dat S220+S221 echt klopt vóórdat er iets op echte klanten losgaat
Val elke dragende claim aan (fable-tegenspreker), meet in de bron (fable-diepte), rapporteer
alleen wat je met een sessie-resultaat kunt bewijzen (fable-afronding). Rapport in
`docs/sessions/S222-review.md`.

### Blok A — S221-bouwsprint natoetsen (prod, read-only)
1. **Overgeslagen taken (3.4):** `my-tasks?include_done=true` toont skipped+completed, cap 100;
   terugzet-knop → pending; undo-toast. Klik het op prod door (Playwright) — de knop/undo is in
   S221 NIET live doorgeklikt (browserlock). Controleer ook dat het dashboard-widget nog steeds
   alléén open taken toont.
2. **Ontdubbelen concepten (3.2):** genereer 2× hetzelfde (next_step + reply) → 1 concept;
   free_compose → wél 2. Stap-wissel gooit verouderde 'volgende stap'-concepten weg, antwoord-
   concepten blijven. Migratie `s221_ai_draft_intent_step` op head.
3. **Classificatie direct na sync (blok 4):** bevestig in de logs dat na een sync met nieuwe mail
   direct `classify_new_emails` draait (geen 6-min-wachtronde meer).
4. **Begrip-eerst antwoordroute (4.3):** draai de testronde (zie Blok B). Val de spelregels aan:
   verzint hij nooit bedragen? escaleert hij bij advocatenbrief/AVG? noemt hij de klantnaam?
5. **Punt 11 / Blok 5-UX:** bedragen niet in spatie-kolommen; Intake weg uit menu; Bankimport→
   Betalingen; ratio-label+tooltip; dossiernummer klikbaar in maillijst.
6. **Sjablonen (S221):** brief-lettertype overal Calibri (reseed geverifieerd); verzoekschrift-
   bijlage rendert per zaak ingevuld MÉT logo (huidige tussenoplossing — zie Blok D).

### Blok B — AI-antwoord-testronde draaien (het proefwerk)
Script bestaat: `backend/scripts/ai/antwoord_testronde.py` (op prod in de image). Draai op prod:
`docker compose exec -T backend python -m scripts.ai.antwoord_testronde --goud 40 --tenant-id <uuid> --out /tmp/rapport.md`
(tenant-id: `SELECT id FROM tenants LIMIT 1`). Analyseer het rapport (checklist + corrector):
foutpatronen → spelregels in `_REPLY_PROMPT` (`ai_agent/unified_draft_service.py`) bijschaven →
zelfde set opnieuw → score vergelijken. Doel: >90% checklist groen, 0 zware fouten (verzonnen
bedrag/toezegging). Niets versturen, niets op echte dossiers. Vol plan: `docs/plans/PLAN-ai-antwoord-testronde.md`.
**Pas ná groen proefwerk:** auto-concept per categorie AAN zetten voor Verweer + Algemene/overig
(besluit Arsalan — GATED tot de antwoord-route bewezen is).

### Blok C — Backfills-3.3 uitzoeken (NIET zelf sluiten — besluit Arsalan)
Zoek uit wát deze ruis-wachtrijen precies zijn vóór er iets dicht gaat: 470 pending
classificaties (import-backfill?), 14 intake-ruis, 8 verouderde concepten, 3 verouderde adviezen,
79 ongelinkte mails, 348 ongelezen notificaties. Per wachtrij: herkomst + veilig-op-te-ruimen ja/nee
+ voorstel. Rapporteer, wacht op GO.

### Blok D — Verzoekschrift exacte opmaak (apart, alleen vaststellen)
Arsalan wil Lisanne's PDF-lay-out precies, per zaak ingevuld. Volledig onderzoek + mapping staat
al in `docs/sessions/PLAN-verzoekschrift-exacte-nabouw.md`. Deze sessie: mapping/context definitief
maken (Fable), NIET bouwen — dat is een Opus-vervolg (S221b/eigen sessie).

## Openstaand voor S221b (Opus-bouw, ná deze review)
Review-scherm classificatie+concept naast elkaar, voortgangsindicator bij genereren, échte
HTML-tabellen (render/opschoon-pad), Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat,
soft-delete-banner, follow-up dossierlink/dagen/sort, intake-detectie dempen), Blok 6-beslismemo
b2b/b2c, verzoekschrift exacte nabouw.

## Constraints
Read-only waar kan. Geen echte debiteuren mailen. Prod-mutaties (indien nodig): dry-run/telling +
GO. Geen `git add -A`. Beslispunten niet zelf beslissen — vragen. Model = Fable.

## Afsluiten
`/sessie-einde` (SESSION-NOTES + roadmap + tag). Reviewrapport: `docs/sessions/S222-review.md`.
