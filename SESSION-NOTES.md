# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 24 juli 2026, nacht (S246-nacht — Fable-eindreview gedraaid + 4 reviewfixes live + "Verstuur later" óók op batch/follow-up, beide live bewezen op testdossiers).
**Laatste feature/fix:** blinde-wachtrij-guards (betaald dossier / al-verstuurd concept blokkeren) + lopende band uitstelbaar met stap-anker-guard (commits `90aa57f` + `8ef2d88`); beide soorten vertrokken automatisch en dossiers zijn teruggezet.
**Openstaand:** S247 AI-kennislaag (masterplan `docs/plans/PLAN-DEMO-PUNTEN-S243.md`); verse-ogen-review van de NACHT-commits (gebouwd én getest door dezelfde Fable-instantie); **IN100592 3e betwisting + 2 regeling-taken IN100281/IN100537 wachten op Lisanne**; fase-heropening per groep (`docs/plans/BASENET-STATUS-HERSTEL.md`); 4 review-mails ongesorteerde bak + intake Ram Charan Sukhdai. Losse punten: afgeronde taak toont nog "X dagen te laat"; melding bij mislukte geplande mail gaat alleen naar de inplanner (onzichtbaar als die inactief wordt); BaseNet-delisting, kostenblokje, opmaak-restpunt S227, S221b-rest, DMARC, 4 cosmetische restjes S235, sharp-CVE's.
**Volgende sessie:** S247 — verse-ogen-review nachtdiff + AI-kennislaag; zie `docs/sessions/PROMPT-S247.md`.

## Sessie 246-nacht (24 juli 2026, Fable solo op GO Arsalan — eindreview + reviewfixes + lopende band, LIVE)

