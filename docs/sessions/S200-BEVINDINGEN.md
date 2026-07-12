# S200 — "De voorkant liegt"-audit: bevindingen

**Datum:** 12 juli 2026 · **Uitgevoerd door:** Fable (read-only op prod, geen enkele schrijfactie) · **Fixes:** S203 (S201=facturatie-onderzoek en S202=security-delta waren al vergeven)
**Prod-stand tijdens meting:** commit `3eec699` (S199-eind), 607 zaken / 27 actief / 1169 relaties / 6509 gesyncte mails.

**Verificatie-legenda:** elke bevinding is gelabeld:
- ✅ = zelf geverifieerd deze sessie (bron gelezen + SQL/scherm/API-bewijs)
- 🔍 = gevonden door subagent-trace, dragende kern door mij nagelezen
- ⚠️ = subagent-claim, niet zelf herlezen (expliciet vermeld)

**Ernst:** 🔴 blokkeert · 🟠 misleidend · 🟡 cosmetisch/laag

---

## Eerst het goede nieuws (belangrijk voor de weging)

De klassieke S190/S191-leugens zijn weg. **Alle 30+ gecontroleerde cijfers op dashboard, rapportages en badges kloppen op de cent** met onafhankelijke SQL op prod:
actieve zaken 27 ✓, statusverdeling 17+10 ✓, hoofdsom €275.471,76 ✓, ontvangen €14.685,16 ✓, Geïnd €135.354,77 ✓, faseverdeling sluit (9+2+5+1+10=27, bedragen op de cent) ✓, meldingen-badge 20 ✓, Mail-badge 83 ✓, Incasso-badge 18 (=8 klaar + 10 zonder stap) ✓, Follow-up 14 ✓, taken 2 ✓, doorlooptijd 95 dagen ✓.
Frontend-mutaties hebben een globaal foutvangnet (`MutationCache.onError → toast.error`, providers.tsx:36) en alle 141 mutationFn's checken `res.ok` (⚠️ scan door subagent, steekproef klopte).

**Bijvangst — S191-mysterie opgelost:** de "onverklaarbare" meldingen-mismatch (264 vs 299) is geen bug. De bel telt per gebruiker en verbergt het type `classification_done` (`HIDDEN_BELL_TYPES`, notifications/service.py:27). SQL: seidony 20 zichtbaar ongelezen (12+4+2+1+1) = exact de badge. ✅

---

## 🔴 Hoogste prioriteit (raakt Lisanne deze week / juridisch)

### 1. E-mail-autosync kan stil doodgaan — niemand merkt het ✅ (familie 4: stil falen)
- **Wat:** faalt de 5-minuten-sync voor een account (bv. verlopen OAuth-token), dan gaat dat alleen naar de server-log (`scheduler.py:211-212`, zelf gelezen). Er is géén `sync_error`-veld (email_accounts-kolommen op prod gecheckt: alleen `last_sync_at`), geen notificatie, geen banner.
- **Gevolg:** de Correspondentie-tab blijft er normaal uitzien; "geen nieuwe mail" is niet te onderscheiden van "sync al dagen stuk". Inkomende verweren en betaaltoezeggingen worden dan gemist.
- **Bewijs:** code + prod-schema; 4 accounts syncen nu wél (laatste sync 10:04 vandaag).
- **Fix-grootte:** middel — statusveld + waarschuwing in Instellingen→E-mail + notificatie na X uur zonder sync.

### 2. Alle scheduler-jobs falen onzichtbaar — inclusief de verjaringscheck ✅/🔍 (familie 4)
- **Wat:** alle 12 APScheduler-jobs eindigen op `except Exception: logger.exception(...)` (o.a. `scheduler.py:160-161` verjaring, `:238-239` mailsync — zelf gelezen; overige 10 🔍). Geen "laatste run"-status, geen dead-man-switch.
- **Gevolg:** faalt `daily_verjaring_check` structureel, dan verschijnen er gewoon géén verjaring-waarschuwingen — juridisch het gevaarlijkste stilte-scenario.
- **Fix-grootte:** middel — job-heartbeat in DB + dashboard-signaal bij uitblijven.

