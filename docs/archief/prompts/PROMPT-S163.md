# Sessieprompt S163 — Audit-MEDIUMs afhechten (bounded batch)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisiewerk — rekenkern/pipeline + transactie-semantiek; schone context).
**`/effort max` aan het begin.**

---

## Waarom deze sessie
S162 hechtte de S161-security-residuals af (reproduceerbare builds + dep-audit CI-gates + VPS-drift). Wat nu open staat uit de 2026-06-01-systeemaudit zijn vier **bounded** MEDIUMs — concreet, geïsoleerd, elk rood→groen, autonoom te doen. Geen nieuwe features (besluit S160: géén autonome AI-agent).

## Context laden bij start
- `SESSION-NOTES.md` — **S162-entry** bovenaan (wat net is afgehecht + valkuilen).
- `LUXIS-ROADMAP.md` — regel ~118 "Resterend uit audit" + de MEDIUM-tabel voor de exacte bevindingen.
- Diepe details per bevinding: `.audit/AUDIT-REPORT.md` (gitignored, bevat data — alleen lokaal/VPS).

## Taak (op volgorde, elk rode→groen / lokaal geverifieerd vóór push)
Vier bounded MEDIUMs, elk eigen conventional commit + push (auto-deploy):

1. **#66 — relatie-validatie (bounded).** Zie audit-bevinding. Rode test eerst → fix → groen.
2. **#70 — saldo row-lock (eigen blokje).** Concurrency/race op saldo-update → `SELECT ... FOR UPDATE` of equivalent. **Let op transactie-semantiek** (de S161-lockout-bug zat precies hier: `override_get_db` spiegelt nu get_db, dus endpoint-tests dekken commit/rollback echt — gebruik dat).
3. **#73 — bedrag-match op totale schuld via grand_total-cache (bounded).** Match betaling tegen de volledige schuld (incl. rente/BIK) i.p.v. alleen hoofdsom. Hergebruik de bestaande `get_financial_summary`/grand_total-logica (zie AUDIT-H4-fix). Geld onafhankelijk narekenen tegen een wettelijk ijkpunt + test.
4. **#97 — verweer-switch via `move_case_to_step` (bounded).** Verweer-tracking moet door de centrale step-transitie lopen, niet los. Pipeline-test rood→groen.

## Verificatie
- Per change: relevante test rood→groen; bij raken van gedeelde infra (conftest/rekenkern) → volledige suite. Eén run tegelijk (dev-DB).
- Geld: onafhankelijk narekenen tegen `docs/dutch-legal-rules.md` ijkpunten, niet alleen "test groen".
- CI groen vóór en na (`gh run list`). Test lokaal vóór push (memory). Auto-deploy groen bevestigen.

## Constraints (NIET doen)
- Geen nieuwe features. Geen autonome AI-agent. Geen RLS fase 2 / Exact / FIN-2 zonder Arsalan.
- **#95 (Fernet-key los van SECRET_KEY)** NIET in deze batch — vereist token-re-encrypt + deploy-coördinatie (zoals de DB-rolwissel). Apart venster mét Arsalan.
- `--no-cache` only bij dep-wijziging (disk-pressure, `deploy-regels`).

## Alleen mét Arsalan (niet autonoom — plannen liggen klaar)
- **Non-superuser DB-rol (RLS fail-closed):** plan + premortem in `docs/security/rls-nonsuperuser-owner-plan.md`. Onderhoudsvenster + kopie-dry-run.
- **M0b / Outlook her-koppelen / livegang met Lisanne.**

## Commit & deploy
Per fix conventional commit + `git push origin main` → auto-deploy. `gh run list` groen houden.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-163` + prompt S164.
