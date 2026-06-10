# Sessieprompt S161 — Security-diepte audit (vóór livegang met echte cliëntdata)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisie — security is precisiewerk; schone context vereist, NIET aan het eind van een volle sessie).

---

## Waarom deze sessie
Luxis gaat live met **echte cliënt-PII van meerdere advocatenkantoren (tenants)**. Vóór die stap moet de security-diepte gedaan zijn. Grootste angst: **cross-tenant datalek** (kantoor A ziet data van kantoor B) of inbraak. In S160 is alvast **SEC-3 (secrets) gedaan en schoon bevonden** (zie hieronder). Deze sessie: de rest.

## Context laden bij start
Lees zelf:
- `SESSION-NOTES.md` — S160-entry + subsectie "Vervolg ná de sessie-160-tag" (wat al schoon is).
- `docs/premortem-ai-incasso-agent-2026-06-10.md` — **besluit: GEEN autonome AI-agent bouwen.** De assistent (AI maakt concept, Lisanne beslist) blijft. Geen nieuwe features deze sessie — alleen security + finish naar live.

## Al gedaan (S160) — niet overdoen
**SEC-3 secrets ✅ schoon:** geen secrets in repo/git-historie; SECRET_KEY-guard `sys.exit(1)` (`main.py:59`); prod `.env` correct (`APP_ENV=production`, `APP_DEBUG=false`, CORS = enkel het domein, SECRET_KEY 86 tekens). Rate-limiting op auth bestaat (`main.py:114`), `/docs` uit in prod, CORS niet-wildcard.

## Taak — SEC-1/2/4/5/6/7/8 (multi-agent fan-out)
**Aanpak:** stuur parallelle `security-reviewer`-agents de echte code in (één per dimensie), elk leest met Read/Grep/Glob en levert bevindingen (SEVERITY · file:regel · WAT · EXPLOIT · FIX). Daarna: synthese → echte bevindingen fixen met **rode test eerst → groen**. Niet alles tegelijk — prioriteer SEC-5.

1. **SEC-5 — Tenant-isolatie / IDOR (BELANGRIJKSTE).** Kan kantoor A via een id (factuur/dossier/contact/document) data van kantoor B opvragen? Is élk endpoint tenant-gescoped (middleware + RLS, niet alleen één van de twee)? Test cross-tenant GET/PUT/DELETE. RLS is actief sinds S150 (Model A/SET ROLE) — verifieer dat er geen endpoint omheen leunt.
2. **SEC-1 — Auth/JWT.** Algoritme vastgepind bij decode (geen alg-confusion)? exp gecontroleerd? logout/wachtwoordwijziging invalideert tokens? user-enumeration via login-timing/foutmeldingen? token in localStorage (XSS)?
3. **SEC-2 — Injectie.** Rauwe SQL (f-strings i.p.v. params), template-injectie (docxtpl/WeasyPrint met user-input), command-injectie.
4. **SEC-6 — File-upload.** Type/grootte-validatie, path-traversal, XSS via bestandsnaam, hoe/waar bestanden geserveerd worden (case-files, contact-terms PDF's).
5. **SEC-7 — Rate-limiting/brute-force.** Dekking verifiëren (bestaat al op auth) — ook op andere gevoelige endpoints? account-lockout?
6. **SEC-8 — Exposure.** Security-headers (HSTS/CSP/X-Frame-Options via Caddy?), error-responses lekken geen stacktraces, CORS-config (al goed — bevestigen).
7. **SEC-4 — Dependencies.** `cd frontend && npm audit fix` (zónder --force) → daarna `npx tsc --noEmit` + `npm run build` groen → commit. Backend: `pip-audit` (bv. `uvx pip-audit` of in container met writable cache). De 4 npm-vulns (picomatch ReDoS, postcss XSS) zijn build-tooling, laag risico — maar oppakken.

## Verificatie
- Per code-fix: rode test eerst → fix → groen (`docker compose exec backend pytest ... -v`).
- SEC-5 cross-tenant: schrijf een echte test (tenant A token mag tenant B's resource niet ophalen → 404/403).
- Frontend dep-fix: `npx tsc --noEmit` + `npm run build` groen vóór commit.
- Ruff op gewijzigde `app/`-bestanden (writable `RUFF_CACHE_DIR=/tmp`).

## Constraints (NIET doen)
- Geen nieuwe features. Geen autonome AI-agent (besluit S160). Geen RLS fase 2 / Exact / FIN-2 zonder Arsalan.
- Niet de hele audit forceren in één sessie — prioriteer SEC-5, lever bevindingen + gefixte echte issues, rest documenteren.

## Commit
Per fix conventional commit (`fix(security): ...`) + `git push origin main` → auto-deploy. Check `gh run list` blijft groen.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken (SEC-bevindingen + hashes), git tag `sessie-161`, prompt S162.