### 3. AI-conceptbrief valt bij rekenfout stil terug op €0 rente/BIK ✅ (familie 4)
- **Wat:** faalt `get_financial_summary` tijdens draft-generatie, dan wordt de sommatie gebouwd met `rente=0, bik=0, btw=0` en alleen server-side gelogd (`automation_service.py:420-440`, zelf gelezen). Niets markeert de draft als "bedragen onvolledig".
- **Gevolg:** Lisanne reviewt een nette brief met te lage bedragen en verstuurt hem.
- **Fix-grootte:** klein — fallback markeren op de draft + review-taak "bedragen controleren".

### 4. "Hernoemen" van een dossierbestand is een kapotte knop ✅ (familie 1 + 4)
- **Wat:** de frontend doet `PATCH /api/cases/{id}/files/{id}` (use-case-files.ts:102) maar dat endpoint **bestaat niet** — cases/router.py heeft alleen GET download/preview en DELETE (zelf geverifieerd). De mutation heeft bovendien geen `onError` (DocumentenTab.tsx:1296-1308): Enter → 405 → géén melding, het invoerveld blijft gewoon staan.
- **Waar:** Dossier → Documenten → "Hernoemen" (staat op elk van de 2619 case-files).
- **Fix-grootte:** klein — PATCH-endpoint bouwen óf knop verwijderen; onError toevoegen.

### 5. De wettelijke 14-dagenbrief-check is dubbel dood ✅ (familie 2 + 5, juridisch)
- **Wat:** `check_document_compliance` (collections/compliance.py:56-77, zelf gelezen) controleert vóór een B2C-sommatie of er een 14-dagenbrief is — door te zoeken in `generated_documents`. Die tabel is **blijvend leeg** (bevinding 7), dus de check zou élke B2C-sommatie blokkeren. Maar dat merkt niemand, want het endpoint `GET /api/cases/{id}/compliance-check` heeft **nul UI-callers** (bevestigd door twee onafhankelijke traces).
- **Gevolg:** er is feitelijk géén werkende waarborg op art. 6:96 lid 6 BW (14-dagenbrief bij consumenten) — terwijl de code suggereert van wel. Er zijn nu 2 actieve B2C-zaken.
- **Fix-grootte:** middel — check aansluiten op het echte verzendspoor (synced_emails/stap-historie) én aanroepen in de verstuurflow.

### 6. Dashboard: "1169 toegevoegd deze maand" bij Relaties ✅ (familie 3: liegend cijfer)
- **Wat:** de widget telt `contacts.created_at >= 1 juli` — maar álle 1169 contacten hebben created_at 3–8 juli (BaseNet-import-stempel; SQL: min 2026-07-03, max 2026-07-08). Er zijn 0 echt nieuwe relaties. Zelf live op het scherm gezien.
- **Opmerking:** dit is het al bekende "1169 nieuw"-voorbeeld uit de S199-familielijst — het staat dus nog steeds live.
- **Fix-grootte:** klein — importrecords uitsluiten (bron-veld) of de subtitel weglaten.

---

## 🟠 Misleidend (verdient S201, geen acuut risico)

### 7. "Gegenereerde documenten" op de Documenten-tab blijft voor altijd leeg 🔍 (familie 2)
`generated_documents` = 0 rijen terwijl er wél brieven uitgaan: het live pad (AI-concept → `POST /api/email/compose/send`; sjabloon → `render-pdf` als bijlage) persisteert bewust niets naar die tabel (compose_router.py + documents/router.py:250-297, trace 🔍; lege sectie zelf op prod gezien ✅). Het echte spoor zit in `synced_emails` (Sent-sync). Gevolg: geen document-audittrail per dossier én de basis onder bevinding 5. Fix: middel.

### 8. Staphistorie-tab toont altijd "Geen staphistorie" ✅ (familie 2)
`case_step_history` heeft 0 rijen op heel prod (SQL ✅) terwijl de pipeline actief gebruikt wordt. Structurele oorzaak: **AI-intake — het hoofdinstroomkanaal — maakt dossiers aan zonder stap en zonder historie-rij** (intake_service.py:447-463, zelf gelezen: geen `incasso_step_id`, geen `move_case_to_step`). Klopt met de data: precies de 10 stap-loze actieve zaken zijn intake-instroom. Fix: klein/middel — intake een startstap + historie-rij laten zetten.

