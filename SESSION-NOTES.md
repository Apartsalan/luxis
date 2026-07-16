# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 16 juli 2026 (S224, Fable — VEEGSESSIE kruispunt-matrix + live-verzendtoets, teller op nul).
**Laatste feature/fix:** veegsessie vond 5 fouten en fixte er 4 LIVE (M1 classificatie-route, M3 gate op .eml-route, M4 documents-onderwerp, P3 adviezen bij sluiten); 2 nieuwe AST-wachters (M2-drieluik + M4-onderwerp). Live bewezen: AI-antwoord écht verstuurd + bezorgd (drieluik, Re:-thread, €140,49 op de cent), classificatie-trigger vuurt 10 s na sync, documents-route PDF bezorgd met huisformaat-onderwerp.
**Review-uitkomst:** de skill-lijst miste 2 routes (facturen, classificatie-antwoord); testdossier 2026-00006 bleek gearchiveerd (→ geheractiveerd); batch-DOCX-tak op prod onbereikbaar (geen stap met DOCX-sjabloon). Rapport: `docs/sessions/S224-veegsessie.md`.
**Openstaand (→ S225):** ⚠️ 6 beslispunten Arsalan (B1-B6 in het rapport: facturen-afzender, 2 dode routes, wees-advies IN100613, testdossier archiveren, batch-DOCX-toets); S221b-UX-restlijst; auto-concept-gate (steekproef Lisanne). KvK-sleutel ~22 juli → backfill voorrang. MAILSLOT OPEN.
**Volgende sessie:** `docs/sessions/PROMPT-S225.md` — beslispunten B1-B6 afhandelen + S221b-UX-restant (Opus). KvK-backfill voorrang zodra sleutel er is (~22 juli).

## Sessie 224 (16 juli 2026, Fable — VEEGSESSIE kruispunt-matrix + live-verzendtoets)

### Samenvatting
De éénmalige veegsessie uit de skill `breed-testen`: volledige huisregel-lijst ×
alle routes, gemeten in code + prod-DB. Route-inventaris zelf was al een vondst:
12 routes, waarvan 2 (facturen, classificatie-antwoord) niet in de skill-lijst
stonden en 2 dood/legacy zijn. KvK-voorrang-check: sleutel niet binnen → door.

**5 vondsten, 4 gefixt + gedeployd (`5845a3d`):**
1. M1 × classificatie-route: antwoord aan wederpartij ging via persoonlijk
   account → `send_as_tenant_account=True` (zelfde soort als S220-N1).
2. M3 × .eml-route: de 14-dagenbrief-gate bestond op 4 van de 5 deuren — "Open
   in Outlook" bleef open → gate + 'Toch openen'-override + spoor, voor+achter.
3. M4 × documents/send: onderwerp "{titel} — {nr}" (dossiernr dubbel, buiten de
   bouwer; route ontbrak in het S223-rijtje) → huisformaat server + prefill.
4. P3 × adviezen: sluiten ruimde wél concepten maar géén adviezen (prod-bewijs
   IN100613) → `supersede_open_recommendations` op beide sluit-routes.
5. Testdossier 2026-00006 stond gearchiveerd → matcher weigerde de testmail
   ("dossier bestaat niet") → geheractiveerd (beslispunt B5).

**2 nieuwe AST-wachters** (`tests/test_send_route_drift_guard.py`, patroon
auth/RLS-guards): M2 (geen rauwe provider/SMTP-uitgang buiten geloggde routes,
geloggde uitgangen roepen aantoonbaar `write_outbound_log` aan) en M4 (elk
verzend-onderwerp uit de bouwer of gemotiveerd op de allowlist) + eerlijkheids-
test (geen dode allowlist-regels). P3-wachter uitgebreid naar adviezen op alle
3 sluit-routes. 136 tests groen, ruff/tsc schoon, **CI groen (afsluitcheck)**.

**Live-verzendtoets (Taak B, alles op 2026-00006/Arsalans gmail):**
- **Classificatie-trigger eerste prod-vuring bewezen:** sync 17:40:20 →
  trigger 17:40:30 (10 s; losse cyclus stond pas 17:43) → belofte_tot_betaling
  85%, inhoudelijk juist.
- **AI-antwoord écht verstuurd:** instructie exact gevolgd (A3), €140,49 op de
  cent nagerekend (100 + 40 BIK + 0,49 rente = A1), huisstijl compleet (A2),
  drieluik compleet, afzender incasso@ (M1), onderwerp "Re: Vraag over dossier
  2026-00006" (M4), bezorgd in gmail ín dezelfde thread; zaak bleef op Tweede
  sommatie (P1) en concept → sent.
- **Documents-route:** renteoverzicht-PDF bezorgd; dialoog-prefill = exact
  huisformaat (fix 3 live bewezen).
- **Batch-DOCX-tak niet live toetsbaar:** geen actieve stap heeft een
  DOCX-sjabloon (alle stap-sjablonen zijn e-mail) — tak is test+wachter-gedekt;
  live raken = stap-mutatie (beslispunt B6).

### Gewijzigde bestanden
Backend: `ai_agent/service.py`, `email/compose_router.py`, `documents/router.py`,
`cases/service.py`, `workflow/hooks.py`. Frontend: `zaken/[id]/page.tsx`,
`DocumentenTab.tsx`. Tests: `test_send_route_drift_guard.py` (nieuw, 5 wachters),
`test_discard_drafts_on_close.py`, `test_compose_dagenbrief_gate.py` (+2),
`test_ai_agent.py`. Skill `breed-testen` bijgewerkt. Rapport:
`docs/sessions/S224-veegsessie.md`. 1 commit, backend+frontend gedeployd.
Prod-mutaties: alleen heractivering testdossier (1 rij).

### Bekende issues / bewust niet gedaan
- **6 beslispunten (B1-B6, rapport §5-6):** facturen-afzender (persoonlijk vs
  incasso@); dode AI-tool `email_compose` opruimen; legacy endpoint
  `/api/email/cases/{id}/send` opruimen (leeft nog, SMTP geconfigureerd, geen
  gate/SyncedEmail); wees-advies IN100613 → SUPERSEDED (GO); testdossier weer
  archiveren of actief laten; batch-DOCX-tak live toetsen.
- V2c geregistreerd, niet verbouwd: classificatie-onderwerp uit ResponseTemplate
  i.p.v. `build_reply_subject` (beheerde inhoud, geen stale data).
- Mailslot blijft principieel onafdwingbaar op de .eml-route (gebruiker
  verstuurt zelf); de gate dekt nu het juridische risico.

### Volgende sessie
S225: beslispunten B1-B6 met Arsalan afhandelen, dan S221b-UX-restant (Opus:
review-scherm, voortgangsindicator, HTML-tabellen, Blok 5-rest, Blok 6-memo).
KvK-backfill voorrang zodra de sleutel binnen is (~22 juli).

