# Sessieprompt S175 — Onafhankelijke review van het S174-werk (verse ogen)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model + houding
Sterkste beschikbare redeneer-model. Verse ogen, schone lei: lees EERST
`docs/ARCHITECTUUR-KAART.md`, de S174-entry in `SESSION-NOTES.md`, en
`docs/audit/prelabel-dryrun-2026-07-06.md`. Review de diff van de S174-commits
kritisch — zoek wat er MIS is, neem niets aan omdat het "getest" heet.
Oordeel: GO / GO-MITS (must-fixes benoemen) / NO-GO.

## Wat S174 moest opleveren (toets hierop)
Bron: `docs/sessions/PROMPT-S174.md` (ontwerpbesluiten van 6 juli staan erin).

### A. Review-punten (stap 1)
1. Staleness-gate: `next_step`/`free_compose` injecteren alléén als de classificatie bij de
   laatste inbound-mail hoort; `reply` blijft altijd injecteren. **Check: test die een dossier
   bouwt met oude verweer-classificatie + nieuwere ongeclassificeerde inbound → geen injectie.**
2. Debiteur-guard skip-logging: teller + ids in de log.
3. `generate_client_update` met `audience="client"` → geen verweer-bibliotheek/geleerde
   voorbeelden in de prompt, wél AV. **Check: betaal-update op verweer-dossier.**
4. Must-fix classificatie-selectie (3 plekken: `draft_service`, `automation_service`,
   unified): gedeelde helper in `knowledge_context.py`, join op inbound
   `SyncedEmail.email_date` — NIET meer `created_at`. **Check: grep
   `EmailClassification.created_at` → alleen nog per-mail (unified `_load_classification_
   for_email`) en lijstweergave (service.py) mogen overblijven.**

### B. V3 — woordenschat + pre-labeler
1. 13 types constante (keys EN, labels NL); oude keys `annuleringskosten_9_3`/
   `afrekening_voorwaarden_20_4` gemapt op `afwikkeling_intrekking`.
2. Pre-labeler **stript eerst geciteerde AV-blokken** (9.3/20.4/NCNP/disclaimer) vóór het
   matchen — DE valkuil uit de dry-run. **Check: draai `scripts/prelabel_dryrun_s174.py`-logica
   vs. de nieuwe module op dezelfde input → verdeling moet ±overeenkomen (85% gelabeld,
   afwikkeling ~20, verlenging ~12, restant-overig ~15).**
3. Relabel-script: data-only, idempotent, **goedgekeurde rijen ONaangeraakt** (query-check:
   `status='goedgekeurd'` rijen hebben zelfde `defense_type`+`updated_at` als vóór het script).
4. UI: dropdown 13 labels, groepering per type, **bron-context zichtbaar** (inkomende
   mail/dossier per kandidaat).
5. Per type één bewijzende pre-labeler-test; volledige AI-testset groen.

### C. V4 — type-matching (als gebouwd)
1. Classificatie-prompt kiest `defense_type` uit de 13; kolom op `EmailClassification`.
2. `get_learned_examples`: type-match eerst, categorieën als één pool, spreiding als fallback.
3. **Check: dossier met "reeds betaald"-verweer krijgt reeds_betaald-voorbeelden vooraan.**

## Premortem-risico's (uit de Fable-analyse van 6 juli — toets of S174 ze raakt)
1. **Lisanne keurt niet** → loop dood. UI moet het 30-45-min-pad ondersteunen (groepen,
   beste bovenaan, bulk-afwijzen, context). Niets goedkeuren blijft veilig (fallback op de
   5 vaste teksten).
2. **Pre-label fout → verkeerd goedgekeurd type → verkeerde injectie.** Dropdown-correctie
   moet prominent zijn; label is een hint, geen waarheid.
3. **V4 niet gebouwd → "het wordt niet slimmer".** Zonder type-matching blijft de winst
   beperkt tot betere groepering in het dashboard. Flag het expliciet als V4 doorschuift.
4. **PII-lek via anonimisering.** Steekproef 5 goedgekeurde teksten op namen/bedragen.
5. **Wachtrij groeit terug** (5-min-backfill). Nieuwe kandidaten moeten met pre-label
   binnenkomen, niet als 'overig'.

## Rooktest prod (na deploy)
1. Login → Instellingen → Slim leren: groepen zichtbaar, aantallen kloppen met de
   relabel-uitkomst, dropdown werkt, bron-context klikbaar.
2. Concept genereren op een verweer-dossier → log: juiste voorbeelden geïnjecteerd.
3. `docker compose logs backend` — geen nieuwe errors.

## Sessie-einde
SESSION-NOTES + LUXIS-ROADMAP + ARCHITECTUUR-KAART bijwerken, git tag `sessie-175`,
PROMPT-S176 schrijven (verwachte inhoud: Lisanne's beoordeling begeleiden / K2-meting).
