# Sessieprompt S164 — Pipeline-transitie consolideren + H25 (bounded batch)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisiewerk — pipeline-transitie + server-side enforcement; schone context).
**`/effort max` aan het begin.**

---

## Waarom deze sessie
S163 hechtte de vier bounded audit-MEDIUMs af (#66/#70/#73/#97) + een starlette-CVE-bump. Wat autonoom + bounded resteert uit de audit zijn twee items; de rest van de backlog vereist Arsalan of Lisanne (zie onder). Geen nieuwe features (besluit S160: géén autonome AI-agent).

## Context laden bij start
- `SESSION-NOTES.md` — **S163-entry** bovenaan (wat net is afgehecht + de starlette-CVE-les + valkuilen).
- `LUXIS-ROADMAP.md` — regel ~118 "✅ MEDIUM gefixt in S163" + "Resterend uit audit".
- Diepe details per bevinding: `.audit/AUDIT-REPORT.md` (gitignored, alleen lokaal/VPS).

## Taak (op volgorde, elk rood→groen / lokaal geverifieerd vóór push)
1. **`update_case` step-transitie consolideren (bounded, follow-up #97).** De case-detail step-dropdown stuurt `incasso_step_id` via `CaseUpdate` → `update_case` zet 'm met `setattr` (cases/service.py ~580) i.p.v. via `move_case_to_step` → geen `CaseStepHistory`/`pipeline_change`-log en `step_entered_at` reset niet. Laat een step-wijziging in `update_case` door `move_case_to_step` lopen (zoals `create_case` al doet). **Let op:** alleen wanneer `incasso_step_id` daadwerkelijk wijzigt; andere velden ongemoeid; `user_id` doorgeven. Rode test (CaseUpdate met nieuwe stap → CaseStepHistory + activity) → groen.
2. **#H25 — `modules_enabled` server-side afdwingen (bounded).** Per-module pricing wordt nu niet server-side gehandhaafd (alleen UI). Zie audit-bevinding H25. Endpoints van een uitgeschakelde module moeten 403/404 geven. Rode test eerst → guard → groen. **Bevestig de exacte module-set + gedrag met code (geen aannames).**

## Verificatie
- Per change relevante test rood→groen; bij raken van gedeelde infra (conftest/cases-service) → CI's volledige Backend Tests dekt dat. Eén run tegelijk (dev-DB).
- CI groen vóór en na (`gh run list`) — **let op de pip-audit-gate**: die kan rood staan door een nieuwe CVE zónder dat jij iets brak (zie S163). Check vóór je begint; los een blokkerende CVE op met een minimale `uv lock --upgrade-package <pkg>` (host-uv; container-`/app/uv.lock` is read-only).
- Test lokaal vóór push (memory). Auto-deploy groen bevestigen.

## Constraints (NIET doen)
- Geen nieuwe features. Geen autonome AI-agent.
- `--no-cache` only bij dep-wijziging (disk-pressure, `deploy-regels`).

## Alleen mét Arsalan (niet autonoom — plannen liggen klaar)
- **#95 Fernet-key los van SECRET_KEY:** vereist token-re-encrypt + deploy-coördinatie. Apart venster.
- **Non-superuser DB-rol (RLS fail-closed):** plan + premortem in `docs/security/rls-nonsuperuser-owner-plan.md`. Onderhoudsvenster + kopie-dry-run.
- **M0b / Outlook her-koppelen / livegang met Lisanne.**

## Alleen mét Lisanne
- **BTW-op-rente** (juridisch, samen met #54) · H6 14-dagenbrief · 3 derdengelden-vragen.

## Commit & deploy
Per fix conventional commit + `git push origin main` → auto-deploy. `gh run list` groen houden.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-164` + prompt S165.