## Sessie 223 (16 juli 2026, Opus-bouw → Fable-review — AI-antwoord-knop + onderwerp-huisformaat + test-discipline)

### Samenvatting
Arsalans eigen punten uitgevoerd, plus twee kleine restpunten, plus een nieuwe
vaste test-werkwijze na zijn vraag "waarom komen er telkens fouten uit als ik
breder kijk".

**Punt 1+2 — AI-antwoord-knop (LIVE + live doorgeklikt).** Knop "AI-antwoord maken"
op elke inkomende mail van de wederpartij (Mail-pagina) met optioneel instructie-
tekstvak + toon-keuze (mild/zakelijk/streng). Onbeperkt herbruikbaar, wacht niet
op de automatische classificatie. Bestaat er al een open antwoord-concept → eerst
vragen (bestaand openen of vervangen; vervangen laat het oude vervallen via
`force_new`). Nieuw: `GET /api/ai/draft/existing`, `force_new` op de generatie,
`find_open_reply_draft`. 3 generatie-rondes live op IN100607: bedragen/facturen
exact gelijk aan DB, opmaak identiek aan bestaande concepten.

**Instructie-leidend-fix (live gemeten).** Ronde 1 negeerde "zeg dat ik erop
terugkom": de instructie stond inline en raakte begraven onder het later
aangeplakte AV/bibliotheek-blok. Fix: instructie als LAATSTE promptblok +
systeem-spelregel dat de behandelaar-instructie de kern bepaalt. Ronde 2 volgde
hem exact op.

**Punt 3 — onderwerp overal huisformaat.** `build_email_subject` (stap: klant /
debiteur — stapnaam — dossiernr) en nieuw `build_reply_subject` (antwoord:
Re: origineel + partijen/dossiernr, niet dubbel). Wint nu op ALLE routes:
compose, followup, batch (inline+DOCX), stap-concepten, antwoord-concepten. De
stale BaseNet-stap-onderwerpen ("TYPE / / ") worden overal genegeerd — geen
prod-data-mutatie nodig.

**Antwoord-verzending schuift de zaak niet meer door.** `advance-after-send`
schoof na élke concept-verzending door; nu alleen stap-brieven (rode test eerst).

**Kleine punten.** (1) Open concepten vervallen bij zaak sluiten — gedeelde
`discard_open_drafts_on_close` op alle 3 sluit-routes (handmatig, pijplijn-
eindstap, betaling-hook) + wachter-test. (4) 3 tests voor de sync→classificatie-
trigger (had er geen; vuurt op prod pas bij nieuwe mail).

**Nieuwe test-discipline (op verzoek Arsalan).** Skill `breed-testen`: fouten
wonen op kruispunten (route mist huisregel) — benoem het effect, grep alle
routes, loop de route×huisregel-matrix af, elke foutsoort krijgt een wachter.
Verwezen vanuit CLAUDE.md-verificatiestap 4 + memory. Levende huisregel-lijst
M1-M5/P1-P3/A1-A3.

### Reviewvondsten (kruispunt-matrix — beide gefixt + live)
- **Batch-PDF-route** droeg nog het stale onderwerp ("VERZOEKSCHRIFT / / ") →
  nu ook via de gedeelde bouwer + wachter-test.
- **CI stond stil rood sinds 15/7** (S220 voegde 'sommatie' toe aan de rente-
  bijlage-set maar vergat de pin-test; onzichtbaar door SSH-deploys, S217-patroon)
  → test bijgewerkt, CI weer groen.

### Gewijzigde bestanden
Backend: `email/subject.py`, `ai_agent/{unified_draft_service,unified_router,
followup_service,draft_service}.py`, `incasso/{service,router,automation_service}.py`,
`cases/service.py`, `workflow/hooks.py`. Frontend: `correspondentie/page.tsx`.
Tests: `test_email_subject`, `test_unified_draft_service`, `test_incasso_pipeline`,
`test_discard_drafts_on_close` (nieuw), `test_scheduler_email_sync`,
`test_kvk_legal_form`. Werkwijze: `.claude/skills/breed-testen/SKILL.md` (nieuw),
`CLAUDE.md`. Rapport: `docs/sessions/S223-review.md`. 6 commits, backend meermaals
gedeployd (geen migratie).

### Bekende issues / bewust niet gedaan
- **Écht versturen niet live getest** (mailslot open): nieuwe knop + batch-route.
  Verstuurpad zelf = de S220-route die toen bewezen is. → live toetsen S224.
- **Classificatie-trigger** op prod nog nooit gevuurd (geen nieuwe mail) — logica
  wel test-gedekt.
- Filter "Nog te openen" op dossierlijst: badge bestaat, filterknop niet (Arsalan
  koos hem niet). Landregel dagvaarding overgeslagen.
- Restlijst S221b-UX + auto-concept-gate (menselijke steekproef Lisanne) blijven.

### Volgende sessie
S224 = **VEEGSESSIE** (Fable): de hele huisregel-lijst uit `breed-testen` × alle
bestaande routes aflopen, mét live-pass, zodat de teller aantoonbaar op nul staat;
kandidaat-wachters staan in de skill. Plus **live-verzendtoets** zodra mag.
KvK-backfill voorrang zodra sleutel binnen (~22 juli).

## Sessie 222 (15/16 juli 2026 nacht, Opus-bouw → Fable-review — verzoekschrift-nabouw + totaalreview, autonoom)

### Samenvatting
Twee delen conform PROMPT-S222. **Deel 1 (Opus):** de faillissement-bijlage exact in
Lisanne's opmaak nagebouwd — haar BaseNet-sjabloon als basis (crème-balk, logo,
Calibri, randloze tabellen, voetteksten), 106 merge-velden omgezet naar docxtpl,
vorderingen-lus herbouwd, oud adres/mail vervangen, handtekening-placeholder weg.
Twee scenario's gerenderd (met/zonder deelbetaling): alle bedragen tellen op de cent
op, in beide tabellen. **Lokaal klaar; reseed op prod NIET gedaan** — wacht op GO +
4 keuzes (CONCEPT-watermerk, kolomlabel Verzuimdatum, betaalregels samengevoegd,
handtekening). **16 juli LIVE gezet** (GO + 4 keuzes bevestigd): back-up gemaakt,
alleen de verzoekschrift-rij bijgewerkt (45658→86951 bytes), DB-hash = schijf = lokaal,
en een live-render door het echte systeem op zaak IN100521 bewees dat alles goed vult
(debiteur/opdrachtgever/3 facturen, totalen op de cent, BTW-regel valt terecht weg).
**Deel 2 (Fable, autonoom — Arsalan sliep):** volledige review,
rapport in `docs/sessions/S222-review.md`.

