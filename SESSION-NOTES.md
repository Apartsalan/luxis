# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 11 juli 2026 (S197, Opus+Fable) — Codex-hang opgelost (achtergrond + hartslag-bewaker, ultra blijft); S196-review + 4 dashboard-fixes live; mailslot-knop live in Instellingen (user-gestuurd, staat UIT). Details: S197-entry.
**Laatste feature/fix:** mailslot als schakelaar in Instellingen → E-mail (DB-vlag, fail-safe dicht, env-noodslot van prod verwijderd) + 4 review-fixes op het termijn-blok (fout i.p.v. verdwijnen, ververst na regeling-actie, footer-tekst, lichtere query). Live geverifieerd op prod.
**Openstaand:** ⚠️ MAILSLOT staat UIT via de knop — env-noodslot eraf (`.env.bak-s197` op VPS); Arsalan zet mail zélf aan wanneer nodig. Bouwblok 3 nog NIET gedaan → S198 (autonoom). 12 onverklaarde bankbetalingen bewust niet geboekt (S195).
**Volgende sessie:** S198 = AUTONOOM bouwblok 3 (klus 1-4) + Fable-review + Codex code-review. Prompt: `docs/sessions/PROMPT-S198.md`; plan: `docs/plans/PLAN-fase2-bouwblokken.md`.

> 📦 **Archief:** alles ouder dan de laatste 10 sessies staat in `docs/archief/SESSION-ARCHIVE.md` (verplaatst, nooit verwijderd).

## Sessie 197 (11 juli 2026, Opus+Fable — Codex-hang opgelost + S196-review + mailslot-knop; bouwblok 3 NIET gedaan)

### Samenvatting
Sessie liep anders dan PROMPT-S197 (bouwblok 3): Arsalan wilde eerst de Codex-hang oplossen +
een review van S196 vóór verder bouwen, en een mailslot-knop erbij. Bouwblok 3 verschuift daardoor
volledig naar S198 (autonoom).

