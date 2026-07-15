cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 217 — KvK-rechtsvorm-backfill (voorrang) óf dossierpolish

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
- KvK: `docs/sessions/PROMPT-S215.md` (volledig recept + STAND met de gemeten cijfers).
- Dossierpolish: `docs/plans/PLAN-dossierpagina.md` (§2 + "nog open").

## Model
Uitvoeren/bouwen → **Opus**. De KvK-backfill is een naar-buiten-gerichte prod-mutatie →
dry-run + expliciet akkoord Arsalan vóór de echte run. Review = Fable (los moment).

## Hoofdtaak A — KvK-rechtsvorm-backfill (ALS de sleutel er is → VOORRANG)
Zodra Arsalan de **echte productie-KvK-sleutel** meldt, volg `PROMPT-S215.md` §Hoofdtaak:
1. `KVK_API_KEY` **+** `KVK_API_BASE=https://api.kvk.nl/api` als env op de VPS → herstart backend.
   (⚠️ Zonder `KVK_API_BASE` draait de client tegen de TESTomgeving — nooit stil tegen de verkeerde kant.)
2. **Gemeten op prod (S215): 726 relaties, allemaal geldig 8-cijferig, rechtsvorm leeg. ~€14,50 per draai.**
   De `--dry-run` bevraagt de KvK óók echt → proef + echte run samen ~€29. **Overweeg met Arsalan één
   echte run met vooraf-akkoord op de kandidatenlijst** (halveert de kosten; de run print per relatie
   `GEVULD … → rechtsvorm`, dus evenveel zicht als een dry-run).
3. Akkoord Arsalan → draaien → natelling (hoeveel `legal_form` gevuld, hoeveel BV/NV/stichting) →
   meten hoeveel zaken nu géén rentebijlage meer krijgen (rechtsvorm = beperkt aansprakelijk).
Rooktest na env: `docker compose exec -T backend printenv KVK_API_KEY KVK_API_BASE` + één relatie bijwerken.

## Hoofdtaak B — Dossierpolish (ALS de sleutel er NOG NIET is)
Kleine afronding van de S216-verbouwing (`docs/plans/PLAN-dossierpagina.md`):
- Anker-subnav bovenin het Financieel-tabblad (Vorderingen · Betalingen · Regeling) — spring-navigatie.
- Geldstrook gewone zaak uitbreiden met ongefactureerd (`useTimeEntrySummary`) + openstaande facturen
  (`useInvoices({case_id})`) naast OHW+budget.
- Elk onderdeel: tsc + Playwright-doorklik op prod (incasso IN100215 + verse advies-testzaak, daarna
  verwijderen); alle links/knoppen behouden (harde eis).

## Constraints (wat NIET doen)
- Backfill NIET vóór de echte sleutel + NIET zonder akkoord Arsalan.
- Geen `git add -A`; expliciete paden (KvK-PDF's + Renteberekening blijven bewust untracked).
- Mailslot: niets echt versturen.
- Buiten scope: landregel gerechtelijke stukken, Mollie-conflicten, S203-restpunten (alleen op vraag).

## Commit
Env-wijziging = geen code. Codeklusjes: commit + push per onderdeel, deploy frontend/backend via SSH
(deploy-regels). Werk af met `/sessie-einde`.
