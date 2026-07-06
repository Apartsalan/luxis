cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 179 — Opus-bouw: betalingen (fase 1b, gericht) + betalingsregelingen-import

## Model + rol
**Opus.** Uitvoersprint op basis van de S178 gap-audit (zie SESSION-NOTES S178-entry).
Kernconclusie audit: betalingen zijn WEL nodig (29/372 lopende zaken hebben betalingen,
€52.302; ≥5 zaken lijken al (bijna) voldaan → risico onterecht aanmanen) en 12 lopende
zaken hebben een actieve betalingsregeling met toekomstige termijnen — waaronder proefzaak
IN100215 met een termijn op **12 juli 2026**. Regel: dry-run eerst, `--execute` pas na
akkoord Arsalan. Geen prod-mutaties buiten de scripts.

## Context laden bij start
Gebruik de `luxis-researcher` subagent:
"Lees SESSION-NOTES.md (S178-entry) en `docs/ARCHITECTUUR-KAART.md`. Geef compact weer:
wat de gap-audit vond over betalingen/regelingen en hoe de BaseNet-import (fase 1/2) is
opgezet (`scripts/basenet/`)."

## Taak A — betalingen-import (fase 1b, gericht)
Bron: `Xml_02-07-2026_2400.zip` → `231_56 …IncassoBetalingAnders.xml` (56 records:
`incppaydate`/`incpamount`/`incpincassoid`/`incpnote`/`incpuitsluitenkosten`).
- Nieuw script in `scripts/basenet/` (zelfde patroon als `import_basenet.py`: dry-run
  default, idempotent, id-mapping incasso-systemid → case zoals de runner die al kent).
- Betalingen aanmaken via de bestaande betalings-helper (`case_payment_kwargs` /
  `create_payment_for_case`) zodat art. 6:44-toerekening en dossierinstellingen kloppen;
  betaaldatum = `incppaydate` (bepaalt de rente-knip).
- **Reconciliatie verplicht:** vergelijk per zaak de som met BaseNet's eigen cache
  (`230_55 …Incasso.xml`: `cachedpaymentsklant/anders/admin`). Audit-cijfers: cache-totaal
  €369.406 over 135 zaken, het losse bestand dekt maar €165.697/56 records — het verschil
  liep via de boekhouding (geen losse records met datum). Verschillen NIET verzinnen:
  rapporteer per zaak in de dry-run-output (dat lijstje = input voor Lisanne's recept).
- **Vlaggen in dry-run, beslissen met Arsalan:** 4 records met "credit" in de notitie
  (creditnota ≠ betaling?) en 9 records met `incpuitsluitenkosten=true` (BaseNet sloot
  kosten uit bij toerekening — Luxis 6:44 kent die vlag niet).
- Scope: alle 56 records (ook op afgesloten zaken — historie is historie, zelfde moeite);
  `total_paid`/financials per zaak verversen zoals de betalings-service dat doet.

## Taak B — betalingsregelingen-import (12 zaken)
Bron: `232_57 …IncassoBetalingsRegeling.xml` (323 termijnen, 37 zaken; velden
`incbincassoid`/`incbdate`/`incbamount`/`incbdatestart`).
- Alleen zaken met termijnen ná vandaag importeren in `payment_arrangements` +
  `payment_arrangement_installments` (module bestaat, staat leeg). Audit vond 12 lopende
  zaken (o.a. IN100305, IN100329, IN100345 met 62 toekomstige termijnen t/m 2031,
  IN100215-proefzaak met termijn 12-07).
- Verleden termijnen NIET als betaald aannemen — status open/onbekend laten of alleen
  toekomstige termijnen opnemen (kies het kleinste dat de bewaking laat werken; leg keuze vast).
- **IN100215 eerst** (heropende proefzaak, termijn 12 juli) — daarna de rest; regelingen op
  afgesloten zaken alleen als dat gratis meekomt, anders overslaan tot heropening.

## Taak C — klein herstel (alleen als A+B af zijn)
1. Team-tab: frontend roept `/api/users/invite` + update/deactivate aan die niet bestaan
   (`use-users.ts:47`). Kleinste fix: knoppen verbergen met uitleg (beide accounts bestaan al).
2. "Facturen Legalwork" opruimen (akkoord Arsalan in S178): zaak IN100592 (afgesloten)
   omhangen naar LegalWork B.V. (`1e678357-…`), dubbele AV-rij deactiveren,
   `terms_interest_*` op het facturen-contact leegmaken, contact deactiveren.
3. IN100555 (BaseNet-status Lopend, 0 vorderingen) — uitzoeken + in het recept-lijstje.

## Verificatie
- Dry-run output eerst aan Arsalan tonen (aantallen + reconciliatie-verschillen + vlaggen).
- Na execute: steekproef 3 zaken in de UI (saldo, betalingenlijst, regeling zichtbaar),
  IN100215-termijn zichtbaar met deadline.
- Backend: `docker compose exec backend pytest tests/ -k "payment" -v` + ruff.

## NIET doen
- `IncassoBetalingsRegeling` NIET als betalingen importeren (zijn geplande termijnen).
- Geen debiteur-AV-registratie bouwen (audit: bewust niet — 361/372 lopende zaken staan in
  BaseNet zelf op 2%/mnd contractueel; keten dossier>klantkaart>AV>wettelijk dekt uitzonderingen).
- Geen zips committen. D-Break buiten voorbeelden/tests.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-179`, PROMPT-S180.
