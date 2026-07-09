# Sessieprompt S162 — Security-residuals afhechten + reproduceerbare builds

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisiewerk — CI/deploy + transactie-semantiek; schone context).

---

## Waarom deze sessie
S161 deed de security-diepte: SEC-5 (tenant-isolatie) robuust bevonden, 4 echte fixes live (lockout, token-revocatie, upload-cap, deps), deploy-blokkade opgelost. Wat overbleef zijn **laag-risico hardening-residuals** die de go-live-veiligheid afronden — concreet, bounded, autonoom te doen. Geen nieuwe features (besluit S160: géén autonome AI-agent).

## Context laden bij start
- `SESSION-NOTES.md` — **S161-entry** (volledige security-bevindingen + de 5 residuals + valkuilen).
- `LUXIS-ROADMAP.md` — "Voortgang S161"-blok.

## Taak (op volgorde, elk rode→groen / lokaal geverifieerd vóór push)

1. **✅ AL GEDAAN in de S161-vervolg (`775076b`):** harness-gap gedicht — `override_get_db` spiegelt nu get_db (commit/rollback), volle suite onveranderd 987→989 passed. Ook de 2 dev-Mailpit-fails deterministisch gemaakt. **Niet overdoen.** (Coverage-baseline gemeten: 61%, `test_tenant_context.py` toegevoegd, `tests/COVERAGE.md` bijgewerkt met risico-gesorteerde gap-backlog — zie `d186088`.) **S162 begint bij taak 2.**

2. **Reproduceerbare builds + dep-scanning in CI.** Geen lockfile nu + deploy `build --no-cache` met `>=` floors = niet-reproduceerbaar. (a) Genereer `backend/uv.lock` (`uv lock`) en laat de Dockerfile/CI 'm gebruiken. (b) Voeg een `pip-audit`-stap toe aan `.github/workflows/ci.yml` (non-blocking of blocking-met-allowlist — kies + licht toe; `pip` zelf negeren). Frontend: overweeg `npm audit --audit-level=high` in CI. Verifieer CI groen.

3. **App als non-superuser owner in prod (RLS fail-closed).** Nu verbindt de app als superuser + `SET LOCAL ROLE luxis_app` per request → RLS wordt bypassed ná een mid-request commit (nu onschadelijk, latent). Onderzoek of de prod-DB-user veilig naar een non-superuser owner-rol kan zodat FORCE RLS ook zónder SET ROLE closed faalt. **Niet-triviaal/infra → eerst plan + premortem, NIET blind op prod.** Mag ook puur gedocumenteerd worden als het risico op prod-downtime te groot is.

4. **VPS-drift opruimen (klein).** Op de VPS staan ongecommitte `scripts/disk_guard.sh` + `setup-uptime-monitoring.sh` (S159-hardening, alleen op server) → commit ze in git zodat ze niet bij elke pull conflicteren. Zwerf-`test_followup.py` (root + `backend/app/`) + oude `.env.bak-*`: verwijderen (bevestig eerst dat ze niets bevatten dat bewaard moet — `.env.bak`-bestanden bevatten secrets, NIET committen, alleen lokaal op VPS laten of veilig verwijderen).

## Verificatie
- Per change: relevante test rood→groen; bij raken van gedeelde infra (conftest) → volledige suite. Eén run tegelijk (dev-DB).
- CI groen vóór en na (`gh run list`). Test lokaal vóór push (memory).
- Bij CI/deploy-wijziging: bevestig dat de auto-deploy nog groen draait.

## Constraints (NIET doen)
- Geen nieuwe features. Geen autonome AI-agent. Geen RLS fase 2 / Exact / FIN-2 zonder Arsalan.
- Taak 3 niet blind op prod forceren — plan/premortem of documenteren.
- `--no-cache` alleen bij dep-wijziging (disk-pressure, zie `deploy-regels`).

## Commit & deploy
Per fix conventional commit + `git push origin main` → auto-deploy (nu wéér werkend sinds S161). Check `gh run list` blijft groen.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-162` + prompt S163.
