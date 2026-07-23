# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 23 juli 2026 (S244 — mail-werkbank LIVE: draad-gegroepeerde correspondentie, draad overal, Verzonden-map, vrij bericht-shell).
**Laatste feature/fix:** Mail-werkbank (5 bouw-commits) + Fable-eindreview met 4 gefixte vondsten t/m `d2aef7c` (encoding-schade, reply-aan-onszelf, onleesbare smalle rijen, mobiele herkansing) — alles live + visueel bewezen.
**Openstaand:** demo-puntenreeks S245-S247 (taken+meldingen → uitgesteld versturen → AI-kennislaag, masterplan `docs/plans/PLAN-DEMO-PUNTEN-S243.md`); **derde betwistingsmail IN100592 (23-7 16:29) + auto-concept én 2 regeling-taken IN100281/IN100537 (oude verzoeken, S243-tegenlezing) wachten op Lisanne**; fase-heropening per groep (beslislijst `docs/plans/BASENET-STATUS-HERSTEL.md`); 4 review-mails ongesorteerde bak + intake Ram Charan Sukhdai bij Lisanne/Arsalan; IN100015-melding wegklikken; IN100127 beoordelen; 2 open mails (IN100128, IN100586) + verweer IN100592/IN100606 + IN100492 bij Lisanne; verweer-parkeerstap-voorstel; 193 ongelezen meldingen. Losse punten: BaseNet-delisting, kostenblokje, opmaak-restpunt S227, S221b-rest, DMARC, 4 cosmetische restjes S235, sharp-CVE's.
**Volgende sessie:** S245 — taken + meldingen (Opus); zie `docs/sessions/PROMPT-S245.md`.

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

## Sessie 237 (22 juli 2026, Fable-meting → Opus-bouw → Fable-review + Fable-onderzoek — sommatie-reacties + escalatie-taken LIVE + toekomst-repos)

### Samenvatting
Startpunt PROMPT-S237. Model-cyclus expliciet gevolgd na correctie Arsalan
("dit is denkwerk → Fable"): meting/review/onderzoek op Fable, bouw op Opus.

**1. Reacties op de 7 sommaties van 22-7 (vers gemeten op prod).** 0 bounces.
Drie afzenders reageerden:
- **IN100606 (Maatwerk)** — bekende betwisting; concept klaar, wacht op Lisanne
  (keuze Arsalan: laten liggen).
- **IN100592 (Onbevreesd) — nieuwe betwisting die het systeem NIET zag:** debiteur
  Zwartbol mailde 2× vanaf privé-hotmail (ander adres dan waar de sommatie heen
  ging, geen dossiernummer) → ongesorteerde bak, geen melding/beoordeling. Na
  handmatig koppelen (keuze Arsalan, via de gewone app-route) deed Luxis de rest
  binnen 6 min zélf: 2× betwisting geclassificeerd (85%/92%), zaak → 'Verweer
  beantwoorden', concept klaar. Bijvangst: 2 concepten + 2 nakijk-taken (elke mail
  triggerde er één) — opruimronde. **Structureel gat genoteerd: debiteur-reactie
  vanaf onbekend adres valt stil** (alleen zichtbaar in ongesorteerde bak).
- **IN100492 (Petri, buiten de 7)** — debiteur vraagt update op een AFGESLOTEN
  dossier met €0 betaald (~€1.950 open). Vraag voor Lisanne.

**2. Escalatie-taken op de werklijst (keuze Arsalan, LIVE + nageteld).** Elk open
escalatie-advies krijgt een taak "Vervolg bepalen — {zaaknummer}" (source
`followup_escalate`), knop "Beoordelen" → /followup. Sluit mee via supersede/
afwijzen (skipped); de doorschuif-motor sluit bewust alléén verstuur-taken
(brief ≠ escalatie-besluit); 'Uitvoeren' dedupet tegen de spiegel-taak.
Prod: 14 taken = exact de 14 geldige pending escalate-adviezen (waarvan 4 échte
'Voorstel dagvaarding'); IN100521 terecht overgeslagen (advies stale — zaak al op
'Verzoekschrift faillissement'). Fable-review: GO; idempotentie live bewezen
(2e scan → nog steeds 14/14), 0 onterechte sluitingen. Eén cosmetisch restje:
logboekregel zegt "taak aangemaakt" ook als de spiegel al bestond.

