cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 255 — Arsalan bepaalt de hoofdtaak (sterkste kandidaat: de 438 KVK-opzoekingen)

## KOERSREGEL (ongewijzigd)
Geen nieuwe features. Afmaken en verbeteren. Twijfel → "niets doen" adviseren.

## Werkmethode (sinds S253, oogst gedaan in S254)
`WAARHEDEN.md` definieert wat "af" is. Stand: **32 ✅ bewaakt / 5 ⚠️ onbewaakt / 2 ❓ open**.
Elke gevonden fout wordt een waarheid + een wachter voor zijn SOORT; alleen geld, reputatie
of juridische fouten verdienen een wachter. Af = geen ⚠️/❓ meer én twee weken echt gebruik
zonder nieuwe schending.

**Model:** onderzoek/oogst/review = Fable, bouwen/klikwerk = Opus. Signaleer de wissel zelf
vóór je begint (S254 ging hier mis en werd door Arsalan gecorrigeerd).

## Start
`/sessie-start` zoals altijd. Daarna zonder wachten door.
Extra context: `WAARHEDEN.md` (de openstaande ⚠️/❓ zijn de werkvoorraad).

## Hoofdtaak — kandidaat 1: de 438 KVK-opzoekingen + etiket-vergelijking
Dit is de dikste ⚠️ op de lijst en de GO is al gegeven (±€9, S253).

1. **Eerst het filter inbouwen.** `backend/scripts/kvk_backfill_legal_form.py` loopt nu álle
   contacten af (726) i.p.v. alleen wederpartijen (438) — anders €6 te veel én relaties
   verrijken die er niet toe doen. Besluit S253: alleen wederpartijen.
2. **Droogloop → natelling voorleggen → echt draaien → natellen.** Meet hoeveel BV's daarna
   géén rentebijlage meer krijgen (besluit B stond op "bij twijfel wél meesturen").
3. **Daarna de etiket-vergelijking** (rechtsvorm ↔ zakelijk/consument-etiket). Dat dicht de
   ⚠️ structureel. Let op de S252-oorzaak: de import zet `debtor_type` op b2c zodra de
   wederpartij een PERSOON is (`scripts/basenet/mapping.py::resolve_debtor_type`) — een
   eenmanszaak is precies dat blinde gat, en die regel staat nog onveranderd. Een volgende
   import herhaalt de fout dus. Bij b2c→b2b-correcties: rente + kosten opnieuw laten
   berekenen, back-up-tabel maken, per dossier GO (zoals IN100077 in S252).
4. Nieuwe vondst → regel in `WAARHEDEN.md` + wachter voor de soort.

## Alternatieven (als Arsalan iets anders kiest)
- **Resterende ⚠️'s:** actualiteit griffierecht-/nakosten-tarieven (de rente heeft zo'n
  verouderingsalarm wél, deze niet); sjabloonmenu per stap; TOKEN_ENCRYPTION_KEY (mét Lisanne
  plannen — verbreekt haar mailkoppeling); kennisregels admin-only.
- **Nieuwe ❓ uit S254:** de verjaringsteller kent geen stuiting (kaal sommetje opeisbaar + 5
  jaar, terwijl onze eigen sommaties een stuitingsclausule bevatten — S242-meting op IN100015).
  Bouwen of bewust als handwerk-signaal laten? Keuze Arsalan/Lisanne.
- **Keuze C:** ontwerpspoor kleur & leesbaarheid (`docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`).
- Mobiele controle sjabloonmenu 390×844 (4e sessie op rij blijven liggen).

## Voor Lisanne (inhoudelijk, niet zelf oppakken)
Horen 'aanmaning' en 'tweede_sommatie' in menugroep 2? Verweer-concepten en openstaande
dossiervragen liggen bij haar.

## Constraints
- Geen echte debiteuren mailen; testdossiers (2026-00006/…-00015), netjes terug.
- Fase-heropening 406: NIET zonder GO per groep; etiket-controle hoort er eerst bij.
- Geen kennisregels aanraken. Nooit `git add -A` (de hook blokkeert het).

## Bekende valkuilen uit S254 (kost je anders een half uur)
- **Eén pytest-run tegelijk.** Een afgebroken achtergrondrun blijft ín de container doordraaien
  → twee runs op dezelfde testDB geven spookfouten. `docker compose exec -T backend pkill -f pytest`
  vóór een nieuwe run; volledige suite via `docker compose exec -d ... > /tmp/fullsuite.log`.
- **Testgereedschap in de dev-container is met de hand geïnstalleerd** en verdwijnt zodra de
  container hercreëerd wordt. Herstellen:
  `docker compose exec backend sh -c 'cd /app && uv export --frozen --extra dev --no-emit-project -o /tmp/r.txt && UV_LINK_MODE=copy uv pip install --python $(which python) --target /home/appuser/.local/lib/python3.12/site-packages -r /tmp/r.txt'`
  Kandidaat-verbetering: een dev-stage in `backend/Dockerfile`.
- **Een wachter is pas af als hij bewezen bijt.** Sloop de regel tijdelijk en kijk of de test
  rood wordt. In S254 beet de afzender-wachter eerst níet (hij keek of de instelling meegegeven
  werd, niet of hij AAN stond).

## Verificatie & afronding
Relevante tests, `uvx ruff check backend/app/`, geld geraakt → geld-wachters draaien.
Commit per onderdeel + push, deploy via SSH, CI natrekken. `/sessie-einde` (volgende = PROMPT-S256).
