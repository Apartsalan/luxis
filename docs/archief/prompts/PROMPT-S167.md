# Sessieprompt S167 — BaseNet-import UITVOEREN (schone lei → fase 1 + 2 + 3) + backlog #1/#5/#7

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Deploy/uitvoeren: ZELF via SSH** (memory `feedback_deploy_via_ssh` + skill `deploy-regels`). SSH: `root@46.225.115.216`, key `~/.ssh/luxis_deploy`, app `/opt/luxis`. De import-scripts draaien ín de prod-container via `docker cp` (scripts/ zit niet in de prod-image) — zie hoe S166 dit deed (SESSION-NOTES S166-entry).

---

## ⚡ Model + effort per stap (zeg de gebruiker wat te zetten)
De assistent kan het sessie-model niet zelf wisselen. Regel (memory `feedback_model_choice`): **onderzoek/ontwerp → Fable 5 (high); bouwen/uitvoeren/deployen/security/destructief → Opus 4.8 (high).**
- **Documenten-formaat kraken** (nieuw formaat) → **Fable 5 · high**.
- **Wipe + import uitvoeren + fase 2/3 bouwen** (destructief + bouwen) → **Opus 4.8 · high** (hele rest van de sessie).

Begin met: "Zet model op **Fable 5** + effort **high** voor het uitzoeken van het documenten-formaat; ik zeg wanneer we naar Opus omslaan."

## Context laden bij start
Gebruik de luxis-researcher subagent: "Lees SESSION-NOTES.md (sessie 166) + `docs/research/basenet-import-ontwerp.md` (volledig, incl. §4b wipe-plan). Geef compacte samenvatting." Plus memory `project-shadow-learning`.

## Vooraf checken
1. **Is de documenten-backup binnen?** ("Documenten per project van alle medewerkers", ~11,5 GB, meerdere zips, mapstructuur = dossiercode). Zet die in de Luxis-hoofdmap. **Zo niet → STOP en meld het**; zonder e-mailteksten geen fase 2/3 (shadow-learning blijft 0 data). Fase 1 (relaties/dossiers) kan technisch wél zonder, maar we spraken af alles samen te doen op een schone lei.

## Taak (in deze volgorde, mét Arsalan)

### A. Documenten-formaat kraken (Fable)
Uitpakken naar scratchpad; structuur in kaart. Verwacht: bestanden per dossier(map), .eml voor mail. Koppeling aan Luxis-dossier: BaseNet `lepcode` (= inccode, IN-nummer) → Luxis case. **Let op:** fase-1-cases hebben id `uuid5("basenet:case:{incasso_systemid}")`; letters verwijzen via **inccode**, dus bouw `inccode → systemid → case_id` uit de Incasso-export. Richting uit `leinout` (3=uitgaand, 4=inkomend — zie ontwerpdoc §1).

### B. Schone lei (Opus — DESTRUCTIEF, mét verse backup)
Besluit Arsalan (S166): alle prod-data is testdata en mag weg. **Herbevestig de scope live** vóór uitvoeren.
1. **Verse backup** (bewezen restore, `docs/runbooks/restore.md`) — vangnet.
2. **Wipe testdata** (zie ontwerpdoc §4b): verwijder cases/claims/payments/contacts/synced_emails/classifications/ai_drafts/intake_requests/invoices/time_entries/trust/workflow_tasks/notifications/learned_answers. **Behoud:** tenants, users (login), pipeline-steps, templates, tenant-settings, interest_rates, email_accounts (Outlook). FK-veilige volgorde of per-tabel. Verifieer counts = 0 (business) en config intact.

### C. Fase 1 uitvoeren (Opus)
`scripts/basenet/import_basenet.py --execute` in de prod-container (dry-run eerst — moet nu 0 overlap tonen na wipe). Verifieer 1168/607/1563 + steekproef (IN100000 = Incassocenter/Bliksem, cliënt-kenmerk IN121388).

### D. Fase 1b + 2 bouwen + uitvoeren (Opus)
- **Fase 1b:** betalingen (`Payment`/`IncassoBetaling*`) + persoon↔bedrijf `ContactLink` (via `account`). Betaling↔incasso-koppeling eerst decoderen (`entityid`/`entitysysid`).
- **Fase 2:** .eml parsen (Python `email`) → `synced_emails` (direction uit leinout, body_html/text uit .eml, dedup op `basenet:{systemid}`, case via inccode→case_id). `email_account_id` NOT NULL → apart import-account of Lisanne's account; verifieer dat de 5-min-sync het overslaat. Alleen IN-dossier-mails.

### E. Fase 3 — shadow-learning voeden (Opus)
Gerichte AI-classificatie: filter uitgaande mails (sjabloon/lengte), classificeer alléén de voorafgaande inkomende mails (≤3.115). **Kostenraming vooraf + go Arsalan** (memory cost-vs-kwaliteit). Dan `backfill_learned_answers` → dashboard "Slim leren" → **steekproef of geleerde tekst écht een weerlegging is** (geen sjabloon/sommatie/"XXX").

## Verificatie
- Tests: `docker compose exec backend pytest tests/test_basenet_import.py -v` (+ nieuwe fase 2-tests). Ruff: `uvx ruff check scripts/basenet/`.
- Na import: counts + steekproeven; shadow-learning dashboard toont echte voorbeelden per categorie.

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Shadow-learning = assistent; Lisanne beslist.
- Dossiers als **passief archief** (status `afgesloten`, geen pipeline-stap) → geen automatisering op oude zaken.
- Alleen **IN**-dossiers (D overslaan). Boekhouding blijft Exact-leidend.
- Wipe = destructief → ALTIJD verse backup eerst + scope live herbevestigen.

## Backlog na de import
#1 cliënt-kenmerk bij factuur-upload (BaseNet `inckenmerkclient` → `case.reference` is er al; UI-kant nog) · #5 verweer-escalatie (2 reacties → ultimatum → volgende fase) · #7 H25 (`modules_enabled` server-side, hele taak Opus).

## Commit + Sessie-einde
Commit + push per stap (conventional commits). Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP bijwerken + git tag `sessie-167` + PROMPT-S168.
