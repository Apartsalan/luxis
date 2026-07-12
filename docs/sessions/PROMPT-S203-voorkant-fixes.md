cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 203 — Voorkant-fixes (S200-bevindingen afwerken)

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context (alleen wat `/sessie-start` NIET al leest):
`docs/sessions/S200-BEVINDINGEN.md` — het volledige auditrapport met per bevinding
familie, bewijs (file:line + SQL), ernst en fix-grootte. Dit is de werklijst.

## Taak
Werk de S200-bevindingen af in de volgorde van de samenvattingstabel onderin het rapport.
Per fix: EERST rode test (waar zinvol), dan fix, dan groen. Kort per fix:

**Ronde 1 — klein & direct (XS/S):**
1. Tijdlijn-crash: `timeline_service.py:119` leest `duration_seconds`, model heeft
   `duration_minutes` (#13) — 1 regel + test met één time_entry.
2. Hernoemen-knop: PATCH `/api/cases/{case_id}/files/{file_id}` bouwen (alleen
   `original_filename`, tenant-scoped) + `onError` op de mutation (#4).
3. AI-draft €0-fallback markeren: fallback in `automation_service.py:420-440` zet een
   waarschuwing op de draft + review-taak "bedragen controleren" (#3).
4. Dashboard "1169 toegevoegd deze maand": import-contacten niet meetellen of subtitel
   weg (#6). Zelfde patroon checken bij `cases_this_month`.
5. Batch-toast: fouten (`skipped`/`emails_failed`/`errors[]`) als warning/error tonen,
   niet in een groene succes-toast; errors-lijst renderen (#9, incasso/page.tsx:1111).
6. Nep-tabs Instellingen → Meldingen + Weergave verwijderen (#11, #12).
7. Cijfer-cosmetiek: negatief "Openstaand" afdekken ("teveel betaald"), één definitie
   van "Openstaand" per context of label aanpassen (#14); incasso-ratio: teller en
   noemer zelfde populatie geven (#10).

**Ronde 2 — middelgroot (M):**
8. Mailsync-gezondheid: `sync_error`/`last_sync_status` op email_accounts + banner in
   Instellingen→E-mail + notificatie na X uur zonder geslaagde sync (#1).
9. Scheduler-heartbeat: laatste-run-registratie per job + signaal bij uitblijven,
   minimaal voor de verjaringscheck (#2).
10. Intake seedt startstap + historie-rij (#8) — daarmee vult Staphistorie zich weer.
11. 14-dagenbrief-check aansluiten op het echte verzendspoor én aanroepen in de
    verstuurflow (#5, juridisch — overleg bij twijfel, niet stoppen).
12. Sloopronde: 35 dode routes uit het rapport (behalve auth/register, imap/connect,
    DELETE workflow-task — zie kanttekeningen in #16), dode hook `usePendingCount`,
    Gmail-knop verbergen (#17), frontend-logout aansluiten op `POST /api/auth/logout`.

Stop wanneer de sessie vol raakt: elke afgeronde fix apart committen, rapport-tabel
bijwerken met ✅ per afgewerkt nummer.

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -v` (na rondes met gedeelde code)
- Lint: `docker compose exec backend ruff check app/`
- Build: `cd frontend && npm run build`
- Fixes 1-7: ook functioneel in de browser checken (grondig checken = visueel + functioneel)

## Constraints (wat NIET doen)
- Geen nieuwe features naast de lijst; #18 (derdengelden-werkwijze) is een gesprek met
  Lisanne, niet bouwen. Log-persistentie VPS alleen als er tijd over is (klein houden).
- Mailslot NIET aanzetten. Geen prod-data wijzigen buiten wat een fix zelf vereist.
- Bij e-mail-tests: recipient ALTIJD arsalanir@hotmail.com.

## Commit
Commit + push naar main per fix met conventional commit message. Deploy automatisch via SSH.
