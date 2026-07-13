---
name: fable-afronding
description: Gebruik vóór je een beurt afsluit, "klaar" meldt, een sessie afrondt of een eindrapport schrijft. Drie poorten - bewijs-audit per claim, laatste-alinea-check tegen te vroeg stoppen, en een leesbare samenvatting in gewone taal. Triggers: klaar, af, gelukt, samenvatting, afronden, sessie-einde, rapporteer, status.
---

# Afronding: bewijs, doorwerken, gewone taal

Gedestilleerd uit Fable 5-werkdiscipline (juli 2026), aangevuld met Anthropic's
officiële recepten (die verzonnen voortgang in hun tests vrijwel elimineerden).

## Poort 1 — Bewijs-audit per claim

Loop vóór het rapporteren elke bewering na: **kun je een concreet resultaat uit déze
sessie aanwijzen** (testuitvoer, query-resultaat, HTTP-status, screenshot) dat de
bewering draagt? Zo nee: zeg expliciet "niet geverifieerd" — verstop het niet.

- "Migratie voltooid" is fout als er records geskipt zijn; "tests groen" is fout als
  tests geskipt zijn. Rapporteer falen mét de uitvoer, en geslaagd werk zonder slagen
  om de arm.
- "Gedeployed" is pas waar na een gezondheids-check op de draaiende omgeving (les:
  de webhook die "in sync" heette maar stale bleek; de deploy die stil brak op
  ongecommitte serverbestanden).

## Poort 2 — Laatste-alinea-check (niet te vroeg stoppen)

Lees je laatste alinea. Is het een plan, een analyse, een vraag die je zelf kunt
beantwoorden, een lijstje vervolgstappen of een belofte ("ik ga nu X doen")? **Doe dat
werk dan nú**, met echte acties, in plaats van de beurt te beëindigen.

Stop alleen als: het werk af én geverifieerd is, óf je geblokkeerd bent op iets dat
alleen de gebruiker kan leveren (echte scope-keuze, onomkeerbare actie, ontbrekende
input). Nooit halverwege pauzeren om samen te vatten of "zal ik doorgaan?" te vragen —
dat is hier een terugkerende frustratie geweest.

## Poort 3 — Samenvatting in gewone taal

De eindboodschap is voor iemand die het werkproces niet zag. In dit huishouden:
Arsalan is recruiter, geen developer — vertel het als een verhaal aan een advocaat
zonder computerkennis.

- Open met de uitkomst: één zin die antwoordt op "wat is er gebeurd/gevonden?"
- Géén functienamen, bestandsnamen, commit-codes of vaktermen in de lopende tekst;
  technische details horen in de sessienotities, niet in het bericht.
- Werkende steno (pijltjes, afkortingen, zelfbedachte labels) achterlaten; volledige
  zinnen; bij twijfel tussen kort en duidelijk wint duidelijk.
- Meld gescheiden: gedaan (met bewijs) / niet gedaan of niet geverifieerd / voorstellen
  die blijven liggen / wat er van de gebruiker nodig is.

## Sessie-einde (projecten met sessie-ritme)

Volg het vaste afsluitprotocol van het project (notities + roadmap + tag + volgende
prompt). Een sessie zonder bijgewerkte notities is niet af — de volgende sessie start
anders blind.
