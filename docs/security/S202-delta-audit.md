# S202 — Security- & consistentie-audit van de delta sinds S183

**Datum:** 12 juli 2026 · **Model:** Fable (read-only) · **Scope:** `git diff sessie-183..HEAD`
(49 commits, 122 bestanden, +6843/−3956). **Status:** 6 van de 7 blokken afgerond in deze
sessie; **Blok 2 (mailpad) is afgebroken en overgedragen aan Sol/Codex** — zie onderaan de
kant-en-klare vervolgprompt.

Alle bevindingen zijn met bewijs uit déze sessie (code-regel of prod-query, read-only).
Niets is gewijzigd, geen mail verstuurd, geen mutaties op prod. Fixen gebeurt in een latere
Opus/Sol-sessie.

---

## Samenvatting op ernst

| Ernst | # | Kort |
|---|---|---|
| Kritiek | 0 | — |
| Hoog | 3 | Cross-tenant CaseFile-lek bij mailbijlage-opslag · 2× fail-open op "betaald"-guard · "Geïnd"-rapportage telt verwijderde betalingen |
| Middel | 3 | Bulk-status geen lengtecap (DoS) · auto-advance mist terminale-stap-check · app draait als DB-superuser (RLS alleen via SET ROLE) |
| Laag | 3 | Settings-GET niet admin-only (afwijking rollen.md) · SendDocument geen e-mailformaat-check · collection_rate via float |
| Info | 4 | Globaal mailslot zonder tenant_id · e-mailadressen in prod-logs · `.codex/config.toml` leesbare sleutels (lokaal) · PowerSearch cosmetische punten |

**Grote geruststellingen (geverifieerd OK):** RLS op prod is compleet en zonder drift
(44/44 tenant-tabellen FORCE + policy, alleen `users` bewust uitgezonderd). Geen secrets in
de repo of de delta-diff. Frontend-bundle bevat geen `NEXT_PUBLIC_*`-sleutels. PowerSearch
is injectie-veilig en tenant-gescoped. De bulk-status- en pipeline-batch-paden zijn
tenant-gescoped in de query zelf.

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

### L2 (LAAG) — SendDocument mist e-mailformaat-check
`backend/app/documents/schemas.py:170-174` (`SendDocumentRequest.recipient_email`): alleen
`max_length=320`, geen formaat-check — terwijl `compose_router.py:48,115-121` dat wél doet via
`_EMAIL_RE`. Inconsistente validatie tussen twee verzendpaden, geen beveiligingsrisico.
- **Fix:** hergebruik `_EMAIL_RE` op `recipient_email`/`cc`.

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
- `compose_router.py` — alle 4 endpoints valideren `Case.tenant_id`; bijlagen op
  `CaseFile.tenant_id`+`case_id`; cap 3 MB × max 10; e-mailadressen serverzijdig gevalideerd.
