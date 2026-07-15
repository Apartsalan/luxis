cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 215 — KvK-rechtsvorm-backfill (zodra de echte sleutel binnen is)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest): `docs/plans/PLAN-wik-rentebijlage.md`
(besluiten A–D).

## Model
Dit is **uitvoeren → Opus** (env zetten op VPS, script draaien, natellen). De backfill is een
naar-buiten-gerichte prod-mutatie → dry-run + expliciet akkoord Arsalan vóór de echte run.

## Hoofdtaak — KvK-rechtsvorm-backfill (wacht op de echte sleutel)
De WIK-rentebijlage is sinds S212 LIVE, maar de KvK-client is bewust **slapend**: zonder
`KVK_API_KEY`-env raakt niets de KvK, en zolang de rechtsvorm leeg is krijgt volgens **besluit B**
élke zakelijke wederpartij (óók BV's) de rentebijlage bij de 14-dagenbrief/eerste sommatie.
Zodra Arsalan de **echte productie-sleutel** meldt:
1. `KVK_API_KEY` **+** `KVK_API_BASE=https://api.kvk.nl/api` als env op de VPS zetten → herstart backend.
   (⚠️ Zonder `KVK_API_BASE` draait de client tegen de testomgeving — nooit stil tegen de verkeerde kant.)
2. `docker compose exec -T backend python scripts/kvk_backfill_legal_form.py --dry-run` →
   rapporteer wat het zou vullen.
   ⚠️ **GEMETEN OP PROD (S215, 15 juli, lees-only): 726 relaties met KvK-nummer, allemaal met
   lege rechtsvorm (0 al gevuld), allemaal geldig 8-cijferig (713 uniek).** Dus niet ±438/±€9
   maar **~€14,50 per draai** (726 × €0,02). LET OP: de `--dry-run` roept de KvK óók echt aan
   (regel 75 staat vóór de dry-run-check) → proef + echte run samen ~€29. Overweeg daarom één
   enkele echte run met vooraf-akkoord op de kandidatenlijst i.p.v. dry-run+run (halveert de kosten);
   de echte run print per relatie `GEVULD … → rechtsvorm`, dus evenveel zicht als een dry-run.
3. **Akkoord Arsalan** → echt draaien → natelling: hoeveel `legal_form` gevuld, hoeveel BV/NV/stichting.
4. **Meten wat het oplevert:** hoeveel zaken krijgen nu géén rentebijlage meer (rechtsvorm = beperkt
   aansprakelijk) t.o.v. de besluit-B-situatie waarin iedereen 'm kreeg. Rapporteer in gewone taal.

## Verificatie
- Backend na env-wijziging: `docker compose exec -T backend printenv KVK_API_KEY` (gevuld) +
  `KVK_API_BASE` = api.kvk.nl. Rooktest: één relatie met KvK-nummer bijwerken → rechtsvorm komt terug.
- Backfill: dry-run-telling vs echte telling moeten matchen; 0 onverwachte mutaties buiten `legal_form*`.

## Restpunten uit S214 (alleen op expliciete vraag Arsalan)
- **7 Mollie/kop-conflictfacturen** (€10.854,66; 100314/100316/100321/100332/100342/100441/100533):
  Mollie zegt betaald, BaseNet-kop zegt open. Per factuur oordeel Lisanne/boekhouding; daarna evt.
  na-importeren via `scripts/basenet/import_invoices.py`-patroon (doeltabel is nu niet meer leeg —
  poort bewust; een na-import vergt een aparte, kleine gerichte run).
- 12 WIP/concepten (€13.013,07) + 31 losse conceptregels (€6.779,81): handwerk-lijst in
  `docs/research/S201-facturatie-recept.md` §1.
- Landregel op dagvaarding + faillissementsverzoek (S210 bewust niet gedaan — gerechtelijke stukken).
- 206 vorderingen zonder gekoppelde factuur-PDF (S213) — lijstje uit `scripts/link_invoice_files.py --dry-run`.

## Constraints (wat NIET doen)
- **Backfill NIET draaien vóór de echte sleutel er is** en NIET zonder dry-run + akkoord Arsalan.
- Geen `git add -A`; expliciete paden.
- Mailslot: niets echt versturen.
- Buiten scope: S203-restpunten, mail-verstevigingen — alleen op expliciete vraag.

## Commit
Env-wijziging is geen code. Eventuele codeklusjes: commit + push naar main per onderdeel, deploy via
SSH (deploy-regels). Werk af met `/sessie-einde`.
