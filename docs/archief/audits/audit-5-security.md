# Audit 5 — Security (Auth + File Access)

**Datum:** 2026-04-22
**Scope:** `backend/app/*` + `frontend/src/*` + `docker-compose.yml` + `Caddyfile`
**Auditor:** security-reviewer subagent (Opus 4.7)

## Verdict: RISKY

Luxis toont oprechte security-aandacht: bcrypt wachtwoorden met min-12-char complexity, PyJWT met algorithm pinning, refresh-token rotation met reuse-detection en revoke-all, Postgres Row-Level Security met non-owner `luxis_app` role, Fernet encryption voor OAuth tokens at rest, HMAC+Redis-nonce OAuth state, DOMPurify HTML sanitization, Caddy-level HSTS/CSP/X-Frame-Options, per-IP rate limits op auth, en non-root Docker user.

**Maar** er zijn exploitable gaten die een "safe" rating blokkeren.

## Severity counts

- **CRITICAL:** 2
- **HIGH:** 11
- **MEDIUM:** 15
- **LOW:** 9
- **INFO:** 3

---

## CRITICAL

### C1 — Docker-compose default SECRET_KEY omzeilt productie-guard
**Locatie:** `docker-compose.yml:34` + `backend/app/main.py:55` + `backend/app/config.py:12`

`docker-compose.yml` bevat hard-coded `SECRET_KEY: dev-secret-key-change-in-production`. De startup-guard in `main.py` verwerpt **alleen** de literaal `"change-this-to-a-random-string-in-production"` uit de config default. De docker-compose default is een andere string, dus de guard pakt 'm niet. Iedereen met repo-toegang kan geldige JWTs minten voor elke tenant.

**Fix:** Unificeer op één placeholder + assert `len(SECRET_KEY) >= 32` en niet-in-{known placeholders}. Of maak env var required zonder default.

### C2 — Account lockout = DoS + user enumeration
**Locatie:** `backend/app/auth/service.py:55-91`

Lockout increment `failed_login_count` gebeurt bij elke verkeerde poging. 5 pogingen → 15 min lockout, 10 pogingen → 1 uur lockout. Rate limiter `/api/auth/login` is `10/minute` **per IP** — attacker rotate IPs en lockt elke user permanent. Tegelijk: `user is None` path retourneert direct (fast), `user is not None` path doet bcrypt (slow) = timing side-channel voor user enumeration.

**Fix:** Dummy bcrypt compare op user-not-found branch. Rate limit per email (niet alleen per IP). Lockout op IP+email combinatie, niet alleen op user.

---

## A01 — Broken Access Control (HIGH × 3, MEDIUM × 2, LOW × 1)

### HIGH — Workflow endpoints niet admin-gated
**Locatie:** `backend/app/workflow/router.py:65, 128, 234, 244, 255`

Docstrings zeggen "admin only" voor create/update/delete van workflow statuses, transitions, rules. Endpoints gebruiken alleen `get_current_user`. Elke `medewerker` kan tenant-wide workflow config wijzigen.

**Fix:** `Depends(require_role("admin"))` toevoegen.

### HIGH — Managed template upload niet admin-gated
**Locatie:** `backend/app/documents/template_router.py:43, 79, 93, 103`

Upload/update/replace/delete van managed templates heeft geen role gate. Elke user kan `sommatie.docx`/`dagvaarding.docx` vervangen met attacker-content die naar debiteuren verstuurd wordt op firm letterhead.

**Fix:** Require `admin` (of `advocaat`) voor write ops.

### HIGH — `PUT /api/auth/me` accepteert `default_hourly_rate`
**Locatie:** `backend/app/auth/router.py:260-275`

`UpdateProfileRequest` accepteert `default_hourly_rate` zonder validatie of dit een appropriate veld is voor een `medewerker` om zelf te zetten.

**Fix:** Audit elke write endpoint voor role gate.

### MEDIUM — RLS silently disabled in non-prod
**Locatie:** `backend/app/middleware/tenant.py:19-56` + `backend/app/database.py:40`

Initial `get_db` dependency roept geen `set_tenant_context` aan. Elk code path dat session krijgt zonder via `get_current_user` (unauthenticated routes, scheduler/Celery tasks, migrations) draait als session default. Als `luxis_app` role niet bestaat (dev/test DBs), is RLS stil uit.