### Reviewuitkomsten (bewijs in het rapport)
- **B1 LIVE bewezen** (het S221-gat): afgerond-weergave 19 taken, terugzetten op
  testdossier 2026-00006 (8→9 open), opnieuw overslaan + ongedaan-melding. ✅
- **B2:** migratie op head, 0 dubbele open concepten, 23 tests groen; máár nog geen
  nieuw concept sinds uitrol (prod-gedrag onbenut). Vondsten: zaak sluiten laat open
  concepten staan (IN100613 ×2); IN100521 heeft 2 pre-migratie-duplicaten.
- **B3 sync→classificatie: aannemelijk, NIET bewezen** — code in container ✅ maar
  géén test en nog nooit gevuurd (geen nieuwe mail sinds deploy).
- **B4 ✅ compleet:** Intake weg, Betalingen-label, ratio-tooltip, klikbaar
  dossiernummer, Calibri ×9 sjablonen, 0 spatie-kolommen in 58 verse antwoorden.
- **C testronde:** goud-pad crashte (mapper-imports, nooit getest in S221) én
  toetste het verkeerde ding (voedde Lisanne's verstuurde antwoorden als vraag —
  alle 103 bibliotheek-bronnen zijn per definitie haar eigen mails). Beide gefixt
  (`118617a`, `90ad871`) + 2 spelregels aangescherpt na ronde 1. Ronde 2: zuivere
  set 83→89%, goud eerste geldige meting 29/37; restant-afkeuringen grotendeels
  corrector-kalibratie (1 aantoonbare corrector-misser zelf nagelezen). **Poort
  auto-concept NIET gehaald → blijft UIT**; eerst kalibratievraag beantwoorden.
- **D backfills gemeten (níets opgeruimd):** 470 classificaties = 339 op afgesloten
  zaken + 110 oude mails + 21 recente (11 echt werk); 348 notificaties = 302
  classificatie-ruis; 8 concepten (3 opruimkandidaten); adviezen-15 en intake-14
  zijn actueel werk, GEEN opruimkandidaat. Opruimrecept klaar, wacht op GO.

### Wijzigingen
`118617a` (goud-pad imports), `90ad871` (spelregels + goud-lader voedt echte
debiteurenvraag) — beide gedeployed + getest. Nieuw sjabloon staat klaar in
`templates/verzoekschrift_faillissement.docx` (repo, niet op prod). Testronde-
rapporten bewaard: `S222-testronde-r1.md`/`-r2.md`. Prod verder alleen-lezen
behalve de B1-kliktest (netto nul).

### Volgende sessie
Beslispunten 1-6 uit `S222-review.md` met Arsalan doornemen; daarna S221b-restant
(Opus) of KvK-backfill (voorrang zodra sleutel binnen, ~22 juli).

## Sessie 221 (15 juli 2026 avond/nacht, Opus — demolijst DEEL 2, 6 blokken LIVE)

### Samenvatting
Vervolg op S220. Per blok: bouwen → tests → deploy via SSH → prod-verificatie. 7 commits,
1 migratie (additief). Geen echte debiteuren gemaild.

**Blok 3.4 — overgeslagen/afgeronde taken (LIVE + BEWEZEN).** `my-tasks` gaf alleen open
taken terug → de "Afgerond"-weergave op Taken was altijd leeg (17 skipped + 2 completed
onzichtbaar). Nieuw `?include_done=true` (gecapt 100, nieuwste eerst); dashboard-widget
ongemoeid. Terugzet-knop (→ pending) + undo-toast direct na overslaan. **Prod: zonder de
optie 8 open taken, mét de optie 27 waaronder 17 eerder-onzichtbare overgeslagen taken.**

**Blok 3.2/N3 — dubbele concepten + zombies (LIVE, migratie `s221_ai_draft_intent_step`).**
Concepten misten intent + stap-koppeling. Nu: `generate_unified_draft` geeft een bestaand
open concept terug i.p.v. een tweede (betaalde) generatie (next_step→zaak+stap,
reply→zaak+bron-mail, free_compose→nooit); `move_case_to_step` gooit verouderde 'volgende
stap'-concepten weg (net als de adviezen in S220). Auto-conceptroute kreeg dezelfde koppeling.
Tests: 3 dedupe + 1 discard + de S220-supersede-suite groen (72 in de bredere run).

**Blok 4 — classificatie direct ná mailsync (LIVE).** De losse 6-min-cyclus draaide soms nét
vóór de sync klaar was → verse mail wachtte een ronde (~7,5 min). Nu triggert de sync bij
nieuwe mail meteen `classify_new_emails` (idempotent, sleutel-guard). Latency → ~5 min.

**Blok 4.3 — begrip-eerst antwoordroute + testronde-script (LIVE + BEWEZEN op prod).**
`_REPLY_PROMPT` herschreven naar spelregels (feiten ALLEEN uit dossier, geen toezeggingen,
escaleren bij lastige gevallen) i.p.v. sjabloon-dwang; de reply-context krijgt nu
opdrachtgever/debiteur/openstaand/vorderingen mee (`_build_dossier_facts`). Nieuw
`backend/scripts/ai/antwoord_testronde.py`: vaste proefset + corrector-AI + rapport, verstuurt
niets, raakt geen echte dossiers (analyse/iteratie = Fable S222). **Prod-rookproef (de casus
IN100607 "wie zijn jullie"): AI noemt kantoor + opdrachtgever (LegalWork B.V.) + debiteur,
gebruikt alleen echte dossierbedragen; corrector alle checks groen, 0 zware fouten.**

**Blok 4 punt 11 — geen scheve bedrag-kolommen (LIVE).** Beide AI-prompts sturen nu weg van
spatie-uitgelijnde kolommen naar gelabelde regels ("Hoofdsom: € 3.500,00"). Échte HTML-tabellen
vergen aanpassing van het render/opschoon-pad (injectie-oppervlak) → bewust apart gelaten.

**Blok 5 — UX (LIVE).** Intake uit de zijbalk + commando-palet (Mail-tab "Aanvragen" is de
ingang); menu+paginakop "Bankimport" → "Betalingen"; rapportage-label "Incasso-ratio" →
"Geïnd op lopende zaken" + uitleg-tooltip; dossiernummer klikbaar in de mail-LIJSTrij.

### Gewijzigde bestanden
Backend: `dashboard/router.py`, `ai_agent/{models,unified_draft_service,incasso_email_prompts}.py`,
`incasso/{service,automation_service}.py`, `workflow/scheduler.py`, migratie
`s221_ai_draft_intent_step`, `backend/scripts/ai/antwoord_testronde.py` (nieuw). Tests:
`test_workflow.py`, `test_unified_draft_service.py` (+4), `test_supersede_recommendations.py` (+1).
Frontend: `hooks/use-workflow.ts`, `taken/page.tsx`, `layout/app-sidebar.tsx`, `command-palette.tsx`,
`betalingen/page.tsx`, `rapportages/page.tsx`, `correspondentie/page.tsx`.

