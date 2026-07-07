# PLAN — Opvolg-scanner: wacht-stappen overslaan

**Rang: 5 — klein, direct uitvoerbaar. Het liefst vóór of direct na de eerste
heropening-groep** (anders krijgt Lisanne op dag 1 een muur van ruis-aanbevelingen).

## Vastgesteld probleem (audit 7 juli)

`create_followup_recommendations` (`backend/app/ai_agent/followup_service.py`,
regel ~55-165) maakt voor ELKE zaak met een pijplijnstap een aanbeveling zodra
`min_wait_days` verstreken is. Hold-stappen ("Bijhouden regeling", "On hold",
"Verweer beantwoorden") hebben `min_wait_days=0` → **elke zaak op zo'n stap krijgt
direct een "handmatige beoordeling nodig"-aanbeveling**, elke 30 minuten opnieuw
gecheckt. Bij heropening van de volledige werkvoorraad staan er ~100+ zaken op
hold-achtige stappen (86 verweer + 12 regeling + on-hold).

## Besluit (al genomen — niet heroverwegen)

**Alle stappen met `is_hold_step=true` overslaan in de scan**, óók "Verweer
beantwoorden". Onderbouwing: verweer-zaken krijgen hun concept al via de
e-mail-trigger (`trigger_defense_response_for_email`) op het moment dat er echt een
verweer binnenkomt; een kalender-gedreven aanbeveling voegt daar niets aan toe.
Ook `is_terminal=true`-stappen (Betaald/Afgesloten) overslaan — hoort een zaak niet
te hebben, maar kost niets om te guarden.

## Te wijzigen

1. `backend/app/ai_agent/followup_service.py` — in de case-loop (regel ~100-103), na
   het ophalen van `step`: `if step.is_hold_step or step.is_terminal: continue`.
   Controleer dat de stappen-query eerder in de functie deze kolommen meelaadt
   (hij laadt hele step-objecten — dan is het er al).
2. Test in het bestaande followup-testbestand (zoek `test_followup*.py`): zaak op een
   hold-stap → geen aanbeveling; zaak op normale stap → wel.

## Stappenplan

1. Rode test eerst, dan de twee-regel-guard, test groen.
2. Opruimen van al aangemaakte ruis (alleen als de heropening al gedraaid heeft):
   ```sql
   -- eerst tellen, dan pas verwijderen; alleen PENDING ruis op hold-stappen
   SELECT count(*) FROM followup_recommendations fr
   JOIN incasso_pipeline_steps s ON s.id=fr.incasso_step_id
   WHERE fr.status='pending' AND s.is_hold_step;
   DELETE FROM followup_recommendations WHERE id IN (
     SELECT fr.id FROM followup_recommendations fr
     JOIN incasso_pipeline_steps s ON s.id=fr.incasso_step_id
     WHERE fr.status='pending' AND s.is_hold_step);
   ```
3. ruff + pytest, commit, push, deploy backend, health check.

## Randgevallen

- **Alleen `status='pending'` aanbevelingen opruimen** — executed/dismissed zijn
  historie van Lisanne's handelingen, nooit verwijderen.
- De scan draait elke 30 min voor alle tenants; de guard zit per zaak, dus geen
  tenant-effecten.
- `max_wait_days=0` op hold-stappen betekent in de bestaande urgentie-formule
  (regel ~113) al "geen deadline" — er is dus geen deadline-informatie die verloren
  gaat door te skippen.
- Niet skippen op stap-náám ("Bijhouden regeling" etc.) maar op de `is_hold_step`-vlag —
  namen zijn tenant-configuratie en kunnen wijzigen.

## Acceptatiecriteria

1. Nieuwe test groen; bestaande followup-tests groen; ruff schoon; CI groen.
2. Na deploy + eerstvolgende scan (max 30 min): geen nieuwe pending aanbevelingen voor
   zaken op hold-stappen (query uit stap 2 blijft 0).
3. Normale stappen krijgen nog wél aanbevelingen (bestaand gedrag intact — te zien
   zodra de heropening gedraaid heeft).
