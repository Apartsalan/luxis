# Readiness-audit Luxis — kan dit live met echte data?

*Sessie 158 (10 juni 2026, Fable). Scope: security, operations, AVG/privacy — de "mag het live"-laag. App-logica is gedekt door `financiele-samenhang.md` en `connectie-audit.md`. Live geverifieerd op de productie-VPS (SSH, 10 juni): crontab, backups, rclone, disk, alembic, RLS, fail2ban/ufw, logs.*

---

## 1. Eindoordeel

**Technisch fundament is live-waardig.** Backups draaien dagelijks mét off-site kopie, RLS staat aan op 46 tabellen, account-lockout + rate-limiting + security-headers + upload-validatie zijn op orde, 970+ tests groen, resource-limits en healthchecks netjes.

**Drie blockers vóór echte Lisanne-data — samen < 1 dag werk + 1 besluit:**

| # | Blocker | Waarom | Fix |
|---|---|---|---|
| B1 | **Debiteur-PII naar Moonshot/Kimi (China)** | Intake-extractie en e-mail-classificatie sturen naam/adres/e-mail/schuld van debiteuren door de fallback-keten Gemini → **Kimi (api.moonshot.ai)** → Claude (`kimi_client.py:4,27`). Moonshot: geen EU-verwerkersovereenkomst → AVG-datalek-risico bij elke fallback-hit. Gemini-tier onbekend (gratis tier = Google mag trainen). | Kimi uit de keten (config/code, ½ uur). Anthropic heeft DPA + traint niet op API-data. Gemini alleen houden als betaald tier + DPA bevestigd, anders ook eruit. **Besluit Arsalan nodig.** |
| B2 | **Restore nooit getest** | Backup draait perfect (03:00, db 1.7MB + uploads 39MB, 16 lokaal, rclone off-site geconfigureerd). Maar een niet-geteste backup is hoop, geen vangnet. | Eén keer: dump → lege test-DB → restore → app ertegenaan → checklist in docs. ~1 uur. |
| B3 | **Deploy draait geen migraties + rolt niet terug** | `deploy.yml`: pull → build → up → health-curl die alleen **echo't** ("FAIL" = exit 0 = deploy "geslaagd"). Geen `alembic upgrade head` — schema gaat handmatig (prod staat nu wél op head `d4a9c3e87f10`, maar dat is discipline, geen systeem). Code auto-live + schema handmatig = drift-crash wachten. | deploy.yml: `alembic upgrade head` stap + health-fail → `exit 1`. ~½ uur. |

## 2. HOOG — direct na (of bij) livegang

