# PLAN — Demo-punten Arsalan (S243, 23 juli 2026)

Na de demo met Lisanne: 13 punten. Alles in S243 in de bron gemeten (code +
prod-DB + BaseNet-export). Verdeling over 4 sessies; volgorde gekozen door
Arsalan. Model-cyclus: bouwen op Opus, review op Fable (wissel actief melden).

## Al gedaan in S243 (23-7)
- **607-check**: alle export-dossiers staan 1-op-1 in Luxis (0 ontbreken).
- **Vindbaarheid**: zoeken + filter op BaseNet-fase (`062ac4b`, live + visueel
  bewezen: filter én zoekterm geven exact de 11).
- **11 "Akkoord dagvaarden" heropend** (stap gelijknamig, eigenaar Lisanne,
  rente loopt, 0 mails). Rest-fases: beslislijst `BASENET-STATUS-HERSTEL.md`.
- Opruimronde: 37 test-taken dicht, 14 test-adviezen afgewezen, 38 testmails/
  reclame weggedrukt, 15 test-intakes afgewezen (dry-run + natelling, elk exact).

## Besluiten Arsalan (S243)
1. Volgorde: **S244 mail-werkbank → S245 taken+meldingen → S246 uitgesteld
   versturen → S247 AI-kennislaag**.
2. Meldingen: antwoord verstuurd op dossier X → ongelezen máil-meldingen van
   dossier X op gelezen (andere types/dossiers blijven).
3. Geen massa-heropening; per fase-groep GO via de beslislijst.
4. **Alles wat visueel kan, visueel testen** (Playwright, desktop + mobiel,
   screenshots) — les: S233-mailpaneel was functioneel getest maar onwerkbaar.

## S244 — Mail-werkbank (grootste sessie; prompt: PROMPT-S244.md)
1. Correspondentie-tab redesign: draad-gegroepeerd (provider_thread_id, terugval
   genormaliseerd onderwerp), compacte rijen, uitklappen. Eerst 15 min
   referentie-onderzoek (Gmail/Outlook/Clio: conversation list + reading pane).
2. Draadweergave overal: `MailThreadPanel` (bestaat, S233) hergebruiken in het
   Mail-leesvenster én naast het AI-concept (naast elkaar; mobiel gestapeld).
3. Verzonden-map: direction-filter op `/api/email/all` + tabs Postvak IN/Verzonden.
4. Lege sjabloon "Vrij bericht" (aanhef + handtekening/huisstijl, lege romp) +
   Beantwoorden prefillt die shell.
5. Meldingen-vraag (besluit 2) zit in S245, NIET hier.

## S245 — Taken + meldingen (prompt: PROMPT-S245.md)
1. Dossierinfo op taken: `WorkflowTaskResponse` + case-subobject (nummer,
   debiteur, cliënt) via selectinload in `wf_list_tasks`; frontend toont het
   (regel `task.case && …` in taken/page.tsx werkt dan vanzelf).
2. Filters op de Taken-pagina (taaktype/dossier/eigenaar, client-side).
3. Dubbel-wegklik-bug: eerst reproduceren (globale isPending + geen optimistic
   update; herhalende taken maken direct een opvolger), dan per-rij fix.
4. Mail-meldingen automatisch gelezen na verstuurd antwoord op dat dossier
   (nieuwe servicefunctie naast `mark_type_read`; wachters op afbakening).

## S246 — Uitgesteld versturen (prompt: PROMPT-S246.md)
Nieuwe tabel `scheduled_emails` (TenantBase + RLS in dezelfde migratie!),
"Verstuur later" op álle verzenddeuren (7: send_with_attachment-callers +
compose_router send_via_provider), scheduler-job met lock-patroon, presets
(morgen 09:00/15:00/eigen tijd), geplande mails zichtbaar + annuleerbaar.
Kruispunt-check breed-testen verplicht.

## S247 — AI-kennislaag (prompt: PROMPT-S247.md)
1. Placeholder-bug: prompt (incasso_email_prompts.py:314-318) vult
   `<kernverweer letterlijk uit incoming_defense>` niet in — fixen + wachter.
2. Juridische kennisregels (IN100458: "BV wil AV vernietigen — kan niet,
   art. 6:235 BW"): curated regels via de bestaande goedkeur-flow, élke regel
   langs Lisanne. 132 learned_answers wachten al op goedkeuring — aankaarten.
3. Prompts gewijzigd → derde AI-testronde (S238-huisregel).

## Geparkeerd (bestaande kandidaten, niet in deze reeks)
- Verweer-parkeerstap-terugkeer (`VOORSTEL-verweer-parkeerstap-terugkeer.md`).
- "AI-bericht maken" los van inkomende mail (IN100483) — eerst bespreken.
- Fase-heropening per groep (`BASENET-STATUS-HERSTEL.md`).
