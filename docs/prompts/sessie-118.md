Sessie 118 — Luxis
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start

Gebruik de luxis-researcher subagent met deze opdracht:

"Lees de volgende bestanden en geef een compacte samenvatting (max 300 woorden):
1. LUXIS-ROADMAP.md — focus op de status-header bovenaan, de sectie 'Demo Feedback Lisanne (sessie 117)' en de sectie 'Go-To-Market Plan'
2. SESSION-NOTES.md — focus op de entry 'sessie 117 — Demo-feedback Lisanne'

Geef terug:
- Huidige status (bouw/validatie-fase, demos met Lisanne lopen)
- Wat er in sessie 117 is gefixt (adres-parsing + standaard rente per klant met inheritance)
- De 19 geparkeerde DF117-items uit de demo-notities (DF117-03 t/m DF117-21) — wat kan zelfstandig opgepakt worden, wat heeft Lisanne-overleg nodig, en wat is geblokkeerd door andere items
- Openstaande aandachtspunten uit sessie 117 (bv. backend startup-script alembic auto-run discrepantie)"

Lees zelf NIETS anders bij de start. Geen code, geen demo-notities, geen andere docs. Alleen de samenvatting van de subagent.

## Begin de sessie zo

Nadat de subagent klaar is, begroet mij met deze exacte opening:

"Sessie 118. Context geladen.

Status: nog steeds in bouw/validatie-fase met Lisanne. Sessie 117 heeft 2 grote demo-items afgerond (factuur adres-parsing + standaard rente per klant met inheritance — backend, frontend, tests, deploy). 19 demo-feedback items van Lisanne staan nog open in de roadmap als DF117-03 t/m DF117-21.

Wat wil je in deze sessie doen? Een paar mogelijkheden:

- **Doorgaan met DF117 demo-feedback** — bv. uren toevoegen vanuit dossier-tab (DF117-07), zoekfunctie documenten (DF117-08), facturen-filter (DF117-12), klik vanuit facturen naar dossier (DF117-14). Dit zijn zelfstandige UX-quick-wins.
- **Creditnota's grondig fixen** (DF117-16/17/18) — visueel duidelijk + totaal-berekening + bedrag-optie. Financial precision dus test-intensief.
- **Goedkeuren → Versturen echte email** (DF117-13) — koppelen aan OutlookProvider die al bestaat
- **AI uitbreidingen** (DF117-03/06) — AV lezen voor rente, dossier-docs lezen voor berichtvoorstel
- **Iets uit het GTM-plan** als je toch al wilt beginnen
- **Iets anders** wat ik nu niet op het netvlies heb

Wat heb je in gedachten?"

Niet zelf een keuze maken. Niet voorstellen welke optie het beste is. Niet pushen op GTM. Gewoon wachten op mijn antwoord.

## Harde regels tijdens de sessie

- Speel notificatiegeluid via Bash vóór elke wachtmoment: `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"`
- Gebruik Plan Mode (EnterPlanMode) bij niet-triviale taken, inclusief pre-mortem (3 redenen waarom dit zou falen + waarom toch juiste aanpak)
- Verificatie-loop na elke implementatie: build check → visuele check → functionele check. Pas "done" als alle 3 groen zijn.
- Commit + push na elke afgeronde taak (conventional commits, altijd direct git push origin main)
- Dutch UI, English code
- Nooit git worktrees tenzij expliciet gevraagd
- Nooit destructieve acties (rm -rf, drop database, volume delete) zonder expliciete bevestiging
- Financial precision: Decimal + NUMERIC(15,2), nooit float
- Ik bepaal zelf de werkverdeling — geen forced 70/20/10 regel
- **Bij twijfel of "weet ik niet": ZELF onderzoeken in de codebase, niet aan de gebruiker vragen.** Arsalan is geen developer en weet niet hoe het werkt — daar heeft hij Claude voor.

## Wat NIET doen deze sessie

- Niet pushen op verkopen. Nog in bouw-fase.
- Geen marktonderzoek-rapporten opnieuw draaien.
- Niet zelf beslissen waar we aan werken — ik beslis, jij faciliteert.
- DF117-04/05 (incassokosten + provisie op factuur) NIET zelfstandig oppakken — wacht op overleg met Lisanne.
- DF117-20 (batch dossier-aanmaak) NIET oppakken — geblokkeerd door DF117-03/06 die eerst af moeten.
- DF117-21 (derdengelden) NIET oppakken zonder eigen onderzoek-sessie eerst.

## Verplichte eindtaken

Aan het einde van de sessie:
1. Update SESSION-NOTES.md met nieuwe entry bovenaan (format: ## Wat er gedaan is (sessie 118 — DATUM) — ONDERWERP). Update de header-regels.
2. Update LUXIS-ROADMAP.md — markeer afgeronde DF117-items als ✅, voeg nieuwe items toe.
3. Git tag: `git tag -a v118-stable -m "Sessie 118 — [onderwerp]" && git push origin v118-stable`
4. Genereer prompt voor sessie 119 in `docs/prompts/sessie-119.md`. Zelfde format als deze prompt: open vraag, laat mij kiezen.
