cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 222 — DEEL 1 verzoekschrift exacte opmaak (Opus-bouw) → DEEL 2 Fable-review van alles

## Start
Draai eerst `/sessie-start`. Zet `/model` op **Opus** (bouwen). Context S220+S221 staat in
SESSION-NOTES — NIET opnieuw uitzoeken. Mailslot OPEN → géén echte debiteuren mailen
(testdossier 2026-00006 = Arsalans gmail).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md`), daarna dit. NEE → direct door.

---

# DEEL 1 (Opus) — verzoekschrift-bijlage: Lisanne's EXACTE opmaak, per zaak ingevuld

**Wens Arsalan:** de faillissement-bijlage moet EXACT Lisanne's PDF-lay-out hebben (crème-balk +
KESTING LEGAL-logo + tabellen), maar per zaak ingevuld. Volledig onderzoek + veld-mapping +
valkuilen staan al klaar in **`docs/sessions/PLAN-verzoekschrift-exacte-nabouw.md`** — lees dat
eerst, dat is de bouwhandleiding. Niet opnieuw uitzoeken.

Kern (zie plan voor detail):
- Bron = `templates/lisanne/Template Verzoekschrift Bijlage.docx` (BaseNet-merge-sjabloon, 38
  `«…»`-velden, loops/keuzes/berekeningen; logo in het briefhoofd; OUD adres "IJsbaanpad" → fixen).
- Doelbeeld = `templates/lisanne/CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf`.
- Zet de BaseNet-velden om naar de docxtpl-velden die de render-service al levert (exacte lijst in
  het plan). Berekeningen (`#set`/`$func`) mogen weg — Luxis levert de eindwaarden. `#foreach
  vordering` → `{%tr for v in vorderingen %}`. Logo houden via het briefhoofd (image2.png op wit).
- Valkuil: markers zijn over runs gesplitst → eerst runs samenvoegen vóór replace.
- Doel-bestand = key `verzoekschrift_faillissement` (compose bevestigt dit automatisch).

**Verificatie (VERPLICHT — juridisch stuk met bedragen):** render met testdata → PDF →
elk veld visueel controleren (vooral de bedragentabel + per-factuur-regels) → naast de doel-PDF
leggen. Back-up managed_templates → reseed (`scripts/reseed_builtin_templates.py`) → prod byte-check.
Pas "klaar" als een ingevulde testrender én de lay-out kloppen.

---

# DEEL 2 (Fable) — na Deel 1: zet `/model` op Fable en controleer ALLES

Val elke dragende claim aan (fable-tegenspreker), meet in de bron (fable-diepte), rapporteer alleen
bewijsbaar (fable-afronding). Rapport: `docs/sessions/S222-review.md`.

### A — Deel 1 (verzoekschrift) natoetsen
Ingevulde testrender = exact de doel-PDF-lay-out? Alle bedragen op de juiste plek? Logo + huidig
adres? Geen restant BaseNet-velden? Reseed byte-identiek op prod?

### B — S220+S221 natoetsen (prod, read-only)
1. Overgeslagen taken (3.4): `my-tasks?include_done=true` toont skipped+completed; terugzet-knop +
   undo — **live doorklikken (in S221 niet gedaan door browserlock)**; dashboard-widget nog enkel open.
2. Ontdubbelen (3.2): 2× next_step/reply → 1 concept; free_compose → 2; stap-wissel gooit stap-
   concepten weg, antwoord-concepten blijven; migratie op head.
3. Classificatie direct na sync (logs): geen 6-min-wachtronde meer.
4. Punt 11 / Blok 5-UX: geen spatie-kolommen; Intake weg; Bankimport→Betalingen; ratio-label+tooltip;
   dossiernummer klikbaar in maillijst. Brief-lettertype overal Calibri.

### C — AI-antwoord-testronde (het proefwerk)
Script staat op prod in de image: `docker compose exec -T backend python -m scripts.ai.antwoord_testronde
--goud 40 --tenant-id <uuid> --out /tmp/rapport.md` (tenant-id: `SELECT id FROM tenants LIMIT 1`).
Analyseer (checklist + corrector) → foutpatronen → spelregels in `_REPLY_PROMPT` bijschaven → zelfde
set opnieuw → score. Doel >90% groen, 0 zware fouten. Niets versturen. Plan:
`docs/plans/PLAN-ai-antwoord-testronde.md`. **Pas ná groen:** auto-concept per categorie AAN voor
Verweer + Algemene/overig (GATED tot bewezen).

### D — Backfills-3.3 uitzoeken (NIET zelf sluiten — GO Arsalan)
Herkomst + veilig-op-te-ruimen-ja/nee per wachtrij: 470 classificaties, 14 intake, 8 concepten,
3 adviezen, 79 ongelinkte mails, 348 notificaties. Rapporteer, wacht op GO.

## Openstaand voor later (Opus-bouw, ná deze review)
Review-scherm classificatie+concept, voortgangsindicator bij genereren, échte HTML-tabellen,
Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat, soft-delete-banner, follow-up
dossierlink/dagen/sort, intake-detectie dempen), Blok 6-beslismemo b2b/b2c.

## Constraints
Geen echte debiteuren mailen. Prod-mutaties: dry-run/telling + GO. Geen `git add -A` (expliciete
paden). Beslispunten niet zelf beslissen — vragen. Deel 1 = Opus, Deel 2 = Fable.

## Afsluiten
`/sessie-einde` (SESSION-NOTES + roadmap + tag). Reviewrapport: `docs/sessions/S222-review.md`.
