# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 10 juli 2026 (S193, Opus) — bouwblok 1 GEBOUWD + uitgerold (backend+frontend, geen migraties) + Codex-review (Sol Ultra) op beide porties tot APPROVED. Details: S193-entry.
**Laatste feature/fix:** bouwblok 1 live: B1 verstuurpad (e-mailroute + nooit valse "Uitgevoerd"), B13 vast kanaal incasso@ + preview vóór verzenden, B2+A1 verjaring zichtbaar (monitor/badge/taken), A2 dashboardfilter. Mailslot blijft aan (`OUTBOUND_MAIL_LOCK=true`, eraf ~13 juli).
**Openstaand:** ⚠️ MAILSLOT AAN (eraf ~13 juli); visuele doorklik prod nog te doen; ⚠️ check vóór go-live of `Tenant.email` in prod = incasso@ (anders valt afzender terug op klikker); ⚠️ sleutels in `.codex/config.toml` nog niet afgeschermd (wacht op akkoord); idempotency dubbel-verzenden bij rollback-na-send (bekende grens, mailslot dekt); C2-gegevens (stichting-IBAN + BTW) van Arsalan; heropeningsbatch; terugstort IN100334.
**Volgende sessie:** S194 — bouwblok 2 zodra C2 binnen is (bankimport-proef C1 + termijn-vooruitblik B4/A8 + 3 proefzaken B11), anders bouwblok 3. Prompt: `docs/sessions/PROMPT-S194.md`.

> 📦 **Archief:** alles ouder dan de laatste 10 sessies staat in `docs/archief/SESSION-ARCHIVE.md` (verplaatst, nooit verwijderd).

## Sessie 193 (10 juli 2026, Opus + Codex-review — bouwblok 1 gebouwd + uitgerold)

### Samenvatting
Bouwblok 1 (`PROMPT-S193-bouwblok1.md`) volledig gebouwd, getest, door Codex (Sol Ultra,
alleen-lezen) gereviewd tot **APPROVED** op beide porties, en uitgerold naar prod. Mailslot
bleef aan — niets echt verstuurd; alles bewezen via tests + preview.

**De 4 werkorders (allemaal live):**
- **B1 — verstuurpad sommaties + geen valse "Uitgevoerd".** Follow-up "Uitvoeren" én de
  incasso-batch riepen `render_docx` als eerste aan met e-mailsjabloonsleutels
  (`sommatie_drukte`/`faillissement_dreigbrief`) → `NotFoundError` vóór de mailstap; follow-up
  ving de fout en zette 'm tóch op "Uitgevoerd" (niets verstuurd, wél "klaar"). Nu: beide paden
  proberen eerst `render_incasso_email` (brief = e-mailtekst, geen bijlage), DOCX-route alleen
  voor echte briefsjablonen. `execute_recommendation` werpt een fout op bij mislukte/onmogelijke
  verzending → nooit meer vals "Uitgevoerd". E-mailroute archiveert in `content_html`.
- **B13 — vast kanaal incasso@ + preview.** `get_tenant_send_account` (adres = `Tenant.email`,
  hoofdletterongevoelig, nieuwste koppeling eerst) + opt-in vlag `send_as_tenant_account` op de
  4 pijplijn-verzendingen (facturen/handmatig ongewijzigd). `GET /api/followup/{id}/preview` +
  `SendPreviewDialog`: geen één-klik-verzending meer, eerst afzender/ontvanger/onderwerp/tekst.
- **B2+A1 — verjaring zichtbaar.** Monitor filterde op `date_closed` (dat komt uit BaseNet-import,
  niet uit de app → heropende zaken vielen weg); nu op terminale status (`WorkflowStatus.is_terminal`
  per tenant + betaald/afgesloten vangnet). Badge rekent op `verjaring_date` (server-berekend,
  `compute_verjaring_date`, klemt 29 feb → 28 feb net als de monitor). Eigenaarloze tenant-taken
  komen mee in Mijn Taken (`list_tasks include_unassigned`) → verjaring-alarmen zichtbaar.
- **A2 — dashboardblok "Nieuwe Dossiers":** filter `pending` → `pending_review`.

**Codex-review (drie-bedrijven-model, GPT-5.6 Sol Ultra, alleen-lezen):**
- Portie 1 (verstuurpad/afzender/preview): 3 rondes. Codex vond o.a. 2 maskering-zij-ingangen
  (dossier/stap-sjabloon weg → stil "Uitgevoerd"), batch die bij mislukte verzending tóch
  doorschoof, `html_to_pdf` dat `file://` toestond (lokale-bestand-lek via WeasyPrint), escalatie-knop
  die ik permanent blokkeerde, preview-XSS, Word-context die renteoverzicht oversloeg, tenant-scoping.
  Alle verwerkt; ronde 2 ving mijn te-zwakke XSS-fix (verkeerde sanitizer); ronde 3 APPROVED.
- Portie 2 (verjaring): 2 rondes. Badge-datum week 1 dag af rond 29 feb; oninbaar/schikking werden
  niet als eindstatus herkend. Beide gefixt → APPROVED.
- Zelf-review vooraf vond al 2 punten (HTML-doc-preview brak; misleidende afzender in preview).

### Gewijzigde bestanden
- Backend: `ai_agent/followup_service.py` (+`_router`/`_schemas`), `incasso/service.py`,
  `email/oauth_service.py` + `send_service.py`, `documents/pdf_service.py` + `router.py`,
  `documents/docx_service.py`, `workflow/service.py`, `dashboard/router.py`, `cases/service.py`
  + `router.py` + `schemas.py`. Tests: `test_followup.py`, `test_incasso_pipeline.py`,
  `test_workflow.py`, `test_tenant_send_account.py` (nieuw), `test_documents.py`.
- Frontend: `followup/page.tsx` (preview-dialog), `taken/page.tsx`, `zaken/[id]/.../DossierHeader.tsx`,
  `hooks/use-followup.ts` + `use-cases.ts`.
