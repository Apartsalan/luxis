# Advies — Claude Code + Codex (GPT-5.6) samen laten werken

**Datum:** 9 juli 2026 (sessie D-C taak 0, Fable) · **Status:** advies, nog niets geïnstalleerd
**Bronnen:** webonderzoek deze sessie (OpenAI-documentatie, GitHub-repo's, praktijkartikelen) —
niet uit het hoofd; alle links onderaan.

---

## Samenvatting in 5 regels

1. Codex (het terminal-programma van OpenAI) draait gewoon op deze Windows-machine, naast
   Claude Code, en valt onder het bestaande OpenAI-abonnement — **geen extra kosten** binnen
   de gebruikslimieten.
2. Het "grill-me"-patroon van Chase AI bestaat, is volwassen (MIT-licentie, ±500 sterren) en
   doet precies wat Arsalan beschreef: twee AI's van verschillende makers die elkaars werk
   afkraken tot beide tevreden zijn.
3. **Voorstel werkmodel:** Claude blijft de enige kapitein (plant, bouwt, commit, deployt).
   Codex wordt de **externe tegenlezer** op twee vaste momenten: (a) hij grillt de
   onderzoeksrapporten van Fable, (b) hij reviewt de bouw-wijzigingen van Opus vóór deploy.
4. **Wat het NIET moet worden:** Codex die zelf code schrijft of deployt op de Luxis-repo.
   Eén schrijvende partij is een harde les uit dit huishouden (merge-conflicten,
   twee-kapiteins-risico). De "rollen omdraaien"-stand van grill-me (Codex bouwt) dus UIT.
5. **Maandag praktisch:** ±30 minuten installeren + één proefrit (Codex het D-B-rapport
   laten grillen). Daarna standaard onderdeel van het ritme.

---

## 1. Installatie en aansluiting (Windows, deze machine)

- **Installeren:** Codex CLI draait sinds 2026 **native op Windows 11** (door OpenAI nog
  "experimenteel" genoemd). Twee routes: het PowerShell-installatiescript van OpenAI, of
  `npm install -g @openai/codex` (let op: mét `@openai/` — het losse pakket "codex" is een
  ander, oud programma). Node.js 22+ vereist (staat vermoedelijk al op deze machine).
- **Inloggen:** `codex login` → browser-login met het ChatGPT-account. Daarmee valt al het
  gebruik onder het abonnement (~€103/mnd), géén losse API-tegoeden nodig.
- **Modellen:** sinds 6-9 juli 2026 zit de GPT-5.6-familie (Sol / Terra / Luna, incl.
  Sol Ultra) in Codex; betaalde plannen mogen kiezen en de denk-inspanning instellen.
- **Hoe Claude Codex aanroept — 3 opties, met advies:**
  1. **Directe aanroep (`codex exec`) + bestandsoverdracht** — Claude start Codex als
     gewoon terminal-commando, geeft hem een opdracht + bestanden, leest het antwoord uit
     een bestand terug. Simpelst, geen extra infrastructuur, en volgens praktijkverslagen
     de **betrouwbaarste** route. ✅ **Dit adviseren we.** (Dit is ook wat grill-me-codex
     onder water doet.)
  2. **Codex als MCP-server** — netter op papier (Codex wordt een "gereedschap" in Claude
     Code), maar de officiële variant had een hardnekkige bug in het onthouden van
     gesprekken; community-omwegen bestaan maar zijn extra bewegende delen. ❌ Nu niet.
  3. **Tweerichtings-bruggen** (claude-codex-bridge e.d.) — beide kanten kunnen elkaar
     aanroepen. Overkill voor dit huishouden. ❌ Niet.

## 2. Samenwerk-patronen vergeleken

| Patroon | Wat het is | Volwassenheid | Past hier? |
|---|---|---|---|
| **grill-me-codex** (Chase AI) | 3 aktes: (1) Claude grillt de méns over het plan, (2) Codex kraakt Claude's plan af in max 5 rondes (alleen-lezen, oordeel GOEDGEKEURD/HERZIEN, zelfde Codex-sessie onthoudt eerdere kritiek), (3) optioneel rollen om: Codex bouwt, Claude reviewt de diff | MIT, ±503 ⭐, gebouwd op Matt Pococks grill-me | ✅ Akte 2 is precies ons gat; akte 1 overlapt met bestaande fable-skills; akte 3 bewust UIT |
| Codex-als-MCP (codex-as-mcp, tuannvm-server) | Codex als aanroepbaar gereedschap in Claude Code | Werkend maar met sessie-bugs/omwegen | ❌ Later eventueel |
| Bruggen (claude-codex-bridge, ai-cli-mcp) | Beide AI's kunnen elkaar (of drie AI's parallel) aanroepen | Nichegereedschap | ❌ Overkill |
| Zelfgebouwde review-loop | Eigen mini-skill die `codex exec` (alleen-lezen) aanroept met rapport/diff + vaste vraagstelling | n.v.t. | ✅ Terugvaloptie als grill-me-codex niet lekker past — is ±1 avond werk |
| Planner-bouwer-splitsing | De één plant, de ander bouwt | Idee, geen kant-en-klaar pakket | ❌ Botst met "één kapitein" |

**Kern van waarom dit werkt:** niemand beoordeelt zijn eigen werk. Claude die Claude's
rapport controleert (fable-tegenspreker) vangt veel, maar blijft dezelfde familie met
dezelfde blinde vlekken. Een model van een andere maker kijkt structureel anders.

## 3. Voorgesteld werkmodel (Luxis + Recruit)

