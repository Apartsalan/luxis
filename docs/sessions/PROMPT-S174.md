# Sessieprompt S174 — Verweer-woordenschat (V3) + open review-punten

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Opus** (uitvoering). Lees vooraf: `docs/ARCHITECTUUR-KAART.md` + de S173-entry in `SESSION-NOTES.md`.

## Status: Fable-review S173 is AL gedaan (in de S173-sessie)
De verplichte onafhankelijke Fable-review (verse ogen, schone lei) op commit `bc8923e` is
uitgevoerd → **GO-MITS**. De twee must-fixes zijn direct toegepast + getest (commit `34e2b2d`,
57 tests groen, gedeployed):
- categorie-keuze in unified sorteert nu op `SyncedEmail.email_date` i.p.v. `created_at`
  (na de BaseNet-bulkimport was created_at onbetrouwbaar);
- `kimi_client` plain-text fallback `max_tokens` 1024 → 8192 (compose/draft kapten anders af).

**Er is dus GEEN nieuwe review nodig.** Wat resteert zijn de door Fable gemarkeerde
opruimpunten (stap 1) + de bouwtaak V3 (stap 2).

## Stap 1 — Open review-punten afhandelen (kort)
1. ~~BESLISSING Arsalan (kosten vs kwaliteit): compose→Sonnet?~~ **GEDAAN (S173):** Arsalan
   koos Sonnet; `kimi_client` plain-text fallback (compose-dialog + client-update) draait nu op
   Sonnet i.p.v. Haiku (kostenverschil ~paar cent/concept, verwaarloosbaar). Alleen nog te
   overwegen: naar **structured schema** (tool_use, gegarandeerde JSON) i.p.v. plain-text —
   optioneel, niet urgent.
2. **Staleness-grens verweer-injectie** (`unified_draft_service._build_verweer_knowledge`): nu
   injecteert een oude verweer-classificatie AV+voorbeelden in élke latere compose zolang er geen
   nieuwere inkomende mail is geclassificeerd. Overweeg: alleen injecteren als de laatste
   classificatie bij de laatste inkomende mail hoort, of een tijdslimiet.
3. **Skip-logging debiteur-guard** (`learned_answers._DEBTOR_VOICE`): een teller/logregel zodat
   per-ongeluk geskipte échte kandidaten (bv. "namens cliënte betwist ik uw stelling") bij
   calibratie opvallen.
4. **`draft_service.generate_client_update`**: injecteert AV + verweer-voorbeelden als de laatste
   dossier-classificatie toevallig verweer is — ook bij een betaal-update aan de opdrachtgever.
   Bewust? Zo niet: gate op intent.
5. **Klein/cosmetisch:** unified mist het Engelse bibliotheek-voorbeeld dat het incasso-pad wél
   heeft (`get_relevant_examples` filtert op NL); `draft_service`-promptkop zegt nog "(excerpt)"
   terwijl de 3000-cap weg is.

## Stap 2 — V3: Verweer-woordenschat (13 types), Opus
Bron: audit `docs/audit/inventaris-2026-07-05.md` §5.c/§5.d.
**GEVALIDEERD (Fable, 6 juli):** de 13 types + trefwoord-regels zijn droog getest op de
102 echte prod-kandidaten → 85% krijgt een zinvol label, restant 15 is vooral
weggooi-materiaal. Zie `docs/audit/prelabel-dryrun-2026-07-06.md` + geteste regels in
`scripts/prelabel_dryrun_s174.py`. LET OP de valkuil daarin: eerst geciteerde
AV-blokken (9.3/20.4/NCNP/disclaimer) uit de tekst strippen, dán pas matchen — anders
belandt alles wat 9.3 citeert in `betalingsregeling_schikking`.
1. **Woordenschat als constante** (keys EN, labels NL) in `learned_answers.py` of eigen module; de
   2 oude keys (`annuleringskosten_9_3` / `afrekening_voorwaarden_20_4`) mappen op
   `afwikkeling_intrekking`.
2. **Deterministische trefwoord-pre-labeler** (audit §5.d) — vervangt difflib als primair
   toewijzingsmechanisme; difflib blijft alleen duplicaat-filter.
3. **Eenmalig relabel-script** voor de resterende 'overig'-kandidaten (nu 102 kandidaten;
   data-only; **goedgekeurde rijen NIET aanraken**). Draai op prod na verificatie.
4. **UI**: dropdown met de 13 labels bij goedkeuren (backend accepteert `defense_type` al).
5. **UI bron-context (Fable 6 juli):** toon per kandidaat op welke inkomende mail/dossier
   het antwoord was (`source_synced_email_id`/`source_case_id` bestaan al) — zonder context
   kan Lisanne niet goed beoordelen.
Tests: pre-labeler per type één bewijzende case; bestaande AI-tests groen.

## V4 (optioneel, na V3 — klein): type-matching bij genereren
`get_learned_examples` kiest nu op categorie + spreiding, maar kijkt niet welk verweer de
debiteur NU voert. Fix: de AI-classificatie van inkomende mail ook een `defense_type` uit
de 13 laten kiezen (één prompt-veld + kolom) en voorbeelden van dat type voorrang geven.
Maakt de leer-loop pas écht "slim". Zie `docs/audit/prelabel-dryrun-2026-07-06.md` §4.

## Context S173 (klaar, live)
- Gedeelde AV-resolver `ai_agent/knowledge_context.resolve_case_terms` in alle 3 draft-paden;
  automation byte-identiek, `draft_service` op ContactTerms, unified injecteert AV+bibliotheek+
  geleerd **alleen bij verweer-categorie** (op e-maildatum bepaald).
- 2 backfill-guards (Fwd + debiteur-stem); 16 vervuilde kandidaten afgewezen (118→102).
- 57 tests groen. ARCHITECTUUR-KAART AI-tabel = 3×✅. Commits `bc8923e` + `34e2b2d`.

## NIET doen
- Geen consolidatie 3→minder draft-services (latere sprint). Geen sjablonen-naar-DB (DF122-04).
- CLAUDE.md + `.claude/commands/*` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in repo-root niet committen.

## Kaart-discipline + sessie-einde
Na elke wijziging aan een systeemkoppeling: `docs/ARCHITECTUUR-KAART.md` bijwerken (zelfde sessie).
Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP + ARCHITECTUUR-KAART, git tag `sessie-174`,
PROMPT-S175 schrijven.
