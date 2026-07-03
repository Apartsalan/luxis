# Sessieprompt S169 — Verweer-bibliotheek in gebruik nemen + losse eindjes na de BaseNet-import

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

In S168 is de **BaseNet-import volledig uitgevoerd** op productie (zie SESSION-NOTES S168). Stand:
- **1168 relaties · 607 dossiers (passief archief) · 1563 vorderingen · 6393 e-mails** live in prod.
- **130 verweer-kandidaten** staan in "Slim leren" met status `kandidaat` — **ze voeden de AI nog NIET; Lisanne moet ze beoordelen.** Dat menselijke vangnet is nog niet geactiveerd. **Besluit S168: alleen leren van de 7 vaste opdrachtgevers** (Incassocenter, INC Zakelijk, COLLECT 1, LegalWork, SYN Finance 1, CM Zakelijk, Invorderingsbedrijf); one-off-cliënten uitgesloten (1 Fideal-kandidaat al afgewezen). Er is nog géén permanente code-filter hiervoor — optioneel bouwen (zie backlog).
- Kwaliteit is opgeschoond (intro-boilerplate 0, €-lek 0, near-dup 1), maar er zijn bewuste randgevallen die de review opvangt (bedrijfsnamen niet gemaskeerd, af en toe geciteerde debiteur-tekst).

## Hoofdtaak: de verweer-bibliotheek écht in gebruik nemen

**Model:** onderzoek/UX-oordeel → **Fable 5**; bouwen → **Opus 4.8** (memory `feedback_model_choice`).

1. **"Slim leren"-dashboard tegen 131 echte kandidaten** (Fable → Opus): log in op https://luxis.kestinglegal.nl (Playwright, `seidony@kestinglegal.nl` / `Hetbaken-KL-5`) en beoordeel of de review-flow schaalt naar 131 items — paginering, per-categorie filteren, de anonimiseer-diff, bulk-afwijzen van ruis. Nu is het gebouwd voor "een handvol". Verbeter waar nodig zodat Lisanne er dóórheen komt zonder moe te worden.
2. **Steekproef-oordeel mét Arsalan/Lisanne:** loop een paar kandidaten per categorie langs — zijn dit teksten die Lisanne als standaard-weerlegging zou willen? Dit bepaalt of de heuristiek verder bijgesteld moet (drempels in `learned_answers.py`) of dat de review-UX de rest doet.

## Backlog (na de hoofdtaak, in deze volgorde van waarde)

- **Source-mount uitzoeken (infra, Opus):** prod draait met bind-mount `/opt/luxis/backend/app→/app/app` (ontdekt S168). Is dat bedoeld of een dev-override die per ongeluk draait (bekende-fouten #28, `COMPOSE_FILE` in VPS-`.env`)? Bepaalt of "code in image"-aannames elders kloppen én of code-deploys een expliciete herstart nodig hebben. Zie deploy-regels-skill S168-correctie.
- **Permanente "vaste-opdrachtgever"-filter (optioneel, Opus):** nu leert de bibliotheek van élke cliënt; het besluit is alleen van de 7 vaste te leren. Markeer die 7 (flag op contact of allow-list) en filter de backfill erop, zodat toekomstige one-off-dossiers automatisch buiten de leerstroom blijven. Laag-urgent (archief is afgesloten; Lisanne's review vangt het nu op).
- **F7 backfill-perf (Opus):** `backfill_learned_answers` herlaadt elke 5 min ~3.300 outbound-bodies + draait er heuristiek op. Nu de import erin zit is dat merkbaar. Cutoff/markering zodat al-verwerkte mails niet telkens herladen worden. **Pas ná Lisanne's eerste oordeel** (anders zet je de leerstroom verkeerd vast).
- **Fase 1b (optioneel, Opus):** betalingen (`IncassoBetalingAnders` 56 + `IncassoBetalingsRegeling` 323 → payments/arrangements) + persoon↔bedrijf `ContactLink` via **vcode** (145). Maakt het archief-openstaand-saldo accurater; geen AI-kost. Decoderingen staan in ontwerpdoc §7. Alleen doen als Arsalan het wil.
- **Backlog #1** cliënt-kenmerk bij factuur-upload (`inckenmerkclient`→`case.reference` bestaat; UI-kant) · **#5** verweer-escalatie (2 reacties → ultimatum → volgende fase) · **#7** H25 (`modules_enabled` server-side, Opus).

## Deploy/uitvoeren: ZELF via SSH — mét de S168-les
SSH `root@46.225.115.216`, key `~/.ssh/luxis_deploy`, app `/opt/luxis`. **Na een code-deploy: verifieer dat het proces echt herstartte** (`docker inspect luxis-backend --format '{{.State.StartedAt}}'` moet ná je push liggen) — de bind-mount + uvicorn-zonder-reload betekent dat `git pull`+`up -d` de oude code kan laten draaien; zo niet `docker restart luxis-backend`. CI groen + Deploy success checken via `gh run list`. Import-scripts draaien in de container via `docker cp` (schoon: `docker exec -u root ... rm -rf /tmp/scripts` vóór opnieuw kopiëren).

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Verweer-bibliotheek = assistent; Lisanne beslist wat een standaard wordt.
- Nooit een zip committen (PII) — `.gitignore` dekt `*.zip`. Tijdelijke .eml/XML-extracties na gebruik opruimen.
- CLAUDE.md + `.claude/commands/*.md` staan ongecommit gewijzigd (niet van mij) — met rust laten tot Arsalan zegt anders.

## Commit + Sessie-einde
Commit + push per stap, deploy + verifieer per keer. Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP + git tag `sessie-169` + PROMPT-S170.