**3. Open-source-onderzoek (verzoek Arsalan, 10 videotools + GitHub-breed).**
Uitkomst: architectuur gevalideerd — géén lijst "werk voor niks". Enige echte
nu-klus: **Anthropic native structured outputs** vervangt de kwetsbare trefwoord-
schema-detectie (`kimi_client._detect_schema`) → **hoofdtaak S238**. Besluiten
Arsalan: (a) **agent-laag komt er t.z.t.** (als Luxis zo goed als klaar is), dan op
pydantic-ai — tot die tijd alles agent-compatibel bouwen (service-laag-eerst, nu
Working Agreement in CLAUDE.md); (b) toekomst-adopties met triggers in
`docs/TOEKOMST-REPOS.md` (CAMT bij 2e bank, Langfuse self-host bij AI×10, Ollama
bij klant-eis, pgvector bij RAG-heroverweging, Docling, mail-parser-reply) mét
attendering-plicht; (c) afgewezen zonder nieuwe feiten: LiteLLM/Outlines/Chonkie/
Crawl4AI/Qdrant/DSPy/Marker.

### Gewijzigde bestanden
Backend: `incasso/service.py` (close_followup_send_tasks → sources-parameter),
`ai_agent/followup_service.py` (escalatie-spiegel + execute-dedupe). Frontend:
`taken/page.tsx` (knop "Beoordelen"). Tests: `test_followup_send_tasks.py`
(+5, 15 totaal). Docs: `docs/TOEKOMST-REPOS.md` (nieuw), `CLAUDE.md`
(agent-compatibel-regel). Commits `ff21d81`, `2a05a6d`; backend+frontend via SSH
`--force-recreate` (geen migratie). Prod-mutatie: 2 mails gekoppeld aan IN100592
via de app-API (natelling 2/2).

### Verificatie
15 wachters groen; kruispunt-run followup/advance/workflow/arrangement 152 groen;
ruff + tsc schoon; CI groen op ff21d81 (conclusion=success via API); containers
healthy, login 200. Werklijst-natelling prod 14/14 met tweede scan (idempotent),
0 onterechte taak-sluitingen. Onderzoek: web-bronnen in sessieverloop.

### Bekende issues / bewust niet gedaan
- **Gat: debiteur-reactie vanaf onbekend mailadres valt stil** (geen melding) —
  kandidaat-verbetering, niet gebouwd (scope).
- Opruimronde wacht op Arsalan+Lisanne: IN100607/IN100613/IN100521 stale adviezen,
  6 oude nakijk-taken van 21-7, dubbel concept+taak IN100592, logboekregeltje
  execute-escalate.
- "Beoordelen"-knop niet visueel doorgeklikt (zelfde patroon als S236-knop; tsc schoon).
- Verweer-concepten IN100592/IN100606 en IN100492-vraag liggen bij Lisanne.

### Volgende sessie
S238: native structured outputs-refactor (alle AI-aanroepen, eigen sessie, Opus +
volle kruispunt-discipline). Zie `docs/sessions/PROMPT-S238.md`.

## Sessie 236 (22 juli 2026, Opus-bouw → Fable-review → Opus-fixes — werklijst-taken + 7 sommaties verstuurd + spook-inkomend-fix, LIVE)

### Samenvatting
Startpunt PROMPT-S236. Besluiten Arsalan vooraf: IN100613 laten liggen (Lisanne nog
niet geantwoord); **Taken-pagina = dé werklijst**; de 7 sommaties mochten na eigen
grondige controle de deur uit ("als jij het hebt nagekeken mag je het doen").

**1. Werklijst-taak voor verstuur-adviezen (LIVE + live bewezen).** Elk openstaand
verstuur-advies van de follow-up-adviseur krijgt een gespiegelde taak
"{stap} versturen — {zaaknummer}" op de Taken-pagina (scanner-backfill dekt ook oude
adviezen; ontdubbeld per advies via rec_id in action_config). De taak sluit op exact
de advies-momenten: brief écht verstuurd → completed op de gedeelde doorschuif-motor
`advance_after_step_send` (dus álle verzendroutes); advies afgewezen/superseded →
skipped (`close_followup_send_tasks` in `supersede_open_recommendations` +
`reject_recommendation`). Taken-pagina kreeg knop "Controleren & versturen" → /followup
(niet visueel doorgeklikt; tsc schoon). Live bewezen: na de 30-min-scan stonden exact
de 4 juiste taken op prod.