**Fix:** Fail-closed in prod. Startup assert dat elke DB pool connection defaults naar `luxis_app`.

### MEDIUM — OAuth callback kan tenant-hop bij SECRET_KEY lek
**Locatie:** `backend/app/email/oauth_router.py:99-122`

OAuth callback schrijft tokens naar user op basis van `state` only. Bescherming via HMAC + Redis nonce (goed), maar bij SECRET_KEY compromise kan attacker zijn mailbox linken aan slachtoffer's account.

**Fix:** Callback ook vereisen dat session cookie matcht state user.

### LOW — Email enumeration via `GET /api/users`
**Locatie:** `backend/app/auth/router.py:316-322`

Elke authenticated user kan alle users in zijn tenant enumeren. Waarschijnlijk prima, maar overweeg PII te gaten achter admin voor `medewerker`.

---

## A02 — Cryptographic Failures (CRITICAL × 1, HIGH × 3, MEDIUM × 1, LOW × 1)

### HIGH — Fernet key afgeleid uit SECRET_KEY
**Locatie:** `backend/app/email/token_encryption.py:19-21`

Fernet key via SHA-256 van `SECRET_KEY`. Gevolg: SECRET_KEY rotatie silently decrypt-fails alle opgeslagen OAuth tokens (users moeten opnieuw verbinden). Compromise van SECRET_KEY = totale compromise (JWT forging + OAuth token exposure + OAuth state forging, alles tegelijk).

**Fix:** Aparte `TOKEN_ENCRYPTION_KEY` env var onafhankelijk van JWT signing key.

### HIGH — Algorithm configurable via settings
**Locatie:** `backend/app/auth/service.py:50-52`

`jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])` — `settings.algorithm` is configurable string (default `HS256`). Oké vandaag, maar misconfiguration `ALGORITHM=none` of `RS256` met HMAC secret is catastrophisch. Geen `iss`/`aud` validatie, geen `leeway`.

**Fix:** `algorithms=["HS256"]` hardcoded pinnen; `iss`, `aud` verifiëren.

### HIGH — Refresh en access tokens delen signing key
**Locatie:** `backend/app/auth/service.py:27-47`

Refresh tokens = JWTs signed met zelfde key als access tokens. Lek SECRET_KEY = beide forgen.

**Fix:** Aparte signing keys of `kid` scheme.

### MEDIUM — bcrypt rounds niet configureerbaar
**Locatie:** `backend/app/auth/service.py:19-20`

`gensalt()` default (rounds=12). Prima, maar niet configurable. Re-hash op login als cost < target.

**Fix:** Parameterize bcrypt rounds via settings (default 12, raise naar 13-14).

### LOW — bcrypt 72-byte truncation
**Locatie:** `backend/app/auth/service.py:20`

bcrypt truncate passwords silently bij 72 bytes. Validatie vereist ≥12 chars, geen hard upper-bound.

**Fix:** `len(password) <= 72` in validator.

---

## A03 — Injection (MEDIUM × 1, LOW × 2, INFO × 1)

### MEDIUM — Tenant middleware f-string raw SQL
Zie ook audit-4 finding #8. Gemitigeerd door strikte UUID-parsing.

### LOW — Jinja2 `autoescape=False` voor user-editable templates
**Locatie:** `backend/app/incasso/service.py:892`

`Environment(autoescape=False)` voor user-editable pipeline email templates. Geen SSTI omdat context strings niet geparsed worden, maar bij HTML use kan attacker die template kan editen HTML/JS injecteren in mails op firm letterhead.

**Fix:** `autoescape=select_autoescape(default=True)`. Gate template edits op admin.

### LOW — docxtpl SSTI risico
**Locatie:** `backend/app/documents/template_router.py:128-178`

`preview_template` accepteert arbitrary uploaded `.docx`, rendert met docxtpl (Jinja2) tegen echte case data, retourneert resultaat. docxtpl gebruikt Jinja2 met `autoescape=False` default. Malicious template kan arbitrary Jinja expressies executen.

**Fix:** `jinja_env_kwargs={"sandboxed": True}` via `jinja2.sandbox.SandboxedEnvironment`. Gate uploads op admin.

### INFO — Raw SQL audit clean
`grep text\(` retourneert alleen tenant-context `SET LOCAL` en RLS-migratie `op.execute()`s. Geen user-input-concatenated raw SQL. Alle queries via SQLAlchemy ORM.