**Rolverdeling — één zin per rol:**
- **Fable/Opus (Claude):** plant, onderzoekt, bouwt, test, commit, deployt — zoals nu.
- **GPT-5.6 via Codex:** leest alleen; grillt rapporten en reviewt wijzigingen; levert
  bevindingen als tekst. Nooit schrijven, nooit committen, nooit deployen.
- **Arsalan:** beslist bij tegenspraak tussen de twee (zoals nu bij fable-tegenspreker).

**Twee vaste inzetmomenten:**
1. **Rapport-gril (kijkfase, nu):** na elk Fable-onderzoeksrapport → Codex krijgt het
   rapport + leestoegang tot de code, opdracht: "probeer de 3 belangrijkste conclusies te
   weerleggen met de code als bewijs". Fable verwerkt wat standhoudt.
2. **Bouw-review (bouwfase, straks):** na elk Opus-bouwblok → Codex reviewt de wijzigingen
   (alleen-lezen) vóór deploy. Opus verwerkt echte vondsten, legt onzin naast zich neer
   (met reden — zie bestaande skill receiving-code-review).

**Wat het NIET moet worden (afspraken vooraf):**
- Codex bouwt/commit/deployt nooit op deze repo's — ook niet "even snel".
- Geen dubbele onderzoeken (twee keer hetzelfde uitzoeken = dubbel betalen, geen winst).
- Geen eindeloze pingpong: max 2-3 grill-rondes, daarna beslist Claude of Arsalan.
- Codex-bevindingen zijn **input**, geen bevel — zelfde regel als bij elke review.

## 4. Kosten en risico's

- **Kosten:** €0 extra bovenop het abonnement zolang de limieten het houden. Limieten
  werken per 5-uurs venster + een weekplafond (Plus: grofweg 15-80 berichten per 5 uur op
  het topmodel; Pro-varianten 5×/20× zoveel). Eén grill- of reviewronde kost een handvol
  berichten → **ruim voldoende voor 1-2 reviews per werksessie**. Status checken kan in
  Codex zelf met `/status`.
- **Risico's + afdekking:**
  - *Twee kapiteins* → afgedekt: Codex krijgt alleen-lezen-stand, alleen Claude schrijft.
  - *Windows-zandbak is zwakker dan op Linux* (kan schrijven waar "Iedereen" al mag
    schrijven) → irrelevant zolang Codex alleen-lezen draait; nog een reden om akte 3 uit
    te laten.
  - *Limiet op* midden in een sessie → review schuift naar later; nooit blokkerend maken
    voor een deploy die al groen is via de eigen keten.
  - *Ruis/schijnvondsten* → zelfde filter als altijd: bevinding pas geloven na eigen
    verificatie in de code (bestaande regel).

## 5. Concreet: waar past dit in het ritme dat NU draait

Het huidige ritme: **Fable kijkt** (menu-doorlichting D-A ✅ / D-B ✅ / D-C vandaag) →
**beslislijst met Arsalan** → **Opus bouwt de werkorders** → deploy. Codex past er zó in:

- **Deze week nog (kijkfase):** Codex grillt de drie audit-rapporten vóór het
  beslisgesprek. Concreet: hij probeert bijv. de D-B-conclusie "sommatie-verstuurpad kapot"
  te weerleggen door zelf de code te lezen. Houdt de conclusie stand → extra zekerheid
  onder de beslislijst. Sneuvelt er één → dat scheelt een verkeerde bouwbeslissing.
- **Volgende week (bouwfase), voorbeeld werkorder B1 (verstuurpad sommaties):**
  1. Opus bouwt de fix op een branch, tests groen.
  2. Codex reviewt de wijzigingen alleen-lezen: logicafouten, gemiste randgevallen,
     security. Uitkomst = lijstje bevindingen.
  3. Opus verwerkt de echte vondsten (of weerlegt ze beargumenteerd), Fable-afronding
     zoals altijd.
  4. Claude commit + deployt. Codex komt nergens aan.
  Dit vervangt níets — het schuift één extra, andersoortig paar ogen tussen "gebouwd" en
  "live", precies op de plek waar Arsalan zelf geen code kan reviewen.
- **Maandag praktisch (13 juli, na het mailslot):** ±30 min: Node/Codex installeren,
  inloggen, grill-me-codex-skills kopiëren (of de eigen mini-skill maken), proefrit op het
  D-B-rapport. Daarna is "Codex-gril" een vast blokje in `/sessie-einde`-prompts.

**Aanbeveling in één zin:** installeer Codex CLI + het grill-me-codex-reviewdeel, gebruik
het als vaste externe tegenlezer op rapporten en bouwblokken, en houd alle schrijf-,
commit- en deployrechten bij Claude.

---

## Bronnen

- OpenAI Codex CLI: https://developers.openai.com/codex/cli · quickstart: https://developers.openai.com/codex/quickstart
- Codex onder ChatGPT-abonnement: https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan · limieten: https://chatgpt.com/codex/pricing/ en https://simplemetrics.xyz/chatgpt-codex-limits-2026/
- GPT-5.6 Sol/Terra/Luna: https://openai.com/index/previewing-gpt-5-6-sol/ · Sol Ultra in Codex (6 juli 2026): https://vertu.com/guides/gpt-5-6-sol-ultra-codex-integration
- grill-me-codex (Chase AI, MIT): https://github.com/chaseai-yt/grill-me-codex · basis: https://github.com/mattpocock/skills
- Praktijkpatronen + valkuilen Claude↔Codex: https://codex.danielvaughan.com/2026/03/27/claude-code-codex-mcp-in-practice/ · Codex als MCP-server: https://codex.danielvaughan.com/2026/03/30/codex-cli-as-mcp-server/
- Windows-installatie + zandbak-beperking: https://itecsonline.com/post/how-to-install-codex-cli-on-windows-2026-guide