### Samenvatting
Nachtopdracht Arsalan ("doe zoveel mogelijk, probeer ook de lopende band met
testdossiers, fix het gewoon"). Alles op Fable gedaan — óók de bouw, want
Arsalan sliep en kon niet naar Opus wisselen; kostenafwijking bewust genomen.

**1. Fable-eindreview S246 (was verplicht open).** Hele diff tegen­gelezen op het
kruispunt "de wereld verandert tussen inplannen en verzenden, en er kijkt geen
mens meer": 4 vondsten, alle gefixt + wachters (`90aa57f`):
- Dossier intussen betaald/afgesloten → geplande mail werd tóch verstuurd. Nu: guard blokkeert + melding.
- AI-concept intussen handmatig verstuurd/afgewezen → geplande kopie = dubbele mail aan debiteur + extra doorschuif. Nu: guard blokkeert + melding.
- Mislukte rij was onopruimbaar (bleef eeuwig staan). Nu: "Weghalen"-knop, foutreden blijft bewaard.
- Nazorg-fout-melding zei "mail IS verstuurd" én "verstuur hem zelf" (uitnodiging tot dubbel). Tekst hangt nu af van of de mail echt weg is. Plus: bijlage-totaalgrootte al bij inplannen bewaakt.

**2. Lopende band (`8ef2d88`, migratie s246c).** Het open ontwerpbesluit is
genomen: bij inplannen gebeurt er NIETS (geen brief, geen document, geen
doorschuiven); op het gekozen moment draait de bezorger exact dezelfde functie
als de knop (batch_execute per dossier / execute_recommendation) — brief krijgt
de rentestand van het verzendmoment, dossier schuift dan pas door. Follow-up:
goedkeuren gebeurt wél meteen (besluit van vanavond), alleen uitvoeren wacht.
Guards: stap-anker (batch: dossier op andere stap → verkeerde brief zou uitgaan
→ blokkeer+meld), follow-up via de bestaande statusmachine (verouderd/al
uitgevoerd → niets + melding), dubbel-plan-guard per aanbeveling. Wachtrij
kreeg een soort-veld ('compose'/'batch_step'/'followup'). UI: gedeelde
"Verstuur later"-knop in het batch-venster en de follow-up-voorvertoning.

**3. Live bewezen op testdossiers (beide ketens, prod):**
- Batch: 2026-00006 (Tweede sommatie) om 00:12 ingepland → 00:14:22 automatisch
  vertrokken; brief gegenereerd óp het verzendmoment, mail via incasso@ in de
  correspondentie, dossier doorgeschoven naar Derde sommatie. Daarna teruggezet.
- Follow-up: 2026-00015 via de nieuwe UI-knop (voorvertoning → Verstuur later →
  eigen tijdstip) → aanbeveling meteen 'approved', uitvoering 00:19:22:
  brief verstuurd, aanbeveling 'executed', dossier doorgeschoven. Teruggezet
  naar Derde sommatie (de verbruikte aanbeveling maakt de 30-min-scanner
  vanzelf opnieuw aan als het dossier weer lang genoeg stilstaat).

### Gewijzigde bestanden
Backend: `email/scheduled_service.py` (guards + 2 soorten + inplan-functies),
`email/scheduled_models.py`, migratie `s246c_sched_kinds.py`,
`incasso/router.py`+`schemas.py` (batch scheduled_at),
`ai_agent/followup_router.py` (schedule-execute).
Frontend: `verstuur-later-menu.tsx` (nieuw, gedeeld), `incasso/page.tsx`,
`followup/page.tsx`, `scheduled-emails-panel.tsx` (Weghalen), hooks.
Tests: `test_scheduled_emails.py` 12→20 wachters. Commits `90aa57f`, `8ef2d88`.

### Verificatie
20 wachtrij-wachters + 78 keten-tests + 181 batch/follow-up/incasso-tests groen
(runs ná elkaar, één tegelijk); ruff + tsc schoon; migratie s246c op prod; alle
containers healthy; login 200; screenshots van batch-venster, follow-up-venster
en wachtrij-blok bekeken; beide live-verzendingen in de database nagetrokken
(rij sent/1 poging, document, synced_email via incasso@, stap-verschuiving).

### Bekende issues / bewust niet gedaan
- **Verse-ogen-review nodig op de nachtdiff** (`90aa57f`+`8ef2d88`): gebouwd én
  getest door dezelfde instantie — tegen de vaste cyclus in; eerste taak S247.
- Melding bij mislukte geplande verzending gaat alleen naar wie hem inplande;
  wordt die gebruiker inactief, dan ziet niemand hem (klein, 2 gebruikers).
- Batch-inplannen via de "Per stap"-weergave niet apart getest (zelfde dialoog).
- CI-runs van de nacht-commits niet afgewacht (deploy via SSH; tests lokaal groen).

### Volgende sessie
S247: verse-ogen-review nachtdiff → AI-kennislaag. Zie `docs/sessions/PROMPT-S247.md`.

## Sessie 246 (23 juli 2026, Fable-plan → Opus-bouw — uitgesteld versturen, LIVE + live-bewijs)

### Samenvatting
Startpunt PROMPT-S246. **Modelfout aan het begin:** Opus deed zelf het onderzoek én
het plan; Arsalan greep in ("plan = Fable"). Plan daarna opnieuw gemaakt op Fable,
gebouwd op Opus. Les vastgelegd in memory `feedback_model_choice` — "Bouwen → Opus"
in een sessieprompt slaat op de BOUWfase, niet op de plan- en reviewfase.

**Twee scope-besluiten van Arsalan vooraf.** (1) "Verstuur later" nu alleen op de
mails die je zelf opstelt (antwoord, AI-concept, gewone mail, sjabloon, vanuit
dossier) — die lopen állemaal via één deur (`/api/email/compose/send`). De twee
lopende-band-knoppen (incassostap/opvolging over meerdere dossiers) zijn bewust
uitgesteld: daar zit doc-generatie + doorschuiven in de CALLER, niet in de gedeelde
verzendfunctie, dus "later versturen" is daar een aparte, grotere klus met een eigen
keuze (schuift de zaak bij het inplannen door of pas bij verzending?). (2) Meldingen-
scope uit S245 blijft tenant-breed → nul codewijziging.

**Gebouwd.** `perform_compose_send` afgesplitst van het endpoint (inhoud ongewijzigd)
zodat de wachtrij-bezorger exact dezelfde machine draait — afzender (incasso@),
huisstijl, bijlagen, renteoverzicht, drieluik-logging, meldingen opruimen en
doorschuiven zijn identiek aan een directe verzending. Nieuwe tabel `scheduled_emails`
(TenantBase, `apply_rls` in dezelfde migratie). Minuut-job in APScheduler. Knop
"Verstuur later" met presets (Morgen 09:00 / 15:00 / eigen tijdstip) op de compose-
dialoog — dus meteen op álle vijf de routes van Arsalans lijstje. Geplande mails
zichtbaar op dossier + Mail-pagina, annuleerbaar.

**Bewust NIET verhuisd naar een nieuw servicebestand:** een drift-wachter en ~6
testbestanden prikken op `app.email.compose_router.*`; verplaatsen zou die stil
breken. Splitsing binnen hetzelfde bestand levert hetzelfde resultaat met de kleinste
kans op schade. De drift-wachter zag de verplaatste provider-uitgang correct en is
bijgewerkt (`send_via_provider` → `perform_compose_send`).

**Twee echte bugs gevangen.**
1. *Dubbelverzendrisico.* De claim (pending→sending) draaide bij een fout mee terug,
   dus een crash tussen claimen en versturen zette de rij weer op "wachtend" → de
   volgende ronde zou een mogelijk al verstuurde mail nógmaals sturen. Fix: claim
   METEEN vastleggen vóór de provider-aanroep. Blijft hij hangen, dan meldt
   `_fail_stuck_claims` na 10 min dat het ONZEKER is — nooit stil opnieuw sturen.
   Gevonden door de eigen wachter (attempts bleef 0).
2. *Migratie-drift (live op prod).* `created_at/updated_at` not-null zonder
   `server_default`; TimestampMixin vult die niet in Python. Inplannen crashte met 500.
   De tests zagen het niet: testDB komt uit de MODELLEN (create_all), prod uit de
   MIGRATIE. Fix s246 + s246b (idempotent) + nieuwe wachter
   `test_migration_timestamp_defaults.py` die álle migraties leest — rood bewezen op
   de echte fout, daarna groen.

### Gewijzigde bestanden
Backend: `email/scheduled_models.py`, `email/scheduled_service.py`,
`email/scheduled_router.py` (nieuw), `email/compose_router.py` (splitsing +
`scheduled_at`/`advance_draft_id`), `incasso/service.py`
(`complete_ai_draft_after_send` naar service-laag), `incasso/router.py` (dun),
`workflow/scheduler.py` (minuut-job), `main.py`, `alembic/env.py`, migraties
`s246_scheduled_emails.py` + `s246b_sched_ts.py`.
Frontend: `email-compose-dialog.tsx` (knop + presets + eigen tijdstip),
`scheduled-emails-panel.tsx` + `use-scheduled-emails.ts` (nieuw),
`correspondentie/page.tsx`, `zaken/[id]/page.tsx`.
Tests: `test_scheduled_emails.py` (12 wachters), `test_migration_timestamp_defaults.py`,
`test_send_route_drift_guard.py` (bijgewerkt), `conftest.py`.
Commits `9197f66`→`4269592`.

### Verificatie
131 tests groen over send/compose/mail/incasso/workflow (basislijn zonder deze
sessie óók gemeten om vervuiling uit te sluiten); ruff + tsc schoon; migratie mét
RLS geverifieerd op prod (FORCE + policy); login 200; bezorger-hartslag zonder fout.
Visueel op prod (desktop + mobiel 390×844, screenshots bekeken): knop + presets,
inplannen zonder te versturen, lijst op het dossier, annuleren.
**Live-bewijs (GO Arsalan):** mail ingepland op 23:25, automatisch vertrokken om
23:25:12 (1 poging), aangekomen in zijn gmail — bevestigd door Arsalan. Spoor klopt:
`synced_emails` outbound met afzender **incasso@kestinglegal.nl** (kantoorkanaal, net
als bij een klik) + `case_activities` "E-mail verzonden naar …".
**Testlessen:** twee pytest-runs tegelijk op dezelfde testDB gaven 68 spookfouten —
één run tegelijk (huisregel bevestigd).

### Bekende issues / bewust niet gedaan
- **Lopende band (batch/follow-up) heeft géén "Verstuur later"** — besluit Arsalan;
  vereist eerst een keuze over het moment van doorschuiven.
- **Fable-eindreview van S246 is nog niet gedraaid** (verplicht: dit raakt alle
  verzendroutes) — eerste taak van de volgende sessie.
- AI-concept-nazorg bij een geplande mail is via wachters bewezen, niet live gedraaid
  (er stond geen echt AI-concept klaar op het testdossier).

### Volgende sessie
Eerst Fable-eindreview S246, daarna S247 AI-kennislaag. Zie `docs/sessions/PROMPT-S247.md`.

## Sessie 245 (23 juli 2026, Opus-bouw → Fable-eindreview — taken+meldingen: 4 demo-punten blok 2, LIVE)

### Samenvatting
Startpunt PROMPT-S245, op Opus (klopt met de prompt: bouwen op Opus, eindreview
op Fable). Masterplan `PLAN-DEMO-PUNTEN-S243.md` sectie S245. Vier onderdelen
gebouwd, elk een eigen commit, daarna gedeployd en live geverifieerd.

**1. Dossierinfo op taken (`3cc8c37`).** `WorkflowTaskResponse` kreeg een compact
`case`-subobject (zaaknummer, cliëntnaam, debiteurnaam) via een before-validator
op het al eager geladen Case-ORM (`lazy="selectin"` op WorkflowTask.case → Case.
client/opposing_party — geen extra selectinload nodig, geen MissingGreenlet).
Fixt beide takeneindpunten tegelijk: `/api/workflow/tasks` én
`/api/dashboard/my-tasks` (die de Taken-pagina echt voedt — de prompt wees naar
`wf_list_tasks`, dat is de alias in dashboard/router). Frontend toonde
`task.case.case_number` al maar kreeg nooit data; nu ook de debiteurnaam in de
taakregel. Debiteur = opposing_party, cliënt = client.

**2. Filters op de Taken-pagina (`2517575`).** Client-side (lijst is al volledig
geladen): vrij zoeken (zaaknummer/cliënt-/debiteurnaam/taaktitel), taaktype-
dropdown (alleen aanwezige types, afgeleid van de volledige lijst — stabiel) en
eigenaar (Alle/Aan mij/Zonder eigenaar). Lege-staat is filter-bewust ("Geen
taken gevonden") + Wissen-knop.

**3. Dubbel-wegklik-bug (`91d00f1`).** Oorzaak in de bron: `completeTask.isPending`
was globaal voor álle rijen én er was geen optimistische update — de rij bleef
tot de refetch, dus na de eerste actie was de knop alweer klikbaar → tweede klik
(en bij herhalende taken meteen een dubbele opvolger). Fix: optimistische status-
update in complete/skip/restore (rij verschuift/verdwijnt meteen, rollback bij
fout, onSettled invalidate) + per-rij bezig-indicator via `mutation.variables`.

**4. Mail-meldingen gelezen na antwoord (`42c6ffb`).** Nieuwe gerichte service-
functie `mark_case_type_read` (tenant-breed, scoped op case_id + type) naast
`mark_type_read`. Aangeroepen op het gedeelde reply-verzendpunt
(`compose_router.send_via_provider`) wanneer een antwoord (`reply_to_message_id`)
op een dossier verstuurd is → ongelezen `email_received`-meldingen van dat
dossier op gelezen. Kruispunt gemeten: `reply_to_message_id` is het enige
reply-signaal en komt alléén in compose_router voor; de S244-shell stuurt het nog
steeds mee (frontend geverifieerd). Verse mail/doorsturen/sjablonen raken de
meldingen niet.

### Scope-keuze om te bevestigen
Onderdeel 4 markeert **tenant-breed** (hele kantoor), niet alleen de verzender —
omdat die mail-meldingen ook tenant-breed worden aangemaakt en de inbound na een
antwoord voor iedereen afgehandeld is. Makkelijk te versmallen naar per-gebruiker
als Arsalan dat liever heeft.

### Gewijzigde bestanden
Backend: `workflow/schemas.py` (TaskCaseInfo), `notifications/service.py`
(mark_case_type_read), `email/compose_router.py` (aanroep op reply).
Frontend: `app/(dashboard)/taken/page.tsx` (filters + debiteur in regel + per-rij
pending), `hooks/use-workflow.ts` (case-type + optimistische updates).
Tests (5 nieuwe wachters): `test_workflow.py` (case-info), `test_notifications_service.py`
(scope mark_case_type_read), `test_reply_marks_mail_read.py` (2 route-wachters:
reply wist + scoping, verse mail wist niet). Commits `3cc8c37`/`2517575`/`91d00f1`/
`42c6ffb`/`bfd57b7`. Backend+frontend gedeployd via SSH `--force-recreate` (geen migratie — additief).

### Verificatie
121 tests groen (brede -k "workflow or task or notification"); ruff + tsc schoon;
CI-groen niet apart afgewacht (deploy via SSH). Live-klikronde op prod (desktop +
mobiel 390×844, screenshots bekeken): dossierinfo op elke taak, zoeken op
debiteurnaam versmalt correct, filtercombinaties + lege-staat, één-klik-wegklik
bewezen op een verse testtaak (2026-00006, daarna via API opgeruimd). Fable-
eindreview: alle 6 commits gelezen + eigen visuele ronde (desktop filters/afgerond/
dashboard + mobiel lange debiteurnaam) — **nul reparaties**. Onderdeel 4 niet
live-gemaild (constraint geen echte debiteuren) — bewezen met de 2 route-wachters.

### Bekende issues / bewust niet gedaan
- **Onderdeel 4-scope** (tenant-breed) wacht op bevestiging Arsalan (zie boven).
- **Cosmetisch (van vóór deze sessie):** afgeronde taak toont nog "X dagen te laat"
  in de regel; meldingen-teller ververst pas bij de 30s-poll (niet direct na antwoord).
- **IN100592 3e betwisting + regeling-taken IN100281/IN100537** blijven bij Lisanne.

### Volgende sessie
S246 — uitgesteld versturen (nieuwe tabel `scheduled_emails` + RLS in dezelfde
migratie, "Verstuur later" op alle 7 verzenddeuren, scheduler met lock-patroon).
Masterplan sectie S246. Zie `docs/sessions/PROMPT-S246.md`.

## Sessie 244 (23 juli 2026, Opus-bouw — mail-werkbank: 4 demo-punten blok 1, LIVE)

### Samenvatting
Startpunt PROMPT-S244, op Opus (klopt met de prompt). Sessie-start: CI S243
nagetrokken (feature-commit + docs-commit + Deploys groen). Referentie-onderzoek
kort: Gmail/Outlook = conversation-lijst + leesvenster; Clio heeft juist een plat
logboek (precies wat onwerkbaar bleek) — Gmail/Outlook als model. Plan
voorgelegd, GO Arsalan ("ga gewoon door"), daarna 4 onderdelen gebouwd, elk een
eigen commit:

**1. Correspondentie-tab draad-gegroepeerd (`ed11d7a`).** De platte maillijst op
het dossier is nu een gesprekkenlijst (compacte rij: richting-pijl, afzender,
onderwerp + aantal, datum, ongelezen-vet, Review-badge, paperclip). Klik opent
het gesprek in het leesvenster: berichten chronologisch, nieuwste open, oudere
ingeklapt en lazy geladen; per bericht volledige kop, AI-beoordeling
(ClassificationCard), bijlagen (download + opslaan in dossier) en acties
(AI-antwoord/Beantwoorden/Doorsturen). Verzend-logboekregels (SMTP-brieven)
staan als compacte regel in het gesprek (inhoud staat in Documenten).

**2. Draad overal (`02ab4d9`).** (a) Mail-leesvenster (beide tabs): eerdere
mailtjes van dezelfde draad onder de geopende mail (MailThreadPanel met nieuwe
hideSource-vlag; alleen dossier-gekoppelde mail). (b) AI-concept-/opsteldialoog:
op lg+ wordt het paneel breder (max-w-5xl) met de draad als rechterkolom (380px)
naast het concept; onder lg blijft de S233-strook onderin (mobiel gestapeld).

**3. Verzonden-map (`dec2c2a`).** direction-parameter (inbound/outbound,
patroon-gevalideerd) op `/api/email/all` + schakelaar Alles / Postvak IN /
Verzonden binnen "Alle e-mails". Server-side, dus zoeken + "meer laden" werken
erdoorheen. Wachter dekt beide richtingen, geen-filter en 422.

**4. Vrij bericht + nette beantwoorden (`a8e4cba`).** Renderer `vrij_bericht`:
aanhef "Geachte heer, mevrouw," (huisconventie van álle sjablonen — prompt zei
"heer/mevrouw", bewust afgeweken voor consistentie) + lege romp + bestaande
huisstijl/handtekening/schuldhulpblok via render_plain_branded; in de dropdown
onder "Overig". "Beantwoorden" op dossier-mail prefillt voortaan deze shell met
het geciteerde origineel onderaan (nieuw optioneel quoted_html-veld op
render-template); de shell is al aangekleed → defaultBodyBranded-vlag voorkomt
dubbele aankleding. Zonder dossier: kale reply, huisstijl komt bij verzenden
(bestaand gedrag). Kruispunt-check verzendroute: vrij_bericht kan nooit
doorschuiven (geen stap-sjabloon), krijgt geen auto-bijlagen, reply-pad slaat
sjabloon-afleiding over. 2 wachters (shell-inhoud, citaat-afbakening).

**5. Klikronde-vondst → fix (`206def8`, LIVE).** Het antwoord van 13:18 op
IN100592 stond los van zijn gesprek: de provider gaf het een nieuw
conversation-id. In de bron gemeten: maar 7 van de 47 provider-threads op
dossier-mails dragen >1 bericht, terwijl 1472 onderwerp-groepen dat wél doen
(BaseNet-import heeft geen bruikbare thread-ids). Groepering nu op
genormaliseerd onderwerp (Re:/Fwd: eraf; leeg onderwerp → thread-id → eigen id);
MailThreadPanel matcht op onderwerp óf thread-id. Na de fix: het
Verweer-gesprek is één draad met 3 berichten.

### Gewijzigde bestanden
Frontend: `zaken/[id]/components/CorrespondentieTab.tsx` (herschreven),
`components/mail-thread-panel.tsx`, `components/email-compose-dialog.tsx`,
`correspondentie/page.tsx`, `zaken/[id]/page.tsx`, `lib/email-reply.ts`,
`hooks/use-email-sync.ts`. Backend: `email/{sync_service,sync_router,
compose_router,incasso_templates}.py`. Tests: `test_email_sync.py` (+1 helper-
param, +1 wachter), `test_email_branding.py` (+2 wachters). Commits `ed11d7a`,
`02ab4d9`, `dec2c2a`, `a8e4cba`, `206def8`; 2× deploy via SSH `--force-recreate`
(geen migratie).

### Verificatie
Brede run compose/send/template/branding 200 groen + test_email_sync 37 groen;
ruff + tsc schoon na elk onderdeel. Playwright-klikronde op prod als Lisanne,
desktop 1440×900 + mobiel 390×844, 11 screenshots bewaard (`~/s244-01` t/m
`-11`): draadlijst, gesprek met 3 berichten (nieuwste open, ouder uitklappen met
lazy-load + beoordeling), Beantwoorden-shell (aanhef/handtekening/betreft/citaat
in de editor gemeten), Verzonden-map (3393 uit / 3137 in, rijen 200/0 en 0/200),
leesvenster-draad "(2)", AI-concept naast draad (dialoog 1024px, kolom 380px;
mobiel gestapeld, geen h-scroll). Login 200, containers healthy, 0 echte
consolefouten. Testspoor opgeruimd: eigen testconcept discarded (natelling:
alleen de automatische systeemdraft + taak van 16:36 blijft — echt werk).
CI: `ed11d7a` + `a8e4cba` + S243-docs-run groen; `02ab4d9`/`dec2c2a`/`206def8`
liepen nog bij schrijven — natrekken bij S245-start.

### Bekende issues / bewust niet gedaan
- **Verzonden-map toont alleen gesynchte mail** — oude SMTP-brieven (email_logs
  zonder synced-spiegel) staan er niet in; die blijven zichtbaar op het dossier.
- Onderwerp-groepering kan binnen één dossier mails van verschillende afzenders
  met identiek onderwerp samenvoegen (bewust: zelfde partijen, zelfde gesprek).
- Reply-shell + gebruiker wist álles in de editor → mail vertrekt zonder
  huisstijl (randgeval; already_branded staat dan al vast).
- Draadpaneel in het Mail-leesvenster alleen voor dossier-gekoppelde mail.
- **Signalering (rolverdeling S240): derde betwistingsmail IN100592 binnengekomen
  23-7 16:29** + automatische concept-draft/nakijk-taak van 16:36 — inhoudelijk
  oppakken is aan Lisanne/Arsalan.

### Nagekomen — Fable-eindreview (modelwissel door Arsalan, "grondig, ook visueel")
Tegenlezing van alle S244-commits + de screenshots daadwerkelijk bekeken +
verse klikronde op prod. **4 vondsten, alle 4 direct gefixt + gedeployd:**
1. **Encoding-schade Mail-pagina (`d2aef7c`, de zwaarste):** op de Verzonden-
   screenshot stond letterlijk "3393 e-mails â€" 200 getoond" — de PowerShell-
   herschrijfstap van onderdeel 4 las het bestand als ANSI en schreef het als
   UTF-8 terug; élk niet-ASCII-teken (em-dash, ë, ·) stond dubbel gecodeerd
   op prod. Hersteld via omgekeerde cp1252-roundtrip; grep 0 restanten; live
   nagemeten ("6534 e-mails — 200 getoond", 0 mojibake). **Les: bronbestanden
   nooit met PowerShell Get/Set-Content herschrijven — Edit-tool gebruiken.**
2. **Beantwoorden op eigen uitgaande mail vulde Aan = onszelf (`5b7d7e2`):**
   reply pakt de afzender, en op een uitgaande mail zijn wij dat; de
   gespreksweergave zet nu op élk bericht een Beantwoorden-knop, dus de val
   was makkelijk te raken. Nu: uitgaand → ontvanger. Live bewezen (Aan =
   ad@on-bevreesd.nl op de sommatie van 12:32).
3. **Lijstrijen onleesbaar in smalle stand (`5b7d7e2` + `f612b54`):** met een
   geopend gesprek (kolom 2/5) én op telefoonbreedte drukte de één-regel-rij
   het onderwerp volledig weg. Smal = twee regels (afzender+datum /
   onderwerp+badges); breed één regel. Beide live + visueel bewezen.
4. **Eerlijkheidscorrectie op de eigen Opus-verificatie:** de 2 "mobiele"
   screenshots van de eerste ronde toonden alleen de bovenkant van de pagina
   (boven de vouw) — mobiel was gestructureerd gemeten maar niet écht gezien.
   Overgedaan mét scroll: lijst, gesprek en Verzonden-map nu echt vastgelegd
   (`s244-12` t/m `-16`).
Verder gecheckt, géén fout: vrij-bericht in de dropdown (visueel), shell +
citaat in de editor, logo-met-lege-src in de editor is vóórbestaand (zelfde
bij het Herinnering-sjabloon; verzendpad plakt het logo er wél in — bewezen
door de 7 sommaties van 22-7). **CI eindstand: álle S244-runs groen** (5
bouw-commits + 3 review-fixes + docs); de ene rode Deploy-run (15:17) was de
bekende race met de handmatige SSH-deploy — latere Deploys groen, prod
nagemeten op de laatste commit, containers healthy, login 200. Parallel kwam
`9808e3f` binnen (S243-tegenlezing andere terminal): natellingen bevestigd,
11 tijdlijn-rijen op prod hersteld, zoekbalk-tekstfix (met deze deploys mee
live), en 2 nieuwe signaleringen — regeling-taken IN100281/IN100537 uit oude
verzoek-mails (inhoud voor Lisanne; die van IN100537 dateert van 22 juni).

### Volgende sessie
S245 (Opus): taken + meldingen — zie `docs/sessions/PROMPT-S245.md`.

## Sessie 243 (23 juli 2026, Opus (start Fable) — opruimronde + demo-puntenlijst: meting, plan, fase-vindbaarheid, 11 heropend)

### Samenvatting
Start volgens PROMPT-S243 (CI S242 nagetrokken: afzender-fix groen; signaleringen
IN100015/IN100127 + 2 open mails doorgegeven). Arsalan koos de opruimronde en gaf
daarna een demo-puntenlijst van 13 wensen/vragen.

**1. Opruimronde (GO per categorie, elk dry-run + natelling exact):** 37
test-taken gesloten (testdossiers 2026-00007 t/m -00019; de 18 echte bleven), 14
test-adviezen afgewezen (8 echte bleven), 38 testmails/reclame weggedrukt, 15
test-intakes afgewezen. Blijft voor Lisanne/Arsalan: 4 mogelijk-echte mails in de
ongesorteerde bak (Incassocenter 7-7, eigen Factuur F2026-00001, 2× Purple
Exchange) + 1 echte intake (Ram Charan Sukhdai, € 10.824,97).

**2. Demo-puntenlijst → gemeten + 4-sessieplan.** Alle 13 punten in de bron
gemeten (code + prod + BaseNet-export). Masterplan
`docs/plans/PLAN-DEMO-PUNTEN-S243.md`; prompts S244 (mail-werkbank: tab-redesign,
draad overal, Verzonden-map, lege sjabloon), S245 (taken: dossierinfo/filters/
dubbel-wegklik + mail-meldingen weg na antwoord — besluit Arsalan), S246
(uitgesteld versturen op alle 7 verzenddeuren), S247 (AI-kennislaag:
placeholder-bug IN100606 + juridische kennisregels IN100458). Harde eis Arsalan:
alles visueel testen met Playwright + screenshots.

**3. Kernvraag Arsalan: "staan de export-dossiers überhaupt in Luxis?" — JA,
bewezen:** alle 607 inccodes uit `Xml_02-07-2026_2400.zip` 1-op-1 vergeleken met
prod: 0 ontbreken, 0 extra. Probleem was vindbaarheid: `basenet_origin_phase`
(S207d) was niet doorzoekbaar. **Gefixt (`062ac4b`, LIVE):** zoekbalk zoekt door
de fase + nieuw fase-filter op de dossierlijst (opties via nieuw endpoint, vóór
de /{case_id}-route). 3 wachters; visueel bewezen op prod (filter én zoekterm
geven exact de 11, screenshot bewaard).

**4. De 11 "Akkoord dagvaarden"-dossiers heropend (prod-mutatie, dry-run + GO +
natelling 11/11):** IN100046/077/246/252/281/294/364/419/487/509/537 → status
in_behandeling, eigenaar Lisanne, stap "Akkoord dagvaarden", rente-bevriezing
gewist (draaiboek-eis #9). Vooraf gecheckt: 0 doorschuifregels vanaf de stap,
geen sjabloon (kan niets versturen), email_logs 54 vóór==ná, 0 archiefzaken
geraakt, verjaringssommetje vroegste feb 2028 (geen ruis-meldingen). Verwacht
effect: per dossier een follow-up-advies "handmatige beoordeling" + taak
"Vervolg bepalen" (bedoeld). Overige 406 dichte werkvoorraad-dossiers per fase
in beslislijst `docs/plans/BASENET-STATUS-HERSTEL.md` — heropening blijft per
groep na GO.

### Gewijzigde bestanden
`backend/app/cases/{service,router}.py` (fase-zoek + filter + opties-endpoint),
`frontend/src/hooks/use-cases.ts`, `frontend/src/app/(dashboard)/zaken/page.tsx`,
`backend/tests/test_basenet_phase_filter.py` (nieuw, 3). Docs: masterplan,
beslislijst, PROMPT-S244 t/m S247. Prod-mutaties: opruimronde (37/14/38/15) + 11
heropend. Commit `062ac4b` + docs-commit.

### Verificatie
3 nieuwe wachters + test_cases 33 groen; ruff + tsc schoon; backend+frontend
gedeployd via SSH `--force-recreate`, containers healthy, login 200. Visueel:
Playwright op prod — fase-filter 11/11, zoekterm 11/11 (screenshot
`s243-fase-filter-11-dossiers.png`). Alle prod-mutaties dry-run + natelling
exact. Model-les: het filter-bouwwerk startte per ongeluk op Fable — door
Arsalan gecorrigeerd, afgemaakt op Opus.

### Bekende issues / bewust niet gedaan
- 193 ongelezen meldingen: bewust laten staan (geen akkoord gevraagd/gegeven).
- Meldingen over de nu gesloten test-taken blijven bestaan (onschadelijk).
- CI van `062ac4b` + docs-commit liep nog bij afsluiten — natrekken bij S244.

### Nagekomen (Fable-tegenlezing + herstel, parallel aan S244)
Tegenlezing van het eigen S243-werk (read-only zolang S244 bouwde; herstel na
GO Arsalan toen S244 klaar was):
- **Bevestigd:** opruim-natellingen, 607-check, filter-code (routevolgorde,
  tenant-scoping), heropening (0 mails, rente conform S207b-uitrol — IN100077
  wettelijk want particulier), rooktest dossierpagina OK.
- **Voorspelling bewezen:** scanner 16:14 → exact 11 adviezen 'escalate' + 11
  taken "Vervolg bepalen". Bijvangst: 2 extra taken "Betalingsregeling
  vastleggen" (IN100281, IN100537) — oude regelingsverzoek-mails (0.95) die nu
  de zaak open is alsnog een bewakingstaak kregen; terecht gedrag, **inhoud voor
  Lisanne** (IN100537-verzoek is van 22 juni!).
- **Hersteld:** staphistorie-gat — 11 open historie-rijen toegevoegd (trigger
  manual, notitie "Heropend uit BaseNet-fase", email_sent=false dus geen
  scanner-effect); tijdlijn toont de stap nu (screenshot
  `s243-herstel-tijdlijn-IN100487.png`). Zoekbalk-tekst noemt nu ook
  factuurnummer + fase (mini-fix op Fable, gemeld).
- **Werkwijze-les (gemaakt fout):** 2 draaiboek-checks (S195-notities,
  rentetype) pas NÁ de heropening gedaan i.p.v. ervoor — uitkomst was schoon,
  volgorde fout. Bij volgende fase-groepen: checks éérst.
- **Signalering:** IN100592 (Zwartbol) mailde 23-7 opnieuw (13:21; derde
  betwisting 16:29 zag S244 ook) — bij Lisanne.

### Volgende sessie
S244 (Opus): mail-werkbank — zie `docs/sessions/PROMPT-S244.md`.

## Sessie 242 (23 juli 2026, Opus-bouw — veegsessie voorstel-lijst: 3 kleine verbeteringen, LIVE)

### Samenvatting
Startpunt PROMPT-S242, op Opus (klopt met de prompt — bouwwerk). Bij start de
administratie afgewerkt: S240-entry alsnog geschreven (parallelle terminal had
hem niet meer geschreven; S232+S233 naar het archief, PROMPT-S241 gearchiveerd),
CI van S241 nagetrokken (alle runs groen) en de 2 verjaringsmeldingen + 2 open
mails aan Arsalan gesignaleerd (niet zelf opgepakt — rolverdeling S240).

**1. Dubbelklik-betaling-slot (S240 vondst 2, `cd4c70a`).** Twee gelijktijdige
identieke deelbetalingen werden allebei geboekt (beide 201, live bewezen S240).
Poort op het gedeelde punt van álle boekroutes (service-laag, agent-laag-afspraak
S237): (a) rij-slot op de zaak (zelfde patroon als derdengelden audit #70)
serialiseert gelijktijdige boekingen — maakt ook de volbetaald-/overbetaal-poort
race-vrij; (b) dedup-venster 10s weigert een identieke betaling (bedrag/datum/
wijze/omschrijving) direct na de vorige, met duidelijke NL-melding. Bron-record-
routes (bankimport, BaseNet-import, S195-script) slaan de dedup-poort expliciet
over (twee identieke échte overboekingen op één dag zijn daar legitiem; het slot
geldt wél). Rode tests eerst, sequentieel én echt gelijktijdig — beide rood
bewezen tegen de oude code. Bekende grens (bewust, in commit): dubbelklik ÉN
overbetaling tegelijk op de derdengelden-route glipt langs het venster
(afgekapt bedrag ≠ ingediend bedrag); upgrade-pad = uniek indienings-id.

**2. Belofte-taak × actieve regeling (S241 voorstel 2, `024eb6b`).** Gekozen
gedrag, beide volgordes van hetzelfde dubbel-werk: belofte-mail op zaak met
lopende regeling → géén belofte-taak (de termijn-bewaking bewaakt die betaling
al; zelfde poort als de regeling-verzoek-taak S235); én regeling vastgelegd
terwijl er al een belofte-taak open staat (de gewone gang van zaken) → open
belofte-taak wordt 'skipped' via de bestaande sluit-helper (S236-conventie).
Tegenproeven: belofte zonder regeling geeft gewoon een taak; geannuleerde
regeling onderdrukt niets meer.

**3. Eigenaarloze te-laat-taken-melding (S241 voorstel 3, `ec10221`).** De
dagelijkse job stuurde de melding voor een taak zonder eigenaar naar de
toevallig 'eerste' gebruiker. Nu: melding bij álle actieve gebruikers,
consistent met de werklijst; taken mét eigenaar blijven bij die eigenaar;
30-dagen-dedup blijft gelden. Eenmalig effect: de andere gebruiker krijgt de
al-gemelde eigenaarloze taken bij de eerstvolgende ochtendrun alsnog — als
bundel-rij (S241-bundeling), geen storm.

### Gewijzigde bestanden
Backend: `collections/service.py` (slot + dedup + regeling-poorten),
`workflow/scheduler.py` (melding-doelen), `ai_agent/payment_matching_service.py`
+ 2 importscripts (skip-vlag). Tests: `test_payment_double_submit.py` (nieuw, 5),
`test_payment_promise_task.py` (+3), `test_deadline_notification_targets.py`
(nieuw, 3). Geen frontend, geen migratie. Commits `cd4c70a`, `024eb6b`,
`ec10221` + 3 docs-commits (administratie).

### Verificatie
Elke fix eerst rood bewezen (het gelijktijdigheids-scenario apart tegen de oude
code via git stash). 11 nieuwe wachters; brede run payment/promise/notification/
scheduler 231 groen + trust/matching 82 groen; ruff schoon (frontend onaangeraakt,
geen tsc nodig). Backend gedeployd via SSH `--force-recreate`, container healthy,
login 200, prod-logs 0 fouten. CI groen op alle drie de fix-commits (success
nagetrokken via gh) + Deploy-runs groen.

### Bekende issues / bewust niet gedaan
- Derdengelden-randgeval van punt 1 (zie boven) — voorstel: uniek indienings-id
  per formulier als het ooit speelt.
- Rest van de voorstel-lijst bewust niet aangeraakt (scope-hek S242): categorie
  'onduidelijk', overbetaling-knop, cascade bij dossier-verwijderen,
  weekend-logica, kostenblokje.
- Inhoudelijk werk blijft bij Lisanne/Arsalan: verjaringsmelding IN100127
  beoordelen, 2 open mails (IN100128, IN100586), verweer-concepten, opruimronde.

### Nagekomen (vraag Arsalan): kent Luxis stuiting? Nee — gemeten op IN100015
Arsalan: "IN100015 is niet verjaard, Lisanne stuit altijd; de deurwaarder heeft
een verzoekschrift betekend — ziet Luxis dat?" Onderzocht (alleen-lezen, niets
gebouwd): **nee.** De verjaringsbewaking is een kaal rekensommetje (oudste
vordering opeisbaar + 5 jaar; hier 15-10-2020 → "VERJAARD" per 15-10-2025) en
kijkt nérgens naar mails, sommaties, deurwaarder of betekening; een
stuitingsveld bestaat niet. Ironie: Luxis' eigen sommatiebrieven bevatten een
stuitingsclausule (art. 3:317 BW) — het systeem schrijft stuitingen maar telt
ze niet. Het bewijs zit wél in het dossier: 15 mails, waarvan 8 over
deurwaarder/betekening/verzoekschrift (apr-mei 2025) en 2 letterlijk over
stuiting. De melding (4-7) is bovendien dubbel achterhaald: dossier is 13-7
afgesloten (afgesloten dossiers worden niet meer gecheckt) — mag weggeklikt.
Zelfde kanttekening geldt voor de IN100127-waarschuwing (zelfde sommetje).
**Voorstel (niet gebouwd, scope-hek): stuitingsdatum op het dossier die de
teller verzet, evt. slimme herkenning van stuitings-/deurwaardermails.**
Verder voor de demo een nakijk-lijst (20 punten) aan Arsalan gegeven; demo-ronde
met Lisanne + Fable-tegenlezing van S242 volgen buiten deze sessie.

### Nagekomen 2 (demo-staart, live met Arsalan)
- **IN100592 uitgelegd (niets gewijzigd):** de twee betwistingsmails schoven de
  keten NIET twee keer door — verzending eerste sommatie = 1 stap door, eerste
  betwisting = parkeren op 'Verweer beantwoorden', tweede mail deed niets met de
  stap. Er is geen sommatie overgeslagen (keten heeft 4 sommatiestappen; alleen
  de eerste is ooit verstuurd). Wel gat: de parkeerstap heeft geen doorschuif-
  regel én alle bewakers slaan hem over → na het verweer-antwoord bewaakt
  niemand de reactietermijn (3-4 dagen) uit de brief.
- **Voorstel vastgelegd (richting akkoord Arsalan, NIET gebouwd):**
  `docs/plans/VOORSTEL-verweer-parkeerstap-terugkeer.md` — verstuurd antwoord +
  X dagen stilte → dossier automatisch terug naar de sommatiestap van vóór het
  verweer; follow-up-adviseur pakt het dan vanzelf op. Met 3 controlepunten
  (openstaand-verweer-slot, generate-only-batch-randgeval, termijn nameten).
- **Demo-vondst afzender-weergave, GEFIXT + LIVE (`7d0b831`, op Fable —
  bewuste afwijking model-regel wegens lopende demo, gemeld):** bij 'Verzenden
  als' kantooradres registreerde het dossier de vervoerende mailbox (seidony@)
  als afzender i.p.v. wat er écht op de mail stond (incasso@). Alleen
  wéérgave — de debiteur zag altijd al incasso@ (bezorging bewezen: 0 bounces,
  antwoorden komen op incasso@ binnen). Rode test eerst + tegenproef, 134
  send/compose-tests groen, gedeployd, login 200. De 9 oude registraties
  (7 sommaties 22-7 + 2 antwoorden 23-7) blijven staan — keuze Arsalan
  (cosmetisch). Structureel verdwijnt seidony@ als vervoerder pas bij de
  geplande M365-verhuizing van Lisanne. CI van deze commit liep nog bij
  afsluiten — natrekken bij S243-start.

### Volgende sessie
S243: Arsalan bepaalt de hoofdtaak (opruimronde met Lisanne is de sterkste
kandidaat volgens de S241-werklastmeting — geen nieuwe bouw nodig). Zie
`docs/sessions/PROMPT-S243.md`.

## Sessie 241 (23 juli 2026, Fable-testronde → Opus-bouw → Fable-tegenlezing — testronde 3 + Negeren-fix + meldingen-bundeling, LIVE)

### Samenvatting
Parallel aan de S240-afronding in een andere terminal (afspraak: administratie
dáár, dus deze afsluiting kwam pas na expliciete opdracht van Arsalan; de
S240-entry ontbreekt hier nog). Model-cyclus netjes gevolgd: testronde op Fable,
bundeling gebouwd op Opus (wissel door Arsalan), Fable-tegenlezing erna.

**Testronde 3 — 10 scenario's, drie verse brillen** (logboek:
`docs/sessions/S241-SCENARIOS.md`; verwacht-resultaat vooraf, wegwerpdossier
2026-00021 volledig gewist + nageteld 0, lokale wegwerp-medewerker idem):
- **Bril A (S240-functies op kruispunten):** belofte-taak met verleden-datum,
  auto-sluiten bij betaling, heropening, dossier-sync×melding — allemaal goed.
  **Vondst 1 (gefixt, `da81429`): een met "Negeren" weggedrukte mail werd bij een
  latere sync stil aan een dossier gekoppeld** (via dossier-sync én via later
  aangemaakt dossiernummer). Rode test eerst; Negeren wint nu van elke sync,
  bounces mogen wél blijven koppelen (tegenproef). 6 wachters, 1002 tests groen.
- **Bril B (twee gebruikers/rollen):** werklijst-verschil seidony 61 vs kesting 38
  = puur toewijzing + bewuste eigenaarloze-taken-regel; rollen-matrix klopt (droog
  + live steekproef lokale omgeving: 4× 403 beheer, 200 dagelijks werk).
- **Bril C (de ochtend van morgen):** server draait UTC → jobs 08:00-10:00 NL;
  morgen kleurt 1 taak, 0 nieuwe meldingen (30-dagen-dedup werkt). Werklast-meting:
  65 taken (39 test/26 echt), 21 adviezen (14/7), 16 aanvragen — opruimronde is de
  sleutel, niet nieuwe bouw. Blok D (derde AI-ronde) bewust overgeslagen: S238
  testte de antwoordlaag vers en S240/S241 raakten dat pad niet.

**Meldingen-bundeling gebouwd + LIVE (GO Arsalan, `275d9f4`).** Meting: 112
ongelezen bij seidony, 93 bij kesting (63× taak-te-laat, 25× nieuwe-mail) — de
bel was onbruikbaar. Nu: typen met 3+ ongelezen worden één bundel-rij met teller
("63 taken of deadlines te laat"); klik → overzichtspagina van dat type + hele
stapel in één keer gelezen (nieuwe route `PUT /read-by-type`, alleen eigen
gebruiker+type). Bundels altijd bovenaan (nooit weggedrukt door de 15-rijen-kap);
losse + gelezen meldingen onveranderd; platte lijst (dossier-actiefeed) expliciet
ongewijzigd — wachter bewaakt beide. Direct effect: 2 verjaringswaarschuwingen
("VERJAARD! Direct actie vereist", IN100015 + IN100127) werden zichtbaar die
eerst in de stapel verdronken → **inhoudelijk oppakken is aan Lisanne/Arsalan
(rolverdeling S240)**. Fable-tegenlezing: geen fouten; 3 bewuste nuances
gedocumenteerd (snooze telt mee in bundel-klik, zelfde rijen als dossier-feed,
badge blijft ruw aantal).

### Gewijzigde bestanden
`backend/app/email/sync_service.py` (Negeren-poort),
`backend/app/notifications/{service,schemas,router}.py` (bundeling),
`frontend/src/hooks/use-notifications.ts`,
`frontend/src/components/layout/app-header.tsx`. Nieuwe tests:
`test_s241_sync_kruispunten.py` (6), `test_notification_bundling.py` (7).
Logboek: `docs/sessions/S241-SCENARIOS.md`.

### Verificatie
Email/sync-suite 1002 groen + 33 meldingen-tests groen; ruff + tsc schoon; 2×
gedeployd via SSH `--force-recreate` (backend; daarna backend+frontend),
containers healthy, login 200, prod-logs 0 fouten. Bundeling live nageteld
(gebundelde én platte lijst naast elkaar); klik-flow live bewezen met 3
wegwerp-meldingen (precies 3 gelezen, 0 andere geraakt, daarna gewist,
natelling 0). CI: fix-commit groen (alleen bekende sharp-audit rood, mag falen);
bundeling-commit liep nog bij afsluiten — **natrekken bij S242-start**.

### Bekende issues
- S240-entry in dit bestand ontbreekt nog (parallelle terminal) — staat die er
  bij S242-start nog niet, schrijf hem dan compact uit `S240-SCENARIOS.md` + git log.
- Voorstellen (niet gebouwd, scope-hek): belofte-taak naast actieve regeling =
  dubbel bewakingswerk; eigenaarloze te-laat-taken melden bij "eerste" gebruiker
  (willekeurige volgorde).

### Volgende sessie
S242 (Opus): kleine veegsessie voorstel-lijst — zie `docs/sessions/PROMPT-S242.md`.

## Sessie 240 (23 juli 2026, Opus-bouw → Fable-review → Fable-testronde 2 — bak-melding + belofte-bewaking + klik-ronde, LIVE)

### Samenvatting
Entry geschreven bij S242-start (compact uit `docs/sessions/S240-SCENARIOS.md` +
git log) — de parallelle terminal sloot af zonder deze entry.

**Bouw (GO Arsalan na S239, `4c8f787`, Opus):** de twee sterkste S239-voorstellen:
- **Melding ongesorteerde bak** — nieuwe binnenkomende mail die niet automatisch
  te koppelen is → melding bij alle actieve gebruikers (dicht het S237-gat
  "debiteur-reactie vanaf onbekend adres valt stil"); geldt alleen NIEUWE
  binnenkomers, de 81 oude ongesorteerde mails spammen niet.
- **Betaalbelofte-bewaking** — belofte-mail (datum+bedrag al herkend door de
  classificatie) → bewakingstaak op de beloofde datum
  (`ensure_payment_promise_task`); sluit automatisch bij volledige betaling.

**Fable-review → 2 fixes (`d141f35`):** belofte-taak sluit ook bij handmátig
zaak-afsluiten (route-kruispunt); melding-doorklik werkt ook als de Mail-pagina
al open staat. Rolverdeling vastgelegd (`b42a140`, Working Agreement CLAUDE.md):
sessies bouwen, Lisanne doet het inhoudelijke werk.

**Testronde 2 (Fable na modelwissel, logboek `S240-SCENARIOS.md`):** bril
"slordige gebruiker" (8 scenario's, prod-API op wegwerpdossier 2026-00021) +
bril "klik-ronde als Lisanne" (6 scenario's, Playwright tegen prod, desktop +
mobiel 390×844). 13/14 goed — validaties overal netjes (422/400 met NL-meldingen,
bedragen op de cent), cijfers dashboard/dossier consistent én handmatig nagerekend.
- **Vondst 1 (🅰, gefixt `6192ac3`):** melding-doorklik naar exact dezelfde URL
  deed niets na eerdere doorklik + handmatige tabwissel — tabwissel maakt de URL
  nu weer kaal; live herbeklikt en bewezen.
- **Vondst 2 (🅲, → S242):** dubbelklik/2 tabs boekt een deelbetaling dubbel
  (beide 201; alleen UI-demping, geen slot in de service-laag).

Bijvangst (echt, niet aangeraakt): IN100592 (Zwartbol) mailde opnieuw mét
dossiernummer → automatisch gekoppeld + als verweer beoordeeld (0.75).

### Gewijzigde bestanden
Backend: `ai_agent/orchestrator.py`, `collections/service.py`,
`email/sync_service.py`, `notifications/service.py`, `workflow/hooks.py`,
`cases/service.py`. Frontend: `correspondentie/page.tsx`, `app-header.tsx`,
`use-notifications.ts`. Tests: `test_email_unsorted_notification.py`,
`test_payment_promise_task.py`. Commits `4c8f787`, `d141f35`, `6192ac3`,
`b42a140`, `d9e35f0`.

### Verificatie
Wegwerpdossier 2026-00021 volledig gewist (natelling 0); klikproef-melding
gewist (natelling 0); geen mail verstuurd; 0 consolefouten in de klik-ronde;
screenshots mobiel bewaard. CI van alle S240-commits groen (nagetrokken in
S241/S242).

### Volgende sessie
S241 draaide parallel (zie entry hierboven); S242 = veegsessie voorstel-lijst.

## Sessie 239 (22/23 juli 2026, nacht — Fable autonoom: scenario-nachtronde + fixloop, LIVE)

### Samenvatting
Arsalans opdracht (avond 22-7): bedenk 20-30+ scenario's waar Lisanne in haar
dagelijkse advocatenwerk tegenaan kan lopen, test ze, en los alles op — fouten +
kleine ergernissen direct fixen, ontbrekende functies als voorstel; echte
AI-aanroepen mochten; niets naar echte debiteuren; Arsalan sliep. Methode vooraf
onderbouwd (persona-/scenario-testen + "soap opera testing") en aangescherpt met:
verwacht-resultaat vóóraf per scenario, driedeling van vondsten, veilig testterrein
met terugdraai-plicht, wachter per foutsoort, einde-criterium.
**Let op: hele nacht op Fable gewerkt (ook de fixes) — Arsalan was er niet om naar
Opus te wisselen; expliciet gemeld.**

**32 scenario's in 5 groepen** (werkdag, rare debiteur, cliënt-kant, tijd/termijnen,
rand/systeem), volledig logboek in `docs/sessions/S239-SCENARIOS.md`. Geld-scenario's
live op een wegwerpdossier (2026-00020, exact teruggedraaid incl. vorderingen);
mail/AI-scenario's met 2 geïnjecteerde testmails + echte AI-calls op 2026-00006
(teruggedraaid); de rest gemeten op prod (read-only) of droog via code + bestaande
wachters.

**13 vondsten → 5 gefixt (commit `6f15a13`, 10 nieuwe wachters, LIVE):**
1. Betaling op volbetaalde zaak werd stil geboekt → totaal openstaand −100 (live
   gereproduceerd); poort gold alleen bij openstaand > 0. Derdengelden houdt
   surplus-gedrag.
2. Samengesteld kenmerk (`D102733_I71828409`) nooit herkend (underscore-woordgrens);
   na de fix koppelde de sync direct 2 échte mails die 9 dagen resp. 5 weken
   ongesorteerd lagen.
3. Concept weggooien liet de nakijk-taak eeuwig open (8 spooktaken op prod);
   gedeelde sluit-helper op alle 3 vervall-routes (P3-uitbreiding), live bewezen.
4. Regeling nagekomen maar zaak niet vol betaald → bleef stil op pauzestap; nu taak
   "Regeling afgerond — vervolg bepalen" (S235-recept, met tegenproef).
5. Dossier onvindbaar op factuurnummer van de vordering; nu in beide zoekpaden.

**Goed bevonden (o.a.):** alle geld-rekenwerk op de cent (rente, BIK-staffel,
6:44-verdeling, herrekening na extra vordering — onafhankelijk nagerekend);
rentetabel actueel (handelsrente 10,40% per 1-7-2026, extern geverifieerd);
autosluiting + factureer-melding + heropening-vangnet; mail-koppeling kiest nooit
stil een verkeerd dossier; ontdubbeling 0 dubbelen; verjaring-monitor bestaat.

**Voorstel-lijst (7, niet gebouwd — scope-hek):** melding ongesorteerde bak
(S237-gat, sterkste kandidaat), betaalbelofte-bewaking (datum+bedrag worden al
herkend, live bewezen 0.95), meldingen-bundeling (145 ongelezen), categorie
'onduidelijk', overbetaling-knop, cascade bij dossier-verwijderen, weekend-logica.

### Verificatie
351 tests groen (alle geraakte kruispunten), ruff schoon, backend deployd via SSH
`--force-recreate`, containers healthy, login 200, prod-logs 0 fouten sinds deploy,
live natellingen per fix (zie logboek). CI: liep nog bij schrijven — natrekken.
Testsporen: wegwerpdossier volledig gewist; blijvend: ai_usage-rijen (bedoeld),
1 spooktaak dicht (2026-00012), 2 echte mails gekoppeld (gewenst effect).

### Vervolg (besloten ochtend 23-7)
Arsalan: GO voor voorstel 1+2 (bak-melding + belofte-bewaking) en testronde 2 met
brillen "slordige gebruiker" + "klik-ronde als Lisanne" — in een VERSE sessie op Opus
(S240, prompt klaargezet). CI beide S239-commits groen (success via gh nagetrokken).
De 2 gevonden mails wachten nog op antwoord — eerste vraag van S240.

## Sessie 238 (22 juli 2026, Opus-bouw → Fable-eindreview — expliciete schema-koppeling + native structured outputs, LIVE)

### Samenvatting
Startpunt PROMPT-S238. Model-cyclus expliciet gevolgd (wissel zelf gesignaleerd
vóór start — les S237): bouw op Opus, eindreview op Fable.

**Hoofdtaak — de kwetsbaarste laag van het AI-fundament vervangen.**
`kimi_client` raadde welk JSON-schema bij een aanroep hoorde via een Nederlands
trefwoord in de prompttekst (`_detect_schema`); een gewijzigde promptzin liet zo'n
aanroep stil terugvallen op tekst-parsen. Nu geeft **elke aanroeper zijn schema en
purpose expliciet mee** (verplichte keyword-args, geen defaults): classificatie,
intake, factuur (tekst + PDF), stap-concepten (`call_draft_ai`), dossier-concepten
(`draft_service`), compose/antwoord (`unified_draft_service`) en het testronde-
script. `_detect_schema`, `_PROMPT_SCHEMA_MAP`, `_parse_json`, `_call_haiku` en
`_call_sonnet` zijn weg. Model-routing ongewijzigd (Haiku extractie, Sonnet
concepten); `ai_usage`-registratie blijft per aanroep werken.

**Native structured outputs + drie live gevonden API-grenzen.** Tekst-routes
draaien op `output_config.format` (GA voor Sonnet 4.6/Haiku 4.5; API garandeert
schema-geldige JSON); de PDF-route houdt forced tool_use (docs garanderen de
combinatie met document-input niet), waar mogelijk met `strict`. De prod-natelling
ving drie niet-gedocumenteerde grammar-grenzen: (1) max 24 optionele velden
(factuurschema: 54 → alle velden verplicht gemaakt, nullable), (2) max 16
nullable/union-velden (factuurschema: 27 → statische poort `_grammar_fits` kiest
dan forced tool_use), (3) **"Grammar compilation timed out" op het intake-schema
dat binnen de limieten past** (Fable-reviewvondst) → runtime-vangnet: elke 400 op
het structured-pad krijgt één herkansing via niet-strict forced tool_use — het
oude bewezen gedrag, maar mét expliciet schema. Nooit meer een harde AI-uitval
door een schemagrens.

**Schema's kloppend gemaakt met hun prompts.** De classificatie vroeg `sentiment`
en `defense_type` die het oude schema niet kende; het factuurschema miste 13 van
de 28 promptvelden (o.a. contactpersonen, crediteur-postadres) — met
`additionalProperties=false` zouden die stil zijn weggefilterd. Nieuwe schema's
naast hun prompt: `CASE_DRAFT_SCHEMA`, `UNIFIED_DRAFT_SCHEMA`, `_CORRECTOR_SCHEMA`.

### Gewijzigde bestanden
Backend: `ai_agent/kimi_client.py` (herschreven), `ai_agent/{service,intake_service,
invoice_parser,draft_service,unified_draft_service}.py`, `incasso/automation_service.py`,
`scripts/ai/antwoord_testronde.py`. Tests: `test_kimi_client_structured.py` (nieuw, 20
wachters: verplichte keyword-args, schema-geldigheid, prompt↔schema-sync per route,
grammar-poort, runtime-terugval), `test_unified_draft_service.py` (mock-signaturen).
Commits `e278a51`, `6cf04a8`, `0687306`, `80786f1`; backend 4× via SSH
`--force-recreate` (geen migratie, geen frontend).

### Verificatie
20 nieuwe wachters groen; brede AI-run 239 groen (kimi/unified_draft/ai_agent/
intake/invoice) + followup/draft-suites 193 en incasso_pipeline 55 groen; ruff
schoon; CI groen op alle 4 commits (conclusion=success via API nagetrokken).
**Live natelling op prod: alle 7 routes** (classificatie, intake, factuur-tekst,
compose/antwoord, dossier-concept, stap-concept, PDF) — elk 1 echte AI-call, resultaat
schema-conform, 7 rijen in `ai_usage` met kosten. Prod-logs sinds deploy: 0 AI-fouten;
containers healthy, login-API 200. **Extra op verzoek Arsalan: antwoord-testronde met
46 verse AI-antwoorden** (18 scenario's + 28 goud-gevallen, corrector aan, niets
verstuurd) — 0 storingen, 0 echte fouten; de 2 corrector-markeringen beide handmatig
weerlegd als controleur-missers (rapport: `docs/sessions/S238-antwoord-testronde.md`).

### Bekende issues / bewust niet gedaan
- **Intake-route loopt structureel via het tool_use-vangnet** ("Grammar compilation
  timed out" reproduceerde 2×) — functioneel identiek resultaat; als Anthropic de
  grammar-compilatie verbetert gaat de route vanzelf native. Geen actie nodig.
- De verweer-PDF-route (`call_draft_ai` mét AV-PDF) is niet apart live afgevuurd —
  zelfde codepad als de wel-geteste PDF-route (enige verschil: het schema, en
  INCASSO_DRAFT_SCHEMA is live bewezen op de tekst-route).
- Lopende zaken onaangeraakt (bij Lisanne): verweer-concepten IN100592/IN100606,
  IN100492-vraag, opruimronde.

### Volgende sessie
S239: **Arsalan legt de hoofdtaak bij start zelf uit** (aangekondigd bij dit
sessie-einde). Achtergrond-punten die er nog liggen (Lisanne-antwoorden,
opruimronde, onbekend-afzender-gat) staan als context in
`docs/sessions/PROMPT-S239.md`.
