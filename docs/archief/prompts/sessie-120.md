Sessie 120 — Luxis
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start

Gebruik de luxis-researcher subagent met deze opdracht:

"Lees LUXIS-ROADMAP.md (bovenste 100 regels + sectie 'Demo Feedback Lisanne sessie 117') en SESSION-NOTES.md (entry 'sessie 119 — Derdengelden afronding'). Geef compacte samenvatting (max 300 woorden):
- Wat is in sessie 119 gedaan (4 commits: shadow-copy weg, /derdengelden overzicht, NOvA CSV exports, SEPA pain.001 export)
- Wat is de huidige migratie head (df119) en wat staat erin
- Welke open punten staan er nog rond derdengelden (MT940 import, SEPA-historie, IBAN-validatie backend, self-approval UI)
- VPS deploy status (alembic head df119, beide containers healthy)
- M0b status (Lisanne overzetten naar M365)"

Lees zelf NIETS anders bij start.

## Begin de sessie zo

Begroet me met:

"Sessie 120. Context geladen.

Status: in sessie 119 is de derdengelden-module afgerond — top-level overzichtspagina, NOvA CSV-rapporten (mutaties + saldolijst), SEPA pain.001 export voor uitbetalingen, en de stale shadow-copy `backend/app/app/` is verwijderd. 4 commits gedeployed naar VPS, alembic head = df119, beide containers healthy.

Wat wil je vandaag doen?

- MT940 bank-import voor de Stichting Derdengelden Rabobank-rekening (auto-deposits aanmaken op basis van bankafschriften)
- SEPA-batch historie pagina met undo-export (voor als een batch nog niet was geüpload bij de bank)
- M0b — Lisanne overzetten naar M365 (vereist Lisanne erbij voor MX-wijziging)
- Lisanne heeft de derdengelden-features getest en heeft nieuwe feedback
- Iets anders dat in je hoofd zit
- Bug die je tegenkomt tijdens testen

Wat heb je in gedachten?"

Niet zelf kiezen. Wachten op antwoord.

## Harde regels
- Notificatiegeluid via `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` voor elk wachtmoment
- Plan Mode bij niet-triviale taken met pre-mortem
- Verificatie-loop: build → visueel → functioneel
- Commit + push + deploy na elke afgeronde taak
- Dutch UI, English code
- Nooit destructieve acties zonder bevestiging
- Financial precision: Decimal + NUMERIC(15,2)
- Bij twijfel: zelf onderzoeken in codebase, niet aan gebruiker vragen
- Tests-first, geen pragmatische excuses voor het overslaan ervan
- **BELANGRIJK**: edits ALTIJD in `backend/app/...` (niet in een per ongeluk teruggekomen `backend/app/app/...`). Sessie 119 heeft de shadow verwijderd, hou dat zo.

## Eindtaken (verplicht aan het einde)
1. SESSION-NOTES.md bijwerken (nieuwste bovenaan)
2. LUXIS-ROADMAP.md bijwerken
3. Git tag v120-stable
4. Sessie-121 prompt in docs/prompts/
