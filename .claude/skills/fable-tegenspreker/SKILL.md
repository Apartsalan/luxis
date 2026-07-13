---
name: fable-tegenspreker
description: Gebruik nadat je een plan, fix, analyse, review of belangrijke conclusie hebt geformuleerd maar vóór je die presenteert of uitvoert — en altijd vóór een schrijfactie op productie. Dwingt een actieve poging je eigen werk te weerleggen. Triggers: plan klaar, fix klaar, conclusie, review, voorstel, migratie, import, deploy, productie.
---

# Tegenspreker: weerleg jezelf vóór je presenteert

Gedestilleerd uit Fable 5-werkdiscipline (juli 2026). Zelfvertrouwen is geen bewijs.
De duurste fouten in dit huishouden waren plausibele beweringen die niemand aanviel.

## De kernregel

Behandel je eigen conclusie als de bewering van een ander die jij moet ontkrachten.
Niet "klopt dit?" (daar zeg je te makkelijk ja op) maar: **"wat zou moeten bestaan als
dit fout is — en heb ik dáár gekeken?"**

Bewezen in dit huishouden:
- "Webhook is in sync" (Recruit S25) — bleek stale; de bewering was nooit tegen de
  echte draaiende versie gehouden.
- Account-lockout "werkte" (Luxis S161) — de teller werd elke keer stil teruggerold;
  alleen een live poging bewees dat het kapot was.
- De rente-conventie-afwijking (S175d) leek een bug, maar de tegenspreker-vraag
  ("wat als beide systemen gelijk hebben?") maakte er een beoordelingsvraag van.

## Procedure

Voor elke dragende bewering of gekozen aanpak, beantwoord schriftelijk (kort, in je
werkproces — niet per se aan de gebruiker):

1. **De drie waarschijnlijkste manieren waarop dit fout is.** Concreet, geen strofiguren.
   Kies daarna de goedkoopste check per manier en voer die uit.
2. **De omgekeerde verklaring.** Als jouw verklaring X is: welk bewijs zou verklaring
   niet-X opleveren? Zoek dat bewijs actief (grep de callers, query de randgevallen,
   probeer het pad dat zou moeten falen).
3. **De dubbeltelling/randgeval-check bij geld en aantallen.** Sommen die "ongeveer"
   kloppen zijn verdacht; exact 2× of exact de helft is bijna altijd een structuurfout
   in de bron (S180: BaseNet telde dezelfde betaling in twee kolommen).
4. **Bij prod-mutaties:** draai eerst de dry-run/leesvariant, vergelijk de uitkomst met
   je verwachting op de cent/het aantal, en bouw een hard slot in (bij afwijking: skip
   + rapporteer, nooit stil doorgaan).

## Wanneer een verse blik verplicht is

Zelfkritiek heeft een plafond: je ziet je eigen blinde vlek niet. Bij werk dat meer dan
een sessie kostte, geld raakt, of livegang bepaalt: laat een **verse, onafhankelijke
context** (subagent zonder jouw aannames, of een aparte reviewsessie) het werk tegen de
specificatie houden. Dit huishouden doet dat al als vaste stap (review-sessies); sla die
nooit over omdat het werk "vast wel goed" is — de reviews vonden vrijwel altijd iets
(S175: de 12-cap; S177: vier bevindingen).