**1 — Codex-hang opgelost (kernbevinding).** Twee sessies (S194/S196) timede Codex "na 10 min" uit.
Oorzaak was NIET Codex/ultra maar een botte 10-min-grens: (a) de skill-guard van 600s + (b) de max
foreground-timeout van de Bash-tool. Bewijs gemeten: een triviale `codex exec` antwoordt in 9,5s
(→ opstart/MCP is níét de blokkade), en een échte S196-review op ultra duurde **21 min** en rondde
gewoon af toen hij op de ACHTERGROND liep. Codex heeft zelf al een 5-min stream-retry
(openai/codex#23807). Oplossing: `scripts/codex-review.sh` — draait de review op de achtergrond
zónder tijdslimiet en bewaakt de HARTSLAG (output-mtime): 6 min écht stil = als vastgelopen stoppen
+ melden, anders onbeperkt nadenken. **Ultra blijft** (Arsalans keuze; ultra vond 4 punten waar
"hoog" er 3 vond).

**2 — S196-review + 4 fixes LIVE.** Codex-review (ultra) van commit `42c3e4c` (termijn-vooruitblik).
Geld/beveiliging/tenant-scoping in orde; 4 robuustheidspunten zelf geverifieerd + gefixt (commit
`f2b526b`): (1) laadfout verborg het hele dashboard-blok stil → nu foutmelding; (2) regeling-acties
(aanmaken/betaling/wanprestatie/annuleren/kwijtschelden) verversten `["dashboard"]` niet → nu wel
(anders tot 30s verouderd); (3) footer "+N meer in de komende 30 dagen" kon liegen → "+N meer";
(4) query laadde volledige Case/Contact-entiteiten (selectin-fan-out) → scalar-kolomprojectie.
23 termijn-tests groen.

**3 — Mailslot-knop LIVE + env-noodslot eraf (op expliciet verzoek Arsalan).** Het bouwfase-mailslot
zat als env-var (`OUTBOUND_MAIL_LOCK`, alleen via SSH+herstart). Nu als DB-vlag in nieuwe globale
`app_config`-tabel (geen tenant_id → geen RLS, zoals interest_rates), schakelbaar via Instellingen →
E-mail. Eén chokepoint blijft: `check_outbound_lock()` leest env OF DB-vlag; de 3 verzendwegen
ongewijzigd. **Fail-safe:** `load_mail_lock` gaat bij ontbrekende rij/DB-fout op slot; geseede rij op
DICHT; stand in geheugen geladen vóór requests (single-proces backend). Env-noodslot op prod op
`false` gezet (`.env.bak-s197` als backup) → **de knop is nu de enige controle en staat op UIT**;
Arsalan zet mail zelf aan wanneer nodig. Openen vraagt bevestiging. Live geverifieerd (screenshot:
"op slot", "Openen" actief, geen server-noodslot-melding). Commits `fc151ed` + `25ec657`.

### Klus 1 (bouwblok 3) — onderzoek gedaan + aanpak MET Arsalan afgestemd (nog niet gebouwd)
Gemeten op prod: status kent feitelijk 2 waarden (afgesloten 580, nieuw 28); `workflow_statuses/
transitions/rules` alle 0 → élke statuswijziging faalt ("Status bestaat niet"), "Volgende stap"-
knoppen kapot, statusfilter leeg, auto-"betaald" vuurt nooit, `date_closed` nooit gezet, de
pijplijn→status-koppeling (S166) checkt het lege systeem en vuurt dus nooit. Pijplijn = de echte
motor (15 actieve stappen, 18 zaken erop, 10 heropende zonder stap). **Afgestemde aanpak:** status
reduceren tot 4 (Nieuw / In behandeling / Betaald / Afgesloten), pijplijn stuurt de status (bestaande
dode koppeling repareren, niet iets nieuws), auto-"betaald" + `date_closed` (met bestaande €0-guard),
Afsluiten/Heropenen-acties i.p.v. kapotte knoppen, statusfilter = 4 waarden, **+ nieuw "Stap"-filter
op de Dossiers-lijst** (Arsalans punt: kunnen filteren op sommatie/dagvaarding/vonnis — dat is de
pijplijn-stap, niet status). Lege status-engine NIET slopen (veegsessie-voorstel).

### Gewijzigde/aangemaakte bestanden
- Backend: `app/settings/models.py` (nieuw, AppConfig), `alembic/versions/s197_mail_lock.py` (nieuw),
  `app/email/service.py` (DB-vlag + fail-safe), `app/main.py` (load bij opstart),
  `app/settings/router.py` + `schemas.py` (GET/PUT mail-lock), `app/collections/service.py`
  (scalar-projectie), `tests/test_mail_lock.py` + `conftest.py`.
- Frontend: `instellingen/email-tab.tsx` (mailslot-kaart), `hooks/use-settings.ts` (mail-lock hooks),
  `(dashboard)/page.tsx` (foutstaat + footer), `hooks/use-collections.ts` (dashboard-invalidatie).
- Tooling: `scripts/codex-review.sh` (hartslag-bewaker).
- Prod: migratie s197 gedraaid (app_config geseed dicht), `.env` OUTBOUND_MAIL_LOCK=false
  (`.env.bak-s197` backup). 4 commits (`fc151ed`/`9a61399`/`f2b526b`/`25ec657`) + docs, tag sessie-197.

### Bekende issues / aandachtspunten
- Mail staat UIT via de knop; env-noodslot is eraf. Enige controle = de DB-vlag (fail-safe dicht).
- Bouwblok 3 volledig open → S198 autonoom.

### Volgende sessie
S198 = AUTONOOM (Arsalan is weg): op Opus klus 1-4 van bouwblok 3 bouwen + deployen, dan Fable-review
(subagent) + Codex code-review via `scripts/codex-review.sh`, findings verwerken. Prompt:
`docs/sessions/PROMPT-S198.md`.

## Sessie 196 (11 juli 2026, Opus — bouwblok 2 afgerond: termijn-vooruitblik + 3 proefzaken)

### Samenvatting
Sessie begon met een correctie: `PROMPT-S196.md` was geschreven vóór de C1-uitvoering op de
S195-avond en droeg de bankimport nog als open taak — Arsalan kreeg daardoor voor de derde
keer dezelfde beslisvragen. Stand gecheckt (SESSION-NOTES + Fable-hercontrole): **C1 was al
af**. Prompt kreeg een achterhaald-banner; alleen taak 2 + 3 uitgevoerd.

**Taak 2 — B4/A8 termijn-vooruitblik (LIVE, commit `42c3e4c`).** Dashboardblok "Aankomende
termijnen" in de incasso-kolom: open termijnen van actieve regelingen over álle zaken
(pending binnen 30 dagen; overdue/partial altijd, rood/geel gemarkeerd), gesorteerd op
vervaldatum, max 8 + "+N meer"-voet, klik → Betalingen-tab van het dossier. Backend:
`list_upcoming_installments` (collections-service, tenant-gefilterd, zelfde
geen-zaakstatus-filter-keuze als het regeling-alarm) + `GET /api/dashboard/upcoming-installments`
(auth). Bewust geen aparte pagina (besluit S191: alleen overzicht; 13 regelingen).

**Taak 3 — B11 proefzaken op hun stap (per zaak akkoord Arsalan).** Conform draaiboek
PLAN-heropening-werkvoorraad regel 118-120, alleen `incasso_step_id`+`step_entered_at`
gezet (guarded SQL, transactie): IN100215 → Bijhouden regeling (actieve regeling, termijn
12 juli deels betaald), IN100040 → Voorstel dagvaarding (BaseNet "Procederen?"), IN100521 →
Voorstel dagvaarding (4e sommatie). email_logs 0 vóór==ná; status bleef 'nieuw'.
Kanttekening genoteerd: draaiboek noemt IN100521 B2C, systeem zegt b2b — maakt voor de stap
niet uit, wél later voor rente/14-dagenbrief.

### Verificatie
- 23 tests groen (`test_payment_arrangements.py`, incl. 2 nieuwe: overview + tenant-isolatie);
  ruff schoon; `tsc --noEmit` + `npm run build` groen.
- Deploy backend+frontend via SSH, containers healthy.
- Live: endpoint geeft 14 termijnen die exact matchen met eerdere sessies (IN100019 gemist
  9 juli bovenaan; IN100215 partial €250 — de S195-Fable-fix zichtbaar); Playwright-doorklik
  dashboard → IN100019 Betalingen-tab: zelfde termijn "Achterstallig". Proefzaken via app-API
  bevestigd op de juiste stap.
- **Codex-tegenlezer overgeslagen:** timede na 10 min uit (S194: zelfde). Werkvorm herzien
  vóór volgende bouwsessie; diff was klein + testgedekt.

### Gewijzigde bestanden
- `backend/app/collections/service.py` (+`list_upcoming_installments`),
  `backend/app/dashboard/router.py` + `schemas.py`, `backend/tests/test_payment_arrangements.py`
- `frontend/src/app/(dashboard)/page.tsx` (widget), `docs/sessions/PROMPT-S196.md` (banner)
- prod-DB: 3 rijen `cases` (stap gezet). Commit `42c3e4c` + docs-commit, tag `sessie-196`.

### Bekende issues
- Codex-tegenlezer 2× op rij onbruikbaar (timeout) — beslissen: andere aanroepvorm of
  voorlopig uit het sessieprotocol.
- IN100521 debtor_type b2b vs draaiboek "B2C" — checken vóór er brieven/rente uitgaan.

### Volgende sessie
Bouwblok 3: B3-versimpeling (status volgt pijplijn) + A5-pauze + A3 dagstart + A7 sjablonen.
Prompt: `docs/sessions/PROMPT-S197.md`.

## Sessie 195 (11 juli 2026, Opus — grondige 1-op-1 betalingsaudit + heropenings-notities live)

### Samenvatting
Geen bouwsessie — controle op verzoek Arsalan: "is alles één-op-één overgezet, bij het juiste
dossier, kloppend met bron en bankrekening?" Alle betalingen + regelingen onafhankelijk
herberekend met de echte parser (`scripts/basenet/parse.py` + `mapping.py`) tegen de
BaseNet-export (`Xml_02-07-2026_2400.zip`) én het bankafschrift, alleen-lezen. Eén materiële
bevinding → op verzoek waarschuwingsnotities op de betrokken dossiers gezet.

### Wat gecontroleerd + resultaat
- **56 losse betaal-records (IncassoBetalingAnders):** alle 56 in Luxis, juiste dossier, juiste
  datum, 0 dubbel, 0 ontbrekend. **199 bankregel-betalingen (CashBankLine, S180):** idem, koppeling
  via `cblpcode` klopt. Totaal 255 betalingen ✅.
- **Bedragen:** 191 op de cent; **64 bewust gecapt** — Luxis rekent rente vanaf verzuimdatum → iets
  lager openstaand dan BaseNet → import capte op openstaand (S179: 17×, S180: 47×; deze audit
  reproduceert exact diezelfde aantallen onafhankelijk). Samen €6.198,46 lager geboekt dan werkelijk
  betaald. **Heropeningsrisico:** heropenen + herrekenen zonder correctie doet debiteur te weinig
  lijken te hebben betaald.
- **13 regelingen / 121 termijnen:** exact — juiste zaak, vervaldatum, bedrag; niets mist/dubbel.
  Bron heeft 323 termijnen/37 zaken; bewust alleen 121 toekomstige (vanaf 9 juli 2026) over 13 zaken
  (S179-afspraak: verleden-termijnen niet, want bron zegt niet of ze betaald zijn). Geen zaak met
  toekomstige termijnen ontbreekt.
- **Bankafschrift-kruiscontrole:** 138 credits exact geboekt; alle 57 venster-boekingen zonder exacte
  credit verklaard (gecapt óf "rechtstreeks aan cliënt" — nooit via derdengeldenrekening).
- **Correctie op de eerdere S195-indeling:** groepen B/C (36 rijen ~€48k) waren GEEN gaten — 34/36 zijn
  gewoon geboekt op het gecapte bedrag; datum+bedrag-match zag ze onterecht als "nooit geboekt". Echt
  onboekt uit B+C: alleen Saltik IN100345 (2×€50, plus 2×€50 in groep A).

### Actie op prod (op expliciet verzoek Arsalan)
- **64 dossier-notities** (`case_activities` type `note`) geschreven, één per gecapte zaak, met de exacte
  bron- vs geboekt-bedragen en de instructie "corrigeer betaalbedrag vóór herrekenen bij heropening".
  Idempotent (`[S195-audit]`-marker → NOT EXISTS-guard). Geverifieerd: 64 notities op 64 zaken, en via
  de app-API zichtbaar bovenaan de recente activiteiten van het dossier.

### Verjaringstaken IN100015/IN100127 — NIET afgevinkt
Voorwaarde Arsalan: alleen als ook in BaseNet gesloten. Bron-status was **Lopend** → taken blijven staan
(kandidaten voor heropeningsbatch).

### Gewijzigde/aangemaakte bestanden
- `docs/sessions/S195-1op1-audit.md` (nieuw — volledige bevindingen + 64-rijen gecapte-lijst)
- `docs/sessions/S195-bankimport-indeling.md` (nieuw — complete indeling 212 credits + correctie-banner)
- prod-DB: 64 rijen `case_activities` (notities). Géén code-wijziging, géén deploy.

### Bekende issues / open
- Gecapte betalingen: notitie is een handmatig vangnet. **Voorstel (niet gebouwd):** automatisch slot/
  waarschuwing bij heropening van een zaak met `[S195-audit]`-notitie.
- Kantoorrekening `NL79KNAB0606569456`: Arsalan bevestigde "ja"; stond al goed in systeem.

### C1 bankimport UITGEVOERD (zelfde sessie, ná de audit — op akkoord Arsalan)
Lisanne's werkwijze verklaarde de gaten: zij verwerkt betalingen maandelijks in BaseNet en
stort maandelijks door aan cliënten; de export (2 juli) loopt dus 1 maand achter — juli-
betalingen van debiteuren stonden nog niet in BaseNet, vandaar niet in Luxis.
- **Reconciliatie (gecorrigeerd, na eigen telfout gevonden):** van 212 afschrift-credits →
  138 exact geboekt, 39 gecapt-geboekt, **35 echt niet geboekt**. Die 35: 17 op zaken die in
  BaseNet nog Lopend waren (maar in Luxis dicht), 16 op partijen zónder Luxis-dossier, 1 al
  voldaan, 1 BaseNet-"Gereed".
- **Geboekt:** `scripts/s195_reopen_book.py --execute` → **17 betalingen (€14.922,60)** op de
  Lopend-zaken, als gewone betaling (art. 6:44, workflow-hook UIT, cap op openstaand, marker
  `[S195-heropen …]`), consistent met de 255 bestaande. **10 zaken heropend** (status afgesloten
  →nieuw) waar restant openstond; 3 die de betaling volledig afbetaalt bleven dicht; IN100547
  (al voldaan) + IN100097 (BaseNet "Gereed") overgeslagen. Saltik IN100345: 4×€50, rente-knip
  chronologisch correct.
- **Geverifieerd:** DB (17 betalingen, 18→28 open zaken) + app-API (betaling zichtbaar op
  IN100002/IN100215/IN100345). `--cleanup` beschikbaar als terugrol.
- **Bewust NIET geboekt (besluit Arsalan):** onbekende betalingen — na Fable-hercontrole
  gecorrigeerd naar **12 rijen, €21.738,96** (Donker €17.500 = "Grave/Donker", Dinc 6×€300+€100,
  Königel €1.708, Makkinga €116, Van der Hem €500); 8 eerder-als-onbekend-getelde bleken de
  bankkant van gecapte boekingen.

### Fable-hercontrole van de Opus-uitvoering (zelfde avond, op verzoek Arsalan)
Verse reconciliatie na het boeken: 138 exact + 14 S195-vol + 48 gecapt (incl. 3 van vanavond)
+ 12 onverklaard = 212 ✓. Geen dubbele boekingen (maandreeksen sluiten aan). **2 fixes:**
(1) IN100215's €250 gekoppeld aan regeling-termijn 12-07 als deelbetaling (anders vals
regeling-alarm); (2) de 3 nieuwe gecapte zaken (IN100480/532/585) kregen dezelfde
heropen-notitie als de 64 → totaal 67. Cap-verschil droogloop-vs-boeking verklaard
(openstaand per betaaldag, juridisch juist). Details: `S195-1op1-audit.md` §Fable-hercontrole.

