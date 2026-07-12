# Codex-masterprompt — Luxis overname (12 juli 2026)

> **Voor Arsalan:** plak dit héle bestand in Codex als eerste bericht. Codex neemt het werk
> over van drie parallelle Claude-sessies (S200, S201, S202). Begin in **Sol Ultra**
> (uitzoekwerk). Codex vertelt je zelf wanneer je naar **Sol High** (bouwwerk) moet
> omschakelen. Over ~3 uur checkt Fable (Claude) alles van Codex na.

---

Je bent vanaf nu de bouwer/onderzoeker op **Luxis** — een praktijkmanagementsysteem voor
Nederlandse advocatenkantoren (eerste klant: Kesting Legal, 1 advocaat, incasso). Je werkt
in de repo `C:\Users\arsal\Documents\luxis`. Je neemt werk over dat Claude (Fable/Opus) is
begonnen. **Doe letterlijk wat Claude altijd doet** — de regels hieronder zijn niet
onderhandelbaar. Arsalan is IT-recruiter, géén developer: leg beslissingen in gewone taal uit.

## 0. Modelrouting — LEES DIT EERST (hard)

Er zijn twee soorten werk. Jij bepaalt welk model je nodig hebt en zegt het tegen Arsalan:

- **Uitzoekwerk (onderzoek, audit, meten, lezen)** → **Sol Ultra**.
- **Bouwwerk (code schrijven, fixen, migraties, tests)** → **Sol High**.

Wanneer een fase van soort wisselt, **stop en print een duidelijke banner**, bijvoorbeeld:

```
============================================================
>>> ARSALAN: zet mij nu op Sol ULTRA (uitzoekwerk) <<<
============================================================
```
of
```
============================================================
>>> ARSALAN: zet mij nu op Sol HIGH (bouwwerk) <<<
============================================================
```

Wacht na de banner tot Arsalan bevestigt dat hij is omgeschakeld, en ga dan pas verder.
De volgorde in deze prompt is zó gekozen dat je maar **één keer** hoeft te wisselen:
eerst alle uitzoekwerk (Ultra), daarna al het bouwwerk (High).

## 1. Onboarding — lees deze bestanden vóór je iets doet

Lees, in deze volgorde, zodat je Luxis volledig begrijpt (het zijn er niet veel, allemaal kort):

1. `CLAUDE.md` (repo-root) — dé regels: financiële precisie, multi-tenant, security, werkwijze.
2. `backend/CLAUDE.md` + `frontend/CLAUDE.md` — module-patroon backend/frontend.
3. `docs/dutch-legal-rules.md` — wettelijke rente, WIK-staffel, art. 6:44 BW, 14-dagenbrief.
4. `docs/ARCHITECTUUR-KAART.md` — de verbindingskaart: hoe alle systemen aan elkaar hangen, in 2 pagina's.
5. `SESSION-NOTES.md` (bovenste ~40 regels + de S200/S202-entries) — wat er net gebeurd is.
6. `LUXIS-ROADMAP.md` (de "🎯 Huidige prioriteit"-sectie) — status en prioriteiten.
7. `docs/security/rollen.md` — rollen-matrix (admin/advocaat/medewerker).

**Existence-check-discipline:** vóór je "X ontbreekt / laten we X bouwen" concludeert, controleer
eerst met grep/glob of het al bestaat. Nooit gokken.

## 2. De regels waar je je ALTIJD aan houdt (uit `CLAUDE.md`)

- **Nederlandse UI, Engelse code.**
- **Geld = Python `Decimal` + PostgreSQL `NUMERIC(15,2)`. NOOIT float.** `ROUND_HALF_UP`
  expliciet. Elke geldberekening krijgt een test.
- **Multi-tenant:** modellen erven `TenantBase` (heeft `tenant_id`). Elke query filtert óók zelf
  op `tenant_id` — vertrouw niet alleen op RLS/middleware. Nieuwe tabel met `tenant_id` → RLS in
  **dezelfde** migratie (`apply_rls(op.get_bind())`).
- **Nieuwe route → auth verplicht** (`Depends(get_current_user)` of `require_role(...)`), tenzij
  echt publiek (login/OAuth) → dan expliciet + rate-limit.
- **Nooit secrets in code** — alleen uit env (`app/config.py`). Geen `NEXT_PUBLIC_*` met secrets.
- **Geen aannames:** verifieer alles met code/git-historie/logs/DB vóór je wijzigt. Twijfel →
  eerst onderzoeken. Bij regressies: zoek in git-historie wanneer het brak.
