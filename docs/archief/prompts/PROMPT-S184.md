cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 184 — Fix-sprint audit S183 (Opus)

## Model + rol
Opus, `/effort max`. Bouwsessie met het auditrapport als werkorder:
**`docs/research/audit-S183-architectuur-security.md`** — lees dat eerst volledig.
Elke fix: eerst rode test, dan fix, dan groen (geldpaden verplicht).

## Context laden bij start
Gebruik de `luxis-researcher` subagent:
"Lees SESSION-NOTES.md (S183-entry) en docs/research/audit-S183-architectuur-security.md
(bevindingen + werkorder). Geef compacte samenvatting van de 5 werkorder-punten."

## Taak — de werkorder, in deze volgorde

1. **S183-3 [HOOG] Pro-rata bij creditfacturen** (`app/collections/interest.py:524-565`,
   `_build_claim_reductions`). Rode test eerst met het bewezen scenario uit het rapport
   (+1000/−200/+200, betaling 500 → nu 600 afgeboekt). Fix-richting: negatieve vorderingen
   buiten de pro-rata-basis; creditbedrag als verrekening. Daarna de 4 heropeningszaken
   (IN100334, IN100469, IN100505, IN100553) op prod herberekenen/controleren (read-only
   vergelijking vóór/na volstaat — bedragen pas aanpassen als Arsalan akkoord is).
2. **S183-1 RLS op `learned_answers` + drift-guard.** Migratie die `rls_statements`
   (uit `app/security/rls.py`) op `learned_answers` toepast, plus een pytest die op het
   echte schema afdwingt: élke tabel met `tenant_id` (behalve `users`) heeft FORCE RLS +
   policy. Die test moet falen op een nieuwe ongedekte tabel.
3. **S183-2 Rolwissel overleeft commits.** Her-toepassing van `SET LOCAL ROLE` +
   `app.current_tenant` ná elke commit binnen een verzoek — één structurele fix
   (bv. SQLAlchemy `after_begin`/session-event), niet 31 losse plekken. Bewijs met een
   test die na een commit `current_user` controleert.
4. **S183-4 Betaling op/vóór verzuimdatum** (`interest.py:276`) — kan mee met punt 1.
5. **`--no-cache` uit `.github/workflows/deploy.yml:29`** (één regel).
6. **Security-regels verankeren (klein, uit vragen Arsalan 8 juli):** (a) sectie
   "Security-regels (HARD)" in `CLAUDE.md`: nieuwe tabel met `tenant_id` → RLS-statements
   in dezelfde migratie verplicht; nieuwe route → auth-dependency verplicht; nooit
   sleutels/secrets in code (alleen env); uploads via de bestaande gevalideerde helpers.
   (b) half A4 `docs/security/rollen.md`: wat admin/advocaat/medewerker mogen (22 routes
   zijn admin-only, rest = elke actieve gebruiker; grep `require_role` als bron).

## Binnengekomen: akkoord Lisanne heropening (8 juli)
Zie het antwoordblok bovenaan `docs/sessions/LISANNE-A4-heropening.md`: 7 restant-dossiers
sluiten (NIET IN100166 — blijft open om te innen), starten met LegalWork B.V. De
heropening zelf is een APARTE sessie ná deze fix-sprint (S185, draaiboek
`docs/plans/PLAN-heropening-werkvoorraad.md`) — de rentefix van punt 1 moet eerst, die
raakt 3 zaken uit de heropeningslijst. In deze sessie mag wél: de 7 dossiers sluiten als
Arsalan dat vraagt (kleine, omkeerbare actie; workflow-guard checkt saldo).

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -k "interest or rls or payment" -v`
  (full suite alleen bij de sessie-afsluiting — punt 3 raakt gedeelde infrastructuur, dus
  dan wél de volledige run)
- Lint lokaal vóór push: `uvx ruff check app/` (vanuit `backend/`)
- Na deploy: healthcheck + de RLS-guard-test tegen prod-schema draaien

## Constraints (wat NIET doen)
- Heropening werkvoorraad blijft wachten op Lisanne. D-Break (IN100555) blijft dicht.
- Geen bedragen op prod aanpassen zonder expliciet akkoord van Arsalan (punt 1: eerst
  vóór/na-vergelijking laten zien).
- Backblaze US-bucket wissen is een aparte actie (~10 juli): check `/var/log/luxis-backup.log`
  op 2 geslaagde EU-runs (8+9 juli, "Off-site upload complete") — zo ja: US-bucket
  `Luxis-backup` wissen, oude key intrekken, remote `luxis-backup` verwijderen, wisbewijs
  in SESSION-NOTES. Zo nee: laten staan en melden.

## Commit
Per fix een conventional commit + push naar main. Deploy automatisch via SSH
(deploy-regels skill); punt 2 heeft een migratie → build eerst, dan migreren.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-184`, PROMPT-S185.