**2. De 7 eerste sommaties (IN100592/98/99, 602/03/04/06) — VERSTUURD.** Controle
per dossier vóór verzending: 0 mails/documenten/staphistorie ooit (vers gemeten);
hoofdsom = som losse vorderingen (7/7 exact, incl. creditnota's −1.200,01 en −621,53
netjes in de brieftabel); **BIK onafhankelijk nagerekend volgens de wettelijke
staffel: 7/7 op de cent**; rente-steekproef IN100604 met de hand (2%/mnd samengesteld):
257,40 vs 257,38 in de brief (deelmaand-conventie); alle 7 b2b → geen
14-dagenbrief-plicht; afzender incasso@ via Graph. Alle 7 sent (0 bounces), elk
dossier → Tweede sommatie, adviezen executed. **IN100603 draagt een negatieve
renteregel (−107,90; creditnota ouder dan facturen — S181-F-gedrag, voordeel
debiteur).** **IN100606 (Maatwerk Zorgbemiddeling) betwistte binnen 25 min**: AI
classificeerde betwisting (0.95), dossier auto → 'Verweer beantwoorden', AI-concept
klaar — de hele verweer-keten live bewezen op een échte debiteur. **IN100607 bewust
NIET verstuurd**: bleek op 'Verweer beantwoorden' te staan (stale eerste-sommatie-
advies van vóór de stap-wissel).