### 9. Incasso-batch: altijd een groene succes-toast, foutdetails verdwijnen ✅ (familie 4)
`onSuccess` bouwt ook bij `skipped > 0` en `emails_failed > 0` een `toast.success` (incasso/page.tsx:1111-1124, zelf gelezen), en de `errors`-lijst van de backend (reden per overgeslagen dossier) wordt nergens in de frontend gerenderd. Welke dossiers níét doorgeschoven zijn moet Lisanne zelf uitzoeken. Fix: klein.

### 10. "Incasso-ratio 49,1%" deelt appels door peren ✅ (familie 3)
Teller = álle betalingen van de laatste 12 maanden, ook op archiefzaken (€135.354,77); noemer = hoofdsom van alleen de 27 open zaken (€275.471,76) — reports_service.py:62-73. De ratio kan boven de 100% uitkomen en zegt nu niets over inningsprestatie. Fix: klein (één populatie kiezen).

### 11. Instellingen → Meldingen is een nep-scherm ✅ (familie 5)
Vier hardcoded voorkeuren-toggles, waarvan twee "aan" tonen; klikken doet alleen een toast "wordt binnenkort toegevoegd" (meldingen-tab.tsx:6-58 🔍; zelf visueel bevestigd op prod ✅). Er bestaat geen backend voor voorkeuren en geen wekelijks overzicht. Fix: klein — tab verwijderen tot de feature bestaat.

### 12. Instellingen → Weergave zit nergens aan vast ✅ (familie 5)
"Sidebar standaard ingeklapt" en "Datumformaat" hebben geen state/persistentie; thema toont één niet-klikbare optie (weergave-tab.tsx:32-57 🔍; zelf visueel bevestigd ✅). Fix: klein — verwijderen.

### 13. Latente crash: dossier-tijdlijn leest een veld dat niet bestaat ✅ (bijvangst audit 2)
`timeline_service.py:119` leest `t.duration_seconds`; het model heeft alleen `duration_minutes` (time_entries/models.py:36 — beide zelf gelezen). Zodra iemand één keer de (altijd zichtbare) timer stopt of uren logt, crasht de dossier-tijdlijn met een 500. Nu gemaskeerd doordat time_entries leeg is; tijdschrijven-module staat wél aan. Fix: 1 regel.

### 14. Twee definities van "Openstaand" + negatieve bedragen in lijsten ✅ (familie 3)
- Lijstkolom "Openstaand" (zaken/incasso) = hoofdsom − betaald; dossier-sidebar "Openstaand" = incl. rente + BIK. Zelfde woord, ander getal: IN100019 toont €8.069,35 in de lijst en €10.772,73 in het dossier.
- Overbetaalde zaken tonen rauwe negatieve bedragen: IN100197 "€ -370,30", IN100350 "€ -224,28" — status nota bene "Nieuw".
- Fix: klein — label/definitie gelijktrekken, negatief afdekken ("teveel betaald").

### 15. Afgesloten dossier met actief rood termijn-alarm — bewust, maar verwarrend ✅
IN100019: status "Afgesloten", tóch actieve regeling (0/11 betaald) + "Gemist"-alarm op het dashboard. De query filtert bewust niet op zaakstatus (docstring collections/service.py:958-963: 9 van de 13 actieve regelingen hangen aan afgesloten zaken — geïmporteerde werkelijkheid). Geen bug, wel een uitlegprobleem: het dossier zegt "klaar", het dashboard zegt "actie". Fix: klein — badge "regeling loopt door" op de dossierkop, of status heroverwegen bij import.

---

## 🟡 Relieken & sloop-kandidaten (familie 6 — lijst voor S201)