---

## A04 — Insecure Design (CRITICAL × 1, HIGH × 2, MEDIUM × 1)

### HIGH — `forgot-password` timing side-channel
**Locatie:** `backend/app/auth/router.py:209-234`

`forgot-password` slowapi limit is `3/hour` per IP. Geen per-email throttle, dus attackers enumeren bestaand via response time (user exists → token gegenereerd + SMTP email als background task = observeerbare side effects).

**Fix:** Constant-time handler; rate-limit per email hash.

### HIGH — Geen `/logout` endpoint
**Locatie:** `backend/app/auth/router.py:254-323`

Geen server-side logout: access tokens blijven 15 min geldig na "logout"; refresh tokens blijven geldig tot gerotate. `revoke_all_refresh_tokens` alleen bij reuse-detection.

**Fix:** `POST /api/auth/logout` die huidige refresh token consumeert + optional alle andere revoket.

### MEDIUM — Password reset niet revoket bestaande sessions
**Locatie:** `backend/app/auth/models.py:62-74`

`password_reset_token` is unique en hashed in DB. One-use is impliciet. Maar: token rotation bij reset revoket niet de refresh tokens van oude password. Attacker die al refresh token heeft gestolen houdt access na victim reset.

**Fix:** Bij password reset: `revoke_all_refresh_tokens(user.id)`.

---

## A05 — Security Misconfiguration (HIGH × 2, MEDIUM × 2, LOW × 2, INFO × 1)

### HIGH — `APP_DEBUG` lekt SQL+credentials naar stdout
**Locatie:** `backend/app/database.py:11` + `docker-compose.yml:38`

`echo=settings.app_debug` → bij `APP_DEBUG=true` streamen alle SQL (incl. `hashed_password` values gelezen op login) naar stdout. Dev compose zet `APP_DEBUG: "true"` default. Als dev compose per ongeluk naar prod env lekt: PII + password hashes in logs.

**Fix:** Aparte `SQL_ECHO` flag; default off overal.

### HIGH — CORS met `allow_methods=["*"]` + credentials
**Locatie:** `backend/app/main.py:91-97`

`allow_origins` uit config + `allow_credentials=True`. Origins whitelisted (goed), maar `allow_methods=["*"]` en `allow_headers=["*"]` met credentials verbreedt attack surface. `CORS_ORIGINS=*` of wildcard-subdomain is catastrophisch.

**Fix:** Methods + headers expliciet pinnen. Startup validatie: reject `*`.

### MEDIUM — `app_env` default = `development`
**Locatie:** `backend/app/main.py:85-86` + `backend/app/config.py:18`

`docs_url="/docs" if settings.app_env != "production" else None` — goed, maar default is `development`. Prod-deploy die `APP_ENV` vergeet te setten exposed `/docs` EN disabled de SECRET_KEY guard.

**Fix:** Fail-fast: require `APP_ENV` expliciet gezet.

### MEDIUM — CSP allows `'unsafe-inline'`
**Locatie:** `Caddyfile:29`

CSP allows `'unsafe-inline'` voor scripts & styles, reduceert XSS mitigation.

**Fix:** Nonce/hash-based CSP voor prod.

### LOW — Permissions-Policy minimaal
**Locatie:** `Caddyfile:26`

Voeg toe: `interest-cohort=()`, `payment=()`, `usb=()`.

### LOW — Default Postgres password in docker-compose
**Locatie:** `docker-compose.yml:34`

`luxis_dev_password`. Dev-only, maar committet DB creds naar git.

### INFO — Docker user is `appuser` (non-root).

---

## A07 — Identification & Authentication Failures (HIGH × 1, MEDIUM × 3, LOW × 1)

### HIGH — Zie C2 (user enum + DoS).

### MEDIUM — `/forgot-password` existence-leak via timing

### MEDIUM — Password policy is zwak
**Locatie:** `backend/app/auth/schemas.py:15-23`

Length + 1 upper + 1 digit. Geen symbol requirement, geen `HaveIBeenPwned`, geen common-password denylist.

**Fix:** Denylist (top 10k) of HIBP k-anonymity integratie.

### MEDIUM — Geen access token revocation
**Locatie:** `backend/app/dependencies.py:15-55`

