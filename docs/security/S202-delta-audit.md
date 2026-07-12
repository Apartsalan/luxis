# S202 — Security- & consistentie-audit van de delta sinds S183

**Datum:** 12 juli 2026 · **Model:** Fable + Sol Ultra (read-only) · **Scope:**
`git diff sessie-183..HEAD` (49 commits, 122 bestanden, +6843/−3956). **Status:** alle 7
blokken afgerond; Blok 2 (mailpad) is op 12 juli door Sol Ultra afgemaakt met code-, test-
en read-only productiebewijs.

Alle bevindingen zijn onderbouwd met bewijs uit de audit (code-regel, gerichte test of
read-only prod-query). Alleen dit rapport is bijgewerkt: geen productcode of productiedata is
gewijzigd. Tijdens de hervatte verificatie is geen mail verstuurd; dat is voor de eerdere,
afgebroken auditrun niet afzonderlijk achteraf te bewijzen. Fixen gebeurt later.

---

## Samenvatting op ernst

| Ernst | # | Kort |
|---|---|---|
| Kritiek | 0 | — |
| Hoog | 3 | Cross-tenant CaseFile-lek bij mailbijlage-opslag · 2× fail-open op "betaald"-guard · "Geïnd"-rapportage telt verwijderde betalingen |
| Middel | 5 | Bulk-status zonder lengtecap · auto-advance zonder terminale-stap-check · app als DB-superuser · opgeslagen dossierdata ongeëscapet in systeemmail-HTML · ontvangers niet centraal/cap-gelimiteerd |
| Laag | 5 | Settings-GET niet admin-only · collection_rate via float · base64-bijlagecaps te laat · mailslotcache vóór commit · logvervalsing via gevouwen mailheaders/bestandsnaam |
| Info | 4 | Globaal mailslot zonder tenant_id · adressen/onderwerpen/bestandsnamen in prod-logs · `.codex/config.toml` leesbare sleutels (lokaal) · PowerSearch cosmetische punten |

**Grote geruststellingen (geverifieerd OK):** RLS op prod is compleet en zonder drift
(44/44 tenant-tabellen FORCE + policy, alleen `users` bewust uitgezonderd). Geen secrets in
de repo of de delta-diff. Frontend-bundle bevat geen `NEXT_PUBLIC_*`-sleutels. PowerSearch
is injectie-veilig en tenant-gescoped. De bulk-status- en pipeline-batch-paden zijn
tenant-gescoped in de query zelf. Alle drie applicatiemailtransporten blokkeren op het
mailslot; prod stond tijdens de controle effectief dicht.

---

## Blok 1 — Nieuwe/gewijzigde endpoints (auth / rol / tenant)

Route-diff `sessie-183..HEAD`: 7 nieuwe endpoints, alle achter minimaal `get_current_user`.
Geen enkele in-scope route is onbedoeld publiek. Details per subagent geverifieerd op
bestand:regel.

### H1 (HOOG) — Cross-tenant CaseFile bij mailbijlage → dossier
`backend/app/email/sync_router.py:527-581` (`save_attachment_to_case`,
`POST /attachments/{attachment_id}/save-to-case/{case_id}`).
De bijlage zelf wordt tenant-gescoped opgehaald (regel 539-547), maar `case_id` uit de URL
wordt **nooit tegen `tenant_id` gecontroleerd** vóór het aanmaken van de `CaseFile` (regel
570-572). Ditzelfde bestand heeft de guard elders wél (`_assert_case_in_tenant` in
`sync_service.py:978-999`, aangebracht als eerdere audit-fix voor `link_email_to_case`).

- **Faalscenario:** gebruiker van tenant A kent/raadt een `case_id` van tenant B → er ontstaat
  een `CaseFile` met `tenant_id=A`, `case_id` wijzend naar een zaak van B, en het bestand
  belandt in pad `CASE_FILES_UPLOADS_BASE/A/<case_id-van-B>/…`. Schending van referentiële
  tenant-integriteit.
