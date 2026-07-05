# Sessieprompt S173 — Verbind-sprint 1: één AI-geheugen + schone leer-wachtrij

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Opus** (uitvoering — het ontwerp ligt vast in de audit). Lees eerst:
1. `docs/ARCHITECTUUR-KAART.md` (5 min, het complete plaatje)
2. `docs/audit/inventaris-2026-07-05.md` §4 + §5 (het waarom + de details)

## Context
Audit S172 (Fable) bewees: er zijn 3 AI-conceptservices met 3 verschillende geheugens —
alleen het verweer-pad ziet de voorwaarden/geleerde voorbeelden; de compose-dialog ziet
NIETS. Plus: ±20 van de 110 "Slim leren"-kandidaten zijn vervuiling (debiteur-tekst of
lege fragmenten). Deze sessie VERBINDT; geen nieuwe features.

## Taak A — Gedeelde AI-kennis-bouwer (kern, ~halve sessie)
Eén functie (voorstel: `ai_agent/knowledge_context.py`) die per (tenant, case, categorie)
teruggeeft: `terms_text` (via `ContactTerms` + `select_terms_for_date`, fallback legacy),
`learned_examples_text` (bestaande `build_learned_examples_text`), `defense_examples_text`
(bestaande `format_examples_for_prompt`). Bron-logica LIFTEN uit `automation_service.py`
(dat pad is correct) — niet herschrijven.
1. `automation_service.py` → gebruikt de bouwer (gedrag identiek, alleen verplaatst).
2. `draft_service.py` → bouwer i.p.v. legacy `Contact.terms_file_path` (regel 125-126 weg).
3. `unified_draft_service.py` → bouwer-injectie in alle 3 intents (next_step/reply/free);
   cap ~4000 tekens zoals de anderen.
**Tests (rood→groen):** per service één test die bewijst dat de prompt de AV-tekst van een
zaak-met-ContactTerms bevat; regressie: bestaande AI-tests groen (80+).

## Taak B — Leer-wachtrij schoonmaken + extractie-guards (~kwart sessie)
1. **Data:** de ±20 vervuilde kandidaten bulk-afwijzen (ID-lijst in audit §5.b; verifieer
   elk ID nog even op status='kandidaat' vóór afwijzen — Lisanne kan intussen beoordeeld
   hebben, en `reject_candidates_bulk` raakt goedgekeurde toch niet aan).
2. **Guards in `learned_answers.backfill_learned_answers`:** (a) subject dat met Fwd:/FW:
   begint → skip (doorgestuurde debiteur-mail); (b) kern die met een debiteur-opener
   begint ("wil ik", "maak ik bezwaar", "betwist ik/wij") → skip. Rode test met een echte
   Fwd-casus uit de audit → groen.
3. Draai backfill NIET opnieuw over het archief (dedup beschermt, maar geen nieuwe ruis
   creëren tijdens Lisanne's review).

## Taak C — Verweer-woordenschat (13 types) (~kwart sessie, mag naar S174 schuiven)
1. Woordenschat uit audit §5.c als constante (keys EN, labels NL) in `learned_answers.py`
   of eigen module; de 2 oude keys (`annuleringskosten_9_3`/`afrekening_voorwaarden_20_4`)
   mappen op `afwikkeling_intrekking`.
2. Trefwoord-pre-labeler (deterministisch, audit §5.d regels) — vervangt de difflib-
   toewijzing als primair mechanisme; difflib blijft alleen als duplicaat-filter.
3. Eenmalig relabel-script voor de 110 'overig'-kandidaten (data-only; goedgekeurde rijen
   NIET aanraken). Daarna groepeert het AI-leren-dashboard vanzelf zinnig.
4. UI: dropdown met de 13 labels bij goedkeuren (backend accepteert `defense_type` al).

## NIET doen
- Geen consolidatie van de 3 services tot één (latere sprint — eerst zelfde geheugen).
- Geen sjablonen-naar-DB (DF122-04, latere sprint). Geen nieuwe features.
- CLAUDE.md + `.claude/commands/*` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in repo-root niet committen.

## Kaart-discipline (nieuw, blijvend)
Na elke wijziging aan een systeemkoppeling: `docs/ARCHITECTUUR-KAART.md` bijwerken (de
AI-tabel in de kaart moet na Taak A drie ✅-rijen tonen). Hoort voortaan bij sessie-einde.

## Sessie-einde
SESSION-NOTES + LUXIS-ROADMAP + ARCHITECTUUR-KAART bijwerken (de AI-tabel in de kaart moet
na Taak A drie ✅-rijen tonen), git tag `sessie-173`, PROMPT-S174 schrijven.

## VERPLICHT — S174 begint met een Fable-review (afspraak Arsalan, S172)
**Als Opus klaar is, zet Arsalan de volgende sessie op Fable** (`/model` → Fable) en laat
die het S173-werk onafhankelijk reviewen vóór er verder gebouwd wordt — zelfde patroon als
S170 (leverde toen 3 echte fixes op). Zet dit als EERSTE stap in PROMPT-S174:
1. Fable-review van alle S173-commits (context-bouwer, guards, woordenschat): klopt de
   AV-injectie in alle drie de paden aantoonbaar, zijn de tests echt bewijzend, is er niets
   stilletjes versimpeld of overgeslagen.
2. Pas daarna de S174-bouwtaken (woordenschat-rest + eerste met/zonder-meting edit-rate).
