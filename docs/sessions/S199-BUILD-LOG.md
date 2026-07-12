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

## Uitslag (nacht 12 juli, met nacht-akkoord Arsalan)

Eigen proof-run: **1218 passed** (18m49s; eerste run vervuild door dubbele
pytest — afgekapte docker-exec liet proces doorlopen, les genoteerd), ruff/tsc/
build zelf groen. 6 commits (28d4555…16cc905) gepusht. Prod-hermeting vóór
migratie: 0/0/0 (4 taken). **Deploy gelukt**: migratie `s199_cleanup_workflow_engine`
= head, 3 tabellen weg op prod, 4 taken intact, containers healthy.
Live-checks: bulk 401 zonder token / {0,0,[]} met token; **Geïnd €135.354,77**
(was €0); faseverdeling sluit: 10+2+5+1+10 = 28 = KPI-som = dashboard (18
in_behandeling + 10 nieuw). Rond 1 ronde, 0 fix-rondes.

## Opruimronde (12 juli, mét Arsalans go — prod, per stuk gemeten vóór mutatie)

Alle data-vegen + taak 6 UITGEVOERD op prod (elk eerst read-only geverifieerd):
- **A12 accountnaam:** seidony@ `full_name` "Lisanne Kesting" → "Arsalan Seidony" (UPDATE 1).
- **6 test-aanvragen:** alle `pending_review` → `rejected` (UPDATE 6; 0 pending over). Soft.
- **2 verweesde verjaringstaken:** IN100015/IN100127 (afgesloten, eigenaarloos) verwijderd (DELETE 2).
- **Spookstappen:** 14 dode transities + 17 inactieve stappen weg (sort 100-115 + dubbele "Eerste
  sommatie"). FK-check vooraf: 0 zaken/0 geschiedenis/0 followup verwijzen ernaar; 15 actieve
  stappen + 15 actief↔actief-transities intact.
- **Testdossier 2026-00001:** hard verwijderd (transactie) — **20 échte mails eerst ONTKOPPELD
  (case_id=NULL), niet vernietigd**; test-rommel weg (4 classificaties, 10 meldingen, 1 followup,
  2 activiteiten, 1 geschiedenis). Werkvoorraad 28 → 27.
- **"AI Intake" → "Nieuwe aanvragen"** (paginakop + broodkruimel + terug-knop; commit `bce1bc7`,
  frontend gedeployed).
- **Fasebalk data-geverifieerd:** 17 actieve zaken met geldige categorie (9 minnelijk/7 admin/1
  regeling) → balk gevuld; 10 zonder stap → balk verborgen. Blanco kan niet meer.

**Nog samen te doen (Arsalan wilde dit expliciet "samen"):** live bulk-status-knop op 2 testzaken
klikken (verandert echte zaakstatus → met hem erbij). Endpoint zelf al bewezen (401-guard + tests).

Notities (geen blokkades):
- Incassopercentage mengt nu periode-geïnd met lopende hoofdsom — bestaand grof
  cijfer, meenemen in S200-narekenen-audit.
- Bulk-respons toont skipped/errors nog niet in de UI-toast (updated-telling klopt).
- Cliëntenfilter uren leest max 200 dossiers (7 vaste opdrachtgevers ruim gedekt).
