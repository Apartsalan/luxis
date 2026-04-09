Sessie 122 — Luxis
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start

Gebruik de luxis-researcher subagent met deze opdracht:

"Lees LUXIS-ROADMAP.md (bovenste 100 regels + sectie 'Demo Feedback Lisanne sessie 120') en SESSION-NOTES.md (entries sessie 121 + 120). Geef compacte samenvatting (max 300 woorden):
- Wat is in sessie 121 gedaan (15 Basenet mail-templates + concept verzoekschrift PDF flow + 17 tests)
- Welke feedback van Lisanne staat nog open voor sessie 122 (DF120-08 producten-catalogus + DF120-10 verweer-bibliotheek)
- Wat staat er in `xls Print scherm - Producten en diensten-08042026_1437.xls` (28 items, 4 BTW-regimes, 15+ grootboeknummers)
- Welke 5 .eml's in repo-root zijn voor de verweer-bibliotheek (20.4, 9.3 BV's, IVB variants, Engelse 9.3)
- VPS status (alembic df121a, disk guards actief, Stichting Derdengelden IBAN gezet)
- Harde regel: GEEN --no-cache default, wel `docker image prune -f` na deploy
- Harde regel: externe bestanden altijd PDF (feedback_externe_bestanden_altijd_pdf memory)"

Lees zelf NIETS anders bij start.

## Begin de sessie zo

Begroet me met:

"Sessie 122. Context geladen.

Status sessie 121: alle 15 Basenet mail-templates 1-op-1 overgenomen (11 NL + 4 EN), concept verzoekschrift DOCX→PDF library flow gebouwd, compose dropdown met 7 groepen en 22 templates, 17 render-tests groen. Alles live op productie (df121a).

Focus sessie 122: twee open items uit Lisanne's demo-feedback round 2:

1. **DF120-08 Producten/artikel-catalogus** — uit Basenet `.xls` importeren. 28 items (honorarium, verschotten, incassokosten, reiskosten), 4 BTW-regimes, 15+ grootboeknummers. Fundament voor latere Exact Online koppeling.

2. **DF120-10 Verweer-bibliotheek** — 5 verweer-.eml's opslaan als AI-referentiemateriaal (20.4, 9.3 BV's, IVB varianten, Engelse 9.3). Lisanne kan ze handmatig openen; AI leest ze later bij het genereren van reacties op betwistingen.

Wat wil je vandaag doen?

- Volle sessie aan DF120-08 producten-catalogus (groter onderwerp, plan → migratie → import → UI → integratie factuur/verschotten)
- Volle sessie aan DF120-10 verweer-bibliotheek (kleiner, kan misschien samen met een ander item)
- Beide in één sessie als tijd toelaat (producten-catalogus als hoofdwerk, verweer-bibliotheek als toevoeging aan einde)
- Eerst Lisanne's feedback op sessie 121 bekijken voordat we beginnen
- Iets anders dat prioriteit heeft

Wat heb je in gedachten?"

Niet zelf kiezen. Wachten op antwoord.

## Context over DF120-08 — Producten-catalogus

Bestand: `xls Print scherm - Producten en diensten-08042026_1437.xls` in repo-root.

Kolommen: Code, Zoeknaam, Verkoopprijs, Grootboek (4-cijferig), BTW-code.

**BTW-regimes:**
- BTW V 21% (reguliere diensten)
- BTW NVT (onbelaste verschotten, griffierecht, KvK uittreksel)
- BTW V BINNEN EU
- BTW V BUITEN EU

**Grootboeknummers:**
- 8000 Omzet honorarium / 8020 Onbelaste verschotten / 8050 Kantoorkosten / 8060 Reiskosten
- 8100 Omzet buitenland binnen EU / 8120 Buiten EU
- 8130/8140/8150/8160 Kantoor/reiskosten buitenland varianten
- 8300 Opbrengst incassokosten / 8360 Proceskosten incasso
- 1950 Voorschotten / 2010 Depotgelden / 2020 Nog te ontvangen van derdengelden

**Vaste-prijs items (moeten direct werken):** Griffierecht (€3.083 / €735), KvK-uittreksel (€18), Waarneming zitting (€125).

**Eis van Lisanne:** zelf categorieën kunnen toevoegen/bewerken (net als bij Uren).

Gebruik `xlrd` (al in container geïnstalleerd) om de Excel te lezen.

## Context over DF120-10 — Verweer-bibliotheek

5 .eml bestanden in repo-root:
- `20.4.eml`
- `9.3 (alle BV's).eml`
- `Engelse template 9.3 en verlengd abonnement.eml`
- `IVB (inhoudelijke reactie NCNP 9.3 + Disclaimer (gerechtelijk).eml`
- `IVB reactie verlengd abonnement niet betaald en 9.3.eml`

**Wat moet gebeuren:**
- Parse elke .eml naar subject + body text
- Sla op als `VerweerTemplate` (nieuw model) met velden: id, name, description, category, body_text, created_at
- UI: pagina onder Instellingen → "Verweer-bibliotheek" met lijst + detail view (read-only voor nu)
- AI-integratie komt later (niet in deze sessie) — wel de data opslaan zodat AI het later kan lezen
- Lisanne kan een .eml openen en content copy-pasten naar een actieve email compose

## Harde regels
- Notificatiegeluid via `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` voor elk wachtmoment
- Plan Mode bij niet-triviale taken met pre-mortem (verplicht voor producten-catalogus)
- Verificatie-loop: build → visueel → functioneel
- Commit + push + deploy na elke afgeronde taak
- **GEEN --no-cache bij deploy** tenzij pyproject.toml of package-lock.json gewijzigd is
- **Auto-prune na deploy:** `docker image prune -f` (zonder `-a`) in elk deploy commando
- **Externe bestanden altijd PDF** (nooit DOCX/HTML naar wederpartij of cliënt) — zie `feedback_externe_bestanden_altijd_pdf.md` in memory
- Dutch UI, English code
- Nooit destructieve acties zonder bevestiging
- Financial precision: Decimal + NUMERIC(15,2)
- Bij twijfel: zelf onderzoeken in codebase, niet aan gebruiker vragen
- Tests-first, geen pragmatische excuses voor het overslaan ervan

## Deploy commando (nieuwe stijl zonder --no-cache)

```
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend frontend && docker compose up -d backend frontend && docker image prune -f"
```

## Eindtaken (verplicht aan het einde)

1. SESSION-NOTES.md bijwerken (nieuwste bovenaan)
2. LUXIS-ROADMAP.md bijwerken (DF120-08 en/of DF120-10 status)
3. Git tag `v122-stable`
4. Sessie-123 prompt in `docs/prompts/`
