cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 213 — KvK-rechtsvorm-backfill + Facturen-menu naar 2 tabs + factuur-PDF's koppelen

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

## Taak 2 — Facturen-menu: van 3 naar 2 tabs (besluit Arsalan, 14 juli)
De huidige 3 tabs mengen categorieën met een weergave: "Debiteuren" is geen aparte soort maar
een per-klant-samenvatting van de kantoorfacturen. Arsalan wil 2 tabs:
1. **Kantoorfacturen** — met binnenin een weergave-schakelaar *Lijst* ↔ *Per klant* (de huidige
   DebiteurenTab-component wordt die tweede weergave; niets weggooien, alleen verplaatsen).
2. **Vorderingen** — blijft, maar het paperclipje wordt een DIRECTE link naar de factuur-PDF
   (openen/downloaden via de bestaande dossierbestand-download-route), niet meer naar het dossier.

## Taak 3 — Factuur-PDF's aan de vorderingen koppelen (prod-schrijfactie, akkoord vereist)
De PDF's bestaan als dossierbestanden (±1.750 `Factuur_<nr>.pdf`), maar 0/1.563 vorderingen
verwijst ernaar (`invoice_file_id` leeg) → de PDF-kolom én de automatische factuur-bijlage op de
verzendpaden vinden bij geïmporteerde dossiers niets. Gemeten (S212): **1.368/1.563 exact
koppelbaar** — zelfde dossier + bestandsnaam-nummer == factuurnummer op de vordering.
Aanpak: koppel-script met eerst `--dry-run` (rapporteer aantal + steekproef) → akkoord Arsalan →
echt draaien → natelling (1.368 verwacht; alleen `invoice_file_id` muteren, niets anders).
Daarna vertelt de PDF-kolom in het Vorderingen-tabblad de waarheid én werkt de auto-bijlage.

## Kleine restpunten (alleen op expliciete vraag Arsalan)
- **Landregel op dagvaarding + faillissementsverzoek** (S210 bewust niet gedaan — gerechtelijke stukken).

## Verificatie
- Backend na env-wijziging: `docker compose exec -T backend printenv KVK_API_KEY` (nu gevuld) +
  `KVK_API_BASE` = api.kvk.nl. Rooktest: één relatie met KvK-nummer bijwerken → rechtsvorm komt terug.
- Backfill: dry-run-telling vs echte telling moeten matchen; 0 onverwachte mutaties buiten `legal_form*`.

## Constraints (wat NIET doen)
- **Backfill NIET draaien vóór de echte sleutel er is** en NIET zonder dry-run + akkoord Arsalan.
- **PDF-koppel-actie (taak 3) NIET zonder dry-run + akkoord** — prod-schrijfactie.
- Geen `git add -A`; expliciete paden.
- Mailslot: niets echt versturen; de rentebijlage is al bewezen via tests/preview.
- Buiten scope: S201-facturatie-import (kantoorfacturen-import = eigen sessie, besluit Arsalan),
  S203-restpunten, mail-verstevigingen — alleen op expliciete vraag.

## Commit
Env-wijziging is geen code. Eventuele codeklusjes: commit + push naar main per onderdeel, deploy via
SSH (deploy-regels). Werk af met `/sessie-einde`.
