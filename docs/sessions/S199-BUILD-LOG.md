# S199 — Bouwlog (Sol bouwt, Claude verifieert)

Werkvorm: codex-build. Spec: `PROMPT-S199.md` (bevroren, door Fable geschreven in S198).
Bouwer: Sol (`gpt-5.6-sol`, effort xhigh), sessie `019f534a-8368-7470-a000-4314e2c2cc12`.
Scope: taak 1–4 + code-delen taak 5. Uitgesloten: taak 6 en prod-data-vegen (per stuk
akkoord Arsalan) — mailslot bleef uit.

## Ronde 1 — Sol's bouw (12 juli, ~22:27–01:38, één run)

30 bestanden, +503/−2492. Eigen proof: 1218 tests groen (24m58s), ruff schoon,
tsc schoon, next build ok. Geen spec-afwijkingen gemeld. DROP-migratie blokkeerde
lokaal terecht op gevulde dev-tabellen (guard bewezen fail-closed).

## Claude's verdict (Fable, nacht 12 juli)

Volledige diff gelezen + bewijzen zelf gedraaid:

- **Taak 1** ✓ — `TERMINAL_STATUSES` in dashboard/reports/collections/ai-sweep/hooks/
  check_verjaring; per plek beoordeeld (geïnd-som is bewust betalingen-in-periode).
- **Taak 2** ✓ — `PUT /api/cases/bulk/status` via `update_case_status` (guards intact),
  auth verplicht, {updated, skipped, errors}; route botst niet met `POST /{id}/status`
  (ander werkwoord). Frontend-payload matcht 1-op-1. Tests: happy/guard-skip/tenant-iso.
- **Taak 3** ✓ — engine weg (hooks/service/router/schemas/models/env.py), taken- en
  verjaring-endpoints intact, geen achterblijvende referenties (grep backend+frontend
  schoon; `_validate_transition` in invoices = naamgenoot, ongerelateerd).
  Fasebalk: fase uit `step_category` van actuele stap; zonder stap → balk verborgen,
  geen blanco. Instellingen-blok gereduceerd tot levende AI-conceptknop.
  **Migratie zelf bewezen**: lokaal dev-relieken geleegd → upgrade gedraaid →
  3 tabellen weg, `workflow_tasks` intact (635 rijen), dode kolom weg. Guard eerder
  bewezen door Sols geblokkeerde run. Prod-telling (0 rijen verwacht) hermeten vóór
  deploy.
- **Taak 4** ✓ — Geïnd = som betalingen in gekozen periode (definitie-comment),
  maandenparam via router→hook→pagina; faseverdeling outer join + "Geen stap"
  (ook in KPI-blok), tenant-scoped join toegevoegd.
- **Taak 5 (code)** ✓ — urenfilter alleen cliënten (afgeleid uit dossiers),
  lege-staten uren/facturen-widgets, label "toegevoegd deze maand".

Zelf gedraaid: `uvx ruff check backend/app/` schoon · `tsc --noEmit` ok ·
`npm run build` ok · volledige pytest-suite → zie onder.

Notities (geen blokkades):
- Incassopercentage mengt nu periode-geïnd met lopende hoofdsom — bestaand grof
  cijfer, meenemen in S200-narekenen-audit.
- Bulk-respons toont skipped/errors nog niet in de UI-toast (updated-telling klopt).
- Cliëntenfilter uren leest max 200 dossiers (7 vaste opdrachtgevers ruim gedekt).
