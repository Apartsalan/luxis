# Sessieprompt S160 — CONN-polish-batch (connectie-audit restant)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (uitvoering — kleine, concrete frontend/backend-fixes).

---

## Context laden bij start
Lees zelf (geen subagent — die timen uit, jouw voorkeur):
- `docs/research/connectie-audit.md` → §3 "Klein — polish" (CONN-8 t/m 12) + §5 volgorde
- `SESSION-NOTES.md` (sessie 159, bovenaan) — wat al dicht is (CONN-1/2/3/4/5/6/14)
- `LUXIS-ROADMAP.md` alleen indien nodig

## Eerst even checken (Arsalan-acties uit S159 — blokkeren niets)
- **Sentry (H1):** gratis account → `SENTRY_DSN=` in `/opt/luxis/.env` + backend recreate.
- **Outlook opnieuw koppelen:** S159-H3 wijzigde `TOKEN_ENCRYPTION_KEY` → oude mailtokens onleesbaar. Instellingen → e-mail → opnieuw verbinden. Vraag Arsalan of dit gedaan is.
- **B2-bucket EU-regio** bevestigen (AVG).

## Taak — CONN-8 t/m 12 (klein, autonoom, elk eigen commit + push)
1. **CONN-8** Rapportages doodlopend → segmenten/staven linken naar gefilterde lijsten (`/zaken?status=`-patroon bestaat al op het dashboard).
2. **CONN-9** Relatie-detail toont geen facturen/saldo → link "facturen van deze klant" via `facturen?contact_id=` (patroon bestaat).
3. **CONN-10** Uren-pagina mist "factureer deze uren"-CTA → knop naar `facturen/nieuw?case_id=` met voorgeselecteerde uren.
4. **CONN-11** Ctrl+K-zoeken dekt geen facturen/e-mails → uitbreiden in `backend/app/search/service.py:56-133` (factuurnummer F2026-xxxx + e-mail-onderwerp/afzender).
5. **CONN-12** Command-palette quick-actions missen: nieuwe factuur, agenda, incasso, bankimport, intake.

## Verificatie
- Frontend: `npx tsc --noEmit` per bestand + browser-check (Playwright, login `e2e-test@kestinglegal.nl` / `testpassword123`).
- Backend (CONN-11): `docker compose exec backend pytest tests/ -k search -v` (rode test eerst voor de nieuwe zoek-bronnen).
- Per taak: commit + push → auto-deploy. Deploy draait nu zelf `alembic upgrade` + faalt hard (S159-B3), dus check `gh run list` blijft groen.

## Constraints (NIET doen)
- **CONN-7** (afwikkel-wizard) — ontwerpkeuze, alleen mét Arsalan (zie FIN-2).
- **CONN-13** (Exact-sync-status) — pas relevant na Exact-activatie.
- Geen RLS fase 2, geen Exact-activatie, geen FIN-2-wizard.
- Polish, geen herstructurering.

## Commit
Per taak conventional commit (`feat(reports):`, `feat(search):`, etc.) + `git push origin main`.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken (CONN-items afvinken met hashes), git tag `sessie-160`, prompt voor S161 schrijven die naar deze files verwijst.