### 16. 35 backend-routes zonder enige caller ⚠️ (trace door subagent, steekproeven ✅)
Volledige lijst in de sessie-log. Kernen:
- **Al `deprecated=True`:** POST/PUT/DELETE `/api/documents/templates*`, POST `/api/documents/cases/{id}/generate` (oude HTML-templates; tabel `document_templates` = 0 rijen).
- **Nooit aangesloten:** o.a. `/api/cases/{id}/compliance-check` (zie bevinding 5!), `/api/cases/{id}/griffierecht`, `/api/ai-agent/client-update/{id}`, `/api/ai-agent/templates(+seed)`, `/api/auth/tenant` (GET+PUT), `/api/email/status`, `/api/workflow/verjaring`, `/api/relations/conflict-check` (POST-variant), `/api/interest-rates` (bewust behouden per UX-RESEARCH-E2), PATCH `/api/ai-agent/drafts/{id}`, PATCH claims link-invoice, exact-online sync-log/sync-invoice, payment-matching kale approve + imports-detail, GET-single-varianten (workflow task, calendar event, expense, arrangement, classification).
- **Niet slopen zonder besluit:** `POST /api/auth/register` (gedocumenteerde ops-flow), `POST /api/email/oauth/imap/connect` (enige herstelkanaal voor de incasso@-IMAP-koppeling), DELETE workflow-task (e2e-cleanup gebruikt hem).
- **Andersom-vondst:** `POST /api/auth/logout` (refresh-token-revocatie, AUD124-21) wordt door de frontend **nooit aangeroepen** — logout is puur client-side. Zou juist aangesloten moeten worden (security).
- **Dode frontend-hook:** `usePendingCount` (ai-agent) heeft nul gebruikers; het bijbehorende endpoint telt 469 "pending" classificaties die nooit iemand reviewt.

### 17. Gmail-koppelknop staat nog live terwijl het beleid "alleen Outlook" is ⚠️/✅
Instellingen → E-mail heeft een werkende `handleConnect("gmail")`-knop (email-tab.tsx:271) + levende Google-OAuth-callback. Beleid sinds feb 2026: geen Gmail. Fix: klein — knop verbergen.

### 18. Derdengelden-module volledig ongebruikt — signaal, geen bug ✅
`trust_transactions` = 0; alle 272 betalingen zijn geboekt als bank/cash búiten het derdengeldenkanaal. De schermen tonen eerlijk €0,00. Voor een incassokantoor (debiteurgeld hoort via derdengelden) is dit een werkwijze-vraag voor Lisanne/Arsalan, geen codefout.

### 19. Overige lege tabellen: eerlijk leeg, geen bevinding ✅/🔍
`invoices`/`invoice_lines`/`invoice_payments`, `time_entries`, `bank_*`/`payment_matches`, `calendar_events`, `contact_links`, `expenses`, `exact_*`, `kyc_verifications` (module uit), `case_parties` (cliënt/wederpartij komen uit cases-kolommen): alles volledig bedraad met nette lege staten — features die wachten op gebruik. `email_logs` = audit-log van het oude verzendpad; het live pad (compose/send) loopt eromheen (reliek-achtig, samenvoegen met bevinding 7).

---

## Audit 7 — prod-logs (beperkte horizon, eerlijk vermeld)

- **Horizon: slechts ~9 uur.** `docker logs` bestaat alleen voor de huidige container; elke deploy (rebuild → recreate) gooit oude logs weg. Er is geen logbestand-persistentie. **Aanbeveling S201: logging-driver met rotatie/persistentie of een simpele file-sink**, anders is elke toekomstige log-audit blind. Ernst: 🟡 proces.
- In die 9 uur: **0 errors**; 1 uniek warning-patroon: 91× "Email … has empty body after extraction — skipping" (AI-sweep slaat lege mails over — verwacht gedrag, wel volume-check waard).
- Caddy (48u): 29× **502**, geclusterd rond deploy-momenten van 10–12 juli (S199-werk). Eén gebruikerszichtbaar slachtoffer: `POST /api/auth/login` → 502 op 11 juli 14:35. Deploys hebben dus een korte downtime-window zonder health-gate. Ernst: 🟡. Plus 2 scanner-probes (`GET /.git/config` — geblokkeerd).

## Audit 8 — de dag van Lisanne (doorgeklikt op prod)

