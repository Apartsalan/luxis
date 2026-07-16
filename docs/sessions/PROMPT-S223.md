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

# DEEL A — Arsalan's nieuwe punten (opgegeven bij start S223, 16 juli)

> 1. **Opnieuw antwoord kunnen genereren op een wederpartij-mail.** Voorbeeld IN100607
>    (gisteren gebruikt als testcasus met fout AI-antwoord): daar kan nu géén nieuw
>    AI-antwoord meer op gemaakt worden. Gewenst: een knop op de mail van de wederpartij
>    zelf — "concept maken" — die je vaker kunt gebruiken (na aanpassingen opnieuw testen),
>    zonder te hoeven wachten op de automatische beoordeling/classificatie.
> 2. **Stuur-tekstvak per antwoord (chat-achtig).** Naast het automatische antwoord een
>    vrij tekstvak: "beantwoord deze cliënt en zeg dat ik erop terugkom" / "…en zeg dat
>    het niet klopt en dat het zo zit". AI gaat uit van zijn eigen antwoord, maar Arsalan/
>    Lisanne kan met een instructie bijsturen. Vraag: kunnen we dit implementeren?
> 3. **Onderwerp van concept-mails nog steeds fout** (gisteren al doorgegeven, niet
>    aangepast): titel moet zijn **cliënt / debiteur — sommatie tot betaling — ons
>    dossiernummer**. Uitzoeken wat er nu gebeurt en waarom de eerdere melding niet is
>    doorgevoerd.

## Onderzoek DEEL A afgerond (Fable, 16 juli) — bouwplan + keuzes Arsalan

**Bevindingen (gemeten in code + prod-DB):**
- Punt 1: elke mail wordt één keer automatisch beoordeeld; er bestaat nérgens in de UI
  een knop om op een specifieke mail een (nieuw) AI-antwoord te vragen. De motor
  bestaat volledig (`POST /api/ai/draft`, intent `reply_to_email`, met `instruction`-veld
  en toon) maar `useGenerateDraft` (use-ai-draft.ts) wordt door geen enkel scherm
  gebruikt. IN100607: classificatie 15/7 `betwisting` status `executed`, fout concept
  "REACTIE OP UW VERWEER" staat nog open (status `generated`).
- Punt 2: `instruction` gaat backend-breed al mee in de prompt ("Extra instructie:") —
  alleen UI ontbreekt.
- Punt 3: S220 bouwde `build_email_subject` (exact het gewenste formaat), maar op de
  stap-routes geldt `step.email_subject_template or build_email_subject(...)` en alle
  6 stappen in prod-DB hebben nog oude BaseNet-onderwerpen ("SOMMATIE TOT BETALING / / ")
  die dus winnen; de AI-concept-routes bewaren bovendien het AI-verzonnen onderwerp.

**Keuzes Arsalan (16 juli):**
1. Antwoord-onderwerp: `Re: <origineel>` aanhouden MÉT klant/debiteur/dossiernummer
   erachter toegevoegd (niet dubbel toevoegen als het dossiernummer al in het
   originele onderwerp staat).
2. Brieftype in onderwerp = stapnaam ("Eerste sommatie", "Tweede sommatie", …).
3. Opnieuw genereren op een mail met al een open concept: EERST VRAGEN
   (dialoog: bestaand openen of vervangen; vervangen = oude vervalt + verse generatie).

**Bouwplan (Opus):**
- **Blok A — knop + stuurvak op inkomende mail** (dossier-correspondentie + mailpagina):
  "AI-antwoord maken" met optioneel instructie-tekstvak + toon-keuze → `POST /api/ai/draft`
  (reply_to_email + source_email_id + instruction). Backend: `force_new`-vlag die het
  open duplicaat netjes laat vervallen (status discarded) vóór verse generatie;
  frontend vraagt eerst (keuze 3). Werkt onbeperkt vaak, wacht niet op classificatie.
- **Blok B — onderwerp overal goed:** (1) prod-data: de 6 oude stap-onderwerpen
  leegmaken/vervangen (dry-run + GO Arsalan); (2) code: `build_email_subject` laten
  winnen op alle stap-mailroutes; (3) AI-concepten: onderwerp server-side zetten
  (stap-concept = vast formaat met stapnaam; antwoord-concept = Re:-regel uit keuze 1)
  i.p.v. het AI-verzonnen onderwerp.

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
