Sessie 119 — Luxis
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start

Gebruik de luxis-researcher subagent met deze opdracht:

"Lees LUXIS-ROADMAP.md (sectie 'Demo Feedback Lisanne sessie 117') en SESSION-NOTES.md (entry 'sessie 118 — DF117-21 derdengelden verrekening + consolidatie'). Geef compacte samenvatting (max 300 woorden):
- Wat is er in sessie 118 gedaan (verrekening + consolidatie + 4 commits)
- Welke bugs/blockers zijn bekend uit sessie 118 (m.n. shadow-copy backend/app/app/)
- Wat staat er nog open: top-level Derdengelden pagina, NOvA-rapporten, SEPA-export, opruimen shadow-copy
- VPS deploy status (df11802a head, beide containers healthy)"

Lees zelf NIETS anders bij start.

## Begin de sessie zo

Begroet me met:

"Sessie 119. Context geladen.

Status: in sessie 118 is DF117-21 derdengelden afgerond — verrekening met cliënt-toestemming + consolidatie van het oude collections.Derdengelden naar trust_funds. 4 commits gedeployed naar VPS.

Bekend issue: er staat nog een verborgen duplicaat van de codebase in `backend/app/app/` die niet door de container wordt gelezen maar wel verwarring kan opleveren — deze moet een keer opgeruimd.

Wat wil je vandaag doen?

- Top-level 'Derdengelden' sidebar-pagina met cross-cliënt saldo overzicht
- NOvA-rapporten (mutatieoverzicht, saldolijst per cliënt, CCV-aangifte ondersteuning)
- SEPA-export voor uitbetalingen vanaf de Stichting Derdengelden Rabobank-rekening
- Opruimen `backend/app/app/` shadow-copy (uitsluitend technisch onderhoud)
- Lisanne heeft vannacht/vanmorgen getest en heeft nieuwe feedback
- Iets anders dat in je hoofd zit
- Bug die je tegenkomt tijdens testen

Wat heb je in gedachten?"

Niet zelf kiezen. Wachten op antwoord.

## Harde regels
- Notificatiegeluid via cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs" voor elke wachtmoment
- Plan Mode bij niet-triviale taken met pre-mortem
- Verificatie-loop: build → visueel → functioneel
- Commit + push + deploy na elke afgeronde taak
- Dutch UI, English code
- Nooit destructieve acties zonder bevestiging
- Financial precision: Decimal + NUMERIC(15,2)
- Bij twijfel: zelf onderzoeken in codebase, niet aan gebruiker vragen
- Tests-first, geen pragmatische excuses voor het overslaan ervan
- **BELANGRIJK**: edits in `backend/app/...` (NIET `backend/app/app/...`). De inner `app/app/` is een verborgen stale duplicaat die niet door de container wordt gelezen.

## Eindtaken (verplicht aan het einde)
1. SESSION-NOTES.md bijwerken
2. LUXIS-ROADMAP.md bijwerken
3. Git tag v119-stable
4. Sessie-120 prompt in docs/prompts/