- **Fix (~5 regels):** vóór stap 3 `await _assert_case_in_tenant(db, user.tenant_id, case_id)`
  (of een `select(Case).where(Case.id==case_id, Case.tenant_id==user.tenant_id)`), 404 als de
  zaak niet bij de tenant hoort.

### M1 (MIDDEL) — Bulk-status: geen lengtecap
`backend/app/cases/schemas.py:130` (`CaseBulkStatusUpdate.case_ids: list[uuid.UUID]`), verwerkt
in `cases/router.py:186-216` met één DB-call per item.
Geen `Field(max_length=...)`. Elke iteratie is zelf tenant-gescoped (via `get_case`), dus
niet-destructief, maar een lijst van tienduizenden UUID's = lange transactie/lock → DoS-vector.
- **Fix (1 regel):** `max_length=200` (consistent met de `per_page`-cap `le=200` elders).

### L1 (LAAG) — Settings-GET's niet admin-only
`backend/app/settings/router.py:30-33,48-54`: `GET /api/settings/mail-lock` en
`GET /api/settings/tenant` gebruiken alleen `get_current_user`, terwijl `docs/security/rollen.md:44`
"Instellingen = admin ✅, advocaat ❌, medewerker ❌" stelt. De **schrijf**-routes (PUT) zijn
wél correct `require_role("admin")` (regel 36-45, 57-64). Read-only, geen PII, geen direct
risico — wel een afwijking van de gedocumenteerde matrix.
- **Fix (keuze):** ofwel rollen.md nuanceren ("schrijven = admin, lezen = alle rollen"),
  ofwel de GET's ook achter `require_role("admin")`. Productbeslissing, niet chirurgisch fixen.

### Geverifieerd OK (Blok 1)
- `PUT /api/cases/bulk/status` — elke `case_id` via `get_case(db, tenant_id, case_id)`
  (tenant-gescoped), `new_status` gevalideerd tegen `CASE_STATUSES`, elke wijziging schrijft
  een `CaseActivity` audit-record (`cases/service.py:698-792`).
- `PUT /api/settings/mail-lock` — correct `require_role("admin")`; env-hard-lock blijft leidend.
- `GET /api/email/all` — filtert altijd op `SyncedEmail.tenant_id`; zoekterm via `ilike()`-param
  (geen SQLi) (`sync_service.py:893-943`).
- `GET /followup/{rec_id}/preview` — recommendation + case + step alle drie tenant-gefilterd,
  verstuurt niets (`followup_service.py:593-628`).
- `POST /intake/from-email/{email_id}` — tenant-gescoped, idempotent, audit-velden gezet.
- `GET /dashboard/upcoming-installments` — leaf-tabel `PaymentArrangementInstallment` op
  `tenant_id` gefilterd (`collections/service.py:953-998`).
- `compose_router.py` — alle 4 endpoints valideren `Case.tenant_id`; dossierbijlagen op
  `CaseFile.tenant_id`+`case_id`. De bestaande 3 MB- en 10-bijlagencaps staan er, met de
  volgorde-beperking uit L4. Ontvangervalidatie is niet overal gelijk (zie M5).
