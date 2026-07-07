# PLAN — Doorloop-regels opschonen + deterministisch maken

**Rang: 3 — direct uitvoerbaar. VERPLICHT vóór de auto-draft-vlag ooit aangaat**
(zie PLAN-automatisering-aanzetten). Nu onschadelijk omdat de vlag uit staat.

## Vastgesteld probleem (audit 7 juli, prod)

De stap "Tweede sommatie" (actief) heeft **twee** actieve default-timeout-regels:
→ "Derde sommatie" (actief, 4 dagen) én → "Ingebrekestelling" (INACTIEVE stap, sort 103,
14 dagen). `evaluate_timeout_rules` (`backend/app/incasso/automation_service.py`,
regel ~57-141) pakt per from_step "de eerste" regel **zonder ORDER BY** — welke wint is
dus toeval per query-uitvoering. Wint de oude regel, dan probeert de draft-generator een
concept voor een stap zonder sjabloon → `ValueError` → dagelijkse error + zaak blijft
hangen. Daarnaast bestaan er nog 3 actieve timeout-regels die **vertrekken vanaf**
inactieve stappen (Ingebrekestelling→, Laatste sommatie (ank. verzoekschrift)→,
Laatste sommatie (ank. dagvaarding)→) — dode regels, alleen verwarrend.

## Te wijzigen

1. **Data-fix op prod** (geen migratie nodig; dit is tenant-configuratie, geen schema):
   ```sql
   -- eerst kijken (verwacht: 4 rijen, de hierboven genoemde)
   SELECT t.id, fs.name AS van, fs.is_active AS van_actief, ts.name AS naar,
          ts.is_active AS naar_actief
   FROM step_transitions t
   JOIN incasso_pipeline_steps fs ON fs.id=t.from_step_id
   JOIN incasso_pipeline_steps ts ON ts.id=t.to_step_id
   WHERE t.is_active AND t.trigger_type='timeout'
     AND (fs.is_active=false OR ts.is_active=false);
   -- dan deactiveren (NIET verwijderen — historie/rollback)
   UPDATE step_transitions SET is_active=false WHERE id IN (<de 4 id's>);
   ```
2. **Code-guard** in `evaluate_timeout_rules` zodat dit nooit meer stil mis kan gaan:
   - filter regels waarvan de doel-stap inactief is (join op `IncassoPipelineStep` voor
     `to_step_id`, of laad de to_steps en check `is_active`);
   - maak de keuze deterministisch: sorteer de regels vóór het vullen van
     `rules_by_from_step` (bv. `ORDER BY created_at, id`) en log een warning als er
     meer dan één default-regel per from_step overblijft.
3. **Test** in `backend/tests/` (zoek het bestaande automation-testbestand, patroon
   overnemen): twee actieve default-regels vanaf dezelfde stap, één naar een inactieve
   stap → verwacht: de regel naar de actieve stap wint, en er komt een warning-log.

## Stappenplan

1. Lees `automation_service.py` regels 57-141 volledig + het bestaande testbestand.
2. Rode test eerst (bekende werkwijze), dan de guard, test groen.
3. `uvx ruff check app/`, relevante pytest, commit + push, deploy backend, health check.
4. Data-fix op prod uitvoeren (stap 1 hierboven), met de SELECT vóór en ná als bewijs.

## Randgevallen

- **NIET alle regels van/naar inactieve stappen deactiveren** — alleen de
  `trigger_type='timeout'`-regels. De manual/payment/debtor_response-regels laten staan
  (deels al inactief; de manual-regels doen niets automatisch).
- De guard moet tenant-scoped blijven (bestaande WHERE op tenant_id niet slopen).
- `condition` is een JSON-string, kan leeg/None zijn — bestaande afhandeling
  (`days<=0 → skip`) intact laten.
- Er zijn twee stappen die "Eerste sommatie" heten (één actief, één inactief) — bij het
  controleren van de fix niet op naam maar op id/is_active matchen.
- Volgorde deploy: eerst code (guard), dan data-fix — dan is er geen moment waarop een
  verkeerde regel gekozen kan worden.

## Acceptatiecriteria

1. Nieuwe test groen, bestaande automation-tests groen, ruff schoon, CI groen na push.
2. Prod-query: 0 actieve timeout-regels van/naar inactieve stappen.
3. Prod-query: per actieve stap hooguit 1 actieve default-timeout-regel
   (`GROUP BY from_step_id HAVING count(*)>1` → 0 rijen).
4. SESSION-NOTES bijgewerkt met vóór/ná-queryresultaten.