### Volgende sessie
Bouwblok 2 restant: B4/A8 termijn-vooruitblik, B11 3 proefzaken. Prompt: `PROMPT-S196.md`.

## Sessie 194 (10 juli 2026, Opus — taak 2 + taak 3 + taak 1, alles live/klaar)

### Samenvatting
`PROMPT-S194.md` uitgevoerd: taak 2 (instellingen-blokkade + waarden), taak 3 (bankimport),
taak 1 (visuele doorklik). Ontdekking vooraf: het aparte derdengelden-veld bestónd al (model
+ scherm), dus taak 2 punt 3 was al gebouwd — alleen waarden restten.

### Taak 2 — admin-fix + instellingen-waarden (LIVE, commit `a5c4332`)
- **Root cause admin-blokkade:** `create_user`/`RegisterRequest`/`User`-model gaven standaard
  rol `medewerker`; `PUT /api/settings/tenant` eist `require_role("admin")` → Arsalans eerste
  account kon niet opslaan. Wens Arsalan: alle accounts admin. Fix: default → `admin` op alle
  drie de plekken + **migratie `s194_all_users_admin`** (idempotent, promoot bestaande users).
  Beide prod-accounts nu admin. `require_role`-mechaniek blijft (security-posture). Test toegevoegd.
  ⚠️ Bijeffect (bewust, gemeld): admin dekt ook Exact/sjablonen/workflow/user-aanmaak — prima voor 1-2-persoons.