### Bekende issues / bewust niet gedaan (→ S221b/S222)
- **NIET gedaan:** review-scherm (classificatie+concept naast elkaar), voortgangsindicator bij
  genereren, échte HTML-tabellen, Blok 5-rest (tijdlijn-mailregel klikbaar, agenda lege staat,
  soft-delete-banner, follow-up dossierlink/dagen-kolom/sorteerbare koppen, intake-detectie
  dempen), Blok 6-beslismemo b2b/b2c.
- **GATED:** auto-concept per categorie (Verweer + Algemene/overig) — bewust NIET aangezet;
  hangt aan de kwaliteit van de antwoord-route → pas ná de testronde (Fable S222).
- **Sjabloon-herzaaiingen — GEDAAN (GO + visueel getest, prod-reseed):**
  (1) Font: de terugval was **Cambria** (niet Courier — die stijl is dood), waardoor sectie-
  kopjes een ander lettertype hadden dan de tekst. Thema-body op **Calibri** gezet in alle 8
  DOCX (`scripts/fix_template_default_font.py`); reseed via `scripts/reseed_builtin_templates.py`.
  ⚠️ Server-render (LibreOffice) maskeerde het verschil al; de winst is vooral zichtbaar als het
  Word-bestand zélf geopend wordt. (2) Verzoekschrift-bijlage: NIET vervangen door de blanco PDF
  (die is leeg → geen bedragen). Keuze Arsalan = **ingevuld mét logo**. Root cause: het invulbare
  sjabloon had nooit een logo; LibreOffice behoudt briefhoofd-logo's wél. KESTING LEGAL-logo
  (image2.png uit Lisanne's origineel) als briefhoofd toegevoegd; alle 62 velden + huidig adres
  blijven. docxtpl-render + PDF **visueel geverifieerd**: logo + ingevulde bedragen + één lettertype.
  Prod DB byte-identiek aan schijf (45658). Back-up: `/root/backup_managed_templates_pre_s221_font.sql`.
- **Open vraag lettertype:** in mijn tests is elke boodschap al één lettertype; als Arsalan het
  mengsel ergens specifieks zag (mail/scherm), schermafbeelding nodig om precies dát te fixen.
- **Verzoekschrift EXACTE opmaak (→ verse sessie, keuze Arsalan):** hij wil Lisanne's PDF-lay-out
  (crème-balk + logo) precies, per zaak ingevuld. Haar bron is een BaseNet-merge-sjabloon (38
  Velocity-velden, loops, keuze-logica) → omzetten naar Luxis docxtpl. Volledig onderzoek +
  mapping + valkuilen in `docs/sessions/PLAN-verzoekschrift-exacte-nabouw.md`. Huidige logo-versie
  blijft intussen live als tussenoplossing.
- **Backfills 3.3** blijven Fable (S222): uitzoeken wát de 470 classificaties/14 intake/8
  concepten/3 adviezen precies zijn vóór er iets gesloten wordt.
- Terugzet-knop/undo-toast (3.4) + maillijst-chip zijn typecheck- + deploy-geverifieerd, niet
  live doorgeklikt (Playwright-browserlock) — meenemen in de visuele Fable-review.
- MAILSLOT OPEN — testdossier 2026-00006 = Arsalans gmail.

### Volgende sessie
Fable-review S220+S221 (VERPLICHT) + antwoord-testronde met de goud-set draaien
(`python -m scripts.ai.antwoord_testronde --goud N --tenant-id <uuid> --out ...` op prod).
Daarna S221b (Opus) voor het restant hierboven. KvK-backfill zodra de sleutel er is (~22 juli).

## Sessie 220 (15 juli 2026 avond, Opus — bouwsprint demolijst, Blok 1/2/3.1/5-fasebalk LIVE)

### Samenvatting
Uitvoersprint op het S219-onderzoek. Per blok: bouwen → tests → deploy via SSH →
prod-verificatie. 9 commits, backend+frontend meermaals gedeployd, 1 prod-DB-mutatie
(stap-teksten) met dry-run + GO Arsalan + natelling. Elk stuk apart getest.

**Blok 1 — verzendpad-fundament (hoofdvondst N1), LIVE + BEWEZEN op prod.** De
primaire verstuurknop (`/compose/send`) ging via het persoonlijke account van de
klikker en legde niets vast. Nu: kantoor-afzender-vangrail (incasso@, patroon B13) +
vastlegging via gedeelde `write_outbound_log` (EmailLog + SyncedEmail + CaseActivity);
`send_with_attachment` gebruikt dezelfde functie; documents-send kreeg de ontbrekende
`send_as_tenant_account=True`. **Testmail op prod (naar Arsalans gmail, GO): from =
incasso@, EmailLog+SyncedEmail+activiteit aangemaakt — bewezen.** Plus: BCC door de
hele keten (schema/providers/.eml/dialog) + CC-verlies-fix; brieftype-afleiding uit de
stap op de AI-concept-route (punt 1/25 — renteoverzicht gaat nu mee, geen factuur);
bijlage-preview-endpoint + "Gaat automatisch mee"-weergave (punt 2); 'sommatie' aan de
rente-set (punt 3); gedeelde onderwerp-bouwer op alle server-routes (punt 5).

**Blok 2 — stap-teksten & sjablonen, LIVE.** De 6 DB stap-mailteksten opgeschoond
(script `scripts/sanitize_step_templates.py`, idempotent, dry-run+GO): oud adres
IJsbaanpad 9 / 1076 CV → Willem Fenengastraat 16E / 1096 BN, kesting@ → incasso@ (beide
kolommen; HTML gebruikte `&nbsp;` → tweede ronde nodig, natelling daarna schoon), aanhef
ingevuld bij de 3 met een losse komma. **Vanaf nu dragen alle AI-concepten het juiste
adres.** Code-sjablonen: aanhef overal "Geachte heer, mevrouw," (keuze Arsalan), BV-naam
uit de aanhef, klant-kenmerk niet meer naar de debiteur (DF138-05), html_renderer-aanhef.

**Blok 3.1 — zombie-opruiming, LIVE.** `move_case_to_step` sluit nu openstaande PENDING
follow-up-adviezen automatisch (nieuwe status SUPERSEDED) → geen dubbel-verstuur-risico
en de scanner is weer vrij (punt 13). Het uitvoerende advies is op dat moment APPROVED,
dus onaangeroerd.

**Blok 5 — fasebalk (punt 14), LIVE.** De 5-vinkjes-balk (vinkte alle categorieën links
af) vervangen door: stapnaam + categoriekleur + "X dagen in deze stap" (step_entered_at
nu in de case-respons) + volgende stap.

**Blok 4.5 — timeout Eerste→Tweede 7→4 (punt 15), GEDAAN op prod.** step_transitions
id 44c31bf7… condition `{"days": 4}` (GO Arsalan; stap-wachttijd + workflow = 4).
Data-only, geen deploy. **Beslissingen S221 (Arsalan):** backfills NIET zelf uitvoeren
→ Fable zoekt eerst uit wat de items zijn; auto-concept AAN voor Verweer + Algemene/overig
maar PAS ná de begrip-eerst-antwoord-route (nut hangt af van antwoordkwaliteit).

### Gewijzigde bestanden
Backend: `email/{compose_router,send_service,subject,providers/*}.py`, `documents/{router,
schemas,docx_service}.py`, `incasso/{service,html_renderer}.py`, `ai_agent/{followup_service,
followup_models}.py`, `collections/compliance.py`, `cases/schemas.py`,
`scripts/sanitize_step_templates.py` (nieuw). Frontend: `email-compose-dialog.tsx`,
`zaken/[id]/{page,components/DossierHeader,components/DocumentenTab}.tsx`,
`correspondentie/page.tsx`, `hooks/{use-documents,use-cases}.ts`. Tests: 5 bestanden
(rente_bijlage_verzendpaden uitgebreid, email_subject, supersede_recommendations nieuw).

### Bekende issues / bewust niet gedaan (→ S221)
- Blok 3.2 (dedupe: bestaand concept tonen i.p.v. tweede maken — `ai_drafts` mist stap-
  koppeling), 3.3 (backfills: 3 verouderde adviezen + 470 pending classificaties + 14
  intake-ruis + 8 verouderde concepten — GO nodig), 3.4 (skipped-taken weergave + herstel).
- Blok 4 (AI-keten): classificatie direct na sync; auto-concept-categorieën (BESLISSING
  Arsalan); antwoord-route begrip-eerst + testronde-script; timeout Eerste→Tweede 7→4 (GO);
  review-scherm. AI-concept-HTML-tabellen (punt 11) hoort hier.
- Blok 5-UX-rest: zaaknummer klikbaar in maillijst, tijdlijn-mailregel klikbaar,
  S218-restanten (menu Intake weg, Bankimport→Betalingen, ratio-label, agenda lege staat,
  soft-delete-banner, follow-up dossierlink/dagen/sort).
- Blok 6: beslismemo b2b/b2c (105 dossiers uit BaseNet-XML) — geen code.
- Deferred prod-mutaties: Courier→Calibri (DOCX-reseed), verzoekschrift-bijlage vervangen
  door de juiste PDF uit de projectmap. Beide sjabloon-herzaaiingen (S210-flow).
- MAILSLOT OPEN — geen echte debiteuren mailen; testdossier 2026-00006 = Arsalans gmail.

## Sessie 219 (15 juli 2026 avond, Fable — demolijst-onderzoek, read-only, ALLE punten onderzocht)

### Samenvatting
Elk demolijst-punt tot op de bodem uitgezocht (prod-DB read-only, code, logs, live
API-render) + een eigen "demoronde": elk demopunt veralgemeend naar een faalpatroon en
daarop breed gejaagd. Volledige metingen: `docs/sessions/S219-onderzoek.md`; status per
punt bijgewerkt in `DEMOLIJST-S218.md`; bouwdraaiboek: `PROMPT-S220.md` (6 blokken).
KvK-voorrang-check gedaan: sleutel duurt nog ~een week (Arsalan).

**Hoofdvondst (N1) — de compose-verstuurknop (dé route van de echte Bayar-sommatie):**
(a) verstuurt via het persoonlijke account van de klikker (voorkeur outlook → seidony@
i.p.v. incasso@; vangrail B13 bestaat alleen op batch/follow-up; zelfde gat op het
document-verzendpad) en (b) legt NIETS vast (geen EmailLog/SyncedEmail/CaseActivity) →
de verstuurde sommatie is onvindbaar in Luxis. Bewijs: mail nergens in synced_emails,
niet in incasso@-INBOX.Sent (sync leest die map), IN100613 heeft alleen pipeline-activiteiten.

**Punt 6/7 (oud adres/handtekening) — bron gevonden:** kantoor-instellingen zijn al
goed; Word- en code-mailsjablonen renderen vers correct (live geverifieerd). Het rot zit
in de 6 stap-mailteksten in `incasso_pipeline_steps` (letterlijke BaseNet-kopieën met
"IJsbaanpad 9" + kesting@) — de AI-prompt kopieert de footer trouw → álle 10 AI-concepten
oud adres (ook verse van 15-07); de verstuurde Bayar-mail had oud adres + kesting@.
Plus: verzoekschrift-bijlage-Word (Lisanne-origineel) hardcoded IJsbaanpad; verzoekschrift-
DOCX hardcoded oud Rabo-derdengelden-IBAN + kosten (beslispunt Lisanne).

**AI-keten gemeten:** echte casus mail→verweer-concept = 7,5 min automatisch (sync 5' +
classificatie 6' + race); handmatige generatie 39 s ($0,07, sonnet, prompt 41k tekens,
geen UI-voortgang → dubbelklik-concepten); auto-concept staat bewust UIT voor alles
behalve verweer (orchestrator.py:78); 470 pending classificaties (import-backfill) +
348 ongelezen notificaties maken wachtrijen onbruikbaar. Punt 21 ("wie zijn jullie"):
geclassificeerd als ongemotiveerde betwisting → standaard-weerlegging zonder klantnaam.

**Fasebalk (punt 14) bewezen:** `isPast = index < currentPhaseIndex` vinkt alle fasen
links van de huidige af, doorlopen of niet; "administratief" is geen fase. Clio/Smokeball
tonen status als label/milestone + tijd-in-fase. Voorstel: stapnaam + dagen-in-stap.

**Nieuwe vondsten demoronde:** (N3) zombie-concepten — IN100613 heeft 2 open "Eerste
sommatie"-concepten terwijl de zaak op Tweede staat (dubbel-verstuur-risico met oud
adres), IN100521 2 identieke; (N4) zes stille ruis-wachtrijen (470/348/79/14/3/18);
route×waarborg-matrix: 14-dagenbrief-gate + mailslot overal gedekt, afzender-vangrail
en logging niet. Kleinere punten: BCC bestaat nérgens in de keten; CC-veld verliest
niet-gecommitte invoer stil; taak IN100607 bestaat nog (status skipped, geen weergave/
herstelknop, 18 taken zo onzichtbaar); timeout 7-vs-4 bevestigd in step_transitions.