- `documents/router.py` — elke `case_id`/`document_id` tenant-gefilterd; `html_to_pdf` via
  `_data_only_url_fetcher` (alleen `data:`-URI's) → SSRF/LFI gemitigeerd.
- `incasso/router.py` move-step/batch — `Case` geladen met `tenant_id`-filter, batch-`case_ids`
  altijd via `Case.tenant_id == tenant_id`.
- `dependencies.py:19-93` — token-type-check, UUID-validatie op `sub`/`tenant_id`,
  `require_role` → 403 bij onvoldoende rol.

---

## Blok 2 — Mailpad (S185-S187) — afgerond

Scope: het volledige uitgaande applicatiemailpad vanaf de routes en systeemtaken tot aan de drie
transporten: generieke SMTP, Outlook Graph en IMAP/SMTP. Bewijs bestaat uit
de actuele code, git-commit `8b658c7`, gerichte lokale probes, de bestaande regressietests
en read-only prod-SQL. Er is geen mail verstuurd.

### M4 (MIDDEL) — Opgeslagen dossierdata kan HTML injecteren in systeemmails
`backend/app/documents/docx_service.py:344-438` bouwt de e-mailcontext rechtstreeks uit
contact-, dossier- en vorderingsvelden. `backend/app/email/incasso_templates.py:123-145`
markeert vervolgens de volledige samengestelde inhoud als vertrouwde `Markup`, terwijl onder
meer omschrijving en factuurnummer ongeëscapet met f-strings worden ingevoegd
(`:168-175,356-365`). Hetzelfde patroon staat in `invoices/service.py:615-620` en
`followup_service.py:476-495`. Jinja's auto-escaping wordt daarmee bewust gepasseerd.

- **Meetbewijs:** een lokale renderprobe met de fictieve cliëntnaam `<b>INJECTED</b>`
  leverde letterlijk die tag in de HTML op; `&lt;b&gt;` kwam niet voor.
- **Prod-stand:** een read-only telling vond **0** hoekhaken in de gecontroleerde naam-,
  adres-, plaats-, dossierkenmerk-, dossieromschrijving-, vorderingsomschrijving- en
  factuurnummervelden. Er is dus geen aangetoonde actuele besmetting.
- **Faalscenario:** geïmporteerde of handmatig opgeslagen tekst kan de opmaak/inhoud van een
  uitgaande juridische systeemmail veranderen, bijvoorbeeld een misleidende link of verborgen
  tekst toevoegen. Scriptuitvoering bij de ontvanger hangt van diens mailclient af en is
  **niet geverifieerd**; inhoudsintegriteit is al zonder scriptuitvoering geraakt.
- **Fix-recept:** escape alle data-afkomstige tekst op de grens van de systeemmailrenderer en
  markeer alleen de eigen vaste HTML-fragmenten als vertrouwd. Laat vrije, door de gebruiker
  gemaakte mail-HTML ongemoeid. Voeg een regressietest toe met naam, kenmerk, omschrijving en
  factuurnummer met HTML-tekens. **Omvang:** klein/middel (renderer + tests).

### M5 (MIDDEL) — Ontvangers worden niet centraal gevalideerd of begrensd
De vrije compose-route valideert syntactisch via `_EMAIL_RE`, maar `ComposeRequest.to/cc`
hebben geen maximale lijstlengte (`compose_router.py:89-121`); een lokale schema-probe
accepteerde 10.000 ontvangers. Andere systeempaden hebben soms alleen `max_length=320` en
geen formaatcheck (`documents/schemas.py:170-186`, `compose_router.py:124-131`). De centrale
service accepteert één ruwe `to: str`
(`send_service.py:95-116`) en dwingt geen normalisatie, adreslimiet of bestemmingbeleid af.
De compose-sendroute heeft ook geen route-specifieke rate-limit.

- **Meetbewijs prod:** **39 van 894** gevulde contactadressen bevatten een komma/witruimte en
  meer dan één `@`. Gesplitst zijn dit **83** afzonderlijke, syntactisch geldige adressen.
  Aan zulke contacten hangen **27** dossiers totaal, waarvan **1 actief**. `email_logs` bevatte
  tijdens de meting in totaal **0 rijen**, dus ook geen bewezen eerdere meervoudige verzending.
- **Faalscenario:** hetzelfde opgeslagen veld kan door SMTP als meerdere ontvangers worden
  geïnterpreteerd, terwijl Outlook Graph het als één ongeldig adres kan weigeren. Dat
  providerverschil is uit de payloadopbouw afgeleid en **niet extern verstuurd/geverifieerd**.
  Een gecompromitteerde ingelogde sessie kan bovendien zonder recipient-cap een grote externe
  lijst aanbieden. Alle rollen mogen volgens `docs/security/rollen.md` dagelijks mailen; dat
  deel is dus geen rollenafwijking.
- **Fix-recept:** één centrale parser/validator vóór elk transport, één canonieke opslagvorm
  (één adres per waarde of expliciete lijst), een redelijke recipient-cap en route-rate-limit.
  Reinig de 39 bestaande velden pas in een aparte, gecontroleerde datamigratie.
  **Omvang:** middel (schema's, service, tests en aparte datacorrectie).

### L4 (LAAG) — Base64-bijlagecaps worden pas na volledig decoderen afgedwongen
`InlineAttachment.data_base64` is onbegrensd; de code decodeert elk item volledig en controleert
daarna pas 3 MB en na de hele lus pas maximaal 10 bijlagen
(`compose_router.py:83-86,207-228`). De reverse proxy begrenst de totale request op 55 MB,
waardoor dit geen onbeperkte DoS is, maar een ingelogde gebruiker kan wel onnodige piekbelasting
veroorzaken.
- **Fix:** cap de lijst in het schema en weiger op base64-lengte vóór decoderen; behoud de
  bestaande controle op gedecodeerde bytes. **Omvang:** klein + regressietest.

### L5 (LAAG) — Mailslotcache wijzigt vóór de request-commit
`email/service.py:73-86` doet `flush()` en zet daarna de procesglobale
`_db_mail_locked`; de requestdependency commit pas later. Mislukt die commit na een unlock,
dan kan het geheugen open blijven terwijl de DB nog dicht staat, totdat een restart of volgende
toggle de waarden weer gelijk trekt.
- **Beperking:** de trigger is smal en prod draait aantoonbaar met één Uvicorn-worker; de
  afwijkende toestand zelf heeft echter geen tijdslimiet. Er is geen verzending aangetoond.
- **Fix:** wijzig de cache pas na succesvolle commit of herlaad bij rollback. **Omvang:** klein.

### L6 (LAAG) — Gevouwen mailheaders/bestandsnaam kunnen logregels vervalsen
De compat32-mailparser die de IMAP-code werkelijk gebruikt behoudt CR/LF in geldige gevouwen
`Subject`- en `Message-ID`-headers. Onderwerpen komen op INFO in
`email/sync_service.py:586,848`; Message-ID op `:750`. Bestandsnamen komen vooral in
warning/error-logs, onder meer op `:442`. Een lokale loggingprobe produceerde met zo'n gevouwen
waarde twee fysieke logregels. Dit voert geen code uit, maar kan containerlogs misleidend maken.
- **Fix:** vervang CR/LF/NUL door spaties vóór loggen en vóór bestandsnaamvorming; log waar
  mogelijk stabiele IDs. **Omvang:** klein + regressietest.

### I2 (INFO) — Adressen, onderwerpen en bestandsnamen in INFO-logs
Er zijn geen tokens, wachtwoorden of mailbodies in de gecontroleerde logger-calls gevonden.
Wel loggen onder meer `sync_service.py:485,586,762-767,848-850`, `send_service.py:189-212`,
`service.py:145`, `providers/imap_provider.py:289,431,615`, `providers/outlook.py:377`,
`oauth_router.py:219`, `oauth_service.py:240-310`, `auth/router.py:224-249` en
`workflow/scheduler.py:208-212` adressen, onderwerpen of bestandsnamen. De actuele
prodcontainer bevatte bij de hermeting **417** adresbevattende "Sync klaar"-regels. Dat is persoonsgegevens-
en metadataretentie in containerlogs.
- **Advies:** maskeer adressen en onderwerp/bestandsnaam op INFO; zet detail alleen tijdelijk
  op DEBUG met beperkte retentie.

### Geverifieerd OK (Blok 2)
- **Applicatiemailslot compleet:** generieke SMTP controleert in `email/service.py:89-111`, Outlook
  vóór `/sendMail` in `providers/outlook.py:300-365`, en IMAP/SMTP vóór verzending in
  `providers/imap_provider.py:535-568`. Het hostscript `scripts/setup-uptime-monitoring.sh:34`
  kent daarnaast een los `mail`-alarm buiten de app en buiten het mailslot. De cron staat op prod,
  maar het `mail`-commando ontbreekt daar; dit pad kan nu dus geen alertmail versturen.
- **Prod effectief dicht:** `app_config.outbound_mail_locked=true`, precies één configrij;
  env `OUTBOUND_MAIL_LOCK=false`. De effectieve OR-logica blijft dus dicht.
- **Regressietests:** in de backendcontainer:
  `python -m pytest tests/test_mail_lock.py tests/test_imap_send.py -q -p no:cacheprovider`
  → **26 passed, 1 warning**. De transports waren gemonkeypatcht/geblokkeerd; er is geen mail
  verstuurd.
- **Header-/IMAP-injectie:** commit `8b658c7` laat `_imap_quote` CR/LF/NUL verwijderen.
  Python `EmailMessage` weigert CR/LF in `Subject`, `To` en de uiteindelijke `From`-
  header. Foldernamen zijn interne constanten.
- **Mailbox read-only:** bronmappen worden met `readonly=True` geopend
  (`imap_provider.py:293,369,423`). Repo-breed zijn geen `STORE`, `DELETE`, `EXPUNGE`,
  `COPY` of `MOVE` gevonden; alleen de bedoelde `APPEND` naar Verzonden na SMTP-succes.
- **Credentials versleuteld:** OAuth- en IMAP-geheimen gaan via Fernet in
  `email/token_encryption.py` en `oauth_service.py`. Prod-ciphertexts waren voor 3 echte
  accounts minimaal 100 bytes. De ene korte `provider='import'`-waarde is aantoonbaar de
  vaste BaseNet-importplaceholder en wordt niet door de scheduler geselecteerd.
- **Menselijke verzendpoort:** follow-up/classificatie voert alleen uit na een expliciete,
  geauthenticeerde approve/execute-request; batchverzending is eveneens expliciet. Er is geen
  automatische antwoordcaller gevonden. De AI-tool `email_compose` is dormant: geen
  productie-instantiatie/caller gevonden (en de handler mist nu het verplichte `attachments`).
- **Rolmatrix:** alle normale compose-/sendroutes eisen authenticatie. Dat alle drie rollen
  dagelijkse mail mogen verzenden is conform `docs/security/rollen.md`, niet per ongeluk publiek.
  `/api/auth/forgot-password` is bewust publiek, rate-limited en gebruikt hetzelfde mailslot.

---

## Blok 3 — PowerSearch (S198) — geen crit/hoog/middel

Geen enkele hoge bevinding. Volledig injectie-veilig en tenant-gescoped.

### Geverifieerd OK
- `search/service.py:109-113,213-217` — tsquery via `websearch_to_tsquery(..., bindparam(...))`,
  echte bind-parameter, geen string-interpolatie. `websearch_to_tsquery` gooit geen syntax-fout
  op vrije tekst → geen crash-DoS.
- Elke deelquery (cases/contacts/documents/invoices/emails) filtert op `tenant_id`
  (`service.py:39,74,125,150,234,263`).
- `router.py:17-18` — `q` `min_length=1, max_length=200`, `limit` `ge=1,le=50`.
- `ts_headline` alleen over al-gematchte rijen + `func.left(...,5000)` → CPU begrensd.
- `extract.py:11,31` — `MAX_EXTRACTED_TEXT_LENGTH = 200_000` + NUL-byte-strip.
- `backfill_extracted_text.py:32-67` — loopt per tenant, filtert SELECT én UPDATE op
  `tenant_id`; draait als superuser (RLS-bypass by design) maar zonder cross-tenant pad.
- Frontend `command-palette.tsx` — resultaten als JSX text-children (React escaped),
  geen `dangerouslySetInnerHTML` → geen XSS via zoekterm/snippet.

### Info (niet urgent)
- `service.py:31` ILIKE-pad escaped `%`/`_` niet → brede matches (UX, geen datalek).
- Geen route-specifieke rate-limit op `/api/search` (app-breed, niet PowerSearch-specifiek).
- PowerSearch kent geen per-dossier ACL: elke rol binnen de tenant doorzoekt alles. Dit klopt
  met `rollen.md` (dagelijks dossierwerk = alle 3 rollen); geen nieuw gat t.o.v. de rest van
  de app. Aparte productbeslissing als per-dossier vertrouwelijkheid ooit nodig is.

---

## Blok 4 — RLS-drift op prod — GEEN DRIFT (geverifieerd op de prod-DB)

Prod-query (`docker compose exec db psql`, read-only) over `pg_class` + `pg_policies` +
`information_schema.columns`, 12 juli 2026:

- **44 tabellen met `tenant_id`** — alle 44 hebben `relrowsecurity=t`, `relforcerowsecurity=t`
  én ≥1 policy. `case_step_history` en `step_transitions` hebben er 2. **Geen enkele
  tenant-tabel zonder RLS.**
- **`users`** — bewust `rls=f` (gedocumenteerde uitzondering, `app/security/rls.py`).
- Zonder `tenant_id` en zonder RLS (correct): `app_config`, `interest_rates`, `tenants`,
  `alembic_version`. `interest_rates` is per ontwerp globaal; `app_config` idem (zie I1).
- Nieuwe tabellen sinds S183: `payment_arrangements`, `payment_arrangement_installments`,
  `app_config`. De twee payment-tabellen hebben RLS+FORCE+policy ✅. `s199_powersearch` voegde
  alleen kolommen toe aan bestaande tenant-tabellen (`case_files`, `synced_emails`) — al gedekt.
- Alembic-stand prod: `s199_cleanup_workflow_engine` (= HEAD). Geen achterstallige migratie.

---

## Blok 5 — Rollen-realiteit (S194: alle accounts admin)

Prod-query, 12 juli 2026:
- **2 gebruikers**, beide `role=admin`, beide `is_active=t`, beide tenant
  `00000000-…-0001`: `lisanne@kestinglegal.nl` en `seidony@kestinglegal.nl`.
- De rollen `advocaat`/`medewerker` bestaan in de code (`ROLES`) maar zijn **nergens in gebruik**.
  De 22 `require_role("admin")`-routes zijn dus vandaag niet onderscheidend (iedereen is admin).
- Zodra ooit een `medewerker`-account wordt aangemaakt, geldt de matrix in `rollen.md` — met de
  afwijking uit L1 (settings-GET's staan open voor alle rollen).

### M3 (MIDDEL) — App verbindt als DB-superuser; RLS hangt volledig aan `SET ROLE`
Prod: `DATABASE_URL` gebruikt rol `luxis` (`rolsuper=t`, `rolbypassrls=t`). RLS wordt afgedwongen
doordat de middleware per request `SET LOCAL ROLE luxis_app` doet (`middleware/tenant.py:49,93`;
`luxis_app` = non-super, geen bypassrls — geverifieerd op prod). Dit is de bekende "Fase 2 nog
open" uit `reference_rls_enforcement.md`.
- **Faalscenario:** elk DB-pad dat de request-middleware níét doorloopt (achtergrondtaken,
  scripts, een toekomstige route die `get_db` omzeilt) verbindt als superuser → RLS staat dan
  volledig uit. De backfill- en sync-scripts vangen dit nu op met handmatige `tenant_id`-filters,
  maar dat is een discipline-afhankelijke vangnet, geen structurele grens.
- **Fix (grote klus, bewust uitgesteld):** de app laten verbinden als `luxis_app` i.p.v. `luxis`
  (Fase 2). Tot dan: elke niet-request-context expliciet tenant-filteren (staat al zo in de
  bestaande scripts).

---

## Blok 6 — Secrets-sweep — repo schoon; één lokaal aandachtspunt

### Geverifieerd OK
- **Repo + delta-diff:** geen echte API-sleutels/private keys/wachtwoorden toegevoegd. De enige
  hit (`password="Wachtwoord12345"`) staat in `backend/tests/test_settings.py` — testfixture.
- **CI** (`.github/workflows/ci.yml:85`): `ANTHROPIC_API_KEY=sk-ant-ci-test-fake-key-not-real`
  — expliciet nep.
- **Frontend-bundle/prod-env:** geen `NEXT_PUBLIC_*`-sleutels; prod-frontend-container heeft
  alleen `BACKEND_URL` + Node-defaults. Alle AI/externe calls lopen server-side ✅.
- **Prod-backend-env:** secrets (`ANTHROPIC_API_KEY`, `SMTP_PASS`, `SECRET_KEY`,
  `TOKEN_ENCRYPTION_KEY`, Google/Microsoft-secrets) staan in de container-env, niet in code ✅.
- **Prod-logs (laatste 2000 regels):** geen API-sleutels/tokens/wachtwoorden. Wel e-mailadressen
  (zie I2).

### I3 (INFO) — `.codex/config.toml` bevat leesbare sleutels (lokaal, niet in repo)
`.codex/config.toml` bevat plaintext `OPENAI_API_KEY`, `MILVUS_TOKEN`, `X-Goog-Api-Key`. **Anders
dan eerdere sessienotities suggereren, staat het bestand nu wél in `.gitignore`** (regel 91:
`.codex/`, en expliciet `.codex/config.toml`) — `git check-ignore` bevestigt: genegeerd, niet
getrackt. Risico is dus beperkt tot de lokale dev-machine, niet de repo/prod. Aanbeveling: deze
sleutels roteren als de machine ooit gedeeld/gecompromitteerd is, en overwegen ze naar
omgevingsvariabelen te verplaatsen.

---

## Blok 7 — Stil falen op de geldpaden (delta sinds S183)

### H2 (HOOG) — Fail-open op de "betaald"-guard
`backend/app/cases/service.py:744-747` (`update_case_status`, óók via bulk-status) én
`backend/app/incasso/service.py:479-490` (`move_case_to_step`, handmatig + batch).
Beide vangen **elke** exceptie van `get_case_outstanding()` op met
`except Exception: outstanding = Decimal("0")` ("fail-open: nooit blokkeren op een rekenfout").
Dat is juist de guard die moet voorkomen dat een dossier mét saldo op "betaald" komt.
- **Faalscenario:** dossier €10.000 open, `interest_type="government"` zonder geseede
  `InterestRate`-rijen → `calculate_case_interest()` gooit `ValueError`. Lisanne zet het dossier
  (of 50 via bulk) op "betaald" → exception geslikt, outstanding wordt €0, dossier sluit stil met
  €10.000 open en verdwijnt uit de werkvoorraad, geen foutmelding.
- **Referentie:** `workflow/hooks.py:49-55` doet het correct (bij exceptie `return None` → sluit
  níét af). Die inconsistentie is de kern.
- **Fix (~4 regels × 2):** fail-closed — bij exceptie `BadRequestError("Kan openstaand saldo niet
  berekenen — probeer opnieuw")` i.p.v. €0 aannemen.

### H3 (HOOG) — "Geïnd"-rapportage telt verwijderde betalingen
`backend/app/dashboard/reports_service.py:62-68` (`get_kpis`, "Geïnd") en `:220-230`
(`get_monthly_stats`). Beide sommeren `Payment.amount` **zonder** `Payment.is_active.is_(True)`.
`delete_payment()` (`collections/service.py:480-496`) soft-delete't (`is_active=False`, rij blijft).
Elke andere Payment-som (`list_payments`, `_refresh_case_financials`) filtert wél op `is_active`
(geverifieerd: `collections/service.py:184`).
- **Faalscenario:** €5.000 op verkeerd dossier geboekt en dezelfde dag verwijderd. Het dossier
  toont €0 (correct), maar Rapportages "Geïnd deze periode" + de maandgrafiek blijven die €5.000
  voor altijd meetellen.
- **Fix (1 regel × 2):** `Payment.is_active.is_(True)` toevoegen aan beide sommen.

### M2 (MIDDEL) — Auto-advance mist terminale-stap-check
`backend/app/incasso/service.py:1070-1151` (`_try_auto_advance`) i.c.m. `:479` (saldo-guard alleen
actief bij `trigger_type in ("manual","batch")`, overgeslagen voor `"auto_advance"`).
`_try_auto_advance` checkt niet of de volgende stap `is_terminal`/`is_hold_step` is. Het commentaar
neemt aan "auto-paden sturen nooit naar een terminale eindstap", maar dat wordt nergens afgedwongen.
Vandaag houdt het toevallig stand (de stap vóór "Betaald" heeft geen `template_type`).
- **Faalscenario:** iemand maakt via de ongerestricte pipeline-step-CRUD een terminale stap mét
  `template_type` vlak vóór "Betaald", of herordent stappen → een batch-verzending/follow-up-advies
  schuift een dossier mét saldo automatisch naar "betaald", zonder énige saldo-check.
- **Fix:** ofwel de `trigger_type`-uitzondering in `move_case_to_step` verwijderen (saldo-check bij
  élke poging naar "betaald"), ofwel in `_try_auto_advance` `if next_step.is_terminal or
  next_step.is_hold_step: return False`.

### L3 (LAAG) — collection_rate via float
`reports_service.py:71-73`: `float(total_collected / total_principal * 100)` — Decimal→float vóór
weergave. Alleen een weergavepercentage, niet geboekt. Stijlafwijking van "ALL money = Decimal".

### Geverifieerd OK (Blok 7)
- `collections/interest.py` — Decimal-discipline consistent (`ROUND_HALF_UP` via `_round2`, geen
  float/kale `round()`); S183-clamps goed onderbouwd.
- `collections/service.py:280-291` (`create_payment`) — overbetaling gooit hard `BadRequestError`
  tenzij expliciet `cap_to_outstanding=True` (alleen derdengelden/bankimport); geen stille cap.
- `collections/service.py:1101-1139` (`_reopen_case_if_no_longer_paid`) — geen try/except om
  `get_case_outstanding`; exceptie propageert (fail-closed).
- Installments/termijnen (`service.py:856-1056`) — Decimal overal, `min()`/`max()`-guards tegen
  negatieve restanten; niet-matchende betaling blijft als Payment geboekt (geen data-verlies).
- `ai_agent/csv_parsers.py` (bankimport, S194-fix) — niet-parsende rijen worden geteld
  (`skipped_count`) én per rij gerapporteerd (`errors[]`); niet stil geskipt.
- `ai_agent/followup_service.py` — `execute_recommendation` gooit `BadRequestError` als er niets
  verstuurd is → nooit stil "Uitgevoerd".
- `incasso/service.py` batch (`generate_document`, `recalculate_interest`) — brede `except` logt +
  rapporteert per dossier in `errors[]`, telt als `skipped`; geen geld geboekt in faal-pad.

### Niet geverifieerd
- `payment_matching_service.py::execute_match` (bankimport-uitvoering) — niet regel-voor-regel
  doorgelicht (buiten de opgegeven delta-lijst).
- Info-randgeval: een dossier zónder vorderingen (`total_principal == 0`) kan zonder betaling op
  "betaald" komen (early-exit `get_portfolio_outstanding`). Vermoedelijk bewust — bevestig bij
  Lisanne.

---

## Fix-prioriteit voor een latere Opus/Sol-fix-sessie
1. **H1** cross-tenant CaseFile (kleinste fix, duidelijkste tenant-lek) — ~5 regels.
2. **H2** fail-open "betaald"-guard (2 plekken) — geld sluit stil weg — ~8 regels.
3. **H3** "Geïnd" telt verwijderde betalingen — ~2 regels, rapportage-integriteit.
4. **M4** systeemmail-HTML escapen bij de datagrens — eerst regressietest met dossierdata.
5. **M5** centrale ontvangerparser/-cap; datacorrectie van 39 velden apart en gecontroleerd.
6. **M1** bulk-status lengtecap + **M2** auto-advance terminale-check — beide chirurgisch.
7. **M3** app-als-superuser (RLS Fase 2) — grote klus, apart plannen.
8. **L4-L6** meenemen als kleine hardeningtests wanneer het mailpad wordt aangepast.
