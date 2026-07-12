# S204 — Fable-review van de S203-voorkant-fixes

**Datum:** 12 juli 2026 · **Uitgevoerd door:** Fable (read-only: geen productcode, geen prod-mutatie, geen mail)
**Review-object:** 15 commits `sessie-203..sessie-203-fixes` + na-tag-commit `27842a2` (14-dagenbrief harde blokkade). Migraties `s203`/`s203b`.
**Verificatie deze sessie:** 155 tests groen (8 relevante suites, docker), `uvx ruff check backend/app/` schoon, prod `alembic_version = s203b_scheduler_heartbeat`, API-cijfers kruisgecheckt met eigen read-only SQL op prod.

**Eindoordeel: 9 van de 11 fixes bevestigd zonder voorbehoud. 2 punten gevonden die een vervolg-bouwsessie nodig hebben:**
1. een **bewezen latent defect** in het nieuwe mailsync-foutpad (één falend account blokkeert de sync van de accounts erna), en
2. de **14-dagenbrief-blokkade heeft twee open zijdeuren** (follow-up "Uitvoeren" en het AI-concept-verzendpad) plus een zwakke "verstuurd"-proxy.

---

## Per fix

### #13 Tijdlijn-crash — ✅ bevestigd
- Model heeft `date` + `duration_minutes` (time_entries/models.py:35-36); de fix leest precies die velden.
- Repo-brede grep: **geen** andere lezers van `duration_seconds`/`entry_date` op TimeEntry. (`entry_date` elders = bank-transactiemodel van payment-matching — daar hoort het.)
- Regressietest dekt het volledige API-pad (entry aanmaken → tijdlijn → 200 + "Tijdregistratie: 1:30"). 🟡 nitpick: hardcoded datum "2026-03-01" in de test (huisregel: relatieve datums).

### #4 Hernoem-knop — ✅ bevestigd
- Nieuwe PATCH-route (cases/router.py:530) gebruikt `get_case_file` die op tenant **én** case **én** is_active filtert → buiten tenant = 404. Auth verplicht.
- Tests: happy path, 404 onbekend, 422 leeg, **cross-tenant 404** (test_case_files_rename.py).
- Frontend stuurt het juiste veld; `onError` sluit nu het invoerveld, globale MutationCache toont de fout.
- 🟡 nitpick: een naam van alléén spaties passeert `min_length=1` en wordt na `.strip()` als lege naam opgeslagen — de frontend voorkomt dit al (trim-guard), backend-check zou netter zijn.

### #3 AI-concept €0-markering — ✅ bevestigd
- De vlag wordt gepopt (automation_service.py:656) **vóór** de `**context`-spread naar de promptbouwer (:666) — de eerdere leklocatie is dicht. `gather_case_context` heeft precies één productie-caller; het ai_agent-draftpad (cliënt-updates) gebruikt `get_financial_summary` helemaal niet, dus geen zusterpad met hetzelfde gat.
- De "alleen bij €-sjabloon"-conditie (:749) is letterlijk dezelfde als in de getrouwheids-poort (:263).
- End-to-end getest: markering landt in `draft.sources.fidelity_issues` én de reviewtaak krijgt ⚠-titel (test_incasso_pipeline.py::test_draft_gate_marks_amounts_fallback_on_amount_template). De monkeypatch in test_draft_amounts_fallback werkt echt (lazy import in de functie zelf).

### #6 "1169 toegevoegd deze maand" — ✅ bevestigd, ook op prod
- Uitsluiting op de import-marker; marker-constante identiek aan het importscript (`[BaseNet-import]`).
- **Prod-SQL:** 1168/1169 contacten dragen de marker; de ene zonder = "Arsalan" (echt nieuw, juli). Dashboard-API toont `contacts_this_month: 1` — klopt exact. Zaken-variant: 0 juli-zaken, dashboard 0.
- 🟡 randgeval: wist iemand deze maand handmatig de notities van een import-relatie, dan telt die weer mee (alleen relevant zolang de importmaand loopt).

### #9 Batch-foutmelding — ✅ bevestigd
- `toast.warning` bij skipped/emails_failed/errors, met max 5 redenen + "… en N meer", 10 s zichtbaar. De backend levert per overgeslagen dossier een reden (incl. de nieuwe 14-dagenbrief-redenen). Alleen code-review; visueel niet opnieuw live bekeken (S203 deed dat al).

### #10 Incasso-ratio — ✅ bevestigd
- Teller (betalingen, `is_active`, join) en noemer (hoofdsom) nu over **dezelfde** populatie: actieve niet-terminale zaken; gecapt op 100. Test dekt de kern (betaling op gesloten zaak telt niet mee; 50,0 exact). Prod: 5,3 ≤ 100 ✓.
- Kanttekening (definitie, geen fout): volledig betaalde zaken zijn terminaal en vallen uit beide kanten — de ratio meet dus alleen deelbetalingen op nog-open zaken en zal structureel laag ogen. De cap-tak zelf heeft geen directe test (leesbaar correct).