### Gewijzigde bestanden
Alleen docs: `docs/sessions/S219-onderzoek.md` (nieuw), `docs/sessions/PROMPT-S220.md`
(nieuw), `docs/sessions/DEMOLIJST-S218.md` (status per punt), SESSION-NOTES, roadmap.
PROMPT-S217/S218 → `docs/archief/prompts/`. Geen code, geen prod-mutaties, niets verstuurd.

### Bekende issues
- De 8 open AI-concepten dragen allemaal het oude adres — NIET versturen vóór S220 blok 2/3.
- Beslispunten: ✅ derdengelden-IBAN (Rabo = stichting, klopt) + ✅ kosten verzoekschrift
  (kloppen) — beantwoord door Arsalan 15-07. Nog open: aanhef-stijl; welke categorieën
  auto-concept aan.
- Punt 21-richting aangepast (Arsalan 15-07): géén vaste antwoord-typen bijbouwen —
  antwoord-route wordt begrip-eerst (AI leest mail + dossier en schrijft zelf het antwoord,
  met spelregels; typen/bibliotheek = referentie). Verwerkt in PROMPT-S220 blok 4.3.
- From-adres Bayar-mail = afleiding (code + afwezigheid in incasso@-Sent); sluitstuk =
  blik in Arsalans M365 Verzonden-map. CC-verlies = code-hypothese, in S220 testen.

