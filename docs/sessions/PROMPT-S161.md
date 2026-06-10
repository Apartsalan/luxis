# Sessieprompt S161 — AUDIT-FE-1 vervolg (palette-migratie via tones.ts)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (uitvoering — mechanische, herhaalbare frontend-migratie).

---

## Context laden bij start
Lees zelf (geen subagent — die timen uit):
- `SESSION-NOTES.md` (sessie 160 + 156 bovenaan) — connectie-polish is áf; AUDIT-FE-1-recept staat in de S156-entry.
- `frontend/src/lib/tones.ts` — de centrale tone-bron (S156). Migratie = bestaande palette-classes vervangen door tone-slots, **visueel identiek**.
- `LUXIS-ROADMAP.md` alleen indien nodig.

## Eerst even checken (Arsalan-acties uit S159 — blokkeren niets, herhaald)
- **Sentry (H1):** gratis account → `SENTRY_DSN=` in `/opt/luxis/.env` + backend recreate.
- **Outlook opnieuw koppelen:** S159-H3 wijzigde `TOKEN_ENCRYPTION_KEY` → oude mailtokens onleesbaar. Vraag of dit gedaan is.
- **B2-bucket EU-regio** bevestigen (AVG).

## ⚠️ Als Arsalan erbij is / het vraagt — dan dít i.p.v. de hoofdtaak
Drie items die expliciet **mét Arsalan** moeten (ontwerp-/infra-keuze, niet autonoom):
- **RLS fase 2** (verbind ALS `luxis_app` i.p.v. SET ROLE — zie `reference_rls_enforcement` memory).
- **Exact-activatie** (eerst FIN-4: payment-sync strippen vóór live).
- **FIN-2 / CONN-7 afwikkel-wizard** (factuurvoorstel → verrekening → restant uitbetalen → sluiten; welke 'klaar'-status — twee status-systemen, zie FIN-2-row in roadmap).

## Taak (autonoom, als Arsalan er niet is) — AUDIT-FE-1 vervolg
Migreer de resterende ~57 bestanden / ~620 palette-classes naar `tones.ts` volgens het **S156-recept** (zie S156-entry):
1. Pak de ergste resterende bestanden eerst (S156 noemde: **correspondentie, agenda, taken**).
2. Per bestand: screenshot vóór → migreer hardcoded palette-classes naar tone-slots → `npx tsc --noEmit` → screenshot ná → **pixel-identiek** controleren → commit per bestand.
3. `npx impeccable detect frontend/src` mag niet stijgen (was 1 bevinding: agenda side-stripe, bewust).

## Verificatie
- Frontend: `npx tsc --noEmit` groen per bestand + screenshot-paar identiek (Playwright 1440×900, ingelogd `e2e-test@kestinglegal.nl` / `testpassword123`).
- Windows hot-reload mist soms component-edits → `docker compose restart frontend` bij stale UI (zie S160-valkuil).
- Geen backend-wijziging → geen pytest.

## Constraints (NIET doen)
- Geen status-waarden in `status-constants.ts` aanraken (eigen shades, bewust — zie S156).
- Geen RLS fase 2 / Exact / FIN-2 zonder Arsalan.
- Migratie = **visueel identiek**; geen herontwerp, geen nieuwe features.

## Commit
Per bestand conventional commit (`refactor(ui): AUDIT-FE-1 <bestand> → tones.ts`) + `git push origin main` → auto-deploy. Check `gh run list` blijft groen.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken (AUDIT-FE-1-teller + hashes), git tag `sessie-161`, prompt voor S162 schrijven die naar deze files verwijst.