- 8 commits (`d6f0037`..`569db64`), uitgerold (backend+frontend, geen migraties). VPS HEAD=569db64,
  container draait vers image, healthy.

### Bekende issues
- ⚠️ **Visuele doorklik prod nog niet gedaan** (preview-dialog + verjaring-badge live bekijken).
- ⚠️ **`Tenant.email` moet in prod incasso@ zijn** — anders vindt `get_tenant_send_account` geen
  account en valt de afzender terug op de klikkende gebruiker (geen regressie, wél doel gemist).
  Checken/zetten in Instellingen vóór het mailslot eraf gaat.
- Idempotency: e-mail verstuurd → DB-commit faalt → rollback → retry kan dubbel sturen. Bekende
  grens (1-gebruiker-kantoor, mailslot dicht); outbox bewust niet gebouwd.
- `.codex/config.toml` bevat leesbare sleutels, nog niet in `.gitignore` (wacht op akkoord Arsalan).

### Volgende sessie
- **Visuele doorklik prod** van de nieuwe schermen (kan direct, mailslot dekt).
- **Bouwblok 2** zodra C2-gegevens binnen zijn: C2 invullen → C1 bankimport-proef (samen) →
  B4/A8 termijn-vooruitblik → B11 stappen 3 proefzaken. Anders **bouwblok 3**.
- Prompt: `docs/sessions/PROMPT-S194.md`.

## Sessie 192 (10 juli 2026, Opus — Codex-werkmodel opgezet, geen Luxis-code)

### Samenvatting
Taak 0 uit `PROMPT-S193-bouwblok1.md` uitgevoerd: Codex (GPT-5.6) naast Claude werkend
gekregen. **Kernbevinding:** Codex was al geïnstalleerd (via de OpenAI desktop-app, niet
npm) en ingelogd op Arsalans ChatGPT-account (`arsalanir@hotmail.com`, model `gpt-5.6-sol`,
effort `ultra`). Dus niet opnieuw installeren — alleen bruikbaar maken + werkafspraak vast.

**Besluit Arsalan (herzien t.o.v. S191-advies):** het volledige drie-bedrijven-model van
grill-me-codex AAN, **inclusief bedrijf 3 (Codex bouwt)**. Zijn redenering, die klopt: er
is nog steeds één bouwer per klus, Claude doet kop (plan) + staart (diff-review, bewijstest,
commit), en GPT-5.6 is sterk + goedkoper in het typwerk (valt onder het abo). Mijn eerdere
"bedrijf 3 UIT"-voorbehoud bleek al als harde regel in de skill te zitten (schone tree,
verplichte diff-lezing, bewijstest door Claude, jij keurt goed vóór commit) → overgenomen.

### Gewijzigde/aangemaakte bestanden
- `docs/research/advies-codex-samenwerking.md` — sectie "Werkafspraak vastgesteld 10 juli":
  geïnstalleerd-status, gekozen model (bedrijf 3 AAN), rolverdeling Fable=brein/Codex=bouwer,
  vangrails, veiligheidsvalkuil `codex exec resume` kent geen `-s`.
- **Globaal (buiten de repo):** 4 skills in `~/.claude/skills/` (`/grill-me-codex`,
  `/grill-with-docs-codex`, `/codex-review`, `/codex-build`); `codex`-shims in
  `~/.local/bin/` (`codex` voor Git Bash, `codex.cmd` voor PowerShell) die de nieuwste
  Codex-versiemap pakken (overleeft app-updates). Beide getest — `codex` werkt als commando.
- Geheugen bijgewerkt: `project_codex_openai.md` + `MEMORY.md`.

### Bekende issues
- ⚠️ `.codex/config.toml` in de repo bevat leesbare API-sleutels (OpenAI/Milvus/Stitch/
  Tavily); untracked maar NIET in `.gitignore`. Afschermen wacht op Arsalans "ja". Nooit
  laten meecommitten.
- Nog géén echte `/codex-build`-proefrit gedaan — alleen een read-only plumbing-test
  (`PLUMBING_OK`) geslaagd. Eerste echte test = bouwblok 1 (S193).

### Volgende sessie
- **S193 bouwblok 1 op Opus** (`PROMPT-S193-bouwblok1.md`), taak 0 is nu klaar. Gebruik het
  als eerste `/codex-review` → `/codex-build`-proefrit. Vraag Arsalan eerst of de sleutels
  afgeschermd mogen worden (`.codex/` in `.gitignore`).

## Sessie 191 (9 juli 2026, Fable — Codex-advies + kijk-sessie D-C: financieel + systeem, 100% read-only)

### Samenvatting
Twee taken uit `docs/sessions/PROMPT-DC-doorlichting.md`:

**Taak 0 — Codex/OpenAI-samenwerkingsadvies** (webonderzoek, niet uit het hoofd):
`docs/research/advies-codex-samenwerking.md`. Kern: Codex CLI draait native op Windows
onder het bestaande OpenAI-abonnement (€0 extra binnen limieten); het "grill-me-codex"-
patroon (Chase AI, MIT, ±500 sterren) bestaat en is volwassen. Voorstel: Claude blijft
enige kapitein (bouwt/commit/deployt), GPT-5.6 via Codex wordt alleen-lezen tegenlezer
op 2 vaste momenten — rapporten grillen (kijkfase) en Opus-diffs reviewen vóór deploy
(bouwfase). Akte 3 (Codex bouwt) bewust UIT. Maandag ±30 min installeren + proefrit.

**Kijk-sessie D-C (laatste van 3)** — Bankimport, Derdengelden, Uren, Facturen,
Rapportages, Instellingen. Rapport: **`docs/research/audit-DC-financieel-systeem.md`**
(9 werkorder-kandidaten C1-C9 + totaal-beslislijst D-A+D-B+D-C in §9, 34 punten in
5 blokken). Gemeten in prod-DB + code + doorgeklikt (0 consolefouten).

