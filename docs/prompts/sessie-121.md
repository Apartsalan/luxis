Sessie 121 — Luxis
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start

Gebruik de luxis-researcher subagent met deze opdracht:

"Lees LUXIS-ROADMAP.md (bovenste 100 regels + sectie 'Demo Feedback Lisanne sessie 120') en SESSION-NOTES.md (entry 'sessie 120 — Demo-feedback round 2'). Geef compacte samenvatting (max 300 woorden):
- Wat is in sessie 120 gedaan (5 commits: creditnota fix, rate_basis/minimum_fee inheritance, seed script, disk-crash preventie)
- Welke feedback van Lisanne staat nog open voor sessie 121 (DF120-08 producten-catalogus)
- DF120-09/10 zijn voor sessie 122 (mail-sjablonen + verweer-bibliotheek)
- Wat staat er in `xls Print scherm - Producten en diensten-08042026_1437.xls` (28 items, 4 BTW-regimes, 15+ grootboeknummers)
- VPS status (alembic head df120a, disk guards actief, 35% used)"

Lees zelf NIETS anders bij start.

## Begin de sessie zo

Begroet me met:

"Sessie 121. Context geladen.

Status: in sessie 120 zijn 2 bugs gefixt (creditnota BTW, overzicht na credit), 2 inheritance-uitbreidingen gedaan (rate_basis + minimum_fee per klant), derdengelden testdata op prod gezet, en een 4-laags disk-crash preventie geïnstalleerd. 5 commits gedeployed.

Focus sessie 121: **producten/artikel-catalogus uit Basenet Excel importeren** (DF120-08). Dit is een nieuwe module die het fundament legt voor facturen, verschotten én de latere Exact Online koppeling (grootboeknummers zijn per item gemapt in de Excel).

Wat wil je vandaag doen?

- Volle sessie aan de producten-catalogus (plan → migratie → model → import → UI → integratie factuur/verschotten)
- Eerst Lisanne's feedback op sessie 120 bekijken voordat we beginnen (misschien is er iets kapot)
- Bug die je tegenkomt tijdens testen
- Iets anders dat prioriteit heeft

Wat heb je in gedachten?"

Niet zelf kiezen. Wachten op antwoord.

## Context over de producten-catalogus (voor als sessie 121 hiermee begint)

Lisanne leverde `xls Print scherm - Producten en diensten-08042026_1437.xls` — dit is HAAR complete Basenet-grootboek: 28 items, niet alleen verschotten maar ook honorarium, incassokosten, reiskosten, provisie, etc. Kolommen: Code, Zoeknaam, Verkoopprijs, Grootboek (4-cijferig), BTW-code.

**BTW-regimes in de Excel:**
- `BTW V 21%` — reguliere diensten
- `BTW NVT` — onbelaste verschotten (griffierecht, KvK uittreksel)
- `BTW V BINNEN EU` — intracommunautair
- `BTW V BUITEN EU` — export

**Grootboeknummers (uit Lisanne's Excel):**
- 8000 Omzet honorarium
- 8020 Onbelaste verschotten
- 8050 Omzet kantoorkosten
- 8060 Omzet reiskosten
- 8100 Omzet buitenland binnen EU
- 8120 Omzet buitenland buiten EU
- 8130 Omzet kantoorkosten buitenland buiten EU
- 8140 Omzet reiskosten buitenland buiten EU
- 8150 Omzet kantoorkosten buitenland binnen EU
- 8160 Omzet reiskosten buitenland binnen EU
- 8300 Opbrengst incassokosten
- 8360 Opbrengst proceskosten incasso
- 1950 Voorschotten
- 2010 Depotgelden verrekend in dossieradministratie
- 2020 Nog te ontvangen van derdengeldenrekening

**Vaste-prijs items (moet direct werken):** Griffierecht (€3.083 / €735), KvK-uittreksel (€18), Waarneming zitting (€125).

Lisanne moet zelf categorieën kunnen toevoegen/bewerken, net zoals we al hebben bij Uren.

## Harde regels
- Notificatiegeluid via `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` voor elk wachtmoment
- Plan Mode bij niet-triviale taken met pre-mortem
- Verificatie-loop: build → visueel → functioneel
- Commit + push + deploy na elke afgeronde taak
- **GEEN `--no-cache` bij deploy** tenzij pyproject.toml of package-lock.json gewijzigd is (sessie 120 lesson learned — 120GB build-cache → DB crash)
- Auto-prune na deploy: `docker image prune -f` (zonder -a)
- Dutch UI, English code
- Nooit destructieve acties zonder bevestiging
- Financial precision: Decimal + NUMERIC(15,2)
- Bij twijfel: zelf onderzoeken in codebase, niet aan gebruiker vragen

## Eindtaken (verplicht aan het einde)
1. SESSION-NOTES.md bijwerken (nieuwste bovenaan)
2. LUXIS-ROADMAP.md bijwerken (DF120-08 status)
3. Git tag v121-stable
4. Sessie-122 prompt in docs/prompts/
