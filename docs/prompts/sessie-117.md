# Sessie 117

Repo: `C:\Users\arsal\Documents\luxis`
Datum vorige sessie: 7 april 2026 (sessie 116)
Status: Technisch ~97% klaar, nog in bouw/validatie-fase met Lisanne

---

## Context laden bij start (VERPLICHT)

Gebruik de `luxis-researcher` subagent met deze exacte opdracht:

> "Lees de volgende bestanden en geef een compacte samenvatting (max 300 woorden):
> 1. `LUXIS-ROADMAP.md` — focus op de status-header bovenaan en de sectie **Go-To-Market Plan (voorbereid sessie 116)**
> 2. `SESSION-NOTES.md` — focus op de entry **sessie 116 — Marktonderzoek + strategische shift**
>
> Geef terug:
> - Huidige status (bouw/validatie-fase, demos met Lisanne)
> - Belangrijkste marktinzichten (incasso moat, Basenet kwetsbaar, Kleos trauma-groep)
> - Het GTM-plan dat klaarstaat voor later (pricing €79/€59, ICP solo incasso Randstad)
> - Openstaande items of dingen die Arsalan vorige keer noemde"

Lees zelf NIETS anders bij de start. Geen code, geen marktonderzoek-rapporten, geen andere docs. Alleen de samenvatting van de subagent.

---

## Begin de sessie zo

Nadat de subagent klaar is, begroet Arsalan met deze exacte opening:

> "Sessie 117. Context geladen.
>
> Status: je bent nog in de bouw/validatie-fase met Lisanne. Technisch zit Luxis op ~97%, de demos met Lisanne lopen, en het marktonderzoek + GTM-plan staat klaar voor wanneer je de markt op gaat — maar dat is nog niet nu.
>
> Wat wil je in deze sessie doen? Een paar mogelijkheden:
>
> - **Bouwen aan Luxis** — bugs fixen, features toevoegen op basis van Lisanne's feedback, iets polijsten
> - **Demo-voorbereiding met Lisanne** — workflow doorlopen, scenario's testen, issues signaleren
> - **Een specifieke bug of feature** die in je hoofd zit en afgemaakt moet worden
> - **Iets uit het GTM-plan** — als je toch al wilt beginnen met voorbereiden (landingspagina, pitch, etc.)
> - **Iets anders** wat ik nu niet op het netvlies heb
>
> Wat heb je in gedachten?"

**Niet zelf een keuze maken. Niet voorstellen welke optie het beste is. Niet pushen op GTM.** Gewoon wachten op Arsalan's antwoord.

---

## Tijdens het werk

1. **Speel notificatiegeluid** via Bash: `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` vóór AskUserQuestion, EnterPlanMode, of wanneer je op input wacht.

2. **Gebruik Plan Mode** (EnterPlanMode) als de taak niet-triviaal is. Pre-mortem: 3 redenen waarom dit plan kan falen + waarom het toch de juiste aanpak is.

3. **Geen forced werkverdeling.** Arsalan bepaalt zelf wat hij nodig vindt. Als hij wil bouwen, bouw je. Als hij wil testen, test je. Als hij wil verkopen, helpt je daarmee. Je bent faciliterend, niet sturend.

4. **Verificatie-loop (HARDE REGEL) bij elke implementatie:**
   - Build check (`tsc --noEmit` of `pytest`)
   - Visuele check (preview/screenshot)
   - Functionele check (klik door de flow)
   - Pas "done" als alle 3 groen zijn

5. **Commit + push na elke afgeronde taak** (conventional commits). Altijd direct `git push origin main` na commit.

6. **Deploys via SSH** als nodig: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216` — zie deploy-regels skill.

---

## Verplichte eindtaken van de sessie

Aan het einde van sessie 117:

1. **Update `SESSION-NOTES.md`** met nieuwe entry bovenaan. Update headers (laatst bijgewerkt, volgende sessie).

2. **Update `LUXIS-ROADMAP.md`** — markeer afgeronde items als ✅, voeg eventuele nieuwe items toe (bugs, features, GTM-acties).

3. **Git tag:** `git tag -a v117-stable -m "Sessie 117 — [onderwerp]" && git push origin v117-stable`

4. **Genereer prompt voor sessie 118** in `docs/prompts/sessie-118.md`. Zelfde format als deze prompt: open vraag, laat Arsalan kiezen.

---

## Harde regels (uit CLAUDE.md)

- **Dutch UI, English code.** UI-tekst in het Nederlands.
- **Lisanne-toets:** "Zou zij dit begrijpen zonder uitleg?" Zo nee, versimpel.
- **Product, geen tooltje.** Alles eruit laten zien alsof het morgen gelanceerd wordt.
- **Notificatiegeluid afspelen** vóór elke wachtmoment.
- **Nooit git worktrees** tenzij expliciet gevraagd.
- **Nooit destructieve acties** zonder expliciete bevestiging.
- **Commit + push na elke taak** — nooit alleen commit.
- **Financial precision:** Decimal + NUMERIC(15,2), nooit float.

---

## Wat NIET doen deze sessie

- **Niet pushen op verkopen.** Arsalan is nog in bouw-fase. Respect daarvoor.
- **Geen marktonderzoek-rapporten opnieuw draaien** — die zijn afgerond.
- **Niet zelf beslissen waar we aan werken** — Arsalan beslist. Jij faciliteert.
- **Geen nieuwe complexe sprints starten** zonder expliciete goedkeuring.

---

## Begin NU

Open de chat. Laad context via subagent. Begroet Arsalan met de opening hierboven. Wacht op zijn antwoord. Ga aan de slag met wat hij kiest.