**3. Fable-review-vondst: spook-inkomend (gefixt, LIVE).** Elke mail namens
kantooradres incasso@ ('Verzenden als' op seidony's account) kwam via de Verzonden
Items-sync als **inbound** terug: eigen sommaties als ontvangen post, mét notificatie
en AI-beoordelingscall (~$0,03 voor 7), patroon sinds 17-7 (verklaart de S233b-
"doorstuurregel gmail"-randobservatie). Rode test eerst; fix: eigen-afzender-set
(accountadres + Tenant.email) in richting-oordeel, ontdubbel-poort en
contact-matching (`sync_service.py`, 3 wachters).

**4. Tweede reviewvondst op eigen werk (gefixt, LIVE).** Het taak-filter keek alleen
naar "stap heeft sjabloon" → 10 oude escalatie-adviezen (van vóór de S234-
briefkoppeling, testdossiers) kregen een misleidende "versturen"-taak. Nu ook
filteren op advies-type GENERATE_DOCUMENT (+wachter).

**5. Prod-opruiming (één transactie, tellingen exact):** 10 misleidende taken weg;
7 spookmails weg mét bijlage- en classificatierijen, hun echte Graph-ids overgezet
op de uitgaande records (= wat de gefixte poort gedaan zou hebben); 14 onterechte
"nieuwe e-mail"-meldingen weg. Echte reacties + meldingen onaangeraakt (nageteld).

### Gewijzigde bestanden
Backend: `ai_agent/followup_service.py` (taak-aanmaak + reject-koppeling),
`incasso/service.py` (`close_followup_send_tasks` + motor + supersede),
`email/sync_service.py` (eigen-afzender-set). Frontend: `taken/page.tsx` (knop).
Tests: `test_followup_send_tasks.py` (nieuw, 10), `test_email_sync.py` (+3).
Commits `e91037d`, `e18c2d2`, `1782310`; backend+frontend via SSH `--force-recreate`
(geen migratie).

### Verificatie
9+1 nieuwe werklijst-wachters groen; 201 kruispunt-tests (followup/advance/workflow/
arrangement) groen; mail-kruispunt 952 groen (15 errors = botsing met parallelle
eigen run, schoon herdraaid: 98/98); ruff + tsc schoon; CI groen op alle 3 commits
(29910413122 + 29911747328 conclusion=success via API nagetrokken; de Frontend
Dependency Audit-job faalt daarbinnen niet-blokkerend op 4 sharp/libvips-CVE's —
extern, zie Bekende issues); containers healthy, login-API 200 na beide deploys;
alle prod-mutaties met dry-run + natelling (10/7/7/7/7/14 exact).

### Bekende issues / bewust niet gedaan
- **Escalatie-adviezen (o.a. 5 échte 'Voorstel dagvaarding'-dossiers) staan NIET op
  de Taken-pagina** — buiten de gekozen scope (verstuur-adviezen). Voorstel voor
  Arsalan: ook die als taak spiegelen.
- **IN100607**: stale pending eerste-sommatie-advies terwijl de zaak op 'Verweer
  beantwoorden' staat — advies zou superseded moeten worden (data-fix, niet gedaan).
- Werklijst-taak is éénrichting: handmatig afvinken laat het advies op de
  Follow-up-pagina staan (bewuste keuze); taak-aanmaak schrijft geen
  dossier-activiteit (cosmetisch).
- Batch-generatie zónder verzending laat de verstuur-taak bewust open (er ging niets
  de deur uit) maar schuift de zaak wél door (bestaand S234-randgeval).
- IN100613 onaangeraakt (wacht op Lisanne); heeft ook nog een oud pending advies.
- **npm-audit-waarschuwing (niet-blokkerend):** `sharp` erft 4 libvips-CVE's
  (CVE-2026-33327/-33328/-35590/-35591, 3× high) — sharp updaten zodra er een
  gepatchte versie is.

### Volgende sessie
S237: reacties op de 7 sommaties verwerken (IN100606-verweer ligt bij Lisanne;
meer reacties verwacht) + de open beslispunten hierboven. Zie
`docs/sessions/PROMPT-S237.md`.

## Sessie 235 (22 juli 2026, Fable-review ontwerp+S234 → Opus-bouw → Fable-review + volledige live-test — betalingsregeling compleet, LIVE)

### Samenvatting
Startpunt PROMPT-S235. Vooraf twee Fable-reviews: (1) het S235-ontwerp tegen de bron
gehouden → 3 correcties (Gat B-meting te rooskleurig: regeling-mail deed automatisch
NIETS; Gat C zou letterlijk gebouwd altijd geweigerd worden door de hold-stap-blokkade in
`advance_guard_reason`; wanprestatie heeft twee routes + 2 NOT NULL-velden vergen een
keuze); (2) S234 nagereviewd → scanner-skip-motivatie klopte niet (zie gecorrigeerde
entry S234), beslispunt werklijst, budgetfix. Daarna Opus-bouw in 5 blokken, daarna
**alles end-to-end live getest op prod-testdossiers** (wens Arsalan: "volledig testen,
niet een deel") en per test exact teruggedraaid.

**Blok 1 — melding bij auto-afsluiten (besluit Arsalan 22-7, LIVE + live bewezen).**
Nieuw meldingstype `case_closed_invoice`: sluit een dossier automatisch na volledige
betaling, dan krijgen alle actieve gebruikers "Dossier {nr} volledig betaald en
afgesloten — wil je de cliënt factureren?" met doorklik naar de facturen-tab
(`notifications/service.py::create_case_closed_invoice_notification`, aangeroepen in
`workflow/hooks.py::on_payment_received`; frontend-type + tab-route). Live bewezen op
2026-00019: echte betaling €358,69 → zaak betaald + rente bevroren + concept discarded +
advies superseded + melding bij béíde gebruikers; doorklik landde op de facturen-tab.
Terugdraai-bijvangst: betaling verwijderen heropent de zaak automatisch (bestaand
vangnet `_reopen_case_if_no_longer_paid` — bevestigd werkend).

**Blok 2 — Gat A flexibel termijnschema (LIVE + live bewezen).** `ArrangementCreate`
accepteert `installments[{due_date,amount}]`; som moet exact het totaalbedrag zijn
(Decimal; 400 bij mismatch, wachter-getest), termijnen letterlijk overgenomen (gesorteerd
op datum), `installment_amount` = eerste termijn (NOT NULL, ontwerpkeuze), start/eind =
eerste/laatste termijn. UI (`BetalingsregelingSection`): schakelaar "Handmatig schema" →
rijen-editor (datum+bedrag) + lopende telling in centen; Aanmaken disabled tot de som
klopt; kaart toont "Flexibel schema" i.p.v. frequentie bij ongelijke bedragen. Live
bewezen op 2026-00007 (2×200+1000, expres ongesorteerd aangeleverd → exact goed).

**Blok 3 — Gat C pijplijnkoppeling (LIVE + live bewezen).** Nieuwe regeling →
`_move_case_to_regeling_step`: zaak naar hold-stap 'Bijhouden regeling' via
`move_case_to_step` (trigger_type "arrangement"); bewust NIET via `advance_guard_reason`
(blokkeert hold-doelen), wél gesloten/verweer-checks; stap ontbreekt → log + niets.
Wanprestatie → `_ensure_arrangement_defaulted_task` op het gedeelde punt van BEIDE
routes (`default_arrangement` + `update_arrangement`), gededuped; annuleren/afronden
geen taak. Live: 2026-00007 verhuisde Derde sommatie → Bijhouden regeling; wanprestatie
gaf direct de taak "Regeling verbroken — vervolg bepalen".

**Blok 4 — Gat B regeling-mail → taak (LIVE + live bewezen mét echte AI).** Nieuwe
orchestrator-handler `handle_email_classified_arrangement` op het classified-event:
categorie `betalingsregeling_verzoek` → `ensure_arrangement_request_task` ("Betalingsregeling
vastleggen — {zaak}", due vandaag) op het moment van herkennen — niet in de dode
goedkeur-wachtrij. Geen taak bij actieve regeling/gesloten zaak/open taak. Kruispunt: de
escalate-tak van `execute_classification` slaat zijn escalatie-taak over zolang de
gerichte taak open staat. Live: testmail "ik wil een betalingsregeling in drie termijnen"
op 2026-00006 → echte AI classificeerde `betalingsregeling_verzoek` (0.95) → taak stond
er direct; 0 nieuwe AI-concepten (verweer-route bleef terecht stil).

**Blok 5 — budgetfix (Fable-reviewpunt S234).** Sjabloon-skips in de dagelijkse AI-batch
worden nu vóór de budget-slice weggefilterd — een skip kost geen AI-oproep en verdringt
geen echte sjabloonloze gevallen meer (`workflow/scheduler.py`).

### Gewijzigde bestanden
Backend: `notifications/service.py`, `workflow/hooks.py`, `workflow/scheduler.py`,
`collections/{service,schemas}.py`, `ai_agent/{orchestrator,service}.py`. Frontend:
`use-notifications.ts`, `use-collections.ts`, `app-header.tsx`,
`BetalingsregelingSection.tsx`. Tests (16 nieuwe wachters):
`test_case_closed_notification.py` (2), `test_arrangement_pipeline.py` (6),
`test_arrangement_request_task.py` (5), `test_payment_arrangements.py` (+3).
Docs: S235-ONTWERP.md (3 correcties), S234-entry gecorrigeerd. Commits `53d52e5`
(ontwerp-review), `5f3dc67` (S234-correctie), `41497aa` (bouw). Backend+frontend
gedeployd via SSH `--force-recreate` (geen migratie — alles additief op bestaande tabellen).

### Verificatie
221 tests groen (brede -k-run installment/regeling/payment/followup/arrangement);
ruff + tsc schoon; CI groen op alle 3 commits (incl. GitHub-Deploy, geen race dit keer);
containers healthy; login+API 200. Live-testronde op prod-testdossiers (2026-00007/-00019/
-00006): alle vier ketens end-to-end bewezen, daarna per keten in één transactie
teruggedraaid en nageteld (staphistorie hersteld, betaling weg, zaak heropend,
meldingen/taken/testmail gewist). Enig blijvend spoor: 1 rij in `ai_usage` (de echte
classificatie-call, ~¢) — dat is juist het doel van die tabel.

### Bekende issues / bewust niet gedaan
- **4 cosmetische restjes** (Fable-review, geen fix nodig): (a) geannuleerd formulier
  onthoudt de handmatige rijen bij heropenen; (b) etiket "Flexibel schema" verschijnt
  alleen bij ongelijke bedragen; (c) som-mismatch-melding toont bedragen met punt
  (1400.00) i.p.v. NL-notatie; (d) status "nieuw" wordt "in_behandeling" bij regeling
  (gevolg van de stap-zet — correct maar goed om te weten).
- **IN100613** blijft wachten op Lisanne (niet aangeraakt).
- **Beslispunt werklijst** (taken- vs follow-up-pagina) ligt bij Arsalan/Lisanne.
- De 7 'Eerste sommatie'-import-dossiers hebben hun sommatie nog nooit gehad — de 7
  pending follow-up-adviezen zijn terecht en wachten op verwerking (GO per verzending).

### Volgende sessie
S236: verwerk het antwoord van Lisanne over IN100613 (dry-run + GO + natelling) en het
werklijst-beslispunt; daarna losse punten of nieuw hoofdonderwerp naar keuze Arsalan.
Zie `docs/sessions/PROMPT-S236.md`.
