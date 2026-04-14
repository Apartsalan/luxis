Sessie 124 — Mailsjablonen-editor (DF122-04)
Repo: C:\Users\arsal\Documents\luxis

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie DF122-04) en SESSION-NOTES.md (sessie 123). Rapporteer compact:
- Wat is in sessie 123 gebouwd
- Scope DF122-04
- Huidige architectuur email templates (backend/app/email/incasso_templates.py: alle _render_* functies + render_incasso_email dispatcher)
- Bestaande ManagedTemplate model (backend/app/documents/models.py) en sjablonen-tab.tsx — kan dit hergebruikt worden voor email templates?
Onder 500 woorden."

## Taak
**DF122-04 — Mailsjablonen-editor**

De incasso email templates staan nu hardcoded in Python (`backend/app/email/incasso_templates.py`, 25+ `_render_*` functies, ~1700 regels). Lisanne wil ze zelf kunnen aanpassen via Instellingen → Sjablonen, zonder developer.

Belangrijkste overweging: de templates mixen Dutch tekst (wat Lisanne wil aanpassen) met dynamische HTML-blokken die context data nodig hebben (vorderingen-tabel, financieel overzicht, handtekening, betalingsinstructies, etc.). Een pure WYSIWYG werkt dus niet — de dynamische blokken moeten als **tokens/placeholders** in de tekst staan, zodat Lisanne tekst kan bewerken maar de structuur intact blijft.

**Onderzoek eerst (CLAUDE.md werkwijze stap 1):**
- Hoe doen Clio, HubSpot, Mailchimp, ActiveCampaign dit? (merge tags, handlebars-style tokens, block editor met variable insertion)
- Welke aanpak past bij Luxis: rich-text editor met token-inserter? of Markdown-veld met `{{tokens}}`?

**Aanbevolen aanpak (validatie gevraagd in plan mode):**
1. Scope beperken: migreer 5 meest-gebruikte templates eerst (aanmaning, sommatie, 14_dagenbrief, herinnering, tweede_sommatie). De rest blijft hardcoded (fallback).
2. Nieuw model `EmailTemplate` (tenant-scoped) met `template_key`, `subject`, `body_html`, `is_builtin`. Builtin = seeded vanuit de huidige hardcoded renderer output (met tokens i.p.v. waardes).
3. Tokens: `{{debtor_name}}`, `{{hoofdsom}}`, `{{rente}}`, `{{bik}}`, `{{totaal}}`, `{{vorderingen_tabel}}`, `{{financieel_overzicht}}`, `{{handtekening}}`, `{{betaal_instructie}}`, `{{schuldhulp_disclaimer}}`, `{{stuiting_blok}}`, etc. — injectie gebeurt server-side bij render.
4. Renderer: `render_email_template(key, context)` → haal DB template → substitueer tokens → return HTML. Fallback naar hardcoded `_render_*` als geen DB template.
5. UI in `frontend/src/app/(dashboard)/instellingen/sjablonen-tab.tsx` uitbreiden met tab "E-mails" naast bestaande DOCX-sjablonen. Rich-text editor (Tiptap of gewoon contentEditable + toolbar) met "Variabele invoegen" knop.

**START MET EnterPlanMode** — dit is een groter onderwerp met meerdere architecturale keuzes.

## Bekende issues sessie 123 (geen blocker)
- Product dropdown werkt soms niet bij eerste keer (browser cache, Ctrl+Shift+R)
- Geen

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -v -k "email or template"`
- Lint: `docker compose exec backend python -m ruff check --no-cache app/email/ app/documents/`
- Frontend: `cd frontend && npx tsc --noEmit`
- Visueel: Instellingen → Sjablonen → tab "E-mails" → bewerk sommatie → klik Sommatie in compose → zie gewijzigde tekst

## Constraints
- Geen worktrees
- Start met EnterPlanMode (non-triviale multi-file feature met architecturale keuzes)
- Pre-mortem: 3 faal-risico's in plan opnemen
- Commit + push + deploy na elke logische stap (model → UI → renderer migratie per template)
- Tag aan einde: `v124-stable`

## Commit
Conventional: `feat(email): ...`, `feat(templates): ...`, `fix(email): ...`
Deploy: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend frontend && docker compose up -d backend frontend && docker compose exec -T backend python -m alembic upgrade head && docker image prune -f"`

## Sessie afsluiten
- `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` bijwerken
- `git tag -a v124-stable && git push origin v124-stable`
- Prompt voor sessie 125 schrijven
