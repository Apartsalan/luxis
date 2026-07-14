cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 213 — KvK-rechtsvorm-backfill (rentebijlage scherpstellen) + kleine restpunten

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): SESSION-NOTES entry S212
(§Bekende issues) + `docs/plans/PLAN-wik-rentebijlage.md` (besluiten A–D).

## Model
Dit is **uitvoeren → Opus** (env zetten op VPS, script draaien, natellen). De backfill zelf
is een naar-buiten-gerichte prod-mutatie → dry-run + expliciet akkoord Arsalan vóór de echte run.

## Hoofdtaak — KvK-rechtsvorm-backfill (wacht op de echte sleutel)
De WIK-rentebijlage is sinds S212 LIVE, maar de KvK-client is bewust **slapend**: zonder
`KVK_API_KEY`-env raakt niets de KvK, en zolang de rechtsvorm leeg is krijgt volgens **besluit B**
élke zakelijke wederpartij (óók BV's) de rentebijlage bij de 14-dagenbrief/eerste sommatie.
Zodra Arsalan de **echte productie-sleutel** meldt:
1. `KVK_API_KEY` **+** `KVK_API_BASE=https://api.kvk.nl/api` als env op de VPS zetten → herstart backend.
   (⚠️ Zonder `KVK_API_BASE` draait de client tegen de testomgeving — nooit stil tegen de verkeerde kant.)
2. `docker compose exec -T backend python -m scripts/kvk_backfill_legal_form.py --dry-run` →
   rapporteer wat het zou vullen (±438 relaties met KvK-nummer, ±€9 aan bevragingen).
3. **Akkoord Arsalan** → echt draaien → natelling: hoeveel `legal_form` gevuld, hoeveel BV/NV/stichting.
4. **Meten wat het oplevert:** hoeveel zaken krijgen nu géén rentebijlage meer (rechtsvorm = beperkt
   aansprakelijk) t.o.v. de besluit-B-situatie waarin iedereen 'm kreeg. Rapporteer in gewone taal.

## Kleine restpunten (alleen op expliciete vraag Arsalan)
- **`/compose/send` ('Direct versturen'-knop)** hangt geen factuur-PDF's/rentebijlage aan (krijgt
  geen `template_type`). S212-observatie, buiten scope gelaten. Wil Arsalan dit dicht? Dan: frontend
  `template_type` meesturen op `postCompose` + backend `send_via_provider` dezelfde helper aanhaken
  als op het `.eml`-pad (`compose_eml_from_case`).
- **Landregel op dagvaarding + faillissementsverzoek** (S210 bewust niet gedaan — gerechtelijke stukken).

## Verificatie
- Backend na env-wijziging: `docker compose exec -T backend printenv KVK_API_KEY` (nu gevuld) +
  `KVK_API_BASE` = api.kvk.nl. Rooktest: één relatie met KvK-nummer bijwerken → rechtsvorm komt terug.
- Backfill: dry-run-telling vs echte telling moeten matchen; 0 onverwachte mutaties buiten `legal_form*`.

## Constraints (wat NIET doen)
- **Backfill NIET draaien vóór de echte sleutel er is** en NIET zonder dry-run + akkoord Arsalan.
- Geen `git add -A`; expliciete paden.
- Mailslot: niets echt versturen; de rentebijlage is al bewezen via tests/preview.
- Buiten scope: S201-facturatie-import, S203-restpunten, mail-verstevigingen — alleen op expliciete vraag.

## Commit
Env-wijziging is geen code. Eventuele codeklusjes: commit + push naar main per onderdeel, deploy via
SSH (deploy-regels). Werk af met `/sessie-einde`.
