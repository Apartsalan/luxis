cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 225 — Bouwsprint: beslispunten uitvoeren + S221b-UX-restant

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Opus** (bouwen/klikwerk). Extra context (naast wat `/sessie-start` leest):
`docs/sessions/S224-veegsessie.md` (§5-6: de beslispunten B1-B6).

## ⚠️ Voorrang-check — GEDAAN (17 juli, Fable)
KvK-sleutel NIET binnen (0 treffers in `/opt/luxis/.env` + container-env) → direct door.

## Beslispunten — ANTWOORDEN ARSALAN BINNEN (17 juli, via Fable)
- **B1 facturen-afzender: → incasso@.** `send_invoice` krijgt
  `send_as_tenant_account=True`; allowlist/motivering in
  `test_send_route_drift_guard.py` bijwerken (M4-onderwerp "Factuur {nr}" blijft
  bewust eigen formaat).
- **B2+B3: beide verwijderen.** Dode AI-tool `email_compose` (registry zonder
  aanroepers) én legacy endpoint `/api/email/cases/{id}/send` + hook
  `useSendCaseEmail` weg; bijbehorende allowlist-regels in
  `test_send_route_drift_guard.py` opruimen (eerlijkheids-test dwingt dat af).
- **B4 Bayar IN100613: NIETS DOEN.** Dossier is 15/7 handmatig door Arsalan
  gesloten (BaseNet zei nog 'Lopend', geen betaling); hij wil het eerst zelf
  bekijken/overleggen. Wees-advies dus óók laten staan. NIET aanraken.
- **B5 testdossier 2026-00006: actief laten** als vast testkanaal.
- **B6 batch-DOCX live toetsen: JA, maar in de Fable-testfase (niet in deze
  Opus-sessie).** ⚠️ Arsalan wil ook nog **iets toevoegen aan de batch** — vóór
  de batch-toets eerst bij hem terugkomen om te horen wat.

## Taak A — B1 + B2/B3 uitvoeren (bouwen)
Zie hierboven. Kruispunt-check (skill `breed-testen`): B1 raakt een verzendroute,
B2/B3 verwijderen routes — wachters (`test_send_route_drift_guard.py`) draaien mee.

## Taak B — S221b-UX-restant (zoveel als past)
Review-scherm classificatie+concept naast elkaar; voortgangsindicator bij
genereren; échte HTML-tabellen in AI-mails (injectie-oppervlak — behoedzaam);
Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat, soft-delete-banner,
follow-up dossierlink/dagen-kolom/sorteerbare koppen, intake-detectie dempen);
Blok 6-beslismemo b2b/b2c (105 dossiers, geen code).

## Daarna (aparte sessie, Fable — afspraak Arsalan 17 juli)
Alles testen/reviewen + de batch-DOCX-tak live toetsen op testdossier
2026-00006. Eerst bij Arsalan langs: wat wil hij aan de batch toevoegen?

## Constraints
Geen echte debiteuren mailen (testdossier 2026-00006 = Arsalans gmail). Prod-
mutaties: dry-run/telling + GO. Geen `git add -A`. Bayar IN100613 niet aanraken
(B4). Kruispunt-check (skill `breed-testen`) bij elk gedeeld effect.

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- Frontend: `npx tsc --noEmit`.
- CI groen na push (`gh run list`) — vaste afsluitcheck.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag +
PROMPT-S226 = de Fable-test/review-sessie hierboven).

## Nog open na S224
- Auto-concept-gate: menselijke steekproef Lisanne (~10 echte concepten) vóór
  activering.
- V2c (klein): classificatie-antwoord-onderwerp naar `build_reply_subject`.
- KvK-backfill zodra sleutel binnen (~22 juli) — houdt voorrang.
