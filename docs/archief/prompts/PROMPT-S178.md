cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 178 — START OP FABLE: go-live gap-audit (BaseNet → Luxis)

## Model + rol
**Start op Fable.** Dit is een onderzoek-/redeneersessie, geen bouwsessie — precies Fable's
kracht. Doel: eerlijk en gegrond bepalen wat Lisanne écht nog mist om volledig in Luxis te
werken i.p.v. BaseNet, en dat prioriteren. Bouwen (indien nodig) = Opus in S179.
Regel (memory `stabiliseren-boven-bouwen`): geen bouwklussen voorstellen om tijd te vullen —
toets elk voorstel: lost het echt iets op, werkt het met de huidige volumes, bestaat het al?
Soms is "er hoeft nu niets" het juiste advies. En: cross-check je eigen bevindingen tegen de
echte prod-data/code vóór je conclusies trekt (memory `verify-own-research`).

## Context laden bij start
Gebruik de `luxis-researcher` subagent:
"Lees `docs/ARCHITECTUUR-KAART.md`, LUXIS-ROADMAP.md (kop + openstaand), SESSION-NOTES.md
(S177-entry) en `docs/audit/inventaris-2026-07-05.md`. Geef een compacte samenvatting van
wat er live is en wat er openstaat richting volledige BaseNet-overstap."

## Hoofdtaak — go-live gap-audit
Beantwoord, gegrond op de echte code + prod-database (SSH: `deploy-regels`-skill), één vraag:
**wat blokkeert Lisanne nog om BaseNet op te zeggen en volledig in Luxis te werken?**
Lever een geprioriteerde lijst (must vóór overstap / nice-to-have / bewust niet), elk punt
met: waarom het blokkeert, huidige toestand in code+data, en de kleinste oplossing.

Neem deze concrete open punten expliciet mee (beoordeel of ze überhaupt moeten):
1. **Betalingen (fase 1b) — nodig of niet?** S168 sloeg de betalingen-import bewust over.
   De 3 proefzaken hebben nauwelijks/geen betalingen (S177 geverifieerd). Maar voor accurate
   openstaande bedragen over de hele portefeuille kan het nodig zijn. Bronnen liggen klaar:
   `Xml_02-07-2026_2400.zip` → `231_56 IncassoBetalingAnders.xml` (echte betalingen:
   `incppaydate`/`incpamount`/`incpincassoid`) + `232_57 IncassoBetalingsRegeling.xml`
   (LET OP: dat zijn geplande TERMIJNEN, geen ontvangen geld — niet klakkeloos importeren).
   Toets: hoeveel zaken hebben betalingen, hoe groot is de vertekening nu, en is het de
   moeite? Art. 6:44: kosten→rente→hoofdsom; betaaldatum bepaalt de rente-knip.
2. **Debiteur-AV vs opdrachtgever-AV (juridische nuance).** De 2%/mnd komt uit art. 13.3
   van de AV van het incassobureau (bureau→eigen klant). De rente die de DEBITEUR verschuldigd
   is, hoort juridisch uit de overeenkomst/AV tussen schuldeiser en debiteur te komen. Lisanne
   hanteert 2%/mnd als contractueel tarief. Redeneer uit (flag, niet bouwen): is dat juridisch
   de juiste debiteur-rente, of een bureau-conventie? Moet er per dossier een debiteur-AV
   kunnen worden vastgelegd? (Memory `luxis-av-rente-artikel-13-3`.)
3. **Datavervuiling "Facturen Legalwork"** (facturen@-relatie, geen echte opdrachtgever —
   kreeg per abuis een AV + 1 zaak). Arsalan: mag opgeruimd worden. Toets impact + kleinste
   opruimactie (verplaats zaak? merge? deactiveren?).

## Verificatie / werkwijze
- Lees, meet, redeneer — schrijf GEEN productiecode deze sessie (Fable = onderzoek).
- Alles wat je op prod checkt: read-only queries. Geen data wijzigen.
- Eindproduct: een korte, eerlijke prioriteitenlijst + (indien nodig) `docs/sessions/PROMPT-S179.md`
  als Opus-bouwopdracht voor het #1-punt. Als de conclusie "weinig tot niets nodig" is: zeg dat.

## NIET doen
- Geen bouwklussen om de tijd te vullen. Geen prod-mutaties. Geen zips committen (`.gitignore` dekt).
- D-Break is geen vaste opdrachtgever — buiten voorbeelden/tests houden.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-178`, PROMPT-S179.
