cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 223 — Arsalan's nieuwe punten + restlijst S222

## Start
Draai eerst `/sessie-start`. Model: onderzoek/review = **Fable**, bouwen = **Opus**,
visueel klikwerk = **Opus** — signaleer het wisselmoment actief. Context S222 staat in
SESSION-NOTES + `docs/sessions/S222-review.md` — NIET opnieuw uitzoeken. MAILSLOT OPEN
→ géén echte debiteuren mailen (testdossier 2026-00006 = Arsalans gmail).

## ⚠️ Voorrang-check EERST
KvK-productiesleutel binnen (~22 juli)? JA → eerst de rechtsvorm-backfill
(`docs/archief/prompts/PROMPT-S217.md` + STAND in `PROMPT-S215.md`), daarna de rest.
NEE → direct door.

---

# DEEL A — Arsalan's nieuwe punten (VULT ARSALAN AAN BIJ START)
> Arsalan zei bij het afsluiten van S222: "ik heb nog een aantal punten." Die staan
> hier nog niet. **Vraag ze bij sessiestart op** (in één keer, niet stap-voor-stap),
> noteer ze hieronder, en bepaal per punt: onderzoek (Fable) of bouwen (Opus).
>
> 1.
> 2.
> 3.

---

# DEEL B — Restlijst uit S222 (afgehandeld tenzij Arsalan anders prioriteert)

**Al LIVE + klaar in S222 (niet opnieuw doen):** verzoekschrift-nabouw live +
bewezen; opruimrecept uitgevoerd (449 classificaties/3 concepten/232 meldingen);
antwoord-kalibratie verwerkt (belofte/kort uitstel = kennisgeving, kwijtschelding =
afwijzen). Bewijs in `S222-review.md`.

**Nog open (kies met Arsalan wat mee moet):**
1. **Auto-concept per categorie AANZETTEN — GATED.** Poort niet gehaald (corrector-
   meetruis ±2). Vóór activering: (a) **menselijke steekproef** — Lisanne leest ~10
   echte concepten als betrouwbare lat i.p.v. de AI-corrector; (b) **bouwklusje (Opus):
   de oude categorie-route in `orchestrator.handle_email_classified` aansluiten op de
   nieuwe antwoordmotor (`unified_draft_service`)** — nu staat die route hard uit
   ("auto-draft disabled"). Pad verstuurt nooit zelf (geverifieerd). Pas aanzetten na
   Lisanne's oordeel.
2. **Datumregel onbevestigd:** spelregel "termijn letterlijk overnemen" is live maar
   niet hergemeten (ronde 4-vangst: "volgende week vrijdag" → "aanstaande vrijdag").
   Meenemen in de menselijke steekproef of een korte hertest.
3. **B3-test (Opus):** er is géén test voor de sync→classificatie-trigger (S221 blok 4)
   en die is nog nooit gevuurd op prod. Rode-test-eerst → bewijzen.
4. **Goud-testpad (Fable/Opus):** de vraag-zoeker pakt soms een opdrachtgever-mail i.p.v.
   de debiteur (4 gevallen in ronde 4) → opdrachtgever-adressen ook uitsluiten.
5. **Concepten laten vervallen bij zaak-sluiten (Opus):** zaak sluiten laat open
   concepten staan (IN100613 had er 2). Zelfde patroon als de stap-wissel-opruiming;
   klein.
6. **S221b-UX-restlijst (Opus):** review-scherm classificatie+concept naast elkaar,
   voortgangsindicator bij genereren, échte HTML-tabellen (render/opschoon-pad =
   injectie-oppervlak, voorzichtig), Blok 5-rest (tijdlijn-mailregel klikbaar, agenda
   lege staat, soft-delete-banner, follow-up dossierlink/dagen-kolom/sorteerbare koppen,
   intake-detectie dempen), Blok 6-beslismemo b2b/b2c.

**Losse klusjes (blijven staan, alleen op expliciete vraag):** landregel op dagvaarding +
faillissementsverzoek; filter "Nog te openen" op de dossierlijst; rest-PDF's (206);
7 Mollie/kop-conflictfacturen (€10.854,66 → oordeel Lisanne/boekhouding); anker-subnav
Financieel + geldstrook-uitbreiding gewone zaak (S216-rest).

## Constraints
Geen echte debiteuren mailen. Prod-mutaties: dry-run/telling + GO Arsalan. Geen
`git add -A` (expliciete paden). Beslispunten niet zelf beslissen — vragen. Na elke
commit `git push origin main` + deploy via SSH (skill `deploy-regels`). Lokaal testen
(`uvx ruff check`, relevante pytest) vóór push.

## Afsluiten
`/sessie-einde` (SESSION-NOTES max 10 entries + roadmap één-prioriteit + git tag +
PROMPT-S224). Reviewrapport indien review: `docs/sessions/S223-review.md`.
