# Start hier — handover voor een nieuwe Claude Code

> **Voor de AI-assistent die dit voor het eerst leest op een nieuwe computer of met een
> nieuw account (bijvoorbeeld dat van Lisanne):** dit bestand vertelt je precies wat er al
> is, wat je nog moet installeren, en hoe je hier werkt. Werk het van boven naar beneden af
> en meld aan de gebruiker (in gewoon Nederlands) wat gelukt is en wat nog handmatig moet.

---

## 0. Lees eerst deze drie (komen automatisch mee met deze map)

1. `WERKWIJZE.md` — hóé je communiceert en werkt (harde regels). **Belangrijkste:** praat
   gewoon Nederlands, geen computertaal, tegen een advocaat zonder computerkennis.
2. `CLAUDE.md` — de technische projectregels (geld = Decimal, multi-tenant, deploy via SSH, enz.).
3. `SESSION-NOTES.md` + `LUXIS-ROADMAP.md` — de actuele stand en wat er nog moet.

Dat is samen 90% van wat je nodig hebt. De rest hieronder is gereedschap.

---

## 1. Wat AL meekomt met deze map (niets voor nodig)

Deze staan in de map zelf en werken automatisch, ongeacht account of computer:

- **Projectkennis-skills** in `.claude/skills/`: `bekende-fouten`, `deploy-regels`,
  `incasso-workflow`, `template-systeem`, `premortem`, `systematic-debugging`,
  `verification-before-completion`, e.a. — lees `bekende-fouten` bij elke niet-triviale taak.
- **De vier werkdiscipline-skills** (ook in `.claude/skills/`): `fable-diepte`,
  `fable-tegenspreker`, `fable-scope-hek`, `fable-afronding`. Dit is de kern van hoe hier
  gewerkt wordt (meet in de bron, spreek jezelf tegen, blijf binnen de opdracht, rond af met bewijs).

## 2. Wat je op de computer moet INSTALLEREN (eenmalig)

Deze zitten niet in de map — regel ze op de nieuwe machine:

**a) Ponytail (denk-discipline: bouw niets wat niet nodig is).**
In Claude Code: `/plugin` → marketplace toevoegen `DietrichGebert/ponytail` → plugin `ponytail`
inschakelen. (Of vraag de gebruiker het via `/plugin` te doen — het is één keer klikken.)

**b) Playwright (om de echte website te bekijken/testen).**
Dit is de enige MCP-koppeling die je in het dagelijkse Luxis-werk echt gebruikt (de site
visueel controleren na een wijziging). Installeren:
`claude mcp add playwright -- npx -y @playwright/mcp@latest`

**c) De ontwikkel-gereedschappen** (waarschijnlijk al aanwezig, anders installeren):
Docker Desktop, Node.js (`npx`), Python 3.12, `uv` (voor `uvx ruff`), `git`, de `gh`-CLI (GitHub).

## 3. Wat je NIET nodig hebt (bewust weglaten)

De gebruiker heeft veel gereedschap staan dat niet bij Luxis hoort — installeer dit NIET:

- **Alle marketing-/verkoop-skills**: `ads-*`, `seo-*`, `copywriting`, `cold-email`,
  `social-content`, `page-cro`, enzovoort. Die horen bij een ánder project (recruitment/marketing).
- **Caveman-plugin** — staat bewust UIT (maakt de taal telegramkort; ongewenst).
- **Research-/zoek-MCP's** (`tavily`, `context7`, `claude-context`, `codebase-memory`,
  `youtube-transcript`, `stitch`) — optioneel, en ze hebben persoonlijke API-sleutels nodig.
  Niet nodig om aan Luxis te werken; alleen installeren als een specifieke taak erom vraagt.

## 4. Geheimen die NOOIT in deze map staan (apart regelen)

Deze kunnen niet in de map/git en moet de gebruiker apart aanleveren:

- **De SSH-sleutel om te deployen** naar de server (`~/.ssh/luxis_deploy`). Zonder deze kun je
  wél bouwen en testen, maar niet uitrollen naar de echte website. Zie `deploy-regels`-skill.
- **De `.env`-bestanden** met wachtwoorden/sleutels (staan lokaal en op de server, niet in git).
- **Inloggegevens** voor de productie-website — vraag de gebruiker.

## 5. Eerste keer aan de slag — korte checklist

1. Lees `WERKWIJZE.md` en `CLAUDE.md`.
2. Installeer Ponytail + Playwright (stap 2a/2b) — of vraag de gebruiker het te doen.
3. Controleer dat Docker draait en `git`/`gh` werken.
4. Vraag de gebruiker om de SSH-deploysleutel als er uitgerold moet worden.
5. Lees `SESSION-NOTES.md` voor de actuele stand en pak de volgende taak op.

> Kort gezegd: de manier van werken en de projectkennis reizen mee in deze map. Je hoeft
> alleen Ponytail, Playwright en de standaard-ontwikkeltools op de nieuwe computer te zetten,
> en de gebruiker om de deploysleutel te vragen. De rest weet je uit de map.
