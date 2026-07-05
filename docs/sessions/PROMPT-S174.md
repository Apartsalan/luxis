# Sessieprompt S174 — Fable-review S173 (VERPLICHT eerst) → Verweer-woordenschat (V3)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Fable eerst** (de review), daarna **Opus** voor de bouwtaken. Zet bij start `/model` → Fable.
Lees vooraf: `docs/ARCHITECTUUR-KAART.md` + de S173-entry in `SESSION-NOTES.md`.

## Stap 1 (VERPLICHT) — Fable-review van het S173-werk
Afspraak Arsalan (S172): na elke Opus-bouwsprint een onafhankelijke Fable-review vóór er verder
gebouwd wordt — leverde in S170 3 echte fixes op. Review commit **`bc8923e`** (verbind-sprint 1):

1. **Klopt de AV-injectie aantoonbaar in ALLE drie de paden?** `knowledge_context.resolve_case_terms`
   → `automation_service` / `draft_service` / `unified_draft_service`. Vooral: is automation écht
   **byte-identiek** gebleven (bibliotheek-injectie in `incasso_email_prompts` onaangeraakt, alle 5
   voorbeelden incl. de Engelse, cap 8000)? Dit was de grootste stille-regressie-risico.
2. **Zijn de tests echt bewijzend of schijn-groen?** golden-guard incasso-pad
   (`test_incasso_prompt_keeps_full_defense_library`), unified wél/niet bij verweer, backfill-guards
   met echte bodies. Iets stilletjes versimpeld of overgeslagen?
3. **`_DEBTOR_VOICE`-guard**: te agressief (skipt echte Lisanne-antwoorden) of te los (laat
   debiteur-tekst door)? Check tegen de resterende prod-kandidaten (nu 102).
4. **Losse eindjes** uit audit §4/§5 die V1/V2 raakten maar niet gedaan zijn (bv. `terms_file_path`-
   kolom-deprecatie, `kimi_client.py`-hernoeming — bewust naar later, of vergeten?).

Lever een **GO / GO-MITS / NO-GO** + genummerde concrete fixes. Pas eventuele fixes toe
(rood→groen) **vóór** V3.

## Stap 2 (na de review) — V3: Verweer-woordenschat (13 types), Opus
Bron: audit `docs/audit/inventaris-2026-07-05.md` §5.c/§5.d.
1. **Woordenschat als constante** (keys EN, labels NL) in `learned_answers.py` of eigen module; de 2
   oude keys (`annuleringskosten_9_3` / `afrekening_voorwaarden_20_4`) mappen op `afwikkeling_intrekking`.
2. **Deterministische trefwoord-pre-labeler** (audit §5.d) — vervangt difflib als primair
   toewijzingsmechanisme; difflib blijft alleen duplicaat-filter.
3. **Eenmalig relabel-script** voor de resterende 'overig'-kandidaten (data-only; **goedgekeurde
   rijen NIET aanraken**). Draai op prod na verificatie.
4. **UI**: dropdown met de 13 labels bij goedkeuren (backend accepteert `defense_type` al).
Tests: pre-labeler per type één bewijzende case; bestaande AI-tests groen.

## Context S173 (klaar, live)
- Gedeelde AV-resolver `ai_agent/knowledge_context.resolve_case_terms` in alle 3 de draft-paden;
  automation byte-identiek, `draft_service` op ContactTerms i.p.v. legacy, unified injecteert
  AV+bibliotheek+geleerd **alleen bij verweer-categorie**.
- 2 backfill-guards (Fwd:-subject + debiteur-stem); 16 vervuilde kandidaten afgewezen (118→102).
- 54 tests groen. ARCHITECTUUR-KAART AI-tabel = 3×✅.

## NIET doen
- Geen consolidatie 3→minder draft-services (latere sprint — eerst zelfde geheugen, nu gedeeld).
- Geen sjablonen-naar-DB (DF122-04). Geen nieuwe features.
- CLAUDE.md + `.claude/commands/*` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in repo-root niet committen.

## Kaart-discipline + sessie-einde
Na elke wijziging aan een systeemkoppeling: `docs/ARCHITECTUUR-KAART.md` bijwerken (zelfde sessie).
Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP + ARCHITECTUUR-KAART bijwerken, git tag `sessie-174`,
PROMPT-S175 schrijven.
