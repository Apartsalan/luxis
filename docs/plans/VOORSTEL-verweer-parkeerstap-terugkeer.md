# Voorstel — dossier keert na verweer-antwoord automatisch terug in de sommatie-keten

**Status: voorstel, NIET gebouwd.** Besproken Arsalan × Claude, 23 juli 2026 (S242-staart,
n.a.v. IN100592). Richting akkoord Arsalan; bouw in een eigen sessie mét de drie
controlepunten hieronder.

## Probleem
"Verweer beantwoorden" is een parkeerstap: geen doorschuifregel, en alle bewakers
(termijncontrole, follow-up-adviseur) slaan parkeerstappen over. Na het versturen van
het verweer-antwoord kijkt er dus niemand meer naar het dossier; de reactietermijn uit
de brief (3-4 dagen) wordt nergens bewaakt. IN100592 live aangetroffen: antwoord
verstuurd, dossier staat stil.

## Gekozen richting (Arsalan, verfijnd met stilte-voorwaarde)
Standaardgedrag = druk houden. Terugzetten naar de keten, maar pas als:
1. het verweer-antwoord daadwerkelijk verstuurd is (staat al in de staphistorie), én
2. de debiteur daarna X dagen niets meer van zich heeft laten horen
   (brieftermijn + speling; instelbaar).

Dan: dossier automatisch terug naar de sommatiestap waar het stond toen het verweer
binnenkwam (IN100592 → Tweede sommatie). De bestaande follow-up-adviseur geeft daarna
vanzelf het advies "tijd voor {volgende sommatie}" + werklijst-taak → Lisanne beslist.
Reageert de debiteur wél opnieuw → bestaande routes (nieuw verweer / regeling /
betaling) grijpen al in; dan géén terugzetting.

Alleen voor de verweer-parkeerstap — "Bijhouden regeling" en "On hold" staan bewust stil.

## Drie controlepunten vóór/tijdens de bouw
1. **Openstaand-verweer-slot:** het systeem weigert doorschuiven bij een openstaand
   verweer. Checken of het verweer bij antwoord-verzending als "beantwoord" wordt
   gemarkeerd; anders staat het dossier na terugzetting alsnog vast.
2. **Generate-only-batch-eigenaardigheid (bekend S234-randgeval):** de dagelijkse
   conceptenronde kan doorschuiven zonder echte verzending — onschuldig zolang
   dossiers geparkeerd staan, gevaarlijk zodra ze automatisch terugkeren. Eerst dicht.
3. **Termijn nameten in het echte sjabloon** (Arsalan zei 4 dagen, sjablonen tonen
   ergens 3) — wachttijd instelbaar maken, niet hard ingebakken.