### Belangrijkste vondsten D-C
- **KERN — financiële laag is af maar nooit gebruikt, géén relieken**: bankimport,
  derdengelden, uren, facturen, Exact alle exact 0 rijen ooit; onderling wél netjes
  verbonden (uren→factuurregels, derdengelden→verrekening, bankimport→derdengelden→
  art. 6:44-betaling) en test-gedekt. Verwachting "meeste eilanden" klopte niet —
  het zijn stilstaande machines, geen kapotte.
- **Bankimport = het regelingen-betaalzicht en is al af**: Rabobank-CSV upload →
  automatch → beoordelen → uitvoeren (+terugdraai). Backlog-gedachte (a) vergt géén
  bouw, alleen een wekelijks upload-ritueel. Eerst C2!
- **HOOG vóór ingebruikname — derdengelden-IBAN = kantoor-IBAN** (beide
  NL20RABO0388506520 in tenants; UI zegt zelf "apart"). SEPA/NOvA-output zou nu
  verkeerd ogen. BTW-nummer ook leeg.
- **Rapportages leeft maar vertelt scheef**: "Geïnd €0/0,0%" (kijkt alleen naar
  lopende zaken; €311.547,70 aan 255 echte betalingen onzichtbaar) en faseverdeling
  15≠18 (inner join skipt de 3 stap-loze proefzaken IN100040/215/521 die het KPI-blok
  ernaast wél telt).
- Klein: uren-relatiefilter laadt alle 1169 relaties; Workflow-tab toont lege
  status-engine zonder uitleg; beide accounts heten "Lisanne Kesting"; meldingen-kop
  264 vs DB 299 ongelezen (onverklaard); producten-catalogus (30, Exact-grootboek)
  ligt klaar voor een facturatie-besluit.

### Verificatie
Alle dragende beweringen zelf gemeten (SQL op prod / code / klik); geen enkele mutatie
op prod; expliciete "niet geverifieerd"-lijst in rapport §7 (o.a. upload-keten niet
gedraaid, vier-ogen-afdwinging niet getest). Tegenspreker-correctie toegepast: claim
"alle 12 tabs bekeken" teruggebracht naar de 5 echt geklikte.

### S191b — fase-2-beslisgesprek DIRECT gevoerd (zelfde avond, met Arsalan)
Arsalan wilde niet wachten: alle 5 stapels ter plekke doorgenomen. Besluiten integraal
in **`docs/plans/PLAN-fase2-bouwblokken.md`**. Kern: stapel 1 akkoord (= bouwblok 1);
C2-gegevens (stichting-IBAN + BTW) levert Arsalan 10 juli; termijn-vooruitblik alleen
als overzicht (dossierniveau bestaat al); **Uren + Facturatie blijven AAN (keuze
Arsalan)** — C5 + dashboard-netjes naar de veegsessie; rest stapel 3 conform
aanbeveling; stapel 4 en 5 akkoord. Codex-besluit herzien na tegenargument Arsalan:
**bouwproef GPT-5.6 onder Claude-toezicht** op een stapel-4-klus na installatie
(~13 juli) — Claude blijft de enige die commit/deployt. PROMPT-S192 (beslisgesprek)
daarmee overbodig → archief. Ook gevonden: persoonlijke Claude-instellingen pinnen
Fable als startmodel voor élke nieuwe sessie — advies aan Arsalan: default op Opus,
Fable per sessie (melding gedaan, niet zelf aangepast).

### Volgende sessie
S193 = bouwblok 1 op Opus (`docs/sessions/PROMPT-S193-bouwblok1.md`): B1 verstuurpad +
B13 vangrails + B2/A1 verjaring + A2 dashboardfix, alles vóór het mailslot eraf gaat.

## Sessie 190 (9 juli 2026, Fable — kijk-sessie D-B: kern-motor, 100% read-only)

### Samenvatting
Tweede van drie kijk-sessies uit `docs/plans/PLAN-doorlichting-menu.md`: Relaties, Dossiers,
Incasso, Follow-up en Intake doorgelicht op techniek (5 vragen), partner-blik en UX/UI.
Gemeten in prod-DB (exacte tellingen, niet de tabel-schattingen — die bleken bij
managed_templates 2 vs 9 fout) + code gelezen + app doorgeklikt (0 consolefouten).
Volledig rapport: **`docs/research/audit-DB-kernmotor.md`** (13 werkorder-kandidaten B1-B13).

### Belangrijkste vondsten
- **HOOG — sommatie-verstuurpad kapot + fout wordt gemaskeerd**: stap-sjabloonsleutels
  `sommatie_drukte`/`faillissement_dreigbrief` zijn e-mailsjablonen, maar Follow-up-"Uitvoeren"
  en Incasso-batch "Document genereren" proberen er eerst een DOCX mee te renderen — sleutel
  bestaat in geen van beide DOCX-registers → faalt. Follow-up markeert de aanbeveling dan tóch
  "Uitgevoerd" (fout weggestopt in execution_result), er gaat niets de deur uit. Raakt 10 van
  13 openstaande aanbevelingen (Eerste sommatie). Consistent: email_logs=0, generated_documents=0.
  De AI-conceptroute per dossier is de gezonde weg. (Code+data-bewijs; niet live geklikt.)
- **HOOG — status-engine leeg**: workflow_statuses/transities/regels alle 0 (exact geteld) →
  dossierstatus onwijzigbaar via UI, "Volgende stap"-knoppen (hardcoded fallback) op elk
  dossier zouden falen, statusfilter Dossiers-lijst is leeg, date_closed wordt nooit gezet.
- **HOOG — verjaring ook in het dossier onzichtbaar**: VerjaringBadge rekent vanaf date_opened
  (IN100015: badge zou jan 2030 zeggen, echt verjaard okt 2025) en verbergt zich op afgesloten
  zaken; de monitor (juiste basis) skipt zaken mét date_closed → IN100016 (verjaart 23-09-2026,
  €16.020) en IN100064 (jun 2027, €37.002) volledig onzichtbaar.
