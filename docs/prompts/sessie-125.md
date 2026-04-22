Sessie 125 — Audit-findings Batch 2: BIK-BTW + rente-na-deelbetaling
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees SESSION-NOTES.md (sessie 124, bovenaan) en LUXIS-ROADMAP.md (sectie 'Audit 124 — 4-assige Opus 4.7 audit'). Rapporteer compact: welke audit-findings zijn in sessie 124 gefixt, welke staan nog open onder AUD124-01 en AUD124-02, en welke bestanden zijn het relevantst. Onder 400 woorden."

Lees daarna zelf pas on-demand:
- `docs/audits/audit-1-financial.md` — voor exacte bevinding-details
- `backend/app/collections/wik.py` + `backend/app/collections/interest.py` — voor huidige implementatie
- `backend/app/collections/service.py` (regel ~195-260 register_payment) + `backend/app/documents/docx_service.py:366` — voor aanroeppunten

## Taak

**Twee findings uit Audit 124, kies in overleg met gebruiker volgorde:**

### AUD124-01 — BIK-BTW voor niet-BTW-plichtige cliënten (Critical, 2-3u)
Nu wordt `calculate_bik(total_principal)` overal zonder `include_btw=True` aangeroepen. Voor cliënten die géén BTW kunnen verrekenen (VvE, stichting, consument, sommige ZZP'ers, VOF) moet de advocaat 21% BTW over de BIK doorbelasten aan de debiteur. Gevolg nu: €99,75 minder geïnd per dossier van €3.500 hoofdsom.

**Te bouwen:**
1. Migratie: `Contact.is_btw_plichtig` Boolean kolom, default True, NOT NULL. Backfill bestaande records op True (meeste cliënten BV's).
2. `Contact` model + schemas bijwerken.
3. UI: checkbox "Cliënt kan BTW verrekenen" op cliënt-edit formulier (default aangevinkt). Helptekst: "Uitvinken bij VvE, stichting, consumenten, VOF — dan wordt 21% BTW over BIK doorbelast aan de debiteur."
4. In `backend/app/collections/service.py::register_payment` (~r240) en `backend/app/documents/docx_service.py::build_base_context` (~r366): haal `client.is_btw_plichtig` op en geef `include_btw=not client.is_btw_plichtig` door aan `calculate_bik(...)`.
5. Test: vordering €3.500 op VOF-cliënt → BIK moet €574,75 zijn (= €475 + €99,75 BTW). Vordering €3.500 op BV-cliënt → BIK blijft €475.
6. Zorg dat alle 4 template-scenario's in `scripts/render_audit_samples.py` kloppen na de fix.

### AUD124-02 — Rente-na-deelbetaling art. 6:44 BW (Critical, 3-4u, kleinere bedragen maar juridisch fout)
Nu gebruikt `calculate_case_interest` altijd `claim["principal_amount"]` — eerdere deelbetalingen verlagen de hoofdsom niet in de berekening. Art. 6:44 BW: betaling gaat eerst naar kosten, dan rente, dan principal. De principal-allocatie van een betaling moet de hoofdsom verlagen vanaf die datum voor toekomstige renteberekening.

**Te bouwen:**
1. Scenario-tests toevoegen (met expected bedragen uit hand-calc): dossier €5000, deelbetaling €1000 na 4mnd, rente berekenen na 10mnd. Verwacht resultaat: ~€270,82 (nu ~€279,18).
2. Payment-history integreren: `calculate_case_interest` krijgt `payments: list[Payment]` erbij, splitst compound-loop in sub-perioden rond elke payment-datum, past principal aan op basis van `payment.allocated_to_principal`.
3. Backward-compatible: als geen payments → huidig gedrag.
4. Unit test edge cases: 2+ deelbetalingen, deelbetaling op anniversary-datum, deelbetaling die hoofdsom op €0 brengt.

**Start met EnterPlanMode** voor AUD124-02 — het is een grotere refactor van de compound-interest loop.

Voor AUD124-01: relatief simpel, mag direct mits de user de checkbox-default confirmeert (True voor bestaande cliënten).

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/test_wik.py tests/test_interest.py tests/test_payment_distribution.py -v`
- Lint: `docker compose exec backend ruff check app/collections/ app/documents/`
- Render sample brieven opnieuw: `python scripts/render_audit_samples.py` — open `docs/audits/rendered-samples/index.html` en verifieer visueel dat BIK-bedrag met BTW klopt voor VOF-scenario.
- Frontend (alleen AUD124-01): `cd frontend && npx tsc --noEmit`

## Constraints
- Geen worktrees, direct op main
- Start EnterPlanMode voor AUD124-02 (grote refactor)
- Pre-mortem verplicht (3 risico's) in het plan
- AUD124-01 en AUD124-02 mogen in aparte commits
- Roadmap-entries AUD124-01 en/of AUD124-02 markeren als ✅ met datum
- Geen nieuwe features buiten scope
- Fix één finding volledig voordat naar volgende overgegaan wordt

## Commit + deploy
Conventional: `fix(collections): include BTW on BIK for non-VAT clients (AUD124-01)`, `fix(interest): apply art. 6:44 BW payment allocation to principal (AUD124-02)`.

Deploy na elke afgeronde finding:
```
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend && docker compose up -d backend && docker compose exec -T backend python -m alembic upgrade head && docker image prune -f"
```

## Sessie afsluiten
- SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken (markeer AUD124-01/02 als ✅)
- `git tag -a v125-stable -m "Sessie 125 — Audit batch 2" && git push origin v125-stable`
- Prompt voor sessie 126 schrijven (volgende audit-batch of nieuwe feature)