Alleen refresh tokens hebben DB row. 15-minuten window na firing medewerker waarin access token geldig blijft.

**Fix:** `users.token_version` int, increment bij password change / deactivation. JWT bevat version, verifiëren op elke request.

### LOW — Login rate limit te genereus
**Locatie:** `backend/app/auth/router.py:50-52`

`10/minute` per IP = 600/uur per IP. Brute-force met distributed password list feasible tegen zwakke passwords.

**Fix:** Tighten naar `5/minute` + per-email.

---

## A08 — Software & Data Integrity (MEDIUM × 1, LOW × 1)

### MEDIUM — LibreOffice spawned op user-uploaded DOCX
**Locatie:** `backend/app/documents/pdf_service.py:32-43`

`soffice --headless` op untrusted DOCX bytes. LibreOffice heeft non-trivial CVE history (macros, OLE objects). Templates zijn user-uploaded.

**Fix:** LibreOffice in sandbox (seccomp/firejail) of replace met `docx2pdf`/`Aspose` in locked-down container.

### LOW — File upload trusts content_type header
**Locatie:** `backend/app/cases/files_service.py:30-46`

Validation trusts `file.content_type` (attacker-controlled) + extension. Geen magic-byte sniffing. Attacker kan HTML uploaden met `.pdf` extension.

**Fix:** `libmagic`/`python-magic` content sniffing. Done voor docx in `template_service._validate_docx_magic` — extend naar alle uploads.

---

## A09 — Security Logging & Monitoring (MEDIUM × 2, LOW × 2)

### MEDIUM — Login failures geen structured audit log
**Locatie:** `backend/app/auth/router.py:58-70` + `backend/app/auth/service.py:77-84`

Alleen `failed_login_count` increment. Geen `logger.warning` voor failed attempts met IP + email.

**Fix:** Elke auth failure + lockout event naar dedicated audit stream.

### MEDIUM — Geen audit trail voor mutations
`case_activities` tabel vangt sommige case-level acties, maar niet cross-module. Wie wijzigde case status, wie deleted file, wie stuurde sommatie — niet overal.

**Fix:** Central audit log tabel met user_id, tenant_id, action, entity, before/after.

### LOW — Email in logs bij password reset
**Locatie:** `backend/app/auth/router.py:204, 227`

`logger.info("Password reset email sent to %s", to)` logt email address. GDPR note.

### LOW — SQL echo exposes bcrypt hashes

---

## A10 — SSRF (MEDIUM × 1, GOOD × 2)

### MEDIUM — WeasyPrint onbeperkt url_fetcher
**Locatie:** `backend/app/invoices/invoice_pdf_service.py:137-140`

WeasyPrint krijgt `base_url=str(TEMPLATES_DIR)`. `factuur.html` Luxis-controlled, maar kan `<img src="…">` bevatten met user-supplied data (tenant logo URL, contact data). WeasyPrint fetcht remote URLs default → malicious user die rendered field controleert kan SSRF naar internal network (`http://db:5432`, `http://169.254.169.254` AWS metadata).

**Fix:** `url_fetcher` met blocklist, of disable remote loading (`presentational_hints=False`, custom `url_fetcher` die non-file URLs rejects).

### GOOD — OAuth IMAP check blokkeert private IPs
`backend/app/email/oauth_router.py:143-172` `_is_blocked_host` correct.

### GOOD — Frontend strip `img[src]` bij render
`frontend/src/lib/sanitize.ts:16-28`.

---

## GDPR / Attorney-Client Privilege (HIGH × 2, MEDIUM × 2, LOW × 1)

### HIGH — Case files unencrypted at rest
**Locatie:** `backend/app/cases/files_service.py`

Uploaded case files worden unencrypted geschreven naar `/app/uploads`. Trust-fund bank statements, privileged correspondence, ID scans (KYC) — alles plaintext op VPS disk.

**Fix:** Files encrypt at rest (per-tenant key via KMS of SECRET_KEY-derived) of zorg dat volume op encrypted filesystem/LUKS staat.

### HIGH — Geen right-to-erasure primitive
`delete_case_file` is soft-delete only. GDPR art. 17 vereist true erasure.

**Fix:** Hard-delete admin endpoint + scheduled purge van soft-deleted records.

### MEDIUM — Sentry kan PII lekken
**Locatie:** `backend/app/main.py:63-68`