### #14 Openstaand-definities — ✅ bevestigd
- Kolomlabel "Openstaand (hoofdsom)" klopt met de backend-berekening (hoofdsom − betaald, incasso/service.py:733); negatief → "teveel betaald" in beide lijsten (zaken + incasso, kaart + tabel). Dossier-sidebar (incl. rente/BIK) bewust anders gelaten en nu door het label onderscheiden.

### #1 Mailsync-gezondheid — ⚠ punt gevonden (latent, bewezen)
**Wat klopt:** kolom + model + API + banner zijn correct bedraad; succes wist de fout (`last_sync_error = None`); commit-per-account voorkomt precies wat de reviewvraag vreesde — een geslaagde sync kan **niet** meer worden teruggerold door een latere account-fout. Prod is gezond: 3 sync-accounts vers (18:47), foutveld leeg, import-account wordt overgeslagen.

**Het defect:** in het foutpad doet de scheduler `rollback()` en dan `commit()` op alleen het foutveld (scheduler.py:257-260). Maar **`rollback()` expireert álle geladen objecten, ongeacht `expire_on_commit=False`**. Bewezen met een probe op de echte sessie-factory (dev-container):
- attribuut **zetten** + committen na rollback: werkt (het foutveld van het falende account komt dus goed in de DB);
- attribuut **lezen** van een ánder object na rollback: `MissingGreenlet`.

Gevolg-keten: account N faalt → rollback → account N+1 crasht op zijn eerste attribuutlezing (sync_service.py:467 `account.provider`) → de log-f-string in de except (scheduler.py:253) leest zélf `account.email_address` → tweede MissingGreenlet ontsnapt aan de binnenste except → de **hele run stopt** (buitenste except vangt af). Accounts ná het falende account syncen niet meer en krijgen géén eigen foutmelding; alleen de generieke "loopt achter"-banner (>60 min) verschijnt, en het dashboard-alarm blijft stil omdat de job zelf "slaagt". Bij een structureel falend account (verlopen token — het meest waarschijnlijke scenario) is dit elke 5 minuten opnieuw zo.

**Fix-voorstel (klein):** e-mailadres per account in een lokale variabele vóór de try; na de rollback de accountlijst herladen óf per account een eigen sessie gebruiken.

### #2 Scheduler-heartbeat — ✅ bevestigd, met 2 kanttekeningen
- Listener + `asyncio.ensure_future` werkt aantoonbaar in prod: 5 heartbeat-rijen met verse timestamps (email_auto_sync 18:47 etc.). Job-ids in `_CRITICAL_DAILY_JOBS` matchen de `add_job`-ids 1-op-1. Geen-vals-alarm-ontwerp (geen rij = geen alarm) getest. Dashboard-banner bedraad; prod `scheduler_alerts: []`.
- ⚠a **Morgen controleren:** de 5 dagelijkse jobs hebben nog géén rij (nog niet aan de beurt geweest sinds de deploy). Verwachting: na de nachtelijke runs verschijnen ze; blijven ze uit, dan is er iets mis met de listener op cron-jobs.
- ⚠b **Beperking (in de code erkend):** de dead-man-switch ziet "draait niet meer", níet "draait maar faalt intern". Alle jobs slikken hun eigen excepties, dus een verjaringscheck die elke nacht crasht ná de start telt gewoon als run. Het S200-scenario is daarmee half afgedekt. Voorstel: in de job-except zelf óók `last_error` zetten (kleine wijziging per job of via een decorator).
- 🟡 fire-and-forget task zonder referentie kan in theorie door GC verdwijnen → hooguit een zeldzame gemiste heartbeat (onschadelijk bij 25u-drempel, kán één vals alarm op een dagelijkse job geven).

### #8 Intake-startstap — ✅ bevestigd
- Het nieuwe blok is regel-voor-regel gelijk aan het normale creatiepad (cases/service.py:584-606): zelfde debtor_type-filter, zelfde `min(sort_order)`, zelfde `trigger_type="auto"`; `move_case_to_step` is de enige bron van historie + status (werk-stap → `in_behandeling`, consistent met de rest). Test dekt de goedkeurflow.
- Prod: nog geen intake-goedkeuring sinds de deploy (case_step_history staat prod-breed nog op 0), dus alleen test-bewijs — verwacht.

