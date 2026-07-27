# Ontwerpplan — kleur met betekenis + leesbaarheid

**Status:** VOORGESTELD, nog niet gebouwd. Arsalan koos de richting (kleur + leesbaarheid
eerst) maar wil er op dit moment niets mee doen. Opgesteld 27 juli 2026 (S250) na de eerste
Impeccable-doorlichting van de live app.

**Volledige doorlichting:** `.impeccable/critique/2026-07-27T11-34-32Z__luxis-kestinglegal-nl.md`
(cijfer 28/40, eerste meting; gemeten op productie, 1440x900 en 390x844).

---

## 1. Waarom

De app is geen AI-slop: geen kleurverlopen, geen glaseffecten, geen marketing-hero. Het
probleem is dat er geen vormtaal achter zit. Er zijn design-tokens, maar de app schildert
met rauwe Tailwind-kleuren: **877 plekken, 15 kleurfamilies, drie keer twee families voor
dezelfde betekenis** (emerald 194x naast green 31x, slate 51x naast gray 22x, violet 59x
naast purple 17x). Daardoor is elk scherm net iets anders, en dat leest als "simpel".

De badge-component bestaat maar wordt in **3 bestanden** gebruikt; de rest van de app
knutselt badges met de hand (26+ inline varianten). Dat is de wortel, niet de symptomen.

## 2. Wat het onderzoek zegt (juli 2026)

- **Radix Colors, 12-stappenschaal:** stap 1-2 achtergrond, 3-5 componentvlakken, 6-8 randen,
  9-10 solide vlakken, **11-12 zijn de enige tinten voor tekst**. Amber/geel/limoen stap 9
  zijn expliciet bedoeld voor DONKERE tekst, nooit wit.
  <https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale>
- **Linear, ontwerp-opfrisbeurt:** twee principes. "Attention distribution" (navigatie moet
  terugtreden, taak-inhoud vooraan; zij dempten hun zijbalk juist) en "structure should be
  felt not seen" (zachtere randen, minder randcontrast, minder en kleinere iconen).
  <https://linear.app/now/behind-the-latest-design-refresh>
- **Rood spaarzaam** (Carbon + ISA SP-101): rood alleen voor storing/fout; boven ~5-6
  alarmsignalen per scherm gaat een mens ze negeren. Urgentie ook via vorm/gewicht tonen,
  niet alleen kleur.
  <https://carbondesignsystem.com/patterns/status-indicator-pattern/>

Onze fout is precies de Radix-regel: we gebruiken tint ~6 als tekstkleur.

## 3. Gemeten contrastfouten (echte pagina, echte kleuren, norm 4,5)

| Element | Nu | Verhouding |
|---|---|---|
| Amber tekst op wit (dagen-teller, waarschuwingen) | `amber-600` | 3,19 |
| Groen tekst op wit ("teveel betaald", positieve bedragen) | `emerald-600` | 3,77 |
| Wit op rode badge (zijbalk-tellers, "9+" in de bel) | `red-500` | 3,76 |
| Lichtrood op lichtroze badge | `red-400` op `red-100` | 2,13 |
| Grijze telling op grijze chip | `gray-500` op `gray-100` | 4,39 |

## 4. Voorgestelde statuskleuren (doorgerekend)

| Betekenis | Nu | Wordt | Op wit | Op app-achtergrond |
|---|---|---|---|---|
| Let op / te laat | amber-600 (3,19) | **amber-700** | 5,02 | 4,81 |
| Goed / betaald | emerald-600 (3,77) | **emerald-700** | 5,48 | 5,25 |
| Fout / mislukt | red-500 (3,76) | **red-600** | 4,83 | 4,63 |
| Neutraal (tellingen) | gray-500 (4,39) | **slate-700** | 10,35 | 9,92 |
| Informatie / primair | blue-600 | blijft | 5,17 | 4,95 |

**Badge-regel:** lichte tint als vlak (50/100) met donkere tekst (700/800) — alle combinaties
gemeten boven 4,5 (amber-700 op amber-100 = 4,51; emerald-700 op emerald-100 = 4,84;
red-700 op red-50 = 5,91). **Nooit** wit op amber (3,19). Wit op rood alleen vanaf red-600.

## 5. Stappen

- **Stap 0 — voorbeeldpagina eerst.** Eén pagina met oud naast nieuw (badges, bedragen,
  zijbalk, stuk incassotabel). Arsalan kijkt, dan pas de app in. ~30 min.
- **Stap 1 — statuskleuren vastleggen** in het tokensysteem (vier betekenissen, waarden
  hierboven).
- **Stap 2 — één badge-component** met vier standen; de handgemaakte badges op de drukste
  schermen erdoor vervangen.
- **Stap 3 — rood terugbrengen** naar wat het betekent: zijbalk-tellers neutraal, rood alleen
  voor wat vandaag misgaat ("attention distribution").
- **Stap 4 — zwevende Timer-knop** alleen tonen als er een timer loopt (dekt nu gemeten de
  AI-suggesties-balk en een bedrag in de incassotabel af).

Stap 1-4 = één sessie. Daarna het langzame deel: de rauwe kleuren op de overige ~100
bestanden per schermgroep omzetten, met screenshot vooraf/achteraf.

## 6. Bewust NIET in dit plan

- **Dashboard opnieuw indelen** (15 kaarten, 2,8 schermhoogtes scrollen, ragged vijfde
  KPI-kaart, twee lege kolommen die 260px kosten). Aparte klus, apart voorstel.
- **Donker thema** en een dichtheidsstand. Genoemd als optie, niet gekozen.
- **Componentwoordenschat opschonen** (kale keuzelijsten naast eigen knoppen, 4 knophoogtes,
  5 hoekrondingen). Losse punten, P3.
- **Impeccable bijwerken** naar 4.0.2 (wij draaien 3.5.0) — gevraagd, niet beantwoord.

## 7. Wat WEL goed is (niet aankomen)

Incassolijst (dichte tabel, decimaal uitgelijnde bedragen, stap-badges, filterchips), de
donkere zijbalk als tweede neutrale laag, en de taal (Nederlands, foutmeldingen die zeggen
wat er misging en wat je nu doet).
