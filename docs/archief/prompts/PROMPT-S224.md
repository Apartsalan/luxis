cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 224 — Veegsessie (kruispunt-matrix) + live-verzendtoets

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door.
Model: **Fable** (audit/review). Extra context (naast wat `/sessie-start` leest):
`.claude/skills/breed-testen/SKILL.md` (de huisregel-lijst + kandidaat-wachters)
en `docs/sessions/S223-review.md`.

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `PROMPT-S215.md`), dán de rest.
NEE → direct door.

## Taak A — DE VEEGSESSIE (hoofdtaak, Fable, read-only tenzij fix nodig)
Volg de skill `breed-testen`. Loop de **volledige huisregel-lijst × alle bestaande
routes** af zodat de foutenteller aantoonbaar op nul staat en daarna door wachters
schoon blijft. Per huisregel: benoem het effect → grep ALLE routes → cel-voor-cel
toetsen (meten in de bron/prod-DB, niet aannemen).

Focus (uit de skill):
- **Uitgaande mail M1-M5** op élke route (compose/send, .eml, documents/send,
  followup inline+DOCX, batch inline+DOCX): afzender = kantoor; drieluik-logging
  (EmailLog+SyncedEmail+CaseActivity); mailslot + 14-dagenbrief-gate; onderwerp via
  de gedeelde bouwer; bijlagen volgen het brieftype.
- **Pijplijn P1-P3**: alleen stap-brieven bewegen de pijplijn; stap-wissel + zaak-
  sluiten ruimen concepten/adviezen op (P3 net gebouwd — verifieer breed).
- **AI-output A1-A3**, **geld**, **toegang** (bestaande drift-guards spiegelen, niet
  aanraken), **zichtbaarheid** (leeskant per pagina).

**Bouw de kandidaat-wachters** uit de skill:
- M2-drieluik-wachter: enumereer aanroepers van de provider-send; elke route zonder
  `write_outbound_log` = rood.
- M4-onderwerp-wachter: geen route zet een concept-/mail-onderwerp buiten
  `build_email_subject`/`build_reply_subject` om.
Elke NIEUW gevonden foutsoort → huisregel bijschrijven in de skill + wachter.

## Taak B — Live-verzendtoets (zodra mailslot/afspraak het toelaat)
In S223 niet gedaan door het open mailslot. Toets écht versturen op een veilig
testadres (Arsalans gmail = testdossier 2026-00006), NIET naar echte debiteuren:
1. Nieuwe AI-antwoord-knop → concept → **Versturen** → mail bezorgd + zichtbaar op
   Mail-pagina, dossier-correspondentie én tijdlijn; onderwerp = Re:-huisformaat.
2. Batch-PDF-route (dagvaarding/verzoekschrift) → onderwerp = huisformaat (geen
   "/ /"), PDF-bijlage bezorgd.
3. Classificatie-trigger: bevestig dat een verse inkomende mail meteen (~5 min)
   geclassificeerd wordt (nog nooit op prod gevuurd).

## Constraints
Geen echte debiteuren mailen (mailslot). Prod-mutaties: dry-run/telling + GO
Arsalan. Geen `git add -A` (expliciete paden). Beslispunten niet zelf beslissen.
Na elke commit `git push origin main` + deploy via SSH. Lokaal testen (`uvx ruff
check`, relevante pytest) vóór push. **CI-check hoort nu in de afsluiting** (stond
sinds 15/7 stil rood, S223).

## Verificatie
- Backend: relevante `pytest` (detached bij full suite), `uvx ruff check app/`.
- CI groen na push (`gh run list`) — niet vergeten (S217/S223-les).

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag +
PROMPT-S225). Veeg-rapport: `docs/sessions/S224-veegsessie.md`.

## Nog open na S223 (kies met Arsalan)
- Auto-concept-gate: menselijke steekproef Lisanne (~10 echte concepten) vóór
  activering; daarna categorie-route op de nieuwe antwoordmotor aanzetten.
- S221b-UX-restant: review-scherm classificatie+concept, voortgangsindicator,
  échte HTML-tabellen (injectie-oppervlak), Blok 5-rest, Blok 6-memo b2b/b2c.
- Losse klusjes: landregel dagvaarding/faillissementsverzoek; filter "Nog te
  openen" (filterknop); rest-PDF's (206); 7 Mollie/kop-conflictfacturen; anker-
  subnav Financieel + geldstrook-uitbreiding gewone zaak.
