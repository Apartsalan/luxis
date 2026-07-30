cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 254 — De oogst: waarhedenlijst compleet maken (nieuwe werkmethode, besluit S253)

## KOERSREGEL (ongewijzigd)
Geen nieuwe features. Afmaken en verbeteren. Twijfel → "niets doen" adviseren.

## NIEUWE WERKMETHODE (besluit Arsalan S253 — lees eerst)
`WAARHEDEN.md` (repo-root) definieert vanaf nu wat "af" is. `WERKWIJZE.md` sectie
"Klaar is een lijst, geen gevoel" beschrijft de vier afspraken. Kern: elke fout wordt
een waarheid + wachter voor zijn soort; alleen geld/reputatie/juridisch verdient een
wachter; af = lijst zonder ⚠️/❓ + twee weken gebruik zonder nieuwe schending.

## Start
`/sessie-start` zoals altijd. Daarna zonder wachten door.

## Hoofdtaak — de oogst (lezen, denken, aanvullen; GEEN bouwwerk behalve wachters)
Doel: `WAARHEDEN.md` van startversie naar compleet. Werkwijze:
1. **Bronnen langslopen** en waarheden oogsten (via luxis-researcher waar het kan):
   docs/archief/SESSION-ARCHIVE.md + SESSION-NOTES.md (elke gefixte fout = kandidaat-waarheid),
   het compliance-hart (`backend/app/collections/compliance.py`), de incasso-huisregels
   (skill `incasso-workflow`), LUXIS-ROADMAP.md, en de S25x-restpuntenlijstjes.
2. **Per kandidaat de zeef:** kost schending geld, reputatie of een juridische fout?
   Nee → niet op de lijst (of als "waar, geen hek nodig" onderaan). Ja → status bepalen:
   bestaat er al een test die de SOORT dekt? (Grep in backend/tests — niet gokken,
   opzoeken.) Ja → ✅ met testnaam. Nee → ⚠️.
3. **Inhoudelijke vragen** → ❓ met naam erbij (Lisanne of Arsalan) — niet zelf beslissen.
4. **De 3-5 gevaarlijkste ⚠️'s meteen dichtzetten** met een wachter-test per soort
   (kandidaten uit de startlijst: gesloten dossier verstuurt nooit iets;
   meldingstypen-natelling config vs bel). Eerst rood bewijzen, dan groen. Eén pytest-run
   tegelijk. De rest van de ⚠️'s: prioriteren, niet allemaal bouwen.
5. **Eindstand rapporteren in gewone taal:** X waarheden, Y bewaakt, Z open, komende
   volgorde. Dat getal is vanaf nu het antwoord op "zijn we er bijna?".

## Wachtrij (Arsalan bepaalt volgorde — niet stil laten vallen)
- **438 KVK-opzoekingen** (±€9, GO gegeven S253) + daarna de etiket-vergelijking
  (rechtsvorm vs zakelijk/consument-etiket) — dát dicht de dikste ⚠️ uit de geldsectie.
  Filter eerst inbouwen: alleen wederpartijen (besluit S253).
- Mobiele controle sjabloonmenu 390×844 (restje S252/S253).
- Keuze C (ontwerpspoor kleur/leesbaarheid) of D (beveiligingsknopjes: TOKEN_ENCRYPTION_KEY
  mét Lisanne plannen + kennisregels admin-only — allebei ⚠️ op de waarhedenlijst).

## Constraints
- Geen echte debiteuren mailen; testdossiers (2026-00006/…-00015), netjes terug.
- Fase-heropening 406: NIET zonder GO per groep; etiket-controle hoort er eerst bij.
- Geen kennisregels aanraken. Nooit git add -A (hook blokkeert het nu ook echt).

## Verificatie & afronding
Zoals altijd: relevante tests, `uvx ruff check backend/app/`, geld geraakt → geld-wachters
draaien. Commit per onderdeel + push, CI natrekken. `/sessie-einde` (volgende = PROMPT-S255).
