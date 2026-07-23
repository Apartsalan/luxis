cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 244 — Mail-werkbank (demo-punten blok 1)

## Model
Bouwen → **Opus**. Check bij start welk model actief is; verkeerd model →
wissel vragen vóór je begint. Eindreview op Fable (wissel melden).

## Start
Draai `/sessie-start`. Masterplan: `docs/plans/PLAN-DEMO-PUNTEN-S243.md`
(sectie S244). CI van de S243-commits natrekken (`gh run list`).

## Hoofdtaak — mail werkbaar maken voor Lisanne (4 onderdelen)
1. **Correspondentie-tab redesign**
   (`frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx`,
   591 regels): nu staan alle mails plat onder elkaar, titel eet het beeld op,
   niets klapt uit. Eerst 15 min referentie-onderzoek (Gmail/Outlook/Clio:
   conversation-lijst + leesvenster), plan kort voorleggen, dan bouwen:
   draad-groepering op provider_thread_id (terugval: genormaliseerd onderwerp),
   compacte rijen (afzender · onderwerp één regel · datum · richting-pijl),
   klik = uitklappen.
2. **Draad overal zichtbaar**: hergebruik `MailThreadPanel`
   (`frontend/src/components/mail-thread-panel.tsx`, S233) in het leesvenster
   van de Mail-pagina (`EmailDetailPanel` in correspondentie/page.tsx) én in de
   AI-concept-review-dialoog: concept links, draad rechts (mobiel gestapeld) —
   Lisanne moet kunnen zien wat er eerder is gezegd terwijl ze het concept leest.
3. **Verzonden-map**: Mail-pagina tabs uitbreiden (Postvak IN / Verzonden):
   direction-queryparam op het bestaande `/api/email/all`-endpoint
   (`email/sync_router.py`), frontend-hook `useAllEmails` + tabs.
4. **Lege sjabloon + nette beantwoorden-mail**: renderer "vrij_bericht" in
   `backend/app/email/incasso_templates.py` — aanhef "Geachte heer/mevrouw,",
   lege romp, bestaande huisstijl + handtekening (via de branding-bouwstenen in
   send_service). Toevoegen aan TEMPLATE_GROUPS (email-compose-dialog.tsx).
   "Beantwoorden" prefillt voortaan deze shell zodat Lisanne alleen inhoud typt.

## Verificatie (HARD — les S233/demo)
- pytest -k "compose or send or template" + bestaande mailsuites; uvx ruff;
  npx tsc --noEmit.
- Kruispunt-check skill `breed-testen` (verzendroute geraakt bij punt 4).
- **Playwright-klikronde op prod als Lisanne, desktop + mobiel 390×844,
  screenshots bewaren**: draad openen in dossier, concept-naast-draad lezen,
  Verzonden-tab, beantwoorden-met-shell. "Werkt" zonder beeld telt niet.
- Deploy via SSH `--force-recreate`, login 200, CI groen.

## Constraints
- Geen echte debiteuren mailen zonder GO per geval; testen op 2026-00006.
- Prompt-JSON gewijzigd → schema mee (S238-huisregel; hier niet verwacht).

## Commit
Per onderdeel een conventional commit + push. Afsluiten met `/sessie-einde`
(volgende prompt = PROMPT-S245).
