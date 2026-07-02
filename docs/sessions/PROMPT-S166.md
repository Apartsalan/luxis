# Sessieprompt S166 — BaseNet-import (voedt shadow-learning) + backlog #1/#5/#7 — mét Fable/Opus-modelstrategie

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Deploy: ZELF via SSH** (memory `feedback_deploy_via_ssh` + skill `deploy-regels`) — niet wachten op CI; die skipt deploy bij rood.

---

## ⚡ ALLEREERST — zeg de gebruiker welk model + effort te zetten

De assistent kan het model/effort van de interactieve sessie **niet zelf wisselen** — `/model` en `/effort` typt de gebruiker. Dus: zeg bij de start letterlijk wat te zetten, en herhaal dat **elke keer dat het werk omslaat van denken naar bouwen.**

**Modelstrategie (memory `feedback_model_choice`):** Fable 5 is tijdelijk **gratis** → benut het gericht voor het denkwerk. Regel: **onderzoek/ontwerp/oordeel → Fable; bouwen vanaf een afgestemd ontwerp + deployen + security → Opus.** Fable niet reflexief voor alles gebruiken (mechanisch bouwwerk doet Opus even goed en houdt het gratis venster voor de waardevolle beurten). Security-getint werk (#7) altijd op Opus — Fable weigert dat soms.

**De eerste stap deze sessie is onderzoek/ontwerp.** Begin de sessie dus met precies dit tegen de gebruiker:
> "Zet het model op **Fable 5** (`/model` → Fable 5) en de effort op **high** (`/effort high`; `/effort xhigh` als je maximale diepgang wilt). Zeg 'klaar' zodra dat staat, dan ga ik verder."

### Stappenplan — model + effort per taak
| Stap | Fase | Model | Effort |
|------|------|-------|--------|
| **BaseNet-import — onderzoek/ontwerp** | formaat doorgronden, mapping + dry-run-plan, koppeling aan shadow-learning | 🟣 **Fable 5** | high (xhigh voor max) |
| **BaseNet-import — bouwen** | parse-scripts, dry-run-rapport, import, deploy | 🔵 **Opus 4.8** | high |
| **#1 cliënt-kenmerk — onderzoek/ontwerp** | hoe lossen Clio/Basenet dit op, aanpak voorstellen | 🟣 **Fable 5** | high |
| **#1 — bouwen** | na akkoord Arsalan | 🔵 **Opus 4.8** | high |
| **#5 verweer-escalatie — ontwerp** | patroon + pipeline-logica bedenken | 🟣 **Fable 5** | high |
| **#5 — bouwen** | implementeren | 🔵 **Opus 4.8** | high |
| **#7 H25 (security)** | modules_enabled server-side afdwingen | 🔵 **Opus 4.8** (hele taak) | high |

**Vuistregel:** iets uitzoeken/ontwerpen/kraken → Fable. Iets bouwen/deployen dat al is afgestemd → Opus. Noem bij elke niet-triviale taak proactief het aanbevolen model + één regel waarom, en laat de gebruiker `/model` + `/effort` zetten.

---

## Waarom deze sessie
S165 bouwde incasso-backlog 2/3/4 + het **shadow-learning-fundament** ("Slim leren", live). Dat fundament heeft alleen nog geen data: de huidige verweer-mails zijn sjablonen met "XXX" waar het argument hoort (XXX zelf is al gefixt in S164). De echte brandstof = de **volledige BaseNet-export**, die Arsalan heeft opgevraagd/klaargezet. Primaire taak: die import bouwen en op shadow-learning aansluiten. Daarnaast resteert backlog #1/#5/#7.

## Context laden bij start
- `SESSION-NOTES.md` — **S165-entry** (incasso-fixes 2/3/4 + shadow-learning-fundament + kernbevinding "0 data want verweer-mails zijn XXX-sjablonen") + de planning-entry 2 juli (deze modelstrategie).
- Memory `project-shadow-learning` — hoe het leersysteem werkt + waarom het op BaseNet wacht.
- Per fix: rood→groen lokaal, dan **zelf via SSH deployen** + health-check.

## Primair: BaseNet-import → voeding voor shadow-learning
**Eerst onderzoeken (CLAUDE.md-werkwijze) op Fable, dan mét Arsalan afstemmen, dan bouwen op Opus.** Zie `docs/future-modules.md` → "Data Migratie: BaseNet → Luxis" (mapping + dry-run-aanpak). **Arsalan geeft de export-details (locatie + formaat) bij de start van de bouwstap.**
- **Wat het oplevert:** BaseNet bevat jaren echte correspondentie. Importeer Lisanne's uitgaande verweer-antwoorden zó dat de backfill ze oppakt: `learned_answers.backfill_learned_answers` leert van **uitgaande mail** (haar correctie), categorie via de classificatie op het dossier, sjablonen + "XXX" al uitgesloten. BaseNet-mails zijn waarschijnlijk HTML → `_email_body_text` dekt dat.
- **Aandachtspunten:** export-formaat pas zien als het er is → parse-scripts + ID-mapping + **dry-run-rapport** (verwacht vs geïmporteerd). Boekhouding is het gevoeligst → apart/later. Begin met **relaties + correspondentie** (dát voedt shadow-learning).
- **Verificatie:** na import → backfill draaien → dashboard "Slim leren" toont echte voorbeelden per categorie; **steekproef of de geleerde tekst écht een weerlegging is** (geen sjabloon/sommatie).

## Resterende backlog
**#1 Cliënt-kenmerk bij factuur-upload.** Kenmerk staat vaak níét op de factuur; cliënten kunnen het niet toevoegen. Bedenk een manier om het tóch bij upload in Luxis te krijgen. Eerst onderzoeken (Clio/Basenet) op Fable, dan mét Arsalan — geen aanname.
**#5 Verweer-escalatie: 2 reacties → ultimatum → volgende fase.** Lisanne reageert ~2× inhoudelijk; daarna één afsluitend ultimatum en dán naar de volgende fase. De agent moet dit patroon herkennen.
**#7 H25 — `modules_enabled` server-side afdwingen.** Bounded, zie `.audit/AUDIT-REPORT.md` (H25). Hele taak op Opus.

## Verificatie
Per fix relevante test rood→groen; `npx tsc --noEmit` bij frontend-wijzigingen; **zelf via SSH deployen** + `curl -sf https://luxis.kestinglegal.nl/health`.

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Shadow-learning = assistent; Lisanne beslist + handelt.
- Juridische bewoording = Lisanne's oordeel; jij fixt de structuur/flow.
- Shadow-learning leert van wat Lisanne ÉCHT verstuurt (uitgaande mail), niet van het AI-voorstel. Sjabloon-sommaties + oningevulde "XXX" blijven uitgesloten.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-166` + prompt S167.
