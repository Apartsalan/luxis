# PLAN — Automatische conceptbrieven aanzetten (de vlag)

**Rang: 7 — LAATSTE stap, pas 1-2 weken ná een stabiele heropening. Niet eerder.**
Dit plan is klein maar de poortwachters zijn heilig.

## Wat de vlag doet (geverifieerd 7 juli)

`tenants.pipeline_auto_drafts_enabled` (nu `false`). Zodra `true`: de dagelijkse job van
08:00 UTC (`daily_pipeline_auto_drafts`, scheduler regel ~648) evalueert de
timeout-regels en genereert **concepten + reviewtaken** — max `DAILY_DRAFT_RATE_LIMIT=50`
per dag (`automation_service.py` regel ~466). Er wordt ook mét vlag NIETS automatisch
verstuurd; versturen blijft een klik van Lisanne.

## Harde randvoorwaarden (allemaal aantoonbaar af vóór het zetten van de vlag)

1. ✅/❌ PLAN-timeout-regels-opschonen uitgevoerd (anders kans op dagelijkse errors en
   verkeerde stap-keuzes) — check: de acceptatie-queries uit dat plan geven 0 rijen.
2. ✅/❌ PLAN-14-dagenbrief-sjabloon live (anders faalt elke B2C-zaak op die stap).
3. ✅/❌ PLAN-followup-hold-steps gedeployed (minder ruis, zelfde sessie mag).
4. ✅/❌ Heropening ≥ 1-2 weken stabiel; Lisanne werkt dagelijks in Luxis en heeft de
   concepten-reviewflow (Taken) al eens handmatig gebruikt.
5. ✅/❌ Expliciet akkoord van Lisanne én Arsalan, per bericht, op de startdatum.

## Stappenplan

1. Loop de randvoorwaarden af, met bewijs per punt (queries/verwijzingen), in de sessie.
2. Voorspel de eerste run VOORAF: draai de matches-query als dry-run —
   hoeveel zaken staan langer dan hun `condition.days` in hun stap? Verwacht bij een
   weken-oude heropening: veel → de eerste dagen wordt de 50/dag-limiet geraakt. Schrijf
   het verwachte aantal op.
3. Zet de vlag:
   ```sql
   UPDATE tenants SET pipeline_auto_drafts_enabled=true WHERE name='Kesting Legal';
   ```
4. Volg de eerstvolgende 08:00-run in de logs (`docker compose logs backend | grep
   auto-draft`). Verwacht: "generated N drafts", geen exceptions.
5. Check met Lisanne na dag 1 en dag 3: zijn de concepten bruikbaar? Zo nee → vlag uit
   (zelfde UPDATE met false), bevindingen noteren, eerst sjablonen verbeteren.

## Randgevallen

- **Burst na aanzetten**: elke zaak die al langer dan de regel-termijn in zijn stap
  staat matcht meteen. 50/dag-limiet dempt dit, maar Lisanne moet weten dat er de
  eerste dagen ~50 reviewtaken per dag bijkomen. Eventueel eerst de limiet verlagen
  (constante in code = deploy) of per opdrachtgever-groep heropenen zodat de voorraad
  klein is.
- Concepten voor zaken die net betaald zijn: de draft-generator kijkt naar de zaak op
  het moment van genereren; een zaak die gisteren volledig betaald werd maar nog een
  stap heeft, krijgt gewoon een concept. Werkinstructie voor Lisanne: eerst
  betalingen verwerken, dan concepten reviewen.
- Rate-limit telt per tenant per dag (`count_drafts_today`) — handmatig gegenereerde
  drafts tellen mee; op drukke handmatige dagen komt de batch dus lager uit. Geen bug.
- Rollback is triviaal (vlag terug naar false) en verliest niets — al gegenereerde
  concepten blijven staan.

## Acceptatiecriteria

1. Randvoorwaarden-checklist volledig afgevinkt mét bewijs in SESSION-NOTES.
2. Eerste batch-run zichtbaar in logs, 0 exceptions, aantal ≈ voorspelling (of
   verklaard verschil).
3. Lisanne heeft na ≤3 dagen bevestigd dat de concepten bruikbaar zijn, of de vlag
   staat weer uit met een bevindingenlijst.
