# PLAN — Menu-doorlichting: heel Luxis kritisch langs, dan afbouwen

**Aanleiding (Arsalan, 9 juli 2026):** de mail-doorlichting (S185–S188) leverde veel op.
Datzelfde kritische oog nu op élk menu-onderdeel: doet het het, wordt het gebruikt, hangt
het ergens aan, moet het weg of juist aangesloten? Doel: Luxis afkrijgen.

**Kernkeuze volgorde:** Fable is beschikbaar t/m **12 juli**. Daarom: ALLE doorlichtingen
eerst (Fable, read-only, deze dagen), daarna bouwsprints (Opus, geen deadline). Niet om
en om — dan halen we vóór 12 juli maar 2-3 onderdelen en missen we het totaalbeeld dat
nodig is om te prioriteren en samenhang te zien.

## Fase 1 — Doorlichting (Fable, 100% read-only, vóór 12 juli)

Drie sessies, geclusterd op samenhang. Mail is klaar (S185–S188) en doet niet mee.

| Sessie | Onderdelen | Opmerking |
|---|---|---|
| **D-A: Werkschil** | Dashboard, Mijn Taken (19), Agenda, Documenten | Wat Lisanne dagelijks ziet |
| **D-B: Kern-motor** | Relaties, Dossiers, Incasso (8), Follow-up (13), Intake (6) | Deels bekend (S183-audit, heropening); hier géén herhaling van security — alleen gebruik/aansluiting/waarde |
| **D-C: Financieel + systeem** | Bankimport, Derdengelden, Uren, Facturen, Rapportages, Instellingen | Vermoedelijk de meeste eilanden/relieken |

### Per onderdeel — drie lagen (van Arsalan, 9 juli: "een complete check")

**Laag 1 — Techniek (de 5 vragen):**
1. **Doet het het?** Doorklikken in de ingelogde prod-app + fouten/consolefouten noteren.
2. **Wordt het gebruikt?** Meten op prod (aantallen rijen, laatste-gebruik-datums) — niet gokken.
3. **Is het ergens aan verbonden of een eiland?** Code-tracering: voedt het iets, leest iets het uit?
4. **Verdict:** houden / repareren / aansluiten / verwijderen / bewust laten liggen.
5. **Missen we iets** dat we juist wél zouden moeten gebruiken (bestaat al maar ligt stil)?

**Laag 2 — Partner-blik (product/waarde, specialist advocatuur + SaaS):**
- Zou een willekeurig advocatenkantoor dit willen (CLAUDE.md-toets)? Wat doet de
  concurrentie hier (Clio, BaseNet, Legalsense, Smokeball)?
- Lost het een écht probleem van Lisanne op, of is het "gebouwd omdat het kon"?
- Kansen: wat zou dit onderdeel nóg waardevoller maken (alleen als voorstel, geen bouwbesluit)?
- Denk vanuit de dagelijkse praktijk: incassokantoor, 1 advocaat, honderden dossiers.

**Laag 3 — Gebruiksblik (UX/UI):**
- Minimale clicks naar de kerntaak? Logische flow? Lege-staten en foutmeldingen netjes?
- Consistent met de rest (Gmail/HubSpot-stijl, data-dense, Nederlands, geen jargon buiten vakmodules)?
- Ziet het er professioneel uit — zou je dit aan een betalende klant durven tonen?

### Spelregels doorlichting
- 100% read-only op prod (zoals S181-F/S183): niets muteren, niets versturen.
- Elke bevinding met bewijs (query-uitkomst, schermafdruk-beschrijving, code-verwijzing).
- Uitkomst per sessie: rapport in `docs/research/` + werkorder-lijst (zoals S183 → S184 werkte).
- Precedent relieken: S27 vond eerder al kapotte relieken van vóór de S23-verbouwing
  (Recruit); verwacht hetzelfde patroon hier.

## Fase 2 — Beslissen (samen met Arsalan, kort)
Eén lijst met alle verdicts doornemen. **Verwijderen gebeurt nooit autonoom** — per
onderdeel expliciet akkoord. Daarna volgorde van bouwen vaststellen (belangrijkste eerst).

## Fase 3 — Bouwen (Opus, blokken, na 12 juli ook prima)
- Per blok: werkorder uitvoeren → tests → doorklikken in prod-app → pas dan volgende blok.
- Review per blok: adversariële subagent (Fable zolang beschikbaar, daarna Opus met
  tegenspreker-discipline / fable-skills).
- Verwijderingen: archiveren/uitzetten boven hard weggooien waar dat kan.

## Status
- [ ] D-A Werkschil — doorlichting
- [ ] D-B Kern-motor — doorlichting
- [ ] D-C Financieel + systeem — doorlichting
- [ ] Fase 2 beslislijst met Arsalan
- [ ] Bouwblokken (volgorde na fase 2)