### Volgende sessie
S220 (`docs/sessions/PROMPT-S220.md`, Opus): 6 blokken — verzendpad-fundament (vangrail+
logging+brieftype-afleiding+CC/BCC+onderwerp-bouwer), stap-teksten saneren, zombie-
opruiming, AI-keten sneller, fasebalk+UX-rest, beslismemo b2b/b2c. KvK-backfill voorrang
zodra sleutel binnen (~22 juli).

## Sessie 218 (15 juli 2026 middag/einde middag, Fable — demo Arsalan: demolijst + 3 oorzaken bewezen, read-only)

### Samenvatting
Demosessie werd foutenjacht. Arsalan raakte als eerste dossier IN100613 (VOF Bayar transport)
aan en de rente-PDF ontbrak → uitgezocht, daarna demolijst van **25 punten** verzameld
(`docs/sessions/DEMOLIJST-S218.md` — dé bron; werkverdeling: S219 Fable-onderzoek → S220
Opus-bouw → Fable-review). Niets gebouwd (bewuste keuze Arsalan), geen prod-mutaties door mij.

**Oorzaak 1 — rentebijlage ontbreekt op de AI-concept-route (punt 1, bewezen).** Arsalan
verstuurde de eerste échte sommatie (IN100613, 12:24) via AI-concept → compose. De bijlage-
beslissing hangt volledig aan het meegegeven sjabloontype; een AI-concept draagt er geen
(`ai_drafts` heeft geen stap-koppeling) → server zag "gewone mail" → geen renteoverzicht-PDF
en geen factuur-PDF's. Beslisregel + render zelf bewezen gezond (b2b + lege rechtsvorm →
bijlage JA; PDF rendert 82kB). S212-review-aanname "AI-concepten zijn geen sommaties" was fout —
dit ÍS de hoofdroute. **Fix-ontwerp (S220, punt 25):** bij verse dossier-mail aan de debiteur
zonder sjabloonkeuze het brieftype afleiden uit de huidige pijplijnstap (antwoord/doorsturen
blijft zonder bijlage; recipient-check op debiteur; GEEN factuur-auto-attach op deze route —
Arsalan: "we sturen normaal geen facturen mee"). Plus: compose-venster moet tonen wat er
automatisch meegaat (punt 2) en documentenroute-gaatje ('sommatie'-brieftype ontbreekt in de
bijlage-typeset) dichten (punt 3).

**Oorzaak 2 — follow-up toont verouderde adviezen én blokkeert nieuwe (punt 13, bewezen).**
IN100607 stond WÉL in follow-up maar onder "Eerste sommatie" (advies 9 juli) terwijl die al
verstuurd was — uitnodiging tot dubbel versturen. Buiten de follow-up-knop om uitvoeren ruimt
het advies nooit op, én de scanner slaat dossiers met een openstaand advies over (ontdubbeling
per dossier, niet per stap) → het volgende advies komt NOOIT. Gemeten: 3/15 adviezen verouderd
(IN100607, IN100613, IN100521). Fixrichting: bij stap-wissel open adviezen automatisch afsluiten.

**Oorzaak 3 — wachttijden beantwoord + inconsistentie (punt 15).** Twee klokken: follow-up-
advies na min-wachttijd van de stap (sommaties: 4 dagen, scanner elk half uur) en dagelijkse
timeout-automatisering (concept+taak na 15/7/4/4/4 dagen). ⚠️ Eerste→Tweede: timeout-regel
zegt 7 dagen, stap-wachttijd 4 — gelijktrekken in S220.

**Verder gemeten:** 105 dossiers BaseNet-B2C-fase vs Luxis-b2b (import: bedrijf→zakelijk;
raakt WIK-route → beslismemo Lisanne, punt 16). IN100613 schoof na verzending netjes door
naar Tweede sommatie; IN100607 staat op Verweer beantwoorden (hold). Arsalan: geen nasturen
bijlagen naar Bayar. Referentiebestanden in projectmap: juiste verzoekschrift-PDF
("CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf") + handtekening-voorbeeld-.eml.

### Gewijzigde bestanden
Alleen docs: `docs/sessions/DEMOLIJST-S218.md` (nieuw), `docs/sessions/PROMPT-S219.md` (nieuw),
SESSION-NOTES, roadmap. Geen code, geen migraties, geen deploy.

### Bekende issues
- Eerste échte sommatie (IN100613) is verstuurd zónder rente-PDF (rente stond wel in de tekst;
  b2b dus geen harde WIK-plicht; Arsalan besloot: niets nasturen).
- PROMPT-S218 (UX-sprint) is NIET uitgevoerd — punten gaan mee in S220 (ontdubbelen met demolijst).
- 12 échte follow-up-aanbevelingen wachten nog op beoordeling Arsalan/Lisanne (3 zijn verouderd).

### Volgende sessie
S219 (`docs/sessions/PROMPT-S219.md`, Fable): demolijst-onderzoek — sjablonen-audit (matrix
sjabloon × punt), AI-keten (snelheid/kwaliteit/klikken), fasebalk + concurrent-onderzoek,
kleinere punten; daarna PROMPT-S220 (Opus-bouw) schrijven. KvK-backfill heeft voorrang zodra
de sleutel er is.

## Sessie 217 (15 juli 2026 middag, Fable-audit + Opus-fixes — vibe-code-doorlichting, CI-herstel, follow-up bewezen)

