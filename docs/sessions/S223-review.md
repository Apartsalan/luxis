# S223 — Review (Fable, 16 juli 2026)

Review van alles wat deze sessie is gebouwd, uitgevoerd met de nieuwe
kruispunt-discipline (skill `breed-testen`): per gedeeld effect álle routes
langsgelopen, niet alleen de route die gebouwd werd.

## Wat er deze sessie is gebouwd (Opus) en hoe het is geverifieerd

| # | Wat | Bewijs |
|---|-----|--------|
| 1 | "AI-antwoord maken"-knop op inkomende mail (Mail-pagina), met instructie-tekstvak + toon | Live doorgeklikt op prod (IN100607, 3 generatie-rondes via Playwright); knop alleen op inkomende mail mét dossier |
| 2 | Vervang-flow: bestaand concept → eerst vragen; vervangen laat oude vervallen (`force_new`) | Live: vraagdialoog verscheen; DB-natelling: ronde 1+2 op `discarded`, ronde 3 open |
| 3 | Onderwerp server-side: vast huisformaat (stap-concepten) / Re:-regel (antwoorden) | Live: "Re: SOMMATIE … / IN100607" zonder dubbel dossiernummer; tests (7 stuks) |
| 4 | Instructie-leidend-fix: instructie als LAATSTE promptblok + systeemregel | Live gemeten: vóór fix genegeerd, ná fix exact opgevolgd ("…overleg voeren met onze cliënt en daarna bij u terugkomen"); test op blok-volgorde |
| 5 | Antwoord versturen schuift de zaak NIET meer door (`advance-after-send`) | Rode test eerst (bewees de bug), fix, regressietest stap-concept schuift wél |
| 6 | Concepten vervallen bij zaak sluiten — 3 routes (handmatig, pijplijn-eindstap, betaling-hook) | Wachter-test sluit via élke route + tegencheck heropenen; 4 groen |
| 7 | Sync→classificatie-trigger: 3 tests (verse mail → meteen; geen mail → niet; geen sleutel → niet) | Suite groen; echte vuring wacht op eerste nieuwe prod-mail |
| 8 | AI-dossierdata-getrouwheid | Live: openstaand € 4.068,71 + facturen LW101811/LW103666 exact gelijk aan DB |

## Reviewvondsten (kruispunt-matrix)

### Vondst 1 — MUST-FIX, gevonden én gefixt: batch-PDF-route had nog het stale onderwerp
De onderwerp-fix van vanmiddag dekte de concept-routes en follow-up, maar de
**batch-verzendroute met PDF-bijlage** (dagvaarding/verzoekschrift) bouwde zijn
onderwerp nog via het oude BaseNet-stap-sjabloon — zonder slot-vulling, dus een
debiteur zou letterlijk `VERZOEKSCHRIFT FAILLISSEMENT / / ` als onderwerp krijgen.
Gefixt in `_build_step_email`: het onderwerp komt nu ALTIJD uit de gedeelde
bouwer (huisregel M4), de body blijft uit het stap-sjabloon komen. Wachter-test
toegevoegd: een stale subject-sjabloon op de stap mag het onderwerp nooit meer
bepalen. Hiermee zijn alle bekende onderwerp-producerende routes gedekt:
compose (.eml + send), followup (inline + DOCX), batch (inline + DOCX),
stap-concepten, antwoord-concepten.

### Gecheckt en in orde (geen actie)
- **Bulk-status-wijziging** (meerdere zaken tegelijk sluiten) loopt door dezelfde
  functie als losse sluiting → de nieuwe concept-opruiming dekt hem automatisch.
- **Geen andere sluit-routes**: AI-gereedschappen lezen status alleen;
  afwikkel-/collections-code heropent alleen (date_closed → leeg).
- **Verstuurroute AI-antwoord** = de gedeelde geloggde route (S220): drieluik
  EmailLog + SyncedEmail + CaseActivity → zichtbaar op Mail-pagina, dossier-
  correspondentie én tijdlijn (leeskant per pagina geverifieerd in de bron).
- **Follow-up-pagina** blijft consistent: antwoorden bewegen de pijplijn niet
  meer, dus geen ten-onrechte-opgeruimde adviezen bij een antwoord-verzending.

### Vondst 2 — MUST-FIX, gevonden én gefixt: CI stond stil rood sinds S220 (15 juli)
De review-check op CI (S217-les) ving het: élke CI-run sinds gisterochtend was
rood op één test. Oorzaak: S220 voegde bewust 'sommatie' toe aan de
rente-bijlage-set (punt 3, documentenroute) maar vergat de pin-test die de oude
inhoud vastlegt. Onzichtbaar doordat deploys via SSH gaan (exact het
S217-patroon). Test bijgewerkt naar het besloten gedrag + waarschuwing in de
test dat een bewuste set-wijziging de pin in dezelfde commit bijwerkt.
Niet van vandaag, maar vandaag óók niet opgemerkt bij 5 pushes — de
CI-check hoort in de vaste afsluitroutine.

### Opgeruimd (GO Arsalan)
IN100607: het foute auto-concept van 15/7 én het strenge test-concept van vandaag
op `discarded` gezet (UPDATE 2, nageteld). Alleen de écht verstuurde sommatie
staat nog als `sent`.

## Eerlijke beperkingen
- Écht versturen via de nieuwe knop is niet getest (mailslot: geen echte
  debiteuren mailen). Het verstuurpad zelf is de S220-route die toen live is
  bewezen; de koppeling ernaartoe is dezelfde dialoog als altijd.
- De sync→classificatie-trigger is op prod nog nooit gevuurd (geen nieuwe mail
  sinds deploy); de logica is nu wel test-gedekt.
- De batch-PDF-onderwerp-fix is test-gedekt maar niet live verstuurd (zelfde
  mailslot-reden).

## Vervolg (afgesproken)
**Veegsessie ná deze review** (aparte sessie): de volledige huisregel-lijst uit
`breed-testen` × alle bestaande routes aflopen, inclusief live-pass, zodat de
teller aantoonbaar op nul staat. Kandidaat-wachters staan in de skill
(o.a. M2-drieluik-wachter, M4-onderwerp-wachter).
