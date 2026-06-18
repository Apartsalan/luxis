# Sessieprompt S166 — BaseNet-import (voedt shadow-learning) + resterende S165-backlog

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisiewerk). **`/effort max` aan het begin.**
**Deploy: ZELF via SSH** (memory `feedback_deploy_via_ssh` + skill `deploy-regels`) — niet wachten op CI; die skipt deploy bij rood.

---

## Waarom deze sessie
S165 bouwde de incasso-backlog 2/3/4 + het **shadow-learning-fundament** ("Slim leren", live). Dat fundament heeft alleen nog geen data: de huidige verweer-mails zijn sjablonen met "XXX" waar het argument hoort (XXX zelf is al gefixt in S164). Arsalan verwacht **~19 juni de volledige BaseNet-export** — dát is de echte brandstof. Primaire taak: die import bouwen en op shadow-learning aansluiten. Daarnaast resteert backlog #1/#5/#7.

## Context laden bij start
- `SESSION-NOTES.md` — **S165-entry bovenaan** (incasso-fixes 2/3/4 + shadow-learning-fundament + de kernbevinding "0 data want verweer-mails zijn XXX-sjablonen").
- Memory `project-shadow-learning` — hoe het leersysteem werkt + waarom het op BaseNet wacht.
- Per fix: rood→groen lokaal, dan **zelf via SSH deployen** + health-check.

## Primair: BaseNet-import → voeding voor shadow-learning
**Eerst onderzoeken (CLAUDE.md-werkwijze), dan mét Arsalan afstemmen, dan bouwen.** Zie `docs/future-modules.md` → "Data Migratie: BaseNet → Luxis" (mapping + dry-run-aanpak).
- **Wat het oplevert:** BaseNet bevat jaren echte correspondentie. Importeer Lisanne's uitgaande verweer-antwoorden zó dat de backfill ze oppakt: `learned_answers.backfill_learned_answers` leert van **uitgaande mail** (haar correctie), categorie via de classificatie op het dossier, sjablonen + "XXX" worden al uitgesloten. BaseNet-mails zijn waarschijnlijk HTML → `_email_body_text` dekt dat al (haalt tekst uit body_html).
- **Aandachtspunten:** export-format pas zien als het er is (Arsalan zet klaar) → parse-scripts + ID-mapping + **dry-run-rapport** (verwacht vs geïmporteerd). Boekhouding is het gevoeligst → apart/later. Begin met **relaties + correspondentie** (dát voedt shadow-learning).
- **Verificatie:** na import → backfill draaien → dashboard "Slim leren" toont echte voorbeelden per categorie; **steekproef of de geleerde tekst écht een weerlegging is** (geen sjabloon/sommatie). Daarna: laat de agent een concept genereren op een echt dispuut en kijk of Lisanne's stijl terugkomt.

## Resterende S165-backlog
**#1 Cliënt-kenmerk bij factuur-upload.** Het kenmerk staat vaak níét op de factuur en cliënten kunnen we het niet laten toevoegen. Bedenk een manier om het tóch bij upload in Luxis te krijgen. Eerst onderzoeken (Clio/Basenet), dan mét Arsalan — geen aanname.
**#5 Verweer-escalatie: 2 reacties → ultimatum → volgende fase.** Lisanne reageert ~2× inhoudelijk; daarna één afsluitend ultimatum ("we komen er niet uit, ik adviseer cliënt hun rechten te betrekken / procedures te starten") en dán naar de volgende fase. De agent moet dit patroon herkennen.
**#7 H25 — `modules_enabled` server-side afdwingen.** Bounded autonome taak; zie `.audit/AUDIT-REPORT.md` (H25).

## Verificatie
Per fix relevante test rood→groen; `npx tsc --noEmit` bij frontend-wijzigingen; **zelf via SSH deployen** + `curl -sf https://luxis.kestinglegal.nl/health`.

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Shadow-learning = assistent; Lisanne beslist + handelt.
- Juridische bewoording = Lisanne's oordeel; jij fixt de structuur/flow.
- Shadow-learning leert van wat Lisanne ÉCHT verstuurt (uitgaande mail), niet van het AI-voorstel. Sjabloon-sommaties + oningevulde "XXX" blijven uitgesloten.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-166` + prompt S167.