- **Regelingen buiten beeld**: 13 actieve regelingen (121 termijnen, 0 betaald), 12 op
  afgesloten zaken; eerstvolgende termijnen 9/12/13/15/18 juli; alleen alarm achteraf.
- **Vervuiling**: 17 inactieve pipeline-stappen + dode transities (2 actieve wijzen naar
  inactieve stappen); case_step_history 1 rij; "AI-suggestie"-badge op alle 18 rijen door
  het classificatie-eiland; intake = 7 testaanvragen, 0 echte dossiers ooit.
- **Positief**: Relaties gezond (delete-guard, AV-versies); dossier-detail professioneel,
  rente op de cent (S188b-ijkpunt); slim-leren beoordeeld: 103 goedgekeurd / 28 afgewezen.

### Verificatie
Alle dragende beweringen deze sessie zelf gemeten (SQL op prod / code / klik); schrijfacties
bewust niet uitgevoerd — expliciete "niet geverifieerd"-lijst in het rapport (§7). Geen
enkele mutatie op prod. Sessie-afronding: rapport + PROMPT-DC aangemaakt, plan D-B afgevinkt,
S183-entry naar archief (max-10-regel).

### Volgende sessie
Kijk-sessie D-C (Bankimport, Derdengelden, Uren, Facturen, Rapportages, Instellingen) —
kant-en-klare prompt `docs/sessions/PROMPT-DC-doorlichting.md`, Fable. Sluit af met de
totale beslislijst D-A+D-B+D-C voor fase 2 met Arsalan.

## Sessie 189 (9 juli 2026, Opus+Fable — CI-fix + start menu-doorlichting D-A)

### Samenvatting
Twee dingen: (1) de al sessies rode CI-test gefixt zodat de auto-deploy niet meer stil
overslaat, en (2) op verzoek Arsalan een complete menu-doorlichting van heel Luxis
opgezet — élk menu-onderdeel kritisch langs op techniek + productwaarde + UX/UI — en
de eerste kijk-sessie (D-A) uitgevoerd.

### Taak 1 — CI-rood `test_role_survives_commit_if_role_exists` GEFIXT (commit `375b2f0`)
Oorzaak (bewezen via code + reproductie): `set_tenant_context` cachet rol-beschikbaarheid
één keer per proces. In een volle suite-run zet een eerdere ingelogd-verzoek-test die
cache op False (`luxis_app` bestaat dan nog niet); `test_rls_isolation` maakt de rol pas
halverwege aan. De directe pg_roles-check in de test ziet de rol dán wel → skip niet →
maar de stale cache blokkeert de SET ROLE → `current_user` bleef 'luxis' → rood. In CI's
verse postgres exact dit patroon; lokaal groen omdat luxis_app cluster-breed al bestaat.
**Rood→groen bewezen** op een verse wegwerp-postgres zonder luxis_app (1 failed→44 passed).
Fix chirurgisch in de test (cache resetten + herstellen, nul impact op andere tests);
productiecode ongemoeid (daar bestaat de rol altijd vóór het eerste verzoek). **Volledige
CI groen** na push (alle 8 checks). Openstaand-punt "CI-rood test_role" is hiermee weg.

### Taak 2 — Menu-doorlichting opgezet + D-A uitgevoerd (100% read-only)
Plan: `docs/plans/PLAN-doorlichting-menu.md`. Kernkeuze: Fable is er t/m 12 juli → ALLE
kijkwerk eerst (3 sessies D-A/D-B/D-C), bouwen daarna met Opus (geen deadline). Per
onderdeel 3 lagen: techniek (5 vragen), partner-blik (advocatuur/SaaS-specialist),
UX/UI. Mail valt buiten scope (S185-188 klaar).

**D-A Werkschil (Dashboard, Mijn Taken, Agenda, Documenten) — rapport
`docs/research/audit-DA-werkschil.md`.** Gemeten in prod-DB + code + doorgeklikt.
Belangrijkste vondsten:
- **HOOG:** verjaringsalarm structureel onzichtbaar — monitor vond 2 verjaarde zaken
  (IN100015/IN100127, beide in heropeningslijst, samen €14.286) maar maakt taken zónder
  eigenaar aan, terwijl "Mijn Taken" alleen taken mét eigenaar toont. IN100016 verjaart
  23-09-2026. (Let op: monitor kent stuitingen niet — juridisch oordeel Lisanne.)
- **BUG:** "Nieuwe Dossiers"-blok filtert `pending`, prod = `pending_review` → altijd 0.
- **BUG/tegenstrijdig:** Mijn-Taken-badge 19 vs "Alles gedaan!" (dubbeltelling tellers).
- **Eiland:** 394 e-mail-classificaties allemaal onverwerkt; 264 ongelezen
  "classificatie klaar"-meldingen verzuipen de bel.
- **Product:** dashboard ~40% dood (uren/facturen 0 in 4+ mnd); agenda 0 afspraken ooit
  + Lisanne kan niet syncen; "Documenten" toont alleen sjablonen (2619 echte stukken
  nergens centraal vindbaar).
- **Opruimen (met akkoord):** testdossier 2026-00001 telt mee in werkvoorraad (18 i.p.v. 17).
12 werkorder-kandidaten (A1-A12) in het rapport, voor de fase-2-beslislijst.

### Verificatie
CI-fix: rood→groen op verse wegwerp-postgres (weggegooid na afloop), volledige CI-run
groen (`gh run` 8/8). Doorlichting: alle beweringen gemeten deze sessie (SQL op prod,
code gelezen, app doorgeklikt als seidony@); geen enkele mutatie op prod; "niet
geverifieerd"-punten expliciet benoemd in het rapport (o.a. genereer-flow, verjaring
juridisch).

