---
name: fable-diepte
description: Gebruik bij onderzoek, audits, debugging, "waarom werkt dit niet", gap-analyses, haalbaarheidsvragen of data-vragen — vóór je een conclusie trekt of een plan maakt. Dwingt één stap dieper graven en meten in de bron in plaats van redeneren vanaf een samenvatting. Triggers: onderzoek, uitzoeken, audit, analyseer, waarom, kapot, klopt dit, haalbaar, hoeveel.
---

# Diepte vóór conclusie

Gedestilleerd uit Fable 5-werkdiscipline (juli 2026), gekalibreerd op dit huishouden.
Het verschil tussen een middelmatige en een sterke conclusie is zelden slimheid —
het is één extra graaf-stap die de aanname vervangt door een meting.

## De kernregel

**Meet in de bron vóór je matcht, redeneert of bouwt.** Open het echte bestand, de echte
databasetabel, de echte log — niet de samenvatting, niet de roadmap-regel, niet je
herinnering aan hoe het zat.

Bewezen in dit huishouden:
- Het "onoplosbare fuzzy-matching-probleem" (Luxis S180) bestond niet: de koppel-sleutel
  stond gewoon als kolom in de bron. Eén blik op de echte veldnamen verving een hele
  geplande onderzoekssessie.
- De claim "de AV bevat geen rentepercentage" (S172) was fout en werkte sessies lang door,
  tot iemand de echte PDF's las (S177): art. 13.3 stond er in alle drie.

## Procedure

1. **Identificeer de primaire bron** voor elke belangrijke bewering (bronbestand,
   prod-tabel, log, git-historie). Een samenvatting, memory-notitie of eerdere
   sessienotitie is een wegwijzer, geen bewijs — die kan verouderd of fout zijn.
2. **Lees eerst de structuur van de bron** (veldnamen, kolommen, een handvol echte
   records) vóór je een aanpak kiest. De aanpak volgt uit de data, niet andersom.
3. **Kwantificeer.** "Sommige zaken hebben betalingen" is geen bevinding;
   "29 van 372, samen €52.302, waarvan 5 ≥ hoofdsom" wel. Tel, som, en noem de
   uitzonderingen bij naam.
4. **Ga één stap dieper dan de vraag.** Als het antwoord "ja, 90 zaken" is, is de
   vervolgvraag "en kloppen de bedragen op de cent met een onafhankelijk ijkpunt?"
   Zoek altijd een tweede, onafhankelijke bron die de eerste bevestigt of ontkracht
   (bv. de som van losse records tegen het eigen cache-totaal van het bronsysteem).
5. **Onderzoek van anderen (subagents, eerdere sessies, artikelen) is input, geen
   waarheid.** Cross-check minstens de dragende beweringen zelf (les uit S110: een
   audit op ongecontroleerde subagent-bevindingen faalde).

## Stopregel

Je bent klaar met graven als elke dragende bewering in je conclusie (a) een primaire
bron heeft die je deze sessie zelf hebt gelezen, én (b) minstens één kwantificering of
onafhankelijke bevestiging. Ontbreekt dat voor een bewering: zeg dat expliciet in de
conclusie ("niet geverifieerd"), verstop het niet.
