# S207 — Fable-review van de S205-fixes (14-dagenbrief-gate + mailsync + heartbeat)

**Datum:** 13 juli 2026 · **Uitgevoerd door:** Fable (hoofdmodel, geen subagent)
**Review-object:** 7 commits `d440081`…`ee465b9` (S205), getoetst aan de S204-beslislijst
(`docs/sessions/S204-review.md` §Beslislijst).
**Werkwijze:** volledige diff gelezen, elke bewering zelf in de bron geverifieerd,
prod read-only gecontroleerd (SQL + heartbeat), baseline-tests gedraaid (68 groen vóór
wijziging). Must-fixes direct gebouwd, elk rood→groen bewezen.

**Eindoordeel: 5 van de 6 beslispunten dicht zonder voorbehoud. Punt 3 (verstuurd-proxy)
was half af — de klok liep nog vanaf stap-binnenkomst. Daarnaast een VIERDE verzenddeur
gevonden die niet in de beslislijst stond. Drie must-fixes gebouwd en gedeployd.**

---

## Per beslispunt (S204 → S205)

### 1. Gate in follow-up "Uitvoeren" — ✅ dicht
`execute_recommendation` draait `check_dagenbrief_gate` vóór render/verzending, in de
enige tak die verstuurt (`is_generate`); ESCALATE verstuurt niets; `approve_and_execute`
loopt door dezelfde functie. Fout = luide `BadRequestError`, aanbeveling wordt nooit
"Uitgevoerd". Tests dekken blok + doorlaat.

### 2. Gate op het AI-concept/losse verzendpad — ✅ dicht
`compose/send` gate't een VERSE niet-reply case-mail op een sommatie-/gerechtelijke stap
bij een consument: 422 met code `DAGENBRIEF_GATE`; met `compliance_override` gaat de mail
door + onuitwisbaar spoor (`record_dagenbrief_override`: CaseActivity + notitie op de
staphistorie-rij; rolt terug als de send zelf faalt — consistent). Frontend toont de
ja/nee-bevestiging en herpost met override. Antwoorden/doorsturen bewust vrijgesteld.

### 3. Verstuurd-proxy verstevigd — ⚠ HALF, must-fix gebouwd
**Wat klopte:** de gate telt alleen nog een staphistorie-rij mét `email_sent` — doorschuiven
zonder versturen telt niet meer; het batchpad zet die vlag nu ook (vóór de auto-advance,
`doc` bestaat op beide routes).
**Het gat (must-fix 1):** `get_dagenbrief_sent_at` gaf `entered_at` (stap-BINNENKOMST)
terug als "verzenddatum", terwijl de docstring "aantoonbaar verstuurd" beloofde. Gaat de
brief pas dagen ná binnenkomst de deur uit (batch later gedraaid), dan startte de wettelijke
15-dagen-klok te vroeg → een sommatie kon dagen te vroeg door de gate (art. 6:96 lid 6 BW,
onveilige richting). De S205-tests maskeerden dit: ze zetten `entered_at` 20 dagen terug
mét de vlag, dus binnenkomst ≈ verzending.
**Tweede gat (must-fix 2):** het follow-up-pad riep `mark_current_step_communication_sent`
níét aan na een gelukte send (batch en conceptpad wél) → een via "Uitvoeren" verstuurde
14-dagenbrief telde niet als verstuurd (gate bleef blokkeren ondanks échte verzending;
veilige richting, maar kapotte boekhouding + de sommatie was onzichtbaar in de staphistorie).

### 4. Mailsync eigen sessie per postbus — ✅ dicht
Korte sessie laadt alleen account-IDs; daarna per account een eigen sessie, e-mailadres in
een lokale variabele vóór de try, na rollback wordt het account schoon herladen binnen
dezelfde sessie. De verweer-bibliotheek-backfill kreeg ook een eigen sessie per tenant mét
expliciete commit. Prod-bewijs: `email_auto_sync` draaide vanochtend 07:24 zonder fout
(en S205 zag hem live om 20:19).

### 5. Dagenbrief-sjabloon op de stap — ✅ dicht
Idempotente migratie s205 (alleen stappen zónder sjabloon) + seed. Prod bevestigd:
de stap draagt `template_type='14_dagenbrief'`.