Read-only doorlopen met netwerk-tab + console: dashboard, nieuw-dossier-wizard (3 stappen), dossier IN100019 (alle 11 tabs), incasso-werkstroom, follow-up (14 aanbevelingen), correspondentie (incl. ongesorteerd), agenda, bankimport, rapportages, zaken-lijst + bulk-selectiebalk (Status wijzigen/Exporteren/Verwijderen aanwezig), instellingen (12 tabs).
**Resultaat: 0 console-errors, 0 4xx/5xx** over alle bezochte schermen. De eerder genoemde bevindingen (1169-widget, nep-tabs, negatieve bedragen, lege secties) zijn de enige afwijkingen die een doorklikkende gebruiker tegenkomt.
**Niet uitgevoerd (read-only-regel):** daadwerkelijk submitten van zaak-aanmaak, betaling boeken, brief genereren, mail versturen, bulk toepassen. Die write-flows zijn tot aan het submit-punt gecontroleerd (formulieren/dialogen renderen, endpoints bestaan volgens audit 1); S199 testte bulk-status al live omkeerbaar.
**Datahygiëne-observatie:** S186-testmails ("Luxis proefmail 2", "Luxis diagnose SELF") en de ontkoppelde 2026-00001-testmail staan zichtbaar in de maillijst.

---

## Samenvatting voor de fix-sessie S203 (fix-volgorde) — STATUS na S203

Legenda: ✅ = gebouwd, getest en LIVE op prod (S203, 12 juli) · ⬜ = open.

| # | Bevinding | Ernst | Fix | Status |
|---|---|---|---|---|
| 13 | Tijdlijn-crash `duration_seconds` | 🔴 latent, 1 regel | XS | ✅ (+`entry_date` sibling-bug) |
| 4 | Hernoemen-knop 405 + geen foutmelding | 🔴 | S | ✅ PATCH-route + onError |
| 3 | AI-draft stil €0-fallback | 🔴 | S | ✅ markeert draft + reviewtaak |
| 6 | "1169 toegevoegd deze maand" | 🟠 zichtbaar elke dag | S | ✅ live 1169→1 |
| 9 | Batch-fouten in groene toast | 🟠 | S | ✅ waarschuwing + redenen |
| 1 | Mailsync-gezondheid onzichtbaar | 🔴 | M | ✅ last_sync_error + banner |
| 2 | Scheduler/verjaring dead-man-switch | 🔴 | M | ✅ heartbeat + dashboard-alarm |
| 5 | 14-dagenbrief-check aansluiten | 🟠 juridisch | M | ✅ echt spoor + batch-gate (blok-vs-warn = Lisanne) |
| 8 | Intake seedt geen startstap/historie | 🟠 | S/M | ✅ going-forward (10 bestaande = aparte data-actie) |
| 7 | Document-audittrail (generated_documents) | 🟠 | M | ⬜ niet in S203-takenlijst |
| 10,14 | Cijfer-definities (ratio, openstaand, negatief) | 🟠 | S | ✅ ratio 49,1%→5,3%, "teveel betaald", herlabeld |
| 11,12 | Nep-tabs Meldingen/Weergave weg | 🟠 | S | ✅ verwijderd |
| 15 | Afgesloten-dossier-met-regeling uitleggen | 🟡 | S | ⬜ niet in S203-rondes |
| 16,17 | Sloopronde 35 routes + Gmail-knop + logout aansluiten | 🟡 | M | ◑ Gmail-knop + logout + dode hook ✅; 35-route-sloop ⬜ (eigen verificatie) |
| — | Log-persistentie op VPS | 🟡 proces | S | ⬜ |
| 18 | Derdengelden-werkwijze | vraag aan Lisanne | — | — gesprek |

**S203-uitvoering (12 juli, Opus):** 11 van 12 taken LIVE in 4 deploys, elke fix rood→groen→commit
→push→deploy, migraties s203/s203b op prod. Openstaand voor een vervolgsessie: 35-route backend-sloop
(per-route verificatie), #7 document-audittrail, #15 regeling-badge, log-persistentie VPS. Juridische
beslissing #5 (harde blokkade vs. waarschuwing) ligt bij Lisanne.

**Niet geverifieerd deze sessie:** exacte werking van alle 12 scheduler-jobs behalve de 2 gelezen (claim subagent); de 141-mutations-scan (steekproef klopte); Exact Online end-to-end (geen connectie om mee te testen); of de write-flows na het submit-punt correct afronden (read-only-regel).
