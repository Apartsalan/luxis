# Sessieprompt S159 — Readiness-blockers + connectie-gaten fixen (Opus)

**Context in het kort:** Sessie 158 (Fable) deed drie audits: `docs/research/financiele-samenhang.md`, `docs/research/connectie-audit.md`, `docs/research/readiness-audit.md`. Alle keuzes zijn al gemaakt — deze sessie is puur uitvoeren. Werk de taken hieronder **in volgorde** af. Per taak: rode test eerst waar zinvol, commit + push na elke taak (auto-deploy volgt), verificatie zoals aangegeven. Bij twijfel: het betreffende rapport heeft de details.

**VPS-toegang:** `ssh -i $env:USERPROFILE\.ssh\luxis_deploy root@46.225.115.216` (PowerShell sloopt quotes in remote commands — gebruik simpele commando's zonder geneste quotes, of pipe een script via `bash -s`; let op: Write maakt BOM die bash breekt, gebruik ASCII).

---

## Taak 1 — B3: deploy-pipeline repareren (½ uur)

**Probleem:** `.github/workflows/deploy.yml` (1) draait geen `alembic upgrade head` — schema gaat op handdiscipline; (2) de health-check curlt `http://localhost:8000/health` op de HOST, maar backend-poort 8000 is in prod alleen intern (`expose`, geen `ports`) → check kan nooit slagen; (3) `|| echo " [backend FAIL]"` maakt exit-code 0 → deploy "slaagt" altijd.

**Doe:**
1. In het SSH-script van `deploy.yml`, ná `up -d`, vóór health-check:
   `docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head`
2. Health-check vervangen door één die werkt én hard faalt:
   `curl -sf https://luxis.kestinglegal.nl/health || exit 1` (via Caddy; sleep 15 ervoor) en frontend-check idem of weglaten.
3. `docker exec`-variant kan ook: `docker exec luxis-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1` (binnen container werkt localhost wél).

**Verificatie:** push een docs-wijziging → GitHub Actions → Deploy-run groen mét zichtbare alembic-stap in de log. Bewust een keer testen.

## Taak 2 — B2: restore-test + runbook (1 uur)

**Doe op de VPS** (NIET tegen de echte db):
1. `gunzip -c /backups/luxis/luxis_db_<nieuwste>.sql.gz | head -50` — sanity.
2. Maak tijdelijke db in de bestaande container: `docker exec luxis-db createdb -U luxis luxis_restore_test`
3. `gunzip -c /backups/luxis/luxis_db_<nieuwste>.sql.gz | docker exec -i luxis-db psql -U luxis -d luxis_restore_test`
4. Controles: `psql -d luxis_restore_test -tAc "SELECT count(1) FROM cases"`, idem `contacts`, `invoices`, `trust_transactions` — aantallen > 0 en plausibel vs prod.
5. Uploads-tarball: `tar -tzf /backups/luxis/luxis_uploads_<nieuwste>.tar.gz | head` — leesbaar.
6. Opruimen: `dropdb -U luxis luxis_restore_test`.
7. Schrijf `docs/runbooks/restore.md`: exacte stappen voor totaalverlies (nieuwe VPS: docker compose up, .env terugzetten — staat in `.env.bak-s158` als referentie, db terugladen, uploads-tar uitpakken naar volume, DNS). Vermeld ook rclone-remote `luxis-backup:` voor off-site terughalen.

**Verificatie:** runbook bestaat, counts gelogd in sessienotities.

## Taak 3 — Kimi/Gemini definitief uit de code (½ uur)

**Context:** S158 schakelde de keys al uit op prod (`/opt/luxis/.env`, regels met `#B1disabled#`, backup `.env.bak-s158`). Container draait 100% Anthropic. Nu de code zodat ze nooit terugkomen.

**Doe in `backend/app/ai_agent/kimi_client.py`:**
- Verwijder `_call_kimi` + `KIMI_API_BASE`/`KIMI_MODEL` en de Gemini-equivalenten, of — minimaal-invasief — haal ze uit de fallback-ketens zodat élke route alleen nog Claude (Sonnet voor drafts, Haiku voor intake/classificatie) gebruikt. Kies de minimaal-invasieve variant; de routing-functies behouden hun signatures.
- `backend/app/config.py`: `kimi_api_key`/`gemini_api_key` settings mogen blijven (backwards-compat) maar markeer met comment `# unused since S159 — AVG B1`.
- Compose-files: `KIMI_API_KEY`/`GEMINI_API_KEY` env-regels verwijderen uit `docker-compose.yml` en `docker-compose.prod.yml`.
- Tests die kimi/gemini mocken: aanpassen naar Claude-route.

**Verificatie:** `grep -ri "moonshot\|kimi\|gemini" backend/app/` → alleen nog comments/historie. Relevante ai_agent-tests groen. Eén intake of classificatie eind-tot-eind in dev (of prod-log na deploy) toont Claude-aanroep.

## Taak 4 — CONN-6: tab-fallback (5 min)

**Probleem:** `/zaken/{id}?tab=betalingen` vanaf de derdengelden-pagina (`derdengelden/page.tsx:845`) geeft op een NIET-incasso dossier een lege pagina: de tab bestaat daar niet en geen enkele render-conditie matcht.

**Doe in `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` (~regel 101):** na bepalen `tabFromUrl` en `tabIds`: als `tabFromUrl` niet in geldige tab-ids zit → `"overzicht"`. Let op: `tabIds` hangt af van `isIncasso` dat pas na laden bekend is — valideer dus in een effect of bij render (bv. `const safeTab = tabs.some(t => t.id === activeTab) ? activeTab : "overzicht"` en gebruik `safeTab` voor rendering).

**Verificatie:** `npx tsc --noEmit` groen; in browser: niet-incasso dossier + `?tab=betalingen` → overzicht-tab toont.

## Taak 5 — CONN-1: factuur-overdue keten (½–1 sessie)

**Probleem:** status `overdue` wordt nérgens gezet (geen job, geen UI). Filter "te laat" altijd leeg; geen signaal bij vervallen declaratie. Aging op debiteuren-tab werkt al (op `due_date`).

**Doe:**
1. **Backend-job** in `backend/app/workflow/scheduler.py` (naast de bestaande daily task-job, zelfde patroon): zet `invoices.status='overdue'` voor `status='sent' AND due_date < CURRENT_DATE AND is_active`. Idempotent.
2. **Notificatie** per nieuw-overdue factuur via `create_notification_if_not_exists` (`backend/app/notifications/service.py` — voeg type `invoice_overdue` toe aan de types daar), met `case_id` indien aanwezig zodat de header-link werkt.
3. **Frontend** `facturen/page.tsx`: rij-badge "Te laat" tonen (status-kleur bestaat al in status-config; check `lib/status-constants.ts`).
4. Rode test eerst: factuur sent + due_date gisteren → job → status overdue + notificatie bestaat. Plaats in `backend/tests/test_invoices.py` of nieuw `test_invoice_overdue_job.py`.

**Verificatie:** pytest groen (invoices-suite), browser: factuurlijst toont badge na job-run in dev.

## Taak 6 — CONN-2: vier-ogen-notificatie (klein)

**Probleem:** pending trust-transacties (uitbetaling/verrekening) geven geen notificatie/taak — goedkeurder ziet niets tenzij hij zelf kijkt.

**Doe:** in `backend/app/trust_funds/service.py` ná het aanmaken van een `pending_approval`-transactie (in `create_transaction` voor disbursements én `create_offset_to_invoice`): `create_notification` (type `trust_approval_pending`, nieuw) voor alle actieve users van de tenant behálve de creator; met case_id. Test: transactie aanmaken → notificatie voor andere user, niet voor creator.

**Verificatie:** trust-suite + nieuwe test groen.

## Taak 7 — CONN-3 + CONN-4 + CONN-14: sidebar (klein)

**Doe in `frontend/src/components/layout/app-sidebar.tsx` (ALL_SECTIONS, regel ~49):**
- Sectie "Beheer": item `{ name: "Intake", href: "/intake", icon: Inbox, badge: "ai-pending" }` (badge `ai-pending` bestaat al in het NavItem-type:41 maar is nergens gekoppeld — CONN-14; koppel hem aan pending-intake-count via de bestaande badge-mechaniek, zie hoe `payment-pending` werkt).
- Onder Incasso: `{ name: "Follow-up", href: "/followup", icon: Zap, module: "incasso" }` met pending-count-badge (hook `use-followup` heeft stats).

**Verificatie:** tsc groen, browser: beide items zichtbaar, badges tonen counts.

## Taak 8 — CONN-5: notificaties met tab-context (klein)

**Doe:** `frontend/src/components/layout/app-header.tsx:234` — link per type: `email_received` → `/zaken/{id}?tab=correspondentie`, `deadline_overdue` → `?tab=taken`, `trust_approval_pending` (nieuw) → `?tab=betalingen`, `invoice_overdue` (nieuw) → factuur: als notificatie geen invoice-link heeft, dan `?tab=facturen`. Simpele type→tab-map in de frontend volstaat (geen backend-wijziging nodig).

**Verificatie:** tsc groen; klik in browser landt op juiste tab (werkt samen met Taak 4-fallback).

## Taak 9 — VPS-hardening H1/H2/H3/H5 (1 uur, via SSH)

1. **H1 Sentry:** gratis account aanmaken kan Arsalan — als DSN beschikbaar: zet `SENTRY_DSN=` in `/opt/luxis/.env` + recreate backend. Zo niet: sla over, noteer.
2. **H2 uptime:** draai `/opt/luxis/scripts/setup-uptime-monitoring.sh --check` handmatig op de VPS, kijk waarom hij nooit logde (waarschijnlijk faalt iets onder `set -e`), fix; én adviseer Arsalan UptimeRobot (extern) — monitors: `https://luxis.kestinglegal.nl` + `/health`.
3. **H3 token-key:** genereer secret, voeg `TOKEN_ENCRYPTION_KEY=<secret>` toe aan `/opt/luxis/.env` + recreate backend. **Gevolg:** Outlook-koppeling éénmalig opnieuw verbinden (Instellingen → e-mail) — meld dit aan Arsalan. Fix ook `.env.production.example`: vervang de foute `FERNET_SALT`-comment door `TOKEN_ENCRYPTION_KEY` en vul de ontbrekende vars aan (SMTP/MICROSOFT_*/ANTHROPIC/SENTRY — zie docker-compose.prod.yml welke verwacht worden).
4. **H5 ufw:** `ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable`. Test daarna direct site + SSH (nieuwe verbinding openen vóór oude sluiten!). NB: poort 3100 (Recruitment) bewust NIET openen — loopt via Caddy.

**Verificatie:** site bereikbaar, SSH werkt, mail-koppeling opnieuw verbonden of taak voor Arsalan genoteerd.

## Afsluiting
- SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken (READY/CONN-items afvinken met commit-hashes), git tag `sessie-159`, push.
- Wat niet af is: eerlijk noteren onder "Volgende sessie".

**NIET in deze sessie:** RLS fase 2, Exact-activatie, FIN-2 afwikkel-wizard (alle drie mét Arsalan), CONN-7 t/m 13 (polish-batch later).