### Volgende sessie
Kijk-sessie D-B (Relaties/Dossiers/Incasso/Follow-up/Intake) — kant-en-klare prompt
`docs/sessions/PROMPT-DB-doorlichting.md`, start op Fable. Daarna D-C (Financieel +
Systeem). Pas ná alle 3 de kijk-sessies: fase-2-beslislijst met Arsalan → Opus-bouwblokken.
Heropening werkvoorraad blijft parallel klaarstaan.

## Sessie 188c (9 juli 2026, Opus-bouw + Fable-review-fixes — mailwerk-review + 2 fixes)

### Samenvatting
Eerst Fable-review van het mailwerk S185-187 (read-only, alleen broncode/git/tests — bewust
geen echte mails of mailschermen om het model-filter niet te triggeren). Oordeel: goed en veilig
gebouwd; 26/26 endpoints geauth, XSS twee keer afgedekt (inkomende weergave + geciteerd origineel
bij reply/forward), koppeling voorzichtig. Twee ECHTE gebreken gevonden + op Opus gefixt:

**Fix 1 — aanvraag-detectie liep vast (bewezen op prod).** `detect_intake_emails` pakte de 10
oudste onverwerkte mails maar markeerde niet-matches nooit → venster slibde dicht met oude
systeem-/eigen mail (32 wachtend, 10 oudste kansloos). Root-cause-fix: alleen mail van een bekende
opdrachtgever (adres of niet-ambigu domein) is nog kandidaat; opdrachtgever-kaart wordt vóór de
mailquery gebouwd en mee-gefilterd, dus elke kandidaat matcht en verlaat de wachtrij. Geen migratie.

**Fix 2 — "Negeren" niet heilig.** `_rematch_unlinked_emails` filterde niet op `is_dismissed` →
een genegeerde mail kon bij een latere sync alsnog gekoppeld worden (0 gevallen op prod, sluimerend).
Eén filterregel toegevoegd.

### Verificatie
3 regressietests toegevoegd (detectie-venster slibt niet dicht; her-koppeling respecteert Negeren
+ koppelt niet-genegeerde wél). **52 tests groen** in test_intake.py + test_email_sync.py, gedraaid
in een geïsoleerde wegwerp-postgres op de VPS (bind-mount van de wijzigingen; prod-data niet geraakt,
wegwerp-db daarna verwijderd). Commit `edf88da`, gepusht. Lint niet los gedraaid (uvx ontbrak in de
wegwerp-container) → teststraat pikt ruff op.

### S188d — de 6 kleinere verbeterpunten alsnog gebouwd (op verzoek Arsalan, commit `2806a9e`)
Allemaal op Opus, met tests; frontend tsc + ruff schoon; 91 mail/intake-tests groen (geïsoleerde
wegwerp-postgres, prod-data niet geraakt).
1. **Echte tekstversie** van uitgaande mail, afgeleid uit de HTML (`_html_to_text`) i.p.v. de
   placeholder-zin — beter voor tekst-only clients + spamscore.
2. **Doorsturen met bijlagen**: `forward_from_email_id` → achterkant laadt de bijlagen van de
   oorspronkelijke mail van schijf (`_load_forwarded_attachments`); voor- en achterkant bedraad.
3. **Server-side adres-validatie** op `/compose/send` (to + cc, lege to afgewezen).
4. **IMAP-ontsmetting**: Message-ID in de HEADER-zoekopdracht wordt geëscaped (`_imap_quote`).
5. **Afzendernaam**: "Kesting Legal <incasso@...>" via `from_name` (kantoornaam) op beide verzendpaden.
6. **Verzonden-map-namen** in één constante (`SENT_FOLDER_CANDIDATES`), consistent gebruikt.

### S188e — Fable-review van het S188c/d-werk: GO met 1 gevonden+gefixte restfout
Volledige diff-review op Fable (beide commits regel voor regel + randgevallen tegen prod-metadata
en de modellen gehouden). Uitkomsten:
- **Detectie-fix klopt**: databasefilter en nazorg-lus consistent (ambigue domeinen, hoofdletters,
  exacte-adres-voorrang); NULL-valkuil in de NOT-IN-subquery kán niet (kolom verplicht, prod 0 NULLs).
- **Alle 3 providers** accepteren `from_name` (geen kapotte aanroep); huisstijl heeft geen
  `<style>`-blok dus de tekstversie blijft schoon; prefill wordt op beide pagina's gewist.
