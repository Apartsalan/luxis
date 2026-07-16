cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 225 — Beslispunten veegsessie + S221b-UX-restant

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Opus** (bouwen/klikwerk). Extra context (naast wat `/sessie-start` leest):
`docs/sessions/S224-veegsessie.md` (§5-6: de beslispunten B1-B6).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `PROMPT-S215.md`), dán de rest.
NEE → direct door.

## Taak A — Beslispunten B1-B6 afhandelen (antwoorden Arsalan ophalen/verwerken)
Uit `S224-veegsessie.md` §5-6 — per punt eerst Arsalans keuze, dan uitvoeren:
- **B1** facturen-afzender: persoonlijk account houden of `send_as_tenant_account=True`
  (1 regel + allowlist-regel M4-wachter bijwerken als het incasso@ wordt)?
- **B2** dode AI-tool `email_compose` (registry zonder aanroepers): verwijderen?
- **B3** legacy endpoint `/api/email/cases/{id}/send` + hook `useSendCaseEmail`:
  verwijderen? (Leeft nog, SMTP geconfigureerd, geen gate + half drieluik.
  Verwijderen = ook de allowlist-regels in `test_send_route_drift_guard.py` opruimen.)
- **B4** wees-advies IN100613 → SUPERSEDED (1 UPDATE + natelling, GO).
- **B5** testdossier 2026-00006: weer archiveren of actief laten als testkanaal?
- **B6** batch-DOCX-tak live toetsen (vereist tijdelijke stap-mutatie) — nu of later?

## Taak B — S221b-UX-restant (zoveel als past)
Review-scherm classificatie+concept naast elkaar; voortgangsindicator bij
genereren; échte HTML-tabellen in AI-mails (injectie-oppervlak — behoedzaam);
Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat, soft-delete-banner,
follow-up dossierlink/dagen-kolom/sorteerbare koppen, intake-detectie dempen);
Blok 6-beslismemo b2b/b2c (105 dossiers, geen code).

## Constraints
Geen echte debiteuren mailen (testdossier 2026-00006 = Arsalans gmail). Prod-
mutaties: dry-run/telling + GO. Geen `git add -A`. Beslispunten niet zelf
beslissen. Kruispunt-check (skill `breed-testen`) bij elk gedeeld effect — de
nieuwe wachters (`test_send_route_drift_guard.py`) draaien mee in de suite.

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- Frontend: `npx tsc --noEmit`.
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag +
PROMPT-S226).

## Nog open na S224
- Auto-concept-gate: menselijke steekproef Lisanne (~10 echte concepten) vóór
  activering.
- V2c (klein): classificatie-antwoord-onderwerp naar `build_reply_subject`.
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
