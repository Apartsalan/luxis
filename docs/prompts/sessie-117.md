# Sessie 117 — Go-To-Market Start

Repo: `C:\Users\arsal\Documents\luxis`
Datum vorige sessie: 7 april 2026 (sessie 116)
Status: Technisch klaar, strategisch omgeschakeld naar verkopen

---

## Context laden bij start (VERPLICHT)

Gebruik de `luxis-researcher` subagent met deze exacte opdracht:

> "Lees de volgende bestanden en geef een compacte samenvatting (max 300 woorden):
> 1. `LUXIS-ROADMAP.md` — focus op de sectie **Go-To-Market Sprint (sessie 116, 7 april 2026)** en de status-header bovenaan
> 2. `SESSION-NOTES.md` — focus op de entry **sessie 116 — Marktonderzoek + strategische shift naar Go-To-Market**
>
> Geef terug:
> - De strategische beslissing (lifestyle + AI-leverage)
> - De ICP (wie is de doelgroep)
> - De pricing (founding customer + standaard)
> - De werkverdeling 70/20/10
> - De GTM-actielijst (GTM-01 t/m GTM-11)
> - Openstaande concrete stappen voor deze sessie"

Lees zelf NIETS anders. Geen code, geen marktonderzoek-rapporten, geen andere docs. Alleen de samenvatting van de subagent.

---

## Begin de sessie zo

Nadat de subagent klaar is, begroet Arsalan met deze exacte opening:

> "Sessie 117. Ik heb de context geladen: we zitten in de Go-To-Market fase, eerste 10 klanten verkopen tegen €59/mnd founding customer pricing, ICP is solo incasso-advocaten in de Randstad, werkverdeling 70% verkopen / 20% bugs / 10% features.
>
> Er staan 11 openstaande GTM-acties (GTM-01 t/m GTM-11) in de roadmap. Ik ga NIET beslissen waar we aan werken — dat beslis jij.
>
> Welke van deze opties wil je nu oppakken?
>
> 1. **Lisanne-introducties vragen** (GTM-01) — kort script schrijven om Lisanne om 10 warme intro's te vragen
> 2. **Landingspagina bouwen** (GTM-02) — simpele luxis.nl met alleen demo-aanvraag
> 3. **Pitch schrijven** (GTM-03) — 3-zinnen pitch die je kunt gebruiken in gesprekken
> 4. **LinkedIn outreach template** (GTM-04) — persoonlijk bericht-template voor cold outreach
> 5. **Demo-script** (GTM-05) — 15-minuten script voor eerste kennismakingsgesprekken
> 6. **Kleos-migratiepagina** (GTM-08) — wedge voor ex-AdvocaatCentraal trauma-groep
> 7. **Basenet-migratiepagina** (GTM-09) — wedge voor Blinqx prijsschok klanten
> 8. **Advocatenblad artikel** (GTM-10) — 1-dag werk om naambekendheid op te bouwen
> 9. **Fidura check** (GTM-07) — snel verifiëren of Fidura nog bestaat als advocaten-PMS
> 10. **Iets anders** — niet in de lijst maar wel relevant
>
> Wat wil je? En hoe lang heb je vandaag? Dan plan ik het werk daarop."

**Niet zelf een keuze maken. Niet voorstellen welke optie het beste is. Gewoon wachten op Arsalan's antwoord.**

---

## Tijdens het werk

Als Arsalan een keuze maakt:

1. **Speel notificatiegeluid** via Bash: `cscript //nologo //e:vbscript "C:\Users\arsal\.claude\notify.vbs"` vóór AskUserQuestion, EnterPlanMode, of wanneer je op input wacht.

2. **Gebruik Plan Mode** (EnterPlanMode) als de taak niet-triviaal is. Pre-mortem: 3 redenen waarom dit plan kan falen + waarom het toch de juiste aanpak is.

3. **Hou je aan de 70/20/10 regel.** Als Arsalan wil coderen terwijl er GTM-werk open staat, herinner hem daaraan. Maar respecteer zijn beslissing als hij zegt "ik wil nu bouwen".

4. **Geen over-engineering.** Landingspagina = simpel. Pitch = 3 zinnen. Demo-script = 15 min. Dit is marketing, niet productwerk — KISS.

5. **Commit + push na elke afgeronde taak** (conventional commits: `docs(gtm):`, `feat(marketing):`, etc.). Altijd direct `git push origin main` na commit.

6. **Géén deploys nodig** voor deze sessie waarschijnlijk (tenzij landingspagina live moet). Als deploy wel nodig is: `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216` en volg de deploy-regels skill.

---

## Verplichte eindtaken van de sessie

Aan het einde van sessie 117:

1. **Update `SESSION-NOTES.md`** met nieuwe entry bovenaan (format: `## Wat er gedaan is (sessie 117 — DATUM) — ONDERWERP`). Update headers (laatst bijgewerkt, volgende sessie).

2. **Update `LUXIS-ROADMAP.md`** GTM-sectie: markeer afgeronde items als ✅, voeg eventuele nieuwe items toe.

3. **Git tag:** `git tag -a v117-stable -m "Sessie 117 — [onderwerp]" && git push origin v117-stable`

4. **Genereer prompt voor sessie 118** in `docs/prompts/sessie-118.md`. Zelfde format als deze prompt: open vraag, laat Arsalan kiezen, geef opties vanuit de openstaande GTM-acties.

---

## Harde regels (uit CLAUDE.md, niet vergeten)

- **Dutch UI, English code.** Als je iets bouwt voor de landingspagina: alle gebruikersfacing tekst in het Nederlands.
- **Lisanne-toets:** "Zou een niet-techneut dit begrijpen?" Zo nee, versimpel.
- **Product, geen tooltje.** Alles wat je bouwt moet eruit zien alsof het morgen gelanceerd wordt.
- **Notificatiegeluid afspelen** vóór elke wachtmoment (AskUserQuestion, plan approval, taak-einde).
- **Nooit git worktrees** tenzij expliciet gevraagd.
- **Nooit destructieve acties** (rm -rf, drop database, volume delete) zonder expliciete bevestiging.
- **Commit + push na elke taak** — nooit alleen commit, altijd direct push.

---

## Wat NIET doen deze sessie

- **Geen nieuwe features bouwen** tenzij direct gevraagd door een bestaande of aanstaande klant
- **Geen marktonderzoek-rapporten opnieuw draaien** — die zijn afgerond
- **Geen Urios/Legalsense/Fidura herdraaien** — wachten tot na 10 echte advocaten-gesprekken
- **Geen Stitch UI redesign** — gedescoped
- **Geen externe security audit** — niet nu
- **Geen paid ads, geen funnels, geen marketing automation** — gewoon persoonlijk contact tot 10 klanten
- **Niet zelf beslissen waar we aan werken** — Arsalan beslist. Jij faciliteert.

---

## Begin NU

Open de chat. Laad context via subagent. Begroet Arsalan met de opening hierboven. Wacht op zijn keuze. Ga aan de slag.