- `documents/router.py` — elke `case_id`/`document_id` tenant-gefilterd; `html_to_pdf` via
  `_data_only_url_fetcher` (alleen `data:`-URI's) → SSRF/LFI gemitigeerd.
- `incasso/router.py` move-step/batch — `Case` geladen met `tenant_id`-filter, batch-`case_ids`
  altijd via `Case.tenant_id == tenant_id`.
- `dependencies.py:19-93` — token-type-check, UUID-validatie op `sub`/`tenant_id`,
  `require_role` → 403 bij onvoldoende rol.

---

## Blok 2 — Mailpad (S185-S187) — ⚠️ AFGEBROKEN, OVERGEDRAGEN AAN SOL/CODEX

Deze audit is door de gebruiker afgebroken vóór afronding (tokens). **Nog niet geauditeerd.**
Kant-en-klare vervolgprompt staat onderaan dit document ("Vervolgprompt voor Sol/Codex").
Bekende aanknopingspunten uit deze sessie (niet geverifieerd als bevinding, wel als startpunt):
- IMAP CR/LF-injectiefix in `_imap_quote` (commit `8b658c7`, S188e) moet heraudit worden +
  gecheckt of hetzelfde patroon elders voorkomt (subject in MIME-headers, folder-namen).
- Mailslot-vlag: `email/service.py:40` combineert env (`OUTBOUND_MAIL_LOCK`) OF DB-vlag met
  OR-logica, en `email/service.py:66` valt bij een ontbrekende DB-rij terug op `True` (dicht) —
  dit **lijkt** fail-safe, maar moet per verstuurpad (compose, batch, followup, AI-agent)
  geverifieerd worden. Prod-stand nu: `app_config.outbound_mail_locked = true` (dicht),
  env `OUTBOUND_MAIL_LOCK=false`.

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

## Vervolgprompt voor Sol/Codex — Blok 2 (mailpad) afmaken

> **Taak:** maak Blok 2 van de S202-security-audit af. 100% read-only (prod-queries mogen,
> geen mutaties, geen mail versturen, geen fixes bouwen — alles als bevinding naar het rapport).
> Voeg je bevindingen toe onder "## Blok 2 — Mailpad" in `docs/security/S202-delta-audit.md`
> (vervang de ⚠️-placeholder), gerangschikt op ernst met bewijs (bestand:regel of prod-query).
>
> **Scope:** het mail-verstuurpad gebouwd sinds tag `sessie-183` (S185-S187, S188e, S197).
> Bestanden: `backend/app/email/send_service.py`, `email/providers/imap_provider.py`,
> `email/compose_router.py`, `email/sync_service.py`, `email/service.py`, `email/oauth_service.py`,
> `email/incasso_templates.py`, `settings/models.py` + `settings/router.py`, `config.py`.
> Tests als referentie: `backend/tests/test_imap_send.py`, `test_mail_lock.py`.
>
> **Check:**
> 1. **Header-/CR-LF-injectie** — verifieer de `_imap_quote`-fix (commit `8b658c7`) en zoek
>    hetzelfde patroon elders: subject/naam/adres in SMTP-MIME-headers, IMAP-commando's,
>    folder-namen. Kan een debiteurnaam of onderwerp headers injecteren?
> 2. **Mailslot fail-safe** — `email/service.py:40` (OR van env + DB-vlag) en `:66` (ontbrekende
>    DB-rij → `True`). Verifieer dat élk verstuurpad (compose, pipeline/batch, followup, AI-agent)
>    de vlag checkt, niet slechts één. Prod-stand: `app_config.outbound_mail_locked=true`,
>    env `OUTBOUND_MAIL_LOCK=false`.
> 3. **Wie mag versturen** — rol-checks op compose/send-endpoints? Kan elke ingelogde gebruiker
>    als `incasso@` naar willekeurige adressen mailen (spam/phishing bij gecompromitteerd account)?
> 4. **Log-lekken** — mail-body/adressen/credentials in `logger`-calls? (Bekend: sync logt
>    e-mailadressen op INFO-niveau — zie I2 hieronder, bevestig scope.)
> 5. **IMAP read-only** — geen STORE/DELETE/EXPUNGE op de bron-mailbox behalve de bedoelde
>    APPEND-naar-Verzonden. Worden SMTP/IMAP-credentials versleuteld opgeslagen (TOKEN_ENCRYPTION_KEY)
>    of plaintext?
> 6. **Recipient-validatie op systeempaden** — voorkomt iets dat een batch/followup naar een
>    verkeerd/extern adres mailt zonder menselijke actie?
>
> Rapporteer per bevinding: [ernst] — bestand:regel — wat — faalscenario — fix-recept + geschatte
> fix-grootte. Plus een "geverifieerd OK"-lijst met bestand:regel. Onzeker = label "niet geverifieerd".

### I2 (INFO) — E-mailadressen in prod-logs
`app.email.sync_service` logt op INFO-niveau regels als
`Sync klaar voor <adres>@kestinglegal.nl: 43 opgehaald, …`. Geen sleutels/inhoud, wel PII
(mailboxadressen) in de container-logs. Laag; overweeg maskeren als logs ooit extern gaan.

---

## Fix-prioriteit voor een latere Opus/Sol-fix-sessie
1. **H1** cross-tenant CaseFile (kleinste fix, duidelijkste tenant-lek) — ~5 regels.
2. **H2** fail-open "betaald"-guard (2 plekken) — geld sluit stil weg — ~8 regels.
3. **H3** "Geïnd" telt verwijderde betalingen — ~2 regels, rapportage-integriteit.
4. **M1** bulk-status lengtecap — ~1 regel. **M2** auto-advance terminale-check — ~3 regels.
5. **M3** app-als-superuser (Fase 2) — grote klus, apart plannen.
6. Blok 2 (mailpad) — **eerst auditen via de bovenstaande Codex-prompt**, dán fixen.
