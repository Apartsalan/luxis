Sessie 116 — Vervolg na Feature & UX Audit
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Lees LUXIS-ROADMAP.md en SESSION-NOTES.md (sessie 115).

## Situatie
Alle Feature & UX Audit items zijn afgerond (sessie 113-115). Demo-feedback van Lisanne is verwerkt (11 items).
Git tag `v115-stable` staat als rollback-punt.

Wat nog open staat (afhankelijk van Lisanne):
- M0b: Lisanne overzetten naar M365 (samen met Lisanne plannen)
- Data migratie: BaseNet → Luxis (wacht op BaseNet export van Lisanne)
- AI Incasso Agent: backlog (wacht op M365)

## Taak
Vraag Arsalan wat de prioriteit is voor deze sessie. Mogelijke richtingen:
1. Nieuwe features of verbeteringen die Lisanne/Arsalan aandragen
2. M0b voorbereiden (Lisanne's mailbox overzetten naar M365)
3. Data migratie scripts bouwen (als Lisanne BaseNet export heeft)
4. Performance/polish/testing sprint

## Verificatie
- pytest voor backend changes (alleen relevante modules, niet volledige suite)
- tsc --noEmit voor frontend changes
- Commit + push na elke afgeronde deeltaak
- Deploy automatisch na commit+push
- Git tag aan einde sessie: `git tag -a v116-stable -m "Sessie 116 — [onderwerp]" && git push origin v116-stable`

## Constraints
- Backend bestanden op `backend/app/` pad, NIET `backend/app/app/`
- Verifieer na deploy dat de juiste code in de container zit
- Geen worktrees
- Eén test run tegelijk, alleen relevante modules