| # | Punt | Detail | Fix |
|---|---|---|---|
| H1 | **Geen error-tracking actief** | Sentry-code staat klaar (`main.py:77`, `send_default_pii=False` ✓) maar `SENTRY_DSN` is leeg op prod. Fouten zijn nu onzichtbaar tot Lisanne belt. | Gratis Sentry-account → DSN in `/opt/luxis/.env` → restart. 15 min. |
| H2 | **Uptime-monitoring faalt stil** | Cron `*/5` staat erin, maar `/var/log/luxis-uptime.log` bestaat niet → script heeft nog nooit gelogd (zou elk heel uur "OK" schrijven). Vermoedelijk faalt het script silently (permissions/set -e). Of UptimeRobot extern is ingericht: onbekend. | Script één keer handmatig draaien, fixen; én UptimeRobot aanzetten (extern > zelf-check). 30 min. |
| H3 | **`TOKEN_ENCRYPTION_KEY` niet gezet (#95)** | Fernet-sleutel valt terug op SECRET_KEY (`token_encryption.py:17`). SECRET_KEY ooit roteren = alle OAuth-mailtokens kapot zonder waarschuwing. Veel kleiner dan triage dacht: env-var bestaat al in code. | Var zetten + Outlook 1× opnieuw koppelen. 10 min. NB: `.env.production.example` noemt het verouderd `FERNET_SALT` — template fixen. |
| H4 | **RLS fase 2** | Fase 1 live (middleware `SET ROLE luxis_app`, 46 tabellen, force RLS, fail-closed predicate — degelijk). Fase 2 = verbinden áls luxis_app zodat ook een vergeten code-pad nooit als superuser query't. | Gepland werk (eigen sessie, met toezicht — connection-string-wijziging). |
| H5 | **ufw inactive** | Geen host-firewall. Risico beperkt: db/redis hebben géén host-ports (alleen intern; prod-redis mét wachtwoord ✓), alleen 22/80/443/3100 op de host. Maar poort 3100 (Recruitment-app op zelfde VPS) is mogelijk direct van buiten bereikbaar náást Caddy. | `ufw allow 22,80,443` + enable; 3100 alleen via Caddy. 15 min, even opletten met Docker-iptables. |

## 3. MIDDEL / aanbevelingen

- **`.env.production.example` loopt achter:** mist SMTP/MICROSOFT_*/ANTHROPIC/KIMI/TOKEN_ENCRYPTION_KEY die prod-compose wél verwacht; noemt `FERNET_SALT` die nergens gelezen wordt. Bij server-herinrichting is dit de checklist — nu misleidend.
- **Bekende open MEDIUMs** (triage S157): #66 relatie-validatie, #70 saldo row-lock (laag risico bij 1 user), #73 bedrag-match totale schuld, #97 verweer-switch buiten `move_case_to_step`.
- **Crontab bevat Bearer-token in plaintext** voor de Recruitment-cron (poort 3100) — ander project, zelfde host; verplaats naar env-file.
- **E-mailopslag**: volledige bodies + bijlagen in DB/volume (by design, nodig voor dossiervorming). AVG-kant: opnemen in verwerkingsregister; bewaartermijn 7 jaar (art. 2:10 BW) is gedekt door backup-retentie? Nee — backups roteren (7d/90d); de DB zélf is het archief. OK zolang DB niet geschoond wordt. Documenteer.
- **Verwerkersovereenkomsten checklist** (organisatorisch, geen code): Hetzner (DE ✓), Anthropic, Google (Gemini, indien gehouden), Microsoft (Graph), Exact (straks), Sentry (straks), rclone-doel (welke provider is `luxis-backup:`? — check of dat EU is).
- **2 test-fails dev-only** (Mailpit beantwoordt SMTP) — CI groen; optioneel skipbaar maken.
- **Access-token 15 min + refresh 7d** ✓ goed; lockout 5→15min/10→1uur ✓; reset-rate 3/uur ✓.

## 4. Wat aantoonbaar op orde is (geverifieerd)

- **Backups:** cron 03:00 dagelijks, db + uploads, 7d lokaal (16 files), rclone-remote `luxis-backup:` actief (90d off-site), laatste run vannacht succesvol. Alleen restore-test ontbreekt (B2).
- **RLS fase 1 live:** 46 tabellen `relrowsecurity=true`, FORCE, WITH CHECK, fail-closed (`security/rls.py`), adversarial test in suite.
- **Auth:** bcrypt, JWT 15min, lockout (SEC-20), rate-limits op login/refresh/reset (XFF-spoofing-resistent, AUDIT-H3).
- **Headers (Caddy):** HSTS+preload, CSP, X-Frame DENY, nosniff, Permissions-Policy, -Server.
- **Uploads:** extensie-whitelist + 50MB cap (cases), .docx + 10MB (templates).
- **Containers:** mem/cpu-limits, healthchecks op alle services, restart unless-stopped, redis mét wachtwoord (prod), db/redis niet publiek.
- **Host:** fail2ban actief, disk 46% (78G vrij), disk_guard elk uur, wekelijkse docker prune.
- **Schema:** prod = alembic head. Geld = Decimal/NUMERIC overal (audit-gedekt).
- **Sentry-integratie codeklaar** met `send_default_pii=False`.

## 5. Aanbevolen volgorde (Opus-uitvoerbaar, behalve besluiten)

1. **B1** — Kimi strippen (besluit + ½ uur code) → daarna mag echte data erin
2. **B3** — deploy.yml: migraties + faal-hard (½ uur)
3. **B2** — restore-test + runbook (1 uur)
4. **H1+H2+H3+H5** — Sentry, uptime, token-key, ufw (samen ~1 uur, deels op VPS)
5. **H4** — RLS fase 2 (eigen sessie, met Arsalan erbij)
6. Middel-lijst meenemen in reguliere sessies

## Verwante documenten
- `docs/research/connectie-audit.md` (CONN-1…14) · `docs/research/financiele-samenhang.md` (FIN-1…7) · `.audit/TRIAGE-S157.md`