### Samenvatting
Drieluik. **(1) Vibe-code-audit** (aanleiding: "mooi gebouw, scheve fundering"-meme): internet-
onderzoek naar de echte 2025/2026-incidenten (Tea App, Moltbook, 170 Lovable-apps) → elk faalpunt
in Luxis nagemeten. Uitkomst: fundering staat — 302 endpoints geteld waarvan 8 bewust publiek
(alle rate-limited/HMAC-state), RLS + drift-guard, DOMPurify op alle 5 mail-render-plekken,
CORS dicht, security-headers, backups draaien (vannacht 03:00, EU-versleuteld), fail2ban 1655 bans,
alleen 22/80/443 open. **3 fixes gebouwd + live:** Pillow 12.2→12.3 (5 CVE's, na-deploy her-audit
bewijst schoon), `test_auth_drift_guard.py` (wachter: elke route eist login, allowlist 8, spiegel
van RLS-guard), postcss-override (npm audit 0; `--force` had Next 15→9 gesloopt).
**(2) Fable-review daarvan** vond het echte gat: **CI stond al sinds 13 juli rood** (laatst groen
12 juli 22:46) — S211/S212 zette de rente-bijlage-PDF op het verzendpad, die rendert via LibreOffice
(`soffice`), zit wél in Docker maar niet op ubuntu-latest → 5 tests rood, onzichtbaar door SSH-deploys.
Fix: apt-install in ci.yml → **CI 8/8 groen**. Ook gecorrigeerd: Pillow-claim was overdreven
(WeasyPrint rendert alleen eigen documenten, externe URL's geblokkeerd).
**(3) Kritische menu-doorlichting** (vraag Arsalan) — alles op prod gemeten:
- **Follow-up:** nooit gebruikt (15/15 pending). LIVE bewezen met testdossier 2026-00006
  (debiteur = Arsalans gmail): controle-dialoog → versturen → mail mét `renteoverzicht_*.pdf`
  in Gmail, status executed, stap doorgeschoven, opgeruimd (soft-delete). Gaten: dossiernr pas
  klikbaar ná openklappen rij; "Dagen"-kolom toont altijd 0d; geen kolomsortering/filters; geen e2e.
- **Intake:** 17 kandidaten ooit, 0 echte zaak — allemaal ruis (testmails, "Blog onderwerpen");
  UNKNOWN = AI vond geen debiteurnaam in die mails. Dubbelop: Mail-pagina heeft al tabblad
  "Aanvragen" met dezélfde wachtrij.
- **Bankimport:** 0 uploads ooit (S179/180-betalingen gingen via scripts); functie zinvol
  (maandelijkse reconciliatie) maar onbewezen pad + misleidende menunaam.
- **Rapportages:** leeft nu (€135.354 geïnd, 612 zaken) — S191-"Geïnd €0" opgelost door imports.
  Wel: "incassoratio 4,7%" = alleen actieve zaken (formule klopt, label misleidt).
- **Agenda-blok dossier (S216):** werkt correct, maar onzichtbaar want 0 actieve afspraken in
  heel Luxis (render-niets-bij-leeg was bewuste keuze). Outlook-agendasync bestáát al
  (scheduler elk kwartier, seidony@ outlook gekoppeld) — wacht op afspraken in M365/Luxis.
- **Mail: AAN.** DB-slot open sinds 13 juli 10:19, env-noodslot uit, inkomend synct foutloos
  (11:35), uitgaand bewezen (testsommatie 11:12), verzendvenster visueel gecheckt (sjablonen,
  bijlagen, Open-in-Outlook). Eerste echte mails kunnen vanavond.

### Gewijzigde bestanden
`backend/pyproject.toml` + `uv.lock` (Pillow-floor), `backend/tests/test_auth_drift_guard.py` (nieuw),
`frontend/package.json` + lock (postcss-override), `.github/workflows/ci.yml` (LibreOffice).
4 commits (`6d0588f`, `d83f939`, `251d991` + docs), deploy backend+frontend via SSH, geen migratie.

### Bekende issues / bewust niet gedaan
- 6 pip-CVE's in prod-container = installatiegereedschap, draait nooit in runtime — bewust gelaten.
- Verwijderd (soft-deleted) dossier blijft via directe URL leesbaar zonder markering.
- Mail-badge: 79 ongelinkte mails; wachtrij groeit stilletjes.
- S216-testzaken 2026-00003/4/5 bleken WÉL netjes opgeruimd (eerdere twijfel onterecht — mijn
  DB-meting vergat `is_active`; les herbevestigd: filter altijd op actief-vlag).

### Volgende sessie
S218 = UX-sprint uit de doorlichting (`docs/sessions/PROMPT-S218.md`); KvK-backfill (PROMPT-S217)
heeft voorrang zodra de sleutel binnen is. Lisanne + Arsalan sturen vanavond de eerste echte mails.

## Sessie 216 (15 juli 2026, Opus-bouw + Fable-review — dossierpagina-verbouwing blok 1-3, LIVE)

### Samenvatting
De dossierpagina (`zaken/[id]`) was onoverzichtelijk: 11 tabbladen (incasso) / 8 (gewone zaak),
een kop die het hele eerste scherm vulde, alles dubbel (partijen op 4 plekken), 3 losse "notitie"-
begrippen. Onderzoek (code + prod-DB-meting per tabblad + visuele doorklik + concurrentiescan
Clio/Smokeball) → plan `docs/plans/PLAN-dossierpagina.md` (4 harde eisen Arsalan: alles klikbaar
blijft klikbaar; één stijl/geraamte beide types; niets onzichtbaar = inklapbaar; Uren blijft tab).
Drie bouwblokken, elk gebouwd → getest (tsc) → gedeployd → visueel geverifieerd op prod, daarna
Fable-review met 2 must-fixes. Alle testzaken/testafspraken opgeruimd.

- **Blok 1 (`4dba5b3`+`4ef4c0a`):** 11/8 → 7/6 tabbladen (tabbalk past nu; was 5 buiten beeld).
  Financieel bundelt vorderingen+betalingen+regeling+derdengelden; lege regeling/derdengelden
  inklapbaar. Tijdlijn = oud Activiteiten + inklapbare stap-historie. Taken + conflictbanner naar
  Overzicht. Provisie naar Facturen. PartijenTab verwijderd. Vertaaltabel oude ?tab=-links.
- **Blok 2 (`3a927fc`):** kop 4 statkaarten → geldstrook Hoofdsom·Betaald·**Openstaand** (ontbrak).
  Notitie+Telefoonnotitie → één `NoteDialog` met autoFocus (**cursor-bug gefixt**, sneltoets n).
  BaseNet-waarschuwing (`[BaseNet-waarschuwing]`) → oranje balk bovenaan Overzicht. Zijbalk
  type-afhankelijk (Debiteur/Rente alleen incasso = advies-lek dicht; OHW alleen bij uren>0).
- **Blok 3 (`ea07c9a`):** agenda-blok op Overzicht (`useCaseEvents` → `/api/calendar/events?case_id`,
  komende afspraken, klikbaar). Kop gewone zaak: "Volgende stap" (eerstvolgende taak+deadline) i.p.v.
  incasso-fasebalk + **afsluitknop** (ontbrak op niet-incasso). Geldstrook gewone zaak: OHW+budget.
- **Fable-review (`ca33ba9`):** 2 must-fixes — (1) overige partijen (rol+ref) weer zichtbaar in
  Partijen-sectie Overzicht (waren met het opgeheven tabblad onzichtbaar geworden); (2) e2e
  bijgewerkt (zaken Z5 → 6 tabs/role=tab, regression C19 → Financieel-tab). Meldingen-links,
  heropenen-transitie, sneltoetsen aangevallen en overeind.

### Gewijzigde bestanden
Frontend `zaken/[id]/`: `page.tsx`, `components/DossierHeader.tsx`, `DossierSidebar.tsx`, `DetailsTab.tsx`,
`incasso/VorderingenFinancieelTab.tsx` + `BetalingenDerdengeldenTab.tsx`; nieuw `CaseConflictBanner.tsx`,
`BasenetWarningBanner.tsx`, `NoteDialog.tsx`, `AgendaBlok.tsx`; verwijderd `PartijenTab.tsx`.
`hooks/use-calendar-events.ts` (useCaseEvents). e2e `zaken.spec.ts` + `regression.spec.ts`.
8 commits, alle frontend-deploys via SSH. Geen backend/migratie. Plan + prompt bijgewerkt.

### Bekende issues / bewust niet gedaan
- Anker-subnav bovenin Financieel (klein; secties al gegroepeerd+inklapbaar).
- Geldstrook gewone zaak kan later uitgebreid met ongefactureerd + openstaande facturen (bronnen bestaan).
- Meldingslink naar stap-historie landt op Tijdlijn met historie ingeklapt (1 klik extra; bewust).
- Taken-blok toont op elk dossier een lege-staat als er geen taken zijn (3/608 hebben taken).

### Volgende sessie
S217: KvK-rechtsvorm-backfill zodra Arsalan de sleutel meldt (voorrang; gemeten 726 relaties/~€14,50 per
run — zie PROMPT-S215 STAND), anders dossierpolish (anker-subnav + geldstrook-uitbreiding). Prompt:
`docs/sessions/PROMPT-S217.md`.

## Sessie 214 (14 juli 2026, Opus-bouw + Fable-matching — S201 kantoorfacturen-import, LIVE)

### Samenvatting
De 439 definitieve BaseNet-kantoorfacturen (Lisanne's eigen omzet) staan op prod: 630 regels,
325 betalingen (€248.364,17), 344 betaald/86 te laat/9 verzonden, 137 aan hun IN-dossier,
302 D-facturen bewust contact-only (projectcode reist mee in de marker), 23 creditnota's aan hun
origineel. Bruto €302.750,39, openstaand €72.762,09 — elke som onafhankelijk nageteld in de
prod-database én via de API-rooktest (debiteuren €78.469,57 = exact de 88 open gewone facturen).

**Stap 0 vooraf (eerlijkheidsvoorwaarden, migratie `s214_payment_date_null`):**
`invoice_payments.payment_date` nullable → UI toont "Datum onbekend" (handmatige invoer blijft
datum vereisen); betaalmethode `unknown`/"Onbekend (BaseNet)"; creditnota toont afwikkelstatus
i.p.v. valse "Volledig betaald" (guard in `get_payment_summary` + frontend verbergt betaalbalk).

**Recept getoetst aan de bron — 3 veldniveau-fouten gevonden en gecorrigeerd** (vastgelegd in
`S201-facturatie-recept.md` §0): creditnota's hebben géén `invduedate` (→ terugval factuurdatum);
Mollie-betaaldatums komen uit `Payment.payment_status=4` + `insertdate` (niet uit onbestaande
`paidAt`-velden); dossierkoppeling loopt via kop-veld `invpcode` (niet "inccode").
Derdengelden-herkenning = product 100013 ("Verrekening incassodossiers") + expliciete lijst
{100242, 100363} — een `bedrag<0`-regel vangt 109 facturen en is fout.

**Fable-matchingronde ving 3 gaten:** paid_date op de 20 Mollie-bevestigde facturen,
memoriaal-boekingsdatum als gelabelde metadata op de 305 "Datum onbekend"-betalingen (11 liggen
vóór de factuurdatum — dáárom geen betaaldatum), ruwe bronstatus op de 3 nul-facturen. Prod vooraf
read-only nageteld: 52/52 relaties + 127/127 IN-dossiers matchen deterministisch.

### Gewijzigde bestanden
- `scripts/basenet/import_invoices.py` (nieuw) — classificatie op gemeten velden, harde poorten,
  weigert schrijven als doeltabel niet leeg is (dubbele import onmogelijk).
- Backend: `invoices/models.py`, `schemas.py`, `invoice_payment_service.py`,
  migratie `s214_payment_date_null.py`; tests `test_import_invoices.py` (nieuw, 4) +
  `test_invoice_payments.py` (+2, totaal 22).
- Frontend: `facturen/[id]/page.tsx` (creditnota-afwikkelbalk, "Datum onbekend", methode-label),
  `hooks/use-invoices.ts`. 4 commits (`5920d1b`…), deploy backend+frontend+migratie.

### Verificatie
Dry-run op prod: álle poorten groen (439/7/12/19/90, 0 onopgelost, 137 IN, alle euro-sommen exact,
regelformules 630/630, factuur 100532 bewaart €1.631,74). Execute → natelling in DB + API-login-
rooktest groen. 24 tests groen, ruff schoon, tsc schoon. Mailslot niet aangeraakt, niets verstuurd.

### Bekende issues
- **7 Mollie/kop-conflicten** (€10.854,66; nrs 100314/100316/100321/100332/100342/100441/100533):
  Mollie zegt betaald, kop zegt open — per factuur oordeel Lisanne/boekhouding, daarna evt. na-import.
- 12 WIP/concepten (€13.013,07) + 31 losse conceptregels (€6.779,81): handmatig beoordelen (lijst
  in recept §1); 2 negatieve verrekenposten (100242 −€217,80 / 100363 −€735,00) bewust buiten.
- 302 D-facturen koppelen pas aan een dossier na de latere D-dossier-import (projectcode in marker).
- KvK-sleutel nog niet binnen → S214-hoofdtaak (rechtsvorm-backfill) doorgeschoven naar S215.

### Volgende sessie
S215: KvK-rechtsvorm-backfill zodra Arsalan de echte sleutel meldt (env op VPS → droogloop →
akkoord → run → natelling → meten hoeveel BV's geen rentebijlage meer krijgen).
Prompt: `docs/sessions/PROMPT-S215.md`.
