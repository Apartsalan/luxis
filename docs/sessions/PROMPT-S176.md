# Sessieprompt S176 — Lisanne's beoordeling begeleiden + K2-meting

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Opus** (uitvoering, klein werk). Lees vooraf: `docs/ARCHITECTUUR-KAART.md` + de
S174/S175-entries in `SESSION-NOTES.md`.

## Status na S175 (6 juli 2026)
De verplichte onafhankelijke review op S174 is gedaan → **GO**. Eén must-fix direct
toegepast + gedeployed (commit `5fa4592`: `get_learned_examples` keek maar naar de 12
nieuwste goedkeuringen; cap → 200). Alles live en healthy. Geen open bugs.

**De leer-loop staat er nu volledig:** 102 kandidaten per verweer-type gegroepeerd in
"Slim leren" (verdeling: afwikkeling 20 / overig 15 / verlenging 12 / reeds_betaald 8 / …),
dropdown 13 types, bron-context per kandidaat, bulk-afwijzen. Type-matching (V4) werkt
zodra er getypeerde goedkeuringen zijn én nieuwe inbound-mail geclassificeerd wordt.

## Hoofdtaak — afhankelijk van waar Arsalan mee komt

### Spoor A: Lisanne's beoordeling is (deels) gedaan → resultaat verwerken
1. Check de uitkomst: `SELECT status, defense_type, count(*) FROM learned_answers GROUP BY 1,2;`
2. Steekproef 3-5 nieuw goedgekeurde teksten op PII (namen/bedragen — moet `[bedrag]` zijn).
3. Genereer een testconcept op een verweer-dossier waarvan de nieuwste inbound een
   `defense_type` heeft → verifieer in de log/use_count dat het MATCHENDE type vooraan gaat.
   (Let op: testartefacten opruimen — draft verwijderen, use_count terugzetten.)
4. Rapporteer aan Arsalan: hoeveel goedgekeurd per type, welke groepen leeg bleven.

### Spoor B: K2 — geaggregeerde meting (uit het S169-plan, per-voorbeeld attributie GESCHRAPT)
Doel: kunnen zien of de leer-loop wérkt. Kleinste zinvolle vorm:
1. Bestaande `get_learning_stats` (edit-rate, S160) uitbreiden met een uitsplitsing
   mét/zonder geïnjecteerde geleerde voorbeelden — de "met/zonder-vlag" bestaat mogelijk al
   op de draft; check eerst wat er al ligt vóór je iets bouwt (S171-les: K1 bestond al!).
2. Dashboard-weergave in "Slim leren" (klein blok, geen nieuwe pagina).
3. Geen per-voorbeeld attributie, geen A/B-infrastructuur (bewust geschrapt in de premortem).

## Openstaand (achtergrond, alleen op verzoek)
- Consolidatie 3→minder draft-services (opruimklus, latere sprint).
- `language`-parameter in `get_learned_examples` is dood — meenemen bij die opruimklus.
- V4.3 (type-voorrang statische `DEFENSE_EXAMPLES`) bewust niet gebouwd — alle 5 passen
  binnen de cap, geen inhoudelijk effect.
- Unipile-key-rotatie (Recruit) staat los van Luxis — negeren.

## NIET doen
- Geen her-classificatie van oude mails (kost AI-calls; oude dossiers zijn afgehandeld).
- CLAUDE.md + `.claude/commands/*` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in repo-root niet committen.

## Kaart-discipline + sessie-einde
Wijzig je een systeemkoppeling → `docs/ARCHITECTUUR-KAART.md` bijwerken (zelfde sessie).
Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP bijwerken, git tag `sessie-176`,
PROMPT-S177 schrijven.
