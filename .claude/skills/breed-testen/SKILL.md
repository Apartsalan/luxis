---
name: breed-testen
description: Kruispunt-testdiscipline voor Luxis — bij elke bouw- of fixtaak die een gedeeld effect raakt (mail versturen, stap wisselen, concept maken, geld boeken, zaak sluiten). Dwingt de route-matrix af — welke routes hebben hetzelfde effect en gelden alle huisregels op elk daarvan — en zet elke gevonden foutsoort om in een wachter-test. Triggers - bouwen, fixen, versturen, stap, concept, breder kijken, testen.
---

# Breed testen — fouten wonen op kruispunten

Vastgelegd 16 juli 2026 (S223) op verzoek van Arsalan, na het patroon dat "breder
kijken" telkens fouten vond. Analyse van de vondsten S218–S223: **geen enkele zat
in de nieuw gebouwde code — allemaal op kruispunten.** Eén gedrag (mail versturen,
stap wisselen) is via meerdere routes bereikbaar en één route mist de huisregel:

- Rente-PDF ontbrak alléén op de AI-concept-route (S218, punt 1).
- De compose-verstuurknop legde als enige route niets vast (S219, N1).
- Het onderwerp was alléén op de stap-concept-route fout (S223, punt 3).
- Doorschuiven-na-verzending gold voor álle concepten i.p.v. alleen stap-brieven (S223).

Per-functie testen vangt dit nooit. Kruispunt-testen wel.

## De procedure (bij elke bouw-/fixtaak)

1. **Benoem het effect**, niet de functie. Niet "ik pas de AI-antwoordknop aan"
   maar "dit verstuurt mail" / "dit wisselt een stap" / "dit maakt een concept".
2. **Vind ALLE routes met datzelfde effect.** Grep de aanroepers van de gedeelde
   functie. Bestaat er geen gedeelde functie → dat ís de eerste fix (S220-les:
   `write_outbound_log` kwam er pas nadat elke route zijn eigen gat had).
3. **Loop de matrix af:** route × huisregel (lijst hieronder). Elke cel is een
   vraag: geldt regel R op route X? Bij twijfel: meten, niet aannemen.
4. **Vang de soort, niet het geval.** Elke gevonden fout wordt (a) een huisregel
   hieronder en (b) waar mogelijk een WACHTER-test die alle routes automatisch
   afloopt (patroon: `test_auth_drift_guard.py`, RLS-drift-guard) — niet één test
   voor het ene gefixte geval. Een wachter faalt zodra een tóekomstige route de
   regel mist.
5. **Klik de geraakte flows live door** (Playwright op prod, niets échts
   versturen) en tel data-effecten na in de prod-database (read-only).

## De huisregels (levende lijst — vul aan bij elke nieuwe vondst)

**Uitgaande mail (elke route: compose/send, .eml, documents/send, followup, batch):**
- M1. Afzender = kantoor-account (incasso@), nooit het persoonlijke account.
- M2. Laat altijd het drieluik achter: EmailLog + SyncedEmail + CaseActivity
  (→ zichtbaar op Mail-pagina, dossier-correspondentie én tijdlijn).
- M3. Mailslot en 14-dagenbrief-gate gelden op élke route.
- M4. Onderwerp via de gedeelde bouwer (`build_email_subject` /
  `build_reply_subject`), nooit AI-verzonnen of stale sjabloon.
- M5. Bijlagen (renteoverzicht/factuur) volgen het brieftype, route-onafhankelijk.

**Pijplijn:**
- P1. Alleen stap-brieven (intent next_step of NULL-legacy) bewegen de pijplijn;
  antwoorden en vrije berichten nooit.
- P2. Stap-wissel ruimt open adviezen én stap-concepten van de oude stap op.
- P3. Zaak sluiten laat geen open concepten/adviezen achter (nog NIET gebouwd —
  bekend gat, IN100613).

**AI-output:**
- A1. Alleen echte dossierdata: bedragen/factuurnummers op de cent gelijk aan de
  database, niets verzonnen; bij ontbreken: "wordt nagevraagd".
- A2. Altijd de huisstijl-opmaak (logo, handtekening, schuldhulp, disclaimer).
- A3. Behandelaar-instructie is leidend en staat als LAATSTE promptblok.

**Geld:** Decimal + NUMERIC, art. 6:44-volgorde, natellen tegen een
onafhankelijke bron (S180-les: op bron-record reconciliëren).

**Toegang:** elke route auth + tenant-scoped (gedekt door bestaande wachters:
`test_auth_drift_guard.py`, RLS-drift-guard — NIET aanraken, wel spiegelen).

**Zichtbaarheid:** wat op één pagina te zien hoort, hoort op álle relevante
pagina's (Mail / dossier / tijdlijn / follow-up / taken) — check de lezende
kant van elke tabel die je beschrijft.

## Bestaande wachters (het bewijs dat dit werkt)

- `tests/test_auth_drift_guard.py` — elke route eist login (allowlist 8 publiek).
- `tests/test_rls_isolation.py::test_drift_guard_flags_tenant_table_without_rls`.
- Sinds deze twee bestaan is hun foutsoort nooit teruggekomen. Dat is de maat:
  een gevonden fout is pas "af" als zijn soort een wachter heeft.

## Openstaand (kandidaat-wachters, nog te bouwen)

- Wachter M2: elke verzendroute loopt door `write_outbound_log` (enumereer
  aanroepers van provider-send; elke aanroeper zonder log-call = rood).
- Wachter M4: geen route zet een concept-/mail-onderwerp buiten de bouwers om.
- Eénmalige matrix-veegsessie: de hele huisregel-lijst × alle bestaande routes
  aflopen (Fable-audit) zodat de teller op nul staat en de discipline hem
  daarna schoon houdt.