### 6. Heartbeat `last_error` bij intern falen — ✅ dicht
De 5 kritieke dagelijkse jobs schrijven bij een interne exceptie een gegarandeerde (niet
fire-and-forget) fout-heartbeat; kolommen `last_error`/`last_error_at` bestonden al sinds
s203b. Dashboard alarmeert bij een fout < 25u; het alarm dooft op leeftijd (na een schone
run blijft het hooguit ~1 uur langer staan — cosmetisch). Checklist ⚠a afgevinkt: alle 5
dagelijkse jobs hebben vanochtend (06:00–06:40 UTC) een verse heartbeat-rij, foutveld leeg.

---

## Nieuw gevonden: vierde verzenddeur (must-fix 3)

**`POST /api/documents/{id}/send`** ("document per e-mail versturen", Documenten-tabblad,
live in de UI) rendert élk eerder gegenereerd document opnieuw met actuele zaakdata en
mailt het naar een vrij te kiezen ontvanger — zónder gate. Een bestaande sommatie op een
consumentendossier kon zo alsnog de deur uit. Deze deur stond niet in de S204-beslislijst
("drie verzendwegen") en is nu gedicht met exact hetzelfde patroon: gedeelde helper, 422
`DAGENBRIEF_GATE`, `compliance_override` + spoor, bevestigingsdialoog in het tabblad.

## Gebouwde must-fixes (elk rood→groen bewezen)

| # | Commit | Wat |
|---|---|---|
| 1 | `543789c` | Kolom `case_step_history.email_sent_at` (migratie s207); `mark_current_step_communication_sent` legt het échte verzendmoment vast (eerste send wint); de gate rekent daarop, fallback `entered_at` alleen voor oude rijen (prod had er 0) |
| 2 | `50f98fa` | Follow-up "Uitvoeren" markeert de verzending op de open staphistorie-rij (vlag + moment + document), vóór de auto-advance |
| 3 | `452f995` | Gate + override op het document-verzendpad (backend + frontend-bevestiging) |

## Restpunten (geen fix nodig nu — backlog/kennis)

- **`POST /api/email/cases/{id}/send`** (los zaak-mailtje via globale SMTP) is ongegate,
  maar **dood vanuit de UI** (de mutation wordt nergens aangeroepen; alleen een
  `isPending`-restje) → meenemen in de 35-route-sloop (S203-restpunt).
- **AI-agent-tool `handle_email_compose`** (vrije case-mail via de chat-agent) kent de gate
  niet. De agent-chat verstuurt vrije tekst (geen stap-sommaties); zelfde status als vrije
  mail. Meenemen zodra de agent actiever wordt.
- **Classificatie-antwoorden** (`ai_agent/service.py`, send_template) zijn REPLIES op
  binnenkomende debiteurmail → valt onder de bewuste reply-vrijstelling.
- **Over-blokkering:** de compose/document-gate kijkt naar de stap van de zaak, niet naar de
  ontvanger — een mail naar de CLIËNT op een sommatie-stap krijgt ook de waarschuwing
  (override volstaat). Bewuste eenvoud; verfijnen kan later op ontvanger==wederpartij.
- **Stapnaam als anker:** hernoemt een kantoor de stap "14-dagenbrief", dan verliest de
  gate zijn vrijstelling/spoor (pre-existing, geldt ook voor de seed-logica).
- Document-verzendpad markeert bewust GEEN `email_sent` (het verstuurde document hoeft niet
  de stap-brief te zijn; de override is de escape voor een buiten-de-batch verstuurde brief).

## Verificatie

- Baseline vóór wijziging: 68 tests groen over de 5 geraakte S205-suites.
- Per must-fix: nieuwe test(s) rood op de oude code, groen na de fix (fix 3: rood bewezen
  via tijdelijke stash van de gate).
- Geraakte suites samen: 110 groen; `uvx ruff check backend/app/` schoon;
  `tsc --noEmit` + `npm run build` groen.
- Volledige suite + deploy: zie SESSION-NOTES S207.
- **Niet geverifieerd:** de gate live end-to-end (mailslot DICHT, beide actieve B2C-zaken
  stap-loos — zelfde beperking als S205 zelf noteerde); de bevestigingsdialogen alleen via
  build/tsc, niet doorgeklikt. Waarschuwingstekst moet nog langs Lisanne vóór B2C-livegang.