### #5 14-dagenbrief harde blokkade — ✅ de batch-gate zelf, ⚠ drie punten eromheen (JURIDISCH)
**Wat klopt:** de gate in `batch_execute` (incasso/service.py:1255-1272) dekt beide condities (geen dagenbrief-spoor → blok; < 15 dagen → blok), staat vóór beide render-routes (e-mail én DOCX/PDF), geldt alleen voor b2c, zondert de dagenbrief-stap zelf uit, en meldt redenen niet-stil in de errors-lijst (die de nieuwe #9-toast toont). Tests dekken blok/doorlaat(20d)/te-vroeg(5d). De defaultpijplijn heeft geen stap vóór de dagenbrief die B2C zou over-blokkeren.

**⚠ Zijdeur 1 — Follow-up "Uitvoeren" (grootste risico):** `execute_recommendation` (ai_agent/followup_service.py:359, plus approve-and-execute:580) rendert en **verstuurt** exact dezelfde stap-sommaties, zonder enige gate — het bestand bevat nul verwijzingen naar compliance/dagenbrief/b2c. Op prod staan 14 pending aanbevelingen. Een B2C-zaak die (handmatig) op een sommatie-stap staat → "Uitvoeren" → sommatie de deur uit zonder 14-dagenbrief-check. Dit is de "tweede deur" waar de reviewprompt naar vroeg.

**⚠ Zijdeur 2 — AI-concept-verzendpad:** concepten worden verstuurd via `POST /api/email/compose/send` + `POST /api/incasso/cases/{id}/advance-after-send` (incasso/router.py:359) — geen van beide kent de gate. Relevant: op prod hebben alleen "Eerste sommatie", "Tweede sommatie" en "Verzoekschrift faillissement" een batch-sjabloon; álle andere stap-brieven (o.a. Derde sommatie) lopen per definitie via dit concept-pad.

**⚠ Proxy-zwakte — `entered_at` is binnenkomst, niet verzending:** een dossier komt bij creatie al op de dagenbrief-stap (T0) terwijl de brief pas bij een latere batch-run echt uitgaat (T1). De gate rekent vanaf T0 → elke dag tussen T0 en T1 is een dag die de sommatie te vroeg kan. Erger: wie een zaak via "Verplaats naar stap" of handmatig dóór de dagenbrief-stap schuift zonder ooit iets te versturen, voldoet aan de gate. Sterker anker bestaat al: `advance-after-send` zet `email_sent` op de historierij (en er is EmailLog/GeneratedDocument); het batchpad zet die vlag nu níet (`mark_current_step_communication_sent` ontbreekt daar) — dat moet mee in dezelfde fix.

**Operationeel gat (geen S203-fout):** Luxis kan op prod momenteel géén 14-dagenbrief versturen: de stap heeft `template_type = NULL` en geen e-mailsjabloon, terwijl het codesjabloon bestaat (email/incasso_templates.py:631). De enige 2 actieve B2C-zaken (IN100345, IN100350) staan bovendien stap-loos zonder historie → vandaag kan er via de batch óók geen te-vroege sommatie uit (eerdere "geen pipeline stap"-skip), dus geen acuut risico — maar zodra Lisanne B2C echt gaat draaien moet óf de stap een sjabloon krijgen, óf de buiten-Luxis-brief handmatig geregistreerd worden.

**Informatief:** `pre_send_compliance_check` leest nu het echte spoor, maar het endpoint heeft nog steeds geen enkele UI-caller (S200 #16-lijst) — de bescherming zit uitsluitend in de batch-gate.

### #16 Logout + #17 Gmail-knop — ✅ bevestigd
- `POST /api/auth/logout` bestaat (204, trekt álle refresh-tokens van de gebruiker in, auth verplicht); frontend roept hem aan **vóór** de lokale opschoning (juiste volgorde: token nog geldig) en faalveilig (catch → lokaal opruimen gaat altijd door). Login op prod zelf gedaan (werkt). Live uitloggen bewust niet getest: dat zou de refresh-tokens van het seidony-account op prod intrekken (mutatie).
- Gmail-knop weg uit Instellingen→E-mail; tekst aangepast; backend-OAuth-route bewust behouden als herstelpad (gedocumenteerd in de code).

---

## Niet geverifieerd deze sessie (eerlijk vermeld)
- Frontend visueel (banners, warning-toast, "teveel betaald" op het scherm): alleen code gelezen + S203's eigen live-check; niet opnieuw doorgeklikt.
- Dagelijkse heartbeat-rijen: bestaan pas na de eerstvolgende nachtelijke runs (→ checklist morgen).
- Intake-fix op prod-data: nog geen intake goedgekeurd sinds deploy (alleen testbewijs).
- Live logout op prod (bewust, zie #16).

## Beslislijst voor de vervolg-bouwsessie (S205)
| # | Wat | Ernst | Omvang |
|---|---|---|---|
| 1 | 14-dagenbrief-gate óók in follow-up `execute_recommendation` (zelfde helper hergebruiken) | 🔴 juridisch | S |
| 2 | Gate in het AI-concept-verzendpad (advies: in `advance-after-send` + compose-met-draft, vóór verzending) | 🔴 juridisch | S/M |
| 3 | Verzend-proxy verstevigen: echt verzendspoor (email_sent-vlag/EmailLog) i.p.v. `entered_at`; batchpad moet dan ook `mark_current_step_communication_sent` aanroepen | 🟠 juridisch | M |
| 4 | Mailsync-foutpad: accounts herladen na rollback of eigen sessie per account (+ e-mailadres in lokale variabele) | 🟠 | S |
| 5 | 14-dagenbrief verstuurbaar maken: `template_type='14_dagenbrief'` op de stap (sjabloon bestaat al) — of expliciet besluiten: buiten Luxis + handmatige registratie | 🟠 besluit Arsalan/Lisanne | XS |
| 6 | Heartbeat: `last_error` ook zetten als een job intern faalt (per-job of decorator) | 🟡 | S |
| 7 | Checklist: staan er morgen dagelijkse-job-rijen in `scheduler_heartbeat`? | 🟡 | check |
