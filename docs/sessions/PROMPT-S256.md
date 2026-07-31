cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 256 — Arsalan bepaalt de hoofdtaak (4 ⚠️ over, geen dikke meer)

## KOERSREGEL (ongewijzigd)
Geen nieuwe features. Afmaken en verbeteren. Twijfel → "niets doen" adviseren.

## Werkmethode
`WAARHEDEN.md` definieert wat "af" is. Stand: **34 ✅ bewaakt / 4 ⚠️ onbewaakt / 2 ❓ open**.
Elke gevonden fout wordt een waarheid + een wachter voor zijn SOORT; alleen geld, reputatie
of juridische fouten verdienen een wachter. Af = geen ⚠️/❓ meer én twee weken echt gebruik
zonder nieuwe schending.

**Wachter éérst, dan pas fixen (S255-les, twee keer bewezen).** Draai de nieuwe wachter tegen
de ONgefixte code en kijk of hij rood wordt en de juiste regels aanwijst. Doe daarna de fix.
Sloop tot slot de regel weer om te zien of hij bijt. In S255 vond die proef twee keer een gat
in de wachter zelf — een reparatie die niet rood kan worden, staat onbewaakt.

**Model:** onderzoek/oogst/review = Fable, bouwen/klikwerk = Opus. Signaleer de wissel zelf
vóór je begint.

## Start
`/sessie-start` zoals altijd. Daarna zonder wachten door.
Extra context: `WAARHEDEN.md` (de openstaande ⚠️/❓ zijn de werkvoorraad).

## Kandidaten (Arsalan kiest)

**A. Actualiteit griffierecht- en nakosten-tarieven** (⚠️, meest in lijn met de koersregel).
De berekening is getest (`test_nakosten.py`, `test_griffierechten.py`) maar pint de tarieven
van nu vast; een wetswijziging valt niet vanzelf rood. De rente heeft zo'n verouderingsalarm
wél — `test_interest_rate_freshness_guard.py` is het werkende voorbeeld om na te bouwen.
Nakosten staan per 1 februari 2026 op € 189 / € 287 (liquidatietarief).

**B. Sjabloonmenu per pijplijnstap** (⚠️). S252 handmatig gefixt, geen wachter. Hangt samen
met de openstaande vraag aan Lisanne (horen 'aanmaning' en 'tweede_sommatie' in menugroep 2?)
— zonder haar antwoord kan de wachter de inhoud niet vastleggen, alleen de structuur.

**C. TOKEN_ENCRYPTION_KEY** (⚠️, mét Lisanne plannen). Verbreekt haar mailkoppeling, dus
eerst een moment afspreken. Niet solo starten.

**D. Kennisregels admin-only** (⚠️, bekend restpunt Kimi-scan). Let op: de kennisregels zelf
mogen niet aangeraakt worden — dit gaat alleen over wie ze mag beheren.

**E. Verjaring/stuiting** (❓ — dit is een KEUZE, geen bouwklus). De verjaringsteller is een
kaal sommetje (opeisbaar + 5 jaar), terwijl onze eigen sommaties een stuitingsclausule
bevatten (S242-meting op IN100015). Stuitingsdatum op het dossier bouwen, of bewust als
handwerk-signaal laten? Keuze Arsalan/Lisanne — eerst beslissen, dan pas eventueel bouwen.

**F. Keuze C:** ontwerpspoor kleur & leesbaarheid (`docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`).

**G.** Mobiele controle sjabloonmenu 390×844 (5e sessie op rij blijven liggen).

## Voor Lisanne (inhoudelijk, niet zelf oppakken)
- **KvK-nummer 72908475 op de contactkaart van Kaandorp** (IN100077). Zijn dossier staat goed
  (zakelijk sinds S252), maar de kaart mist het nummer — daardoor meldt de nieuwe nachtelijke
  controle dit dossier elke week als "zakelijk etiket zonder bewijs". Staat op de bel.
- Horen 'aanmaning' en 'tweede_sommatie' in menugroep 2?
- Verweer-concepten en openstaande dossiervragen liggen bij haar.

## Constraints
- Geen echte debiteuren mailen; testdossiers (2026-00006/…-00015), netjes terug.
- Fase-heropening 406: NIET zonder GO per groep.
- Geen kennisregels aanraken (behalve kandidaat D: alleen de rechten, niet de inhoud).
- Nooit `git add -A` (de hook blokkeert het).
- Etiket omzetten (b2c↔b2b) op een dossier: rente + kosten opnieuw laten berekenen,
  back-up maken, per dossier GO. Nooit automatisch.

## Bekende valkuilen (kosten je anders een half uur)
- **Eén pytest-run tegelijk.** `docker compose exec -T backend pkill -f pytest` vóór een
  nieuwe run; volledige suite via `docker compose exec -d ... > /tmp/fullsuite.log`.
- **Testgereedschap in de dev-container is met de hand geïnstalleerd** en verdwijnt zodra de
  container hercreëerd wordt. Herstellen:
  `docker compose exec backend sh -c 'cd /app && uv export --frozen --extra dev --no-emit-project -o /tmp/r.txt && UV_LINK_MODE=copy uv pip install --python $(which python) --target /home/appuser/.local/lib/python3.12/site-packages -r /tmp/r.txt'`
- **`npm audit fix --force` NOOIT draaien op de frontend** — die zet Next terug naar 14
  (breaking downgrade). Een advies dichten doe je met `overrides` in `package.json`
  (zoals met sharp in S255). `npm audit` kent géén `--exclude`.
- **De frontend-audit in CI is sinds S255 BLOKKEREND** (alleen runtime, `--omit=dev`) en
  groen. Wordt hij rood, dan is dat een echt advies op een pakket dat meedraait — niet
  wegklikken.
- **Visueel controleren zonder wachtwoorden:** haal een token via `POST /api/auth/login`
  (curl) en zet dat met Playwright in `localStorage` (`luxis_access_token` /
  `luxis_refresh_token`). Nooit inloggen als Lisanne, nooit wachtwoorden typen. Blijft
  Playwright hangen op "browser is already in use", dan draait er nog een oude headless
  Chrome uit het profiel `ms-playwright-mcp` — die afsluiten geeft het slot vrij.

## Verificatie & afronding
Relevante tests, `uvx ruff check backend/app/`, geld geraakt → geld-wachters draaien.
Frontend gewijzigd → `npx tsc --noEmit` + `npm run build`.
Commit per onderdeel + push, deploy via SSH, CI natrekken. `/sessie-einde` (volgende = PROMPT-S257).