Sentry `send_default_pii=False` (goed), maar exception messages bevatten vaak PII (email addresses, case numbers).

**Fix:** `before_send` scrubber die emails/IBANs strippet.

### MEDIUM — Backup encryption
Geen backup strategie zichtbaar in repo. Verplicht voor advocatenkantoor.

### LOW — Audit trail incompleet
`case_activities` niet alles. User profile changes, password resets, tenant settings changes missen.

---

## Frontend XSS (HIGH × 1, MEDIUM × 1)

### HIGH — `dangerouslySetInnerHTML` zonder sanitize in compose dialog
**Locatie:** `frontend/src/components/email-compose-dialog.tsx:731`

`dangerouslySetInnerHTML={{ __html: templateHtml }}` ZONDER `sanitizeHtml` wrapper. `templateHtml` komt van backend-rendered templates. Als template-editing endpoint reachable door attacker (zie A01 unguarded `managed-templates`): script injection = steals `localStorage` JWTs van elke user.

**Fix:** Wrap in `sanitizeHtml()` zoals andere call-sites.

### MEDIUM — DOMPurify allow_attr includes `src` op `img`
**Locatie:** `frontend/src/app/(dashboard)/zaken/[id]/types.tsx:131`, `CorrespondentieTab.tsx:194`, `correspondentie/page.tsx:468`

Gesanitized via DOMPurify — maar `ALLOWED_ATTR` includes `src` en allows `img` tag. `afterSanitizeAttributes` hook strips `img src`, maar bypass zou serieus zijn gezien JWTs in localStorage.

**Fix:** Migrate tokens naar `httpOnly+SameSite=strict` cookie auth (defense-in-depth).

---

## CSRF — GOOD

Bearer token in `Authorization` header = geen classic CSRF. Als tokens migreren naar cookies, CSRF protection nodig.

---

## Rate limiting summary

| Endpoint | Limit | Assessment |
|---|---|---|
| `/api/auth/login` | 10/min per IP | Te loose; geen per-email (HIGH) |
| `/api/auth/forgot-password` | 3/hour per IP | OK per IP, missing per-email (MEDIUM) |
| `/api/auth/reset-password` | 5/hour per IP | OK |
| `/api/auth/refresh` | Unlimited | Add limit |
| `/api/ai-agent/*` | Unlimited | Cost risk — LLM billing. Add per-tenant quota |
| File uploads | Unlimited | Tenant kan disk vullen |

---

## Top quick wins (deze week)

1. **CRITICAL C1** — Docker-compose SECRET_KEY unificeren + assert
2. **CRITICAL C2** — Dummy bcrypt op user-not-found + per-email rate limit
3. **HIGH** — Admin-gate workflow/template write endpoints
4. **HIGH** — `sanitizeHtml()` wrap rond `templateHtml` in compose dialog
5. **HIGH** — Case files encryption at rest of LUKS volume

## Conclusie

**Risky.** Solid foundation, maar de twee CRITICALs en unguarded admin endpoints moeten gefixt voordat we buiten de eerste client schalen.

## Gerefereerde bestanden

- `backend/app/main.py`, `backend/app/config.py`, `backend/app/dependencies.py`
- `backend/app/auth/service.py`, `backend/app/auth/router.py`, `backend/app/auth/models.py`, `backend/app/auth/schemas.py`
- `backend/app/middleware/tenant.py`, `backend/app/middleware/rate_limit.py`
- `backend/app/database.py`
- `backend/app/email/token_encryption.py`, `backend/app/email/oauth_service.py`, `backend/app/email/oauth_router.py`
- `backend/app/cases/files_service.py`, `backend/app/cases/router.py`
- `backend/app/documents/pdf_service.py`, `backend/app/documents/template_router.py`, `backend/app/documents/template_service.py`
- `backend/app/invoices/invoice_pdf_service.py`, `backend/app/incasso/service.py`, `backend/app/workflow/router.py`
- `backend/app/email/compose_router.py`
- `backend/alembic/versions/sec9_row_level_security.py`, `sec9b_force_rls.py`
- `docker-compose.yml`, `docker-compose.prod.yml`, `Caddyfile`
- `frontend/src/lib/token-store.ts`, `frontend/src/lib/sanitize.ts`, `frontend/src/lib/api.ts`
- `frontend/src/components/email-compose-dialog.tsx`
