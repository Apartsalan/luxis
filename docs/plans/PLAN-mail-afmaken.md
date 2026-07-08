# Plan — Mailfunctie afmaken (S186-vervolg)

**Status:** wacht op akkoord Arsalan. Bouwen op Opus.
**Onderzoek:** 8 juli 2026 — gemeten in de bron + prod, en vergeleken met Clio/Smokeball/Karbon.

## Antwoorden op de vragen van Arsalan

- **Waarom kan ik mails in "Alle e-mails" niet openen?** Dat overzicht is in maart als
  puur kijk-lijstje gebouwd (en was tot 8 juli zelfs helemaal leeg door een kapot
  endpoint). Er is nooit een leesvenster aan gehangen. Geen reden — onafgemaakt werk.
- **Waarom werkt de sjabloonkiezer niet bij Nieuwe mail?** Sjablonen hebben
  dossiergegevens nodig (bedragen, namen). Zonder gekozen dossier doet de kiezer
  stilletjes niets — het venster legt dat nergens uit. Uitleg-/volgordeprobleem.
- **Mappen?** Vakgenoten (Clio, Smokeball, Karbon) werken niet met losse mappen maar
  dossier-gericht: elke mail wordt op de zaak gearchiveerd + één actie-wachtrij
  ("triage") waarin je per mail kiest: koppelen / nieuwe zaak maken / afhandelen.
  Luxis heeft die machine al: de **intake-detectie** (draait elke 7 min op prod,
  2 aanvragen wachten nu op review) herkent opdrachtgever-mails als mogelijke
  nieuwe zaak, leest ze met AI uit, en maakt na goedkeuring het dossier aan.
  Beperkingen nu: onzichtbaar vanuit de mailpagina + herkent alleen het exacte
  adres van de vaste contactpersoon (opdrachtgevers mailen met meerdere medewerkers).

## Blok A — de mailbasis afmaken

1. **Mails openen in "Alle e-mails"**: zelfde leesvenster als Ongesorteerd
   (lezen, bijlagen, beantwoorden/doorsturen, koppelen aan dossier).
2. **Verder bladeren** voorbij de nieuwste 200 ("meer laden").
3. **Ongelezen-status** echt laten werken — IMAP-vlaggen meelezen in dezelfde
   ophaalronde (BaseNet-mail komt nu altijd als "gelezen" binnen).
4. **Sjabloonkiezer begrijpelijk**: volgorde "kies eerst een dossier → dan
   sjabloon" zichtbaar maken met uitleg in het venster.
5. **Ophaalvenster verruimen** (nu 14 dagen — na vakantie valt er een gat).

## Blok B — "Nieuwe aanvragen"-map via de bestaande intake

1. Tab **"Nieuwe aanvragen"** op de mailpagina (naast Alle e-mails en
   Ongesorteerd), met teller — gevuld door de bestaande intake-detectie.
2. Per aanvraag: AI-uittreksel + knoppen **"Maak dossier"** / **"Afwijzen"**
   (bestaande intake-acties, hier zichtbaar gemaakt).
3. Herkenning verbreden: **domein-match** op de zeven opdrachtgevers
   (iedereen @incassocenter.nl etc.), niet alleen de vaste contactpersoon.
4. Op elke mail een actie **"Maak dossier van deze mail"** (handmatige intake)
   voor wat de automaat mist.

## Blok C — bewust NIET doen

Geen vrije mappenstructuur (Outlook-stijl) in Luxis: dubbel beheer met de
BaseNet-server, foutgevoelig, en de vakgenoten vervangen het door
dossier-koppeling + aanvragen-wachtrij. Heroverwegen als Lisanne het na
gebruik echt mist. Harde grens: Luxis leest, koppelt en verstuurt; het
mailbox-beheer zelf blijft bij BaseNet.

## Pre-mortem (3 faalredenen + antwoord)

1. *Ongelezen-vlaggen maken de sync traag* → vlaggen meelezen in dezelfde
   fetch, geen extra rondes naar de server.
2. *Domein-herkenning bombardeert elke medewerkersmail tot "aanvraag"* →
   detectie pakt alleen ongekoppelde mails, de AI filtert, en niets wordt
   dossier zonder handmatige goedkeuring.
3. *Scope-creep richting volledige Outlook-kloon* → blok C is de harde grens.

## Omvang

Blok A + B = één stevige bouwsessie (Opus). Alles hergebruikt bestaande
onderdelen: leesvenster, intake-module, verzendroute, huisstijl-aankleding.

Bronnen: karbonhq.com/feature/shared-inbox, help.karbonhq.com (managing emails),
clio.com/compare/clio-vs-smokeball.
