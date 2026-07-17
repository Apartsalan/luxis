cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 227 — A1: AI-antwoord-knop óók op het dossier-tabblad Correspondentie

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules/pagina's, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Opus** (bouwen).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `docs/archief/prompts/PROMPT-S215.md`),
dán A1. NEE → direct door.

## Taak A1 — AI-antwoord-knop op dossierniveau
De knop "AI-antwoord maken" (instructieveld + toon-keuze mild/zakelijk/streng,
onbeperkt herbruikbaar, wacht niet op de automatische classificatie) bestaat nu
ALLEEN op de Mail-pagina (`frontend/src/app/(dashboard)/correspondentie/page.tsx`,
gebouwd in S223). Arsalan wil hem óók op het **tabblad Correspondentie van het
dossier** (`zaken/[id]`), bij de inkomende mails van de wederpartij — zelfde
dialoog, zelfde spelregels.

- **Component delen, niet kopiëren.** De dialoog + generatie-flow uit S223
  hergebruiken (backend bestaat al: `GET /api/ai/draft/existing`, `force_new`,
  `find_open_reply_draft`, `generate_unified_draft` met intent=reply). Alleen de
  knop + dialoog op de dossier-correspondentieweergave inhaken.
- **Startpunt:** zoek het correspondentie-tabblad van het dossier (waarschijnlijk
  `zaken/[id]/components/DocumentenTab.tsx` of een aparte correspondentie-component)
  en de bestaande knop-implementatie op de Mail-pagina; deel de dialoog-component.

⚠️ **Nieuwe route voor het effect "concept maken" → kruispunt-check verplicht**
(skill `breed-testen`): loop de route×huisregel-matrix af en bewijs breed:
- afzender incasso@ (M1), drieluik vastgelegd (M2), onderwerp huisformaat via
  `build_reply_subject` (M4, GEEN dubbele "Betreft:"), antwoord schuift de zaak
  NIET door (P1), open-concept-dedupe (bestaand concept eerst tonen), zichtbaarheid
  op incasso/dossier/tijdlijn/Mail/Taken/follow-up.
- Elke gevonden foutSOORT → een wachter-test (niet één test voor het geval).

## Constraints
Geen echte debiteuren mailen (testkanaal 2026-00006 = Arsalans gmail).
Prod-mutaties: dry-run/telling + GO. Geen `git add -A` (`*.png` etc. gitignored →
force-add alleen bewust). Bayar IN100613 NIET aanraken. Testdata 2026-00007 t/m
-00019 mag opgeruimd worden ná GO (natelling) — Arsalan wilde ze eerst bewaren.

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- Frontend: `npx tsc --noEmit`.
- CI groen na push (`gh run list`) — vaste afsluitcheck.
- Live doorklikken op 2026-00006 (concept genereren + zichtbaarheid).

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag
sessie-227 + PROMPT-S228).

## Nog open na S226
- **DMARC ontbreekt op kestinglegal.nl** → Arsalan/BaseNet publiceert een
  DMARC-record (SPF+DKIM zijn OK); verklaart waarom gmail dagvaarding/
  faillissement wegfiltert. Buiten Claude's bereik — alleen opvolgen.
- S221b-UX-restant: review-scherm classificatie+concept, voortgangsindicator,
  échte HTML-tabellen (injectie-oppervlak), tijdlijn-mailregel klikbaar,
  follow-up sorteerbare koppen, intake-detectie dempen, Blok 6-memo b2b/b2c.
- Auto-concept-gate: menselijke steekproef Lisanne (~10 echte concepten) vóór
  activering.
- V2c (klein): classificatie-antwoord-onderwerp naar `build_reply_subject`.
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
