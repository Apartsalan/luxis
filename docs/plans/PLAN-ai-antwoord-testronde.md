# Plan — AI-antwoord-testronde ("het proefwerk")

**Doel (Arsalan, 15-07):** de antwoord-AI moet binnenkomende debiteursmails écht lezen en
begrijpen en daar een passend antwoord op schrijven — in onze huisstijl en lay-out, zonder
open te staan voor gekke dingen. We toetsen dat met een grote ronde proefmails en meten of
de antwoorden kloppen. Simpel houden.

**Hoe "leren" hier werkt (geen misverstand):** de AI traint niet vanzelf. Sturen doe je met
(1) het instructieblad (de spelregels in de prompt) en (2) de voorbeelden die hij meekrijgt
(de bibliotheek met Lisanne's echte antwoorden — het bestaande "slim leren"-systeem).
De testronde meet of die twee goed staan; bijschaven = spelregels aanpassen en opnieuw
dezelfde test draaien. Omdat de testset vast blijft, zie je objectief of het beter wordt.

---

## Stap 1 — Testset bouwen (eenmalig, ~150-200 gevallen)

Drie bronnen, elk met dossiercontext erbij:

1. **Goud: de bibliotheek (±131 gevallen).** Echte binnengekomen mail + Lisanne's échte
   antwoord (learned_answers, bron-mail via source_synced_email_id). De AI krijgt dezelfde
   mail + hetzelfde dossier; zijn antwoord leggen we naast dat van Lisanne.
2. **Echte recente mails (±10).** O.a. de SRict-mail van IN100607 ("wie zijn jullie en wie
   is jullie klant") — dé casus die het misging.
3. **Zelfgeschreven variaties (±50).** Alles wat een debiteur kan sturen, per soort een paar:
   identiteitsvragen, betwisting mét reden, betwisting zonder reden, "al betaald" (met/zonder
   bewijs), betaalbelofte, regeling-verzoek, deelbetaling-claim, boze/dreigende mail,
   advocatenbrief, faillissement-melding, Engels/Duits, lege of onzin-mail, mail over een
   ánder dossier, vraag om kwijtschelding, klacht over Lisanne, verzoek om uitstel,
   privacyverzoek (AVG), combinaties (vraag + betwisting in één mail).

## Stap 2 — Draaien (veilig en goedkoop)

- Script genereert per testgeval een concept via de nieuwe begrip-eerst-route.
- **Niets wordt verstuurd, niets komt op echte dossiers** — de concepten gaan naar een
  apart testrapport (bestand), niet de ai_drafts-wachtrij in.
- Kosten: ~€0,07 per concept → hele set ±€10-15 per ronde. Verwaarloosbaar.

## Stap 3 — Nakijken (twee lagen)

**Automatisch per antwoord (checklist):**
- Beantwoordt het de daadwerkelijk gestelde vraag/inhoud? (tweede AI kijkt na als
  "corrector": "staat er een antwoord op X in?")
- Kloppen de feiten met het dossier (klantnaam, bedragen, factuurnummers — vergelijken
  met de dossierdata; verzonnen bedrag = zware fout)?
- Huisstijl aanwezig (Betreft-regel, aanhef, ondertekening, schuldhulpblok)?
- Geen verboden dingen (toezegging, kwijtschelding, excuses namens cliënt,
  juridische standpunten die niet in AV/dossier staan)?
- Escaleert hij terecht bij te moeilijke gevallen (advocatenbrief, AVG-verzoek)?
- Bij de 131 goud-gevallen: lijkt de strekking op wat Lisanne echt stuurde?

**Handmatig:** Arsalan/Lisanne kijken de ±20 belangrijkste door (de goud-vergelijkingen
waar AI en Lisanne het meest verschillen + de gevallen die de corrector afkeurt).

## Stap 4 — Bijschaven en opnieuw

Foutpatronen → spelregels aanpassen (of betere voorbeelden meegeven) → zélfde set opnieuw
draaien → score vergelijken. Herhalen tot de score goed is (richtpunt: >90% van de checklist
groen, 0 zware fouten zoals verzonnen bedragen of toezeggingen). Daarna pas live.

## Doorlopend leren daarna (bestaat grotendeels al)

Elke keer dat Lisanne een concept aanpast vóór verzenden is dat een leersignaal: het
verschil tussen concept en verstuurde versie kan als nieuw voorbeeld de bibliotheek in
(het bestaande goedkeur-mechanisme van "Slim leren"). Zo wordt de AI in de praktijk
steeds meer "Lisanne" zonder dat er iets getraind hoeft te worden. De testset blijft
bestaan als vangnet: na elke grote wijziging draaien we hem opnieuw.

## Volgorde

Eerst S220 blok 4.3 (de begrip-eerst-antwoordroute bouwen), dan deze testronde als
sluitstuk van dat blok — testen op de oude sjabloon-dwang-route heeft geen zin, die gaat
juist weg. De testronde zelf is een goede Fable-klus (analyseren), het bouwen van het
script kan Opus meenemen in S220.

## Wat dit NIET is
- Geen model-training/fine-tuning (niet nodig, duur, en de bibliotheek+prompt doen hetzelfde).
- Geen honderden handgeschreven regels per vraagsoort — juist niet; de spelregels blijven
  kort en algemeen, het begrip komt van het model + de dossiercontext + de voorbeelden.