- **Restfout gevonden + direct gefixt** (commit `8b658c7`): `_imap_quote` ontsmette `"` en `\`
  maar niet CR/LF — een gevouwen Message-ID-header kon in theorie een eigen IMAP-commando
  injecteren bij het bijlage-ophalen. CR/LF/NUL → spatie + injectie-regressietest (groen).
- **Deploy S188c/d/e GESLAAGD + geverifieerd**: nieuwe code aantoonbaar in de draaiende backend (grep in container), VPS op 8b658c7, alle containers healthy, site 200. (Container-rename-botsing tijdens up was onschuldig; eindtoestand correct.)

### Openstaand
- CI-rood blijft: `test_role_survives_commit_if_role_exists` (omgevingsgevoelig, S184-security,
  géén mailwerk) → CI-deploy skipt; uitrol gaat via SSH. Verdient losse fix of skip-markering.

## Sessie 188b (9 juli 2026, Fable — heropening LegalWork LIVE, eerste batch)

### Samenvatting
Eerste heropeningsbatch uitgevoerd op prod volgens `docs/plans/PLAN-heropening-werkvoorraad.md`,
met akkoord Arsalan (rente-besluit + go, deze sessie). **14 LegalWork-zaken heropend** in één
atomische transactie met rijenaantal-sloten (afwijking = automatische rollback):
- 9 × Eerste sommatie (IN100592/598/599/602/603/604/605/606/607)
- 3 × Voorstel dagvaarding (IN100410/504/527)
- 2 × Verweer beantwoorden + verweer-vinkje (IN100458/483)
- Alle 14: status nieuw, toegewezen aan Lisanne, `date_closed` leeg. IN100547 (voldaan) bleef dicht.

**Rente-besluit Arsalan (staand beleid):** alle b2b-zaken van de 7 holding-opdrachtgevers
(Invorderingsbedrijf-groep) bij heropening op contractuele AV-rente 2%/mnd enkelvoudig;
B2C blijft wettelijk. Geen vraag meer per groep. Voor nieuwe zaken dekt de AV-laag
(terms_interest, S177) dit al automatisch.

**Rente-valkuil gevonden + gefixt (tegenspreker-check on de cijfers):** dossier-update alleen
(`interest_type=contractual, rate=2.00`) liet de rente **2%/JAAR** rekenen — IN100598 toonde
€50,02 (= exact 31.477,36 × 2% × 29/365). De periode-eenheid zit op de **vorderingen**:
`claims.rate_basis` stond op `yearly` (proefzaken-ijkpunt: `monthly`). Fix: 43 claims van de
14 zaken → `monthly` (guarded, andere zaken ongemoeid: 1511 yearly elders intact).
Ná fix: €600,23 + €181,20 (2%/mnd pro-rata), derde factuur terecht €0 (verzuim 01-08).
Draaiboek bijgewerkt met stap 4b zodat volgende batches dit meenemen.

### Verificatie (alle acceptatiecriteria van het plan)
1. 14 zaken status=nieuw met juiste stap + rente-config — query groen (tabel in transcript).
2. 0 zonder toewijzing, 0 met date_closed — groen. 3. Vangnet BaseNet-Gereed/Geannuleerd: 0 rijen.
4. email_logs vóór==ná==0 (niets gemaild); auto_drafts false. 5. IN100547 nog afgesloten.
6. UI-rooktest: werkstroom 4→18 dossiers, bedragen op de cent gelijk aan recept (o.a. 44.609,73 /
   12.100,00 / 18.934,11), deadline-kleuren zichtbaar; 3 dossiers geopend (598 sommatie /
   458 verweer / 410 dagvaarding): juiste stap, "Contractuele rente", renteoverzicht klopt, geen crash.
Bekende cosmetische beperking (gepland): SQL-heropening schrijft geen case_step_history-regel.

### Volgende sessie
Volgende heropeningsbatch (per opdrachtgever, expliciet akkoord per groep blijft de afspraak) mét
stap 4b; de 11 gestopte-regeling-zaken en de regeling-groep (incl. IN100019) apart. Terugstort-vraag
IN100334 (±€215) nog open bij Lisanne.

## Sessie 188 (9 juli 2026, Opus — mailverificatie live, geen code)

### Samenvatting
De 2 openstaande verificatiegaten uit S187 live dichtgeklikt in de ingelogde prod-app
(seidony@kestinglegal.nl). Geen code gewijzigd; niets verstuurd.

**Gat 1 — Ongesorteerd-tab (gedeeld `EmailDetailPanel`): volledig groen.**
- Bulk-selectie: "Selecteer alles" → "67 geselecteerd" + actiebalk (Koppel aan dossier /
  Negeren / Deselecteer); Deselecteer wist de selectie. Per-rij-vinkjes werken.
- Leesvenster op een mail mét bijlage: afzender/ontvanger/datum, bijlage getoond
  (`LISANNE-A4-heropening… 2 KB`), mailtekst, knoppen aanwezig.
- Beantwoorden opent: "Aan" voorgevuld met afzender, onderwerp "Re: …", origineel als citaat.
- Doorsturen opent: onderwerp "Fwd: …", leeg "Aan", doorgestuurd-blok, Versturen terecht
  uitgeschakeld zonder ontvanger. Beide geannuleerd — niets verstuurd.

**Gat 2 — "Maak dossier van deze mail" (nieuwe knop/endpoint): groen.**
- Klik op de knop → intake-aanvraag aangemaakt, app sprong naar "Nieuwe aanvragen" (2→3).
- AI-uittreksel draaide (model claude-haiku-4-5, zekerheid getoond); op een testmail zonder
  incasso-inhoud kwam het uittreksel terecht leeg (<UNKNOWN>, 10%) — correct gedrag.
- "Details bewerken" navigeert naar `/intake/[id]` (debiteur/factuur/AI-analyse/bron-mail +
  Afwijzen/Goedkeuren). Testaanvraag opgeruimd via Afwijzen (met reden) → teller 3→2.

### Niet uitgevoerd (bewust, met reden)
De laatste deelstap "Maak dossier/Goedkeuren → PERMANENT dossier" niet geklikt: de enige
beschikbare ongekoppelde mails zijn test/self-mails waaruit de AI (terecht) niets haalt, dus
goedkeuren zou een leeg junk-dossier op prod zetten waarvan het opruimen (Case verwijderen)
een echt destructieve prod-actie is. Die deelstap is bovendien bestáánde intake-code (al in
gebruik); het NIEUWE werk uit S187 (mail→aanvraag + domein-herkenning) is hiermee geverifieerd.
Een echte eind-tot-eind dossier-aanmaak kan zodra er een echte nieuwe opdrachtgever-aanvraag
binnenkomt (of op expliciet verzoek een wegwerp-dossier + opruiming).

### Volgende sessie
Heropening werkvoorraad — wacht op input Lisanne/Arsalan. Draaiboek
`docs/plans/PLAN-heropening-werkvoorraad.md` + recept `docs/sessions/S181-werkvoorraad-recept.csv`.

## Tussensessie (9 juli 2026, Fable — documentatie-opruiming, geen code)

### Samenvatting
Levende docs opgeruimd — alles verplaatst naar `docs/archief/`, niets verwijderd (commit `04b6248`):
- **SESSION-NOTES.md 540KB→42KB**: max 10 entries (regel), 168 oudere entries verbatim naar
  `docs/archief/SESSION-ARCHIVE.md`; kop teruggebracht van 15 opgestapelde regels naar 4.
- **LUXIS-ROADMAP.md 180KB→26KB**: 8 afgeronde secties (verbind-sprint, systeem-audit-backlog,
  GTM, audits 110/124, bug-log, volgorde van werken, LF-sprint) + 15 "Vorige:"-regels naar
  `docs/archief/ROADMAP-ARCHIEF.md`. Nu precies één 🎯 prioriteit-sectie. Enig open punt
  (AI Factuur Parsing Validatie, LF-10) overgenomen in Backlog.
- **Mappen**: oude prompts → `docs/archief/prompts/`, mei-audits → `docs/archief/audits/`,
  `docs/audit` hernoemd naar `docs/audits` (verwijzingen bijgewerkt), backups → `docs/archief/sessions/`.
- **Dood duplicaat weg**: `.github/skills/impeccable` (330KB, door niets gebruikt; `.claude`-versie is de echte).
- **Verankering**: archief-regels in `/sessie-einde` + CLAUDE.md; waakhond-hook bij sessiestart
  waarschuwt bij SESSION-NOTES >150KB of roadmap >60KB; luxis-researcher-leeslijst bijgewerkt.
Aanleiding: doorlichting op verzoek Arsalan, getoetst aan officiële Claude Code-documentatie
("pruning is het primaire onderhoud"; instructiebestanden waren al op maat: 116/38/39 regels).

### Verificatie
Tellingen sluitend: 178+25=203 sessie-koppen vóór = 10 live + 193 archief ná; roadmap 17 secties
= 9 behouden + 8 archief (+1 nieuwe prioriteit-sectie). Git toont elke verplaatsing als rename (100%).
settings.json valide JSON; waakhond-logica getest (stil bij huidige maten, vuurt bij lage drempel).

### Volgende sessie
Ongewijzigd S188: eerst de 2 mailverificatie-gaten, dan heropening werkvoorraad (`docs/sessions/PROMPT-S188.md`).

## Sessie 187 (8 juli, Opus-bouw + Fable-review — mailfunctie afmaken, blok A+B)

### Samenvatting
Mailmodule afgemaakt volgens `docs/plans/PLAN-mail-afmaken.md`. Onderzoek/review op Fable,
bouw op Opus (mailwerk triggert het Fable-veiligheidsfilter het hardst → wisselt vaak naar
Opus; dat is een filter aan Anthropic-kant, niet in onze code — zie memory `feedback_model_choice`).
Alles in de ingelogde prod-app doorgeklikt (m.u.v. het openstaande gat hieronder).

### Taak 0 — Fable-review S186-mailwerk (vooraf), 2 fixes LIVE (commit `13f18df`)
- **Reply-threading**: `References` begon bij de directe voorganger i.p.v. de draad-wortel →
  antwoord middenin een lange keten kreeg (na sync) een andere `thread_id` → auto-koppeling
  kon terugvallen naar Ongesorteerd. Nu stuurt de voorkant `references_root` mee; IMAP-provider
  bouwt `References = "root parent"`. Outlook-signatuur meegetrokken (negeert het veld).
- **Kale-mail-ontsnapping**: AI-concept met mislukte huisstijl-wrap (`body_html` leeg) ging tóch
  als `already_branded` de deur uit → kaal. Nu alleen overslaan bij écht opgemaakte HTML.

### Blok A — mailbasis (commit `7b91704`, + fixes `1fce49c`/`7decaf2`)
- **Leesvenster in "Alle e-mails"**: inline detail-JSX van Ongesorteerd geëxtraheerd naar één
  gedeeld `EmailDetailPanel` (lezen, bijlagen, beantwoorden/doorsturen, koppelen). Gekoppelde
  mail toont "Gekoppeld dossier" + Open-dossier; niet-gekoppelde: koppelen + Negeren + Maak-dossier.
- **"Meer laden"**: `useAllEmails` → `useInfiniteQuery` (offset, 200/pagina). Teller = totaal.
- **Gelezen-status**: IMAP-fetch vraagt nu `(FLAGS RFC822)`; `_seen_flag_present` leest `\Seen` uit
  de descriptor; `is_read` volgt de vlag (was hard True). Her-sync werkt bestaande mail bij (alleen
  bij verschil, geen rij-load). Ongelezen = blauwe stip + vet. Live: stippen verschenen na sync.
- **Sjabloonkiezer** altijd zichtbaar; zonder dossier disabled met uitleg "Kies eerst een dossier".
- **Ophaalvenster** `since_days` 14 → 90.

### Blok B — Nieuwe aanvragen (zelfde commit)
- Tab **"Nieuwe aanvragen"** met teller (pending_review), AI-uittreksel per aanvraag + Maak-dossier/
  Afwijzen (bestaande intake-acties). Detail bewerken linkt naar `/intake/[id]`.
- **Domein-herkenning**: `detect_intake_emails` + `create_intake_from_email` matchen ook op
  bedrijfsdomein van de opdrachtgevers; vrije providers (gmail e.d.) + ambigue domeinen uitgesloten.
- **"Maak dossier van deze mail"**: `POST /api/intake/from-email/{email_id}` (idempotent), knop in
  het leesvenster op niet-gekoppelde mail.

### Bugs onderweg gevonden + gefixt (live geverifieerd)
- **Suggesties gaven 500** (`Contact.display_name` bestaat niet → `Contact.name`). Trof élke mail
  met een suggestie; zichtbaar geworden nu je in "Alle e-mails" ook uitgaande/gekoppelde mail opent.
  Commit `7decaf2` + regressietest; endpoint nu 200.
- **`case_number` ontbrak in mail-detail** → gekoppelde mail toonde "Koppel aan dossier" i.p.v.
  "Gekoppeld dossier". Toegevoegd (relatie is `lazy="selectin"`). Commit `1fce49c`, live bevestigd.

### Verificatie
Backend 121 mail/intake-tests groen, ruff schoon; frontend tsc + `next build` schoon. Browser
(ingelogd, prod): 3 tabs + tellers, leesvenster open/lezen/reply-knoppen, paginering "6450 — 200
getoond", ongelezen-stippen, gekoppeld/niet-gekoppeld-varianten, aanvragen-tab met AI-uittreksel,
sjabloon-uitleg. Sync draaide foutloos met de nieuwe vlag-fetch. `suggest-cases` na fix → 200.

### Openstaand (voor S188)
- ⚠️ **Ongesorteerd-tab** en de **"Maak dossier"-flow met een echt nieuw dossier** niet apart live
  doorgeklikt (delen wel het bewezen `EmailDetailPanel`; risico laag, maar niet 0-bewezen).
- Fable-filter blijft mailwerk naar Opus schuiven — Arsalan gaf feedback via `/feedback`. Knop om
  auto-wissel uit te zetten staat in claude.ai-accountinstellingen (niet betrouwbaar in de terminal).
- Nog steeds open sinds S186: DMARC voor kestinglegal.nl; testspoor "Luxis diagnose SELF" opruimen.

## Sessie 186 (8 juli, Opus + Fable — mailfunctie: versturen als incasso@ + blok 2 + huisstijl)

### Samenvatting
Doel: mailmodule doorlichten (menu + dossierniveau) en versturen áls incasso@ bouwen; daarna
de mailfunctie verder afmaken. Onderzoek=Fable, bouw=Opus, alles live geverifieerd.

**Verzenden als incasso@ (blok 1, commits `4d47fb1`/`4a5896e`/`f5ef4d7`):**
- `ImapProvider.send_message` = echte SMTP via `smtp.basenet.nl:587` (STARTTLS+AUTH, zelfde inlog
  als IMAP-ontvangst; was `NotImplementedError`). Afzender = het account (Lisanne = incasso@).
- **Gemeten: BaseNet bewaart SMTP-verzonden mail NIET in Verzonden** → Luxis doet zelf IMAP APPEND
  naar `INBOX.Sent` na elke send (faalt nooit de verzending). 2 proefmails aangekomen + kopie in
  Verzonden bewezen.
- `imap_smtp_kwargs()` (SMTP-host afgeleid uit IMAP-scope) doorgegeven in `send_service` +
  `compose_router` → incasso-machine, facturen, opvolging én compose-knop versturen nu correct.
- Bijlage-lek `/compose/send` gedicht (vielen stil weg); document-send omgeleid van Gmail-noodroute
  → `send_with_attachment`; dossier-mailtab 50→200 mails.

**Blok 2 (commits `ee41b72`/`8a98315`/`3b26a37`/`9aebb45`):**
- Dood `/api/email/all` HERSTELD (verloren bij shadow-map-opruiming) → "Alle e-mails"-tab toont
  6446 mails. Browser-geverifieerd.
- Zoeken door álle mail server-side (onderwerp/afzender/ontvanger/snippet/body). "faillissement"
  = 2009 treffers, browser-geverifieerd.
- Gesprekketting-fix: thread_id = References-WORTEL (was directe voorganger → keten brak na 1 antwoord).
- Beantwoorden/doorsturen vanuit dossier ÉN Ongesorteerd (`lib/email-reply.ts`), koppelt via
  In-Reply-To/References. Browser-geverifieerd (prefill klopt).

**Huisstijl-opmaak (commit `fd4ea8f`):** afspraak Arsalan = álles vanuit de incasso-mailbox draagt
de sjabloon-opmaak (handtekening+logo+schuldhulpblok+disclaimer); alleen de tekst verschilt.
`ensure_branded_body()` centraal; al-opgemaakte HTML (templates/AI-concept) via `already_branded`
overgeslagen (robuust tegen geciteerd 'Betreft:'). Prod-render 7/7 groen. 346 tests groen.

### Gewijzigde bestanden
- Backend: `email/providers/imap_provider.py`, `email/oauth_service.py`, `email/send_service.py`,
  `email/compose_router.py`, `email/sync_router.py`, `email/sync_service.py`,
  `email/incasso_templates.py`, `documents/router.py`; tests `test_imap_send.py`/`test_email_sync.py`/`test_email_branding.py`.
- Frontend: `components/email-compose-dialog.tsx`, `lib/email-reply.ts`, `hooks/use-email-sync.ts`,
  `zaken/[id]/page.tsx`, `zaken/[id]/components/CorrespondentieTab.tsx`, `correspondentie/page.tsx`.

### Bekende issues
- **NIET geverifieerd:** hoe een aangeklede mail er in een échte inbox uitziet (kleuren/logo);
  geen echt antwoord/bijlage-mail verzonden (verzendpad wel bewezen). Reply-citaat staat vóór
  de handtekening (cosmetisch).
- **DMARC ontbreekt** voor kestinglegal.nl (Gmail-aflevering → mogelijk spam). Later regelen bij
  BaseNet/registrar. SPF bevat wel `_spf.basenet.nl`.
- Testspoor: "Luxis diagnose SELF" in incasso@-INBOX (dismissen); enkele proefmails naar
  arsalanseidony@gmail.com.
- Later: incasso@-accountnaam hernoemen.

### Volgende sessie
**Mailfunctie AFMAKEN — plan `docs/plans/PLAN-mail-afmaken.md`, blok A+B, op Opus.**
Blok A: mails openen in "Alle e-mails" (leesvenster ontbreekt), verder bladeren >200, ongelezen-status,
sjabloonkiezer begrijpelijk maken (werkt alleen mét dossier), ophaalvenster >14 dagen.
Blok B: "Nieuwe aanvragen"-tab via de BESTAANDE intake-detectie (draait al, 2 wachten op review),
domein-match op de 7 opdrachtgevers, "maak dossier van deze mail". Blok C = géén vrije mappen.