- **Instellingen-waarden op prod gezet (ná expliciet akkoord Arsalan):** `Tenant.email` kesting@ →
  **incasso@kestinglegal.nl** (B13 vast kanaal werkt nu), BTW leeg → **NL869343610B01**.
  Derdengelden-IBAN stond al goed (NL20RABO0388506520).
- **Kantoorrekening-datafout gecorrigeerd (D-C-audit-punt):** het veld `iban` (kantoorrekening)
  bevatte óók het derdengelden-nummer → elke factuur aan een opdrachtgever vroeg betaling op de
  derdengeldenrekening. Gezet op Lisannes eigen Kesting-rekening **NL79KNAB0606569456**. ⚠️ Arsalan
  leverde `NL79KNAB060656945` (9 cijfers i.p.v. 10); via IBAN-checksum was er precies één geldige
  reconstructie (…9456) → met zijn "ja" gezet. **Nog 1× tegen bankpas checken.** Rekening-scheiding
  in de code klopt: factuur→kantoor-IBAN (2 plekken), sommatie/aanmaning/regeling→derdengelden
  (luide placeholder bij leeg, audit #61), SEPA→derdengelden.

### Taak 3 — bankimport droogloop + parser-fix (commit `19743e8`, LIVE; import zelf NIET gedaan)
- **Parser-bug gevonden + gefixt:** het echte afschrift (`CSV_A_NL20RABO0388506520`, derdengelden,
  1 jaar, 368 regels) gebruikt komma-decimaal (+1013,74); `parse_rabobank_csv` stripte komma's →
  élk bedrag 100× te hoog (droogloop-som €17,7 mln i.p.v. €176.905,81). `_parse_amount` (komma/punt/
  duizendtallen, meest-rechtse scheidingsteken = decimaal) + 3 tests met echte rij. 53 tests groen.
- **Droogloop op prod (100% alleen-lezen, echte parser+matcher):** 212 credits €176.905,81;
  **138 al geboekt** (S179/S180, exact op datum+bedrag) — ⚠️ dubbeltel-valkuil: H17-dedup ziet ze
  NIET (die boekingen liepen buiten de import-pijplijn om) → blind importeren = honderden dubbelen.
  **17 echt-nieuw** na 30 mei (€8.836), **29 gaten** op bekende maar afgesloten zaken (€43.744),
  **22 onbekende** zaken (€40.462, D-/FN-nummers). Matcher kijkt alleen naar 18 actieve zaken.
  Beslislijst 4 groepen → **C1-import samen met Arsalan.** Rapport: `docs/sessions/S194-bankimport-droogloop.md`.

### Taak 1 — visuele doorklik prod (Playwright, seidony@, niets verstuurd)
- **Follow-up "Uitvoeren" → voorbeeldvenster werkt** (B13): afzender/ontvanger/onderwerp/brief;
  afzender = **incasso@kestinglegal.nl** (bewijst afzender-fix + sluit S193-openstaand punt);
  "Versturen" grijs zonder e-mailadres. Getest op testdossier 2026-00001. Escalatie-direct-uitvoeren
  NIET geklikt (zou echte cliëntzaak muteren) — code-pad wel bevestigd.
- **Verjaring:** IN100016 rekent exact op **23-09-2026** (via API, `verjaring_basis_date` 2021-09-23
  + 5 jr); afgesloten zaak toont terecht geen badge; Mijn Taken toont de alarmen. Geen actieve zaak
  heeft nu een verjaring binnen 90 dagen → badge-render niet live te tonen (data, geen bug).
- **Dashboard/Intake niet leeg:** 18 nieuwe dossiers + 6 intake-aanvragen.
- **Instellingen opslaan werkt** (admin-fix live bewezen: tijdelijke wijziging opgeslagen + hersteld,
  geen "admin nodig"); alle waarden correct in beeld.

### Bevinding (klein, niet gefixt — akkoord nodig)
2 verweesde "VERJAARD"-taken op **afgesloten** zaken (IN100015, IN100127), aangemaakt 4 juli vóór de
S193-monitorfix. De monitor maakt ze niet meer aan (filtert nu op terminale status), maar deze twee
blijven in Mijn Taken staan tot iemand ze afvinkt. Opruimen = data-mutatie → wacht op akkoord.

### Verificatie
Backend: test_settings (8) + test_payment_matching (53) + auth/exact/role (72) groen; ruff schoon;
migratie s194 lokaal + op prod toegepast (s184→s194). 3 commits (`a5c4332`/`19743e8`/`8279a29`),
alle gepusht + backend gedeployed via SSH, containers healthy. Prod-waarden via SQL geverifieerd.
Codex-tegenlezer op de parser-diff getimed uit (5 min) → overgeslagen; parser gedekt door 3 nieuwe tests.

### Volgende sessie
Bouwblok 2 restant: C1 bankimport-proef **samen** (beslislijst in droogloop-rapport) → B4/A8
termijn-vooruitblik (alleen overzicht over zaken heen) → B11 stappen 3 proefzaken. Anders bouwblok 3.

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