- **Chirurgisch fixen:** alleen de kapotte zaak; nooit breed features/security terugdraaien.
- **Bugs:** eerst een rode test → fix → groen. Triviale bugs mogen direct.
- **E-mailtests:** recipient ALTIJD overschrijven naar `arsalanir@hotmail.com`. NOOIT
  klanten/wederpartij/lisanne@.
- **Mailslot NIET aanzetten** (`app_config.outbound_mail_locked` staat bewust op `true`).
- **Geen destructieve DB-acties** (volumes/DB wissen, migraties terugdraaien) zonder expliciete
  toestemming van Arsalan.
- **Commit + push per afgeronde taak** (conventional commits: `feat(module):`, `fix(module):`,
  etc.), daarna deploy (zie §7). Werk niet op één grote berg; commit klein.
- **Nooit "klaar" zonder bewijs** (test/build/handmatige check). Onzekerheid benoemen, niet
  verbergen. "Niet geverifieerd" is een geldig label.

Werkritme (Claude's discipline — neem 'm over): meet in de bron en kwantificeer; probeer je eigen
conclusie te weerleggen vóór je 'm opschrijft; wijs vóór elke schrijfactie de zin in de opdracht
aan die het vraagt (extra's = voorstel, niet doen); vóór "klaar" een bewijs-audit per claim.

---

## 3. FASE A — [Sol Ultra] Security-audit afmaken: het mailpad (Blok 2 van S202)

**Waarom:** Fable deed de S202 security-delta-audit (alles sinds 8 juli), maar Blok 2 (het
mail-verstuurpad) is afgebroken door tokengebrek. Jij maakt het af. **100% read-only** —
prod-queries mogen, geen mutaties, geen mail versturen, geen fixes bouwen (alles wordt bevinding).

**Opdracht:** staat kant-en-klaar onderaan `docs/security/S202-delta-audit.md` onder
"Vervolgprompt voor Sol/Codex — Blok 2 (mailpad)". Volg die exact. Kort: header-/CR-LF-injectie
(o.a. de `_imap_quote`-fix, commit `8b658c7`, én hetzelfde patroon elders zoeken), mailslot
fail-safe op élk verstuurpad, wie mag versturen (rollen), log-lekken, IMAP read-only,
credential-opslag, recipient-validatie op systeempaden.

**Klaar-criterium:** vervang de ⚠️-placeholder onder "## Blok 2 — Mailpad" in
`docs/security/S202-delta-audit.md` met je bevindingen (ernst + bewijs `bestand:regel` of
prod-query + fix-recept), plus een "geverifieerd OK"-lijst. Werk daarna de samenvattingstabel en
de fix-prioriteitenlijst bovenaan/onderaan dat rapport bij met de nieuwe mailpad-bevindingen.

**Prod-toegang (read-only):**
`ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose exec -T db psql -U luxis -d luxis -c \"<SELECT ...>\""`

---

## 4. FASE B — [Sol Ultra] Facturatie-migratie-onderzoek afronden (S201)

**Waarom:** Fable begon het read-only onderzoek "wat is er bij de BaseNet→Luxis-migratie blijven
liggen (facturen, uren, boekhouding)?" en mat de veldsemantiek volledig door, maar raakte door de
tokens heen vóór de prod-match-query, het uren-advies, het Donker/Dinc-spoor en de twee
outputdocumenten.

**Startpunt (alles al gemeten, je hoeft niet opnieuw te meten):**
`docs/sessions/S201-HANDOFF-naar-Sol.md` — leest als een complete overdracht met per onderdeel
"GEMETEN" vs "NOG TE DOEN". De oorspronkelijke opdracht + constraints:
`docs/sessions/PROMPT-S201-onderzoek-facturatie.md`. **100% read-only**, geen import uitvoeren.

**Nog te doen (uit §2-§6 van het handoff-doc):** prod-match-query (rcode→contact, D-code→case),
uren-advies (1.320 Hour-records), Donker/Dinc-spoor hard toetsen, dan de twee outputdocumenten:
- `docs/research/S201-facturatie-recept.md` — bouwklaar migratie-recept + mapping + beslislijst.
- `docs/research/S201-volledigheidsmatrix.md` — per BaseNet-entiteit: geïmporteerd? relevant? actie.

**Klaar-criterium:** beide documenten bestaan, gevuld met gemeten cijfers (niet geschat), en de
beslislijst voor Arsalan is concreet (per groep: importeren ja/nee + aantallen/euro's).

> Na Fase B: **print de "zet mij op Sol HIGH"-banner** en wacht op Arsalan. Vanaf hier is het bouwwerk.

---

## 5. FASE C — [Sol High] Voorkant-fixes (S200-bevindingen)

**Waarom:** Fable's S200-audit ("de voorkant liegt") leverde 19 genummerde bevindingen met bewijs.
Dit is de grootste bouwklus en raakt Lisanne direct.

**Opdracht:** staat kant-en-klaar in `docs/sessions/PROMPT-S203-voorkant-fixes.md` — volg die
exact, in de volgorde van de samenvattingstabel. Werklijst met bewijs per bevinding:
`docs/sessions/S200-BEVINDINGEN.md`. Per fix: eerst een rode test (waar zinvol) → fix → groen →
commit → push → deploy. Snelste winst eerst: tijdlijn-crash (#13, 1 regel), hernoemen-knop (#4),
AI-draft €0-fallback markeren (#3).

**Klaar-criterium:** elke afgewerkte bevinding krijgt ✅ in de tabel onderin `S200-BEVINDINGEN.md`;
verificatie per §6 hieronder groen; niet doorgaan met een kapotte taak.

---

## 6. FASE D — [Sol High] Security-fixes (S202-bevindingen)

**Waarom:** de S202-audit (incl. jouw Fase A) leverde concrete beveiligingsfixes. Fix ze in
volgorde van ernst.

**Opdracht:** `docs/security/S202-delta-audit.md` heeft onderaan een "Fix-prioriteit"-lijst. Werk
die af, hoog eerst:
1. **H1** — cross-tenant `CaseFile` bij mailbijlage-opslag (`email/sync_router.py:527-581`): voeg
   de tenant-guard toe die elders in datzelfde bestand al staat (`_assert_case_in_tenant`).
2. **H2** — fail-open op de "betaald"-guard (`cases/service.py:744-747` + `incasso/service.py:479-490`):
   maak fail-closed (bij rekenfout `BadRequestError`, niet €0 aannemen).
3. **H3** — "Geïnd"-rapportage telt verwijderde betalingen (`dashboard/reports_service.py:62-68,220-230`):
   voeg `Payment.is_active.is_(True)` toe.
4. **M1** — bulk-status lengtecap; **M2** — auto-advance terminale-stap-check.
5. Plus de fixes die uit jouw Fase A (mailpad) komen.
   (**M3** — app draait als DB-superuser / "Fase 2" — is een grote klus; NIET nu bouwen, alleen
   als openstaand punt laten staan tenzij Arsalan expliciet vraagt.)

Per fix: rode test → fix → groen → commit → push → deploy. Markeer afgewerkte bevindingen in het
rapport.

---

## 7. Verificatie + deploy (elke bouwfase)

**Verificatie (draai wat de wijziging raakt, niet blind de hele suite):**
- Backend-tests: `docker compose exec backend pytest tests/ -v` (of `-k "<keyword>"` gericht)
- Lint: `docker compose exec backend ruff check app/`
- Frontend-build: `cd frontend && npm run build` (of `npx tsc --noEmit` na TS-wijzigingen)
- Fixes met UI-impact: ook visueel + functioneel in de browser checken ("grondig" = niet alleen tests).

**Deploy na commit+push (autonoom, via SSH):**
- Alleen backend: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend && docker compose up -d backend && docker image prune -f"`
- Backend + migratie: idem met `&& docker compose run --rm backend python -m alembic upgrade head` ná de build, vóór `up -d`.
- Alleen frontend: vervang `backend` door `frontend`.
- Verifiëren: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose ps && docker compose logs backend --tail 5"`
- **Volgorde cruciaal: eerst `build`, dán migreren.** Geen `--no-cache` standaard (vreet schijf).

## 8. Afronding + overdracht terug naar Claude

- Werk `SESSION-NOTES.md` bij (nieuwe entry bovenaan, oudste naar `docs/archief/SESSION-ARCHIVE.md`
  als er >10 zijn) en `LUXIS-ROADMAP.md` (bevindingen op ✅ / nieuwe BUG-#). Houd de kop kort.
- Zet een git-tag per afgeronde grote stap als je wilt (`sessie-203` etc.), niet verplicht.
- **Over ~3 uur checkt Fable (Claude) al jouw werk na.** Laat het daarom makkelijk controleerbaar
  achter: kleine commits met duidelijke messages, per bevinding welk bewijs je draaide, en een
  expliciete "niet geverifieerd"-lijst voor alles wat je niet zelf hebt kunnen bewijzen.
- Twijfel je juridisch of over scope? Flag het in je notitie, stop niet — maar bouw geen nieuwe
  features buiten deze vier fasen.

**Samengevat de volgorde:** Ultra → Fase A (mailpad-audit) → Fase B (facturatie-onderzoek) →
*banner: switch naar High* → Fase C (voorkant-fixes) → Fase D (security-fixes) → afronden.
