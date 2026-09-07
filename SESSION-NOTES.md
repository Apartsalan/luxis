# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 4-7 september 2026 (S256 — beoordeling na 5 weken stilte; Lisanne weer binnen, 10 regelingsdossiers heropend, dagelijkse samenvattingsmail live, geldbedragen-optelfout gefixt).
**Laatste feature/fix:** Dagelijkse samenvattingsmail (09:00 NL) met wat op de advocaat wacht, plus de fix dat de frontend geldbedragen niet meer als tekst optelt (dashboard toonde € 0,00 bij € 78.469,57 open) — beide live, CI groen (S256).
**Openstaand:** koersregel: GEEN nieuwbouw. Waarheden: **35 ✅ / 4 ⚠️ / 2 ❓**. Grootste probleem is gebruik, niet techniek: 37 openstaande brieven (incl. 14 testdossiers die uit Lisannes lijsten moeten), privé-post van Arsalan in de maillijst, ~395 dossiers nog dicht die in BaseNet liepen. Voor Lisanne: bevroren rente op IN100515.
**Volgende sessie:** S257 — testdossiers markeren + uit de lijsten filteren, daarna privé-mail. Zie `docs/sessions/PROMPT-S257.md`.

## Sessie 256 (4 + 7 september 2026, Fable-onderzoek → Opus-bouw → Fable-uitvoering — beoordeling na 5 weken stilte + drie GO's uitgevoerd, LIVE)

### Samenvatting

Eerste sessie na vijf weken stilte. Vraag Arsalan: "wat vind je van Luxis, wat kan beter,
wat is kapot, wat missen we". Rapport: `docs/audits/beoordeling-2026-09-04.md`. Daarna GO
op drie punten, alle drie afgerond.

**0. Fable 5.1-herijking (`0900569`).** Onderzoek naar het nieuwe model (last30days + de
officiele prompting-documentatie). Sessie-start zet effort nu **high** op Fable 5.1 (was
altijd max; op max denkt 5.1 langer voor het schrijft en spawnt het ongevraagd subagents),
max blijft voor Opus. `fable-diepte` kreeg de regel "herkennen is niet kennen, eerst
kijken", `fable-tegenspreker` een natelling op aantallen/limieten/citaten. Anthropic's
eigen modelkeuze-advies bevestigt de S210-regel: Opus standaard, Fable voor review en
lange ketens.

**1. De beoordeling (`7b09766`, gecorrigeerd in `351e28b`).** Techniek is gezond
(containers healthy, backup 03:00, 0 fouten in 7 dagen logboek, 10 nachtjobs met
heartbeat). Het probleem is **gebruik**: sinds 1 augustus een werkdag activiteit, 162 van
164 meldingen ongelezen, terwijl Lisanne gewoon doorwerkte in Outlook (IN100330-draad tot
3 september). Drie oorzaken gemeten: (a) zij kon niet inloggen, (b) ongeveer 405 dossiers
staan op "afgesloten" terwijl BaseNet ze als lopend kende, (c) 19 dossiers wachtten 29-46
dagen op een brief die klaarstond maar op een klik wachtte.

**Drie eigen conclusies gecorrigeerd na doormeten** — de reden dat dit rapport twee
versies heeft:
- "Lisanne zit op slot" was fout: het slot van 19-8 verliep binnen het uur. Zij vroeg om
  13:54 een nieuw wachtwoord aan, de mail ging correct de deur uit (link klopte, pagina
  leeft), maar de link is nooit gebruikt. Geen technische fout.
- "Bel herhaalt 4x per taak" is geen fout: bewust een herinnering per taak per maand, per
  gebruiker (S242). De ruis komt van 48 taken die niemand afhandelt.
- **"Termijnen op gesloten dossiers afboeken" was een gevaarlijk voorstel.** Doorgemeten:
  15 dossiers met een ACTIEVE regeling en gemiste termijnen, 24 termijnen, EUR 11.093,54.
  Eerst leek de teller blind voor betalingen (1 van 266 termijnen heeft een payment_id),
  maar het importscript van 6-7 nam **alleen toekomstige termijnen** over (notes-veld:
  "alleen toekomstige termijnen overgenomen"). Elke betaling van voor die datum hoorde bij
  termijnen die Luxis niet kent. **Alle 24 gemiste termijnen zijn dus echt gemist**;
  koppelen met terugwerkende kracht was niet nodig en zou het alarm ten onrechte hebben
  gedempt.

**2. Lisanne weer binnen.** Nieuw wachtwoord gezet via SSH, teller op 0, reset-token
gewist; login geverifieerd (HTTP 200). De hele herstelketen (mail, link, pagina) bleek
technisch in orde.

**3. Geldbedragen-optelfout + wachter (`aeb5d91`).** De API levert Decimals als string, de
TypeScript-types zeggen `number`, dus `sum + inv.total` rijgt tekst aaneen en `parseFloat`
maakt er een verkeerd getal van. Dashboard "Open facturen" toonde **EUR 0,00** terwijl 88
vervallen facturen (**EUR 78.469,57**) openstonden; dossier IN100016 toonde EUR 145,21 voor
drie facturen van samen EUR 1.062,05. Het dashboard-tegeltje leest nu dezelfde bron als het
debiteurenoverzicht op de Facturen-pagina. `test_frontend_money_sum_guard.py` leest de
frontend-broncode; **rood bewezen** tegen de ongefixte code (4 regels aangewezen), en de
sabotage-proef vond een gat in de wachter zelf (de blokvorm met return glipte door de
eerste regex). Beide schermen op prod nagekeken. WAARHEDEN: 34 naar **35 groen**.

**4. Tien regelingsdossiers heropend** (IN100019/026/305/329/430/454/497/505/535/582),
exact volgens `docs/plans/PLAN-heropening-werkvoorraad.md`: status `in_behandeling`, stap
**Bijhouden regeling**, eigenaar Lisanne, `interest_freeze_date` gewist, een transactie met
terugdraai-tabel `_s256_reopen_backup_cases` en een activiteitenlog-regel per dossier. Alle
acceptatiequery's uit het draaiboek OK: 10/10 op de juiste stap, 0 zonder eigenaar, 0 met
sluitdatum, `email_logs` voor is gelijk aan na (66, er is niets gemaild), vangnet
BaseNet-gesloten = 0. Actieve dossiers 52 naar 62. **Er is geen timeout-transitie vanaf
Bijhouden regeling**, dus er loopt niets automatisch. Wat er speelde: IN100026 reageerde
28-7 en 5-9 op een "niet voldaan aan regeling"-sommatie, IN100582 had begin augustus een
schikkingsgesprek via incasso@ — beide levend terwijl Luxis ze "afgesloten" noemde.
Etiketten zakelijk/consument klopten bij alle tien met de contactkaart.

**5. Dagelijkse samenvattingsmail (`ac59c07`).** Keuze Arsalan: mail, niet automatisch
versturen. `app/notifications/daily_summary.py` + job 07:00 UTC (09:00 NL, na alle
ochtendcontroles). Drie blokken: brieven die op akkoord wachten (te laat eerst), dossiers
in "Verweer beantwoorden", gemiste termijnen op lopende regelingen. **Niets te melden is
geen mail.** Systeemmail aan de eigen gebruikers, gemotiveerd op de allowlist van
`test_send_route_drift_guard.py` (nooit naar een debiteur). Vier tests op de mailopbouw
(leeg, alle blokken, afkappen bij 20 met telling, HTML-ontsnapping). Proefdraai naar
seidony@: "37 brieven, 3 verweren, 24 gemiste termijnen".

**6. Beveiligingsachterstand sinds 31 juli (`7fc338d`).** De CI stond rood op beide
afhankelijkheids-audits. Frontend: nanoid (**high**), dompurify, tiptap, postcss —
`npm audit fix` **zonder** `--force` (Next 15.5.22 naar 15.5.25), audit weer 0. Backend:
aiosmtplib 5.1.1 naar 5.1.2 (CVE-2026-55558), cryptography 48.0.1 naar 50.0.1 (4
PYSEC-adviezen); pip-audit op de vergrendelde runtime-set schoon, Fernet-proef groen.
**CI daarna volledig groen (8/8)**, prod draait op deze versie.

### Gewijzigde bestanden
- `backend/app/notifications/daily_summary.py` (nieuw) — samenvattingsmail
- `backend/app/workflow/scheduler.py` — job `daily_summary_mail` (07:00 UTC) + heartbeat
- `backend/tests/test_daily_summary_mail.py`, `test_frontend_money_sum_guard.py` (nieuw)
- `backend/tests/test_send_route_drift_guard.py` — allowlist (systeemmail, met motivering)
- `frontend/src/app/(dashboard)/page.tsx` — tegeltje leest `/api/invoices/receivables`
- `frontend/src/app/(dashboard)/zaken/[id]/components/DocumentenTab.tsx` — Number() op 3 sommen
- `backend/pyproject.toml` + `uv.lock`, `frontend/package-lock.json` — beveiligingsupdates
- `WAARHEDEN.md` (35 groen), `docs/audits/beoordeling-2026-09-04.md` (nieuw)
- `.claude/commands/sessie-start.md` — effort per model
- Prod-database: 10 dossiers heropend + `_s256_reopen_backup_cases`; wachtwoord Lisanne gereset

### Bekende issues
- **IN100515 heeft een bevroren rentedatum (9-6) terwijl het dossier open is.** Bestond al
  voor deze sessie (regeling door Lisanne aangemaakt op 6-8); NIET aangeraakt. Als dat niet
  bewust is, loopt daar geen rente. **Voor Lisanne.**
- **14 testdossiers (2026-00006 t/m 00020) staan tussen de echte** en dus ook in de nieuwe
  ochtendmail (37 brieven = 23 echt + 14 test). Eerste klus S257.
- Arsalans prive-post (Hetzner, Philips Hue) staat in de maillijst omdat seidony@ als
  kantoormailbox meesynct; 63 "ongesorteerd". Keuze Arsalan: ontkoppelen of filteren.
- Lisanne's eigen mailbox (kesting@) is niet gekoppeld — haar directe correspondentie is
  alleen zichtbaar als incasso@ in de cc staat.
- Ongeveer 395 dossiers staan nog op "afgesloten" terwijl BaseNet ze als lopend kende;
  heropening blijft per groep, na GO.
- 48 taken "te laat", 143 mail-classificaties en 26 AI-concepten wachten op beoordeling;
  3 intakes sinds 19-8 onbeoordeeld.
- Geen gerechtelijke werkstroom na "Akkoord dagvaarden" (11 dossiers staan daar stil).
- De weergave van de samenvattingsmail in Outlook zelf is niet gecontroleerd (geen inzage).

### Volgende sessie
S257: testdossiers markeren en uit Lisannes lijsten plus de ochtendmail filteren, daarna de
prive-mail-keuze. Zie `docs/sessions/PROMPT-S257.md`.

## Sessie 255 (31 juli 2026, Opus-bouw ↔ Fable-onderzoek/review — KVK-backfill + etiket-keten + beveiligingsachterstand, LIVE)

### Samenvatting

**1. De 438 KVK-opzoekingen (`2ada81a`).** Script liep álle 726 contacts af; filter toegevoegd
op "is wederpartij op minstens één zaak". Op prod nagemeten vóór de bouw: 726 → **438**
(33 met lopende zaak, 405 alleen afgesloten). Droogloop → echte run: **437 rechtsvormen
gevuld**, 1 leeg (Kroon Vleeswaren B.V., KvK gaf niets terug → besluit B, wél bijlage).
Verdeling: 223 eenmanszaak, 172 BV, 35 VOF, 2 stichting, 2 maatschap, 1 VvE, 1 NV, 1 CV.
**Effect: 175 wederpartijen krijgen de rentebijlage niet meer (20 lopende dossiers)** —
end-to-end geverifieerd door `should_attach_rente_bijlage` op echte prod-dossiers te draaien
(IN100527 BV → False, IN100077 eenmanszaak → True).

**2. Etiket-wachter, beide richtingen (`ec4eae9` + `67f4961`).** `find_debtor_type_mismatch`
+ dagelijkse veegronde 06:50 + samenvattende melding. Richting 1 (b2c-etiket op een
onderneming, te wéínig gevorderd — de Kaandorp-fout van €6.300): 0 treffers. **Richting 2
kwam er pas bij na zelfkritiek:** b2b-etiket op een persoon zonder KvK én zonder rechtsvorm
is de gevaarlijkere kant (kosten boven de dwingende staffel), en de b2c-grendel én de
staffel-veegronde filteren allebei op `debtor_type='b2c'` — die lieten dit dus door.
1 treffer op prod (IN100077, kaart mist het KvK-nummer). 8 tests, 4× bewezen bijtend.
**Import-regel bewust ongewijzigd:** het `rela.person`-record in de BaseNet-export bevat
géén KvK-veld (nagemeten op het echte XML-bestand), dus op importmoment is het niet te weten.

**3. Beveiligingsachterstand (`667f756`).** De frontend-audit stond op `continue-on-error`
én audit'te dev-deps mee → permanent rood, door iedereen genegeerd. Daarin verstopt: **acht
échte Next.js-adviezen** (DoS in Server Actions, SSRF via rewrites, cache-confusion van
response bodies, ongeauth. disclosure van Server Function endpoints). 15.5.20 → **15.5.22**
lost alle acht op. dompurify 3.3.3 → 3.4.12 (lek zit in `CUSTOM_ELEMENT_HANDLING`, dat wij
niet gebruiken — nagekeken in `lib/sanitize.ts`). sharp-override `^0.35.3` (Next trekt ^0.34.3
mee voor `next/image`, dat nergens gebruikt wordt). **NIET via `npm audit fix --force`: dat zet
Next terug naar 14.** CI: runtime-audit (`--omit=dev`) nu BLOKKEREND en groen; bouwgereedschap
in een eigen informatieve stap (brace-expansion blijft daar rood, alleen te dichten door heel
eslint te forceren).

**4. Rechtsvorm zichtbaar (`390cce5` + `ec45a1a` + `2d6b973`).** "B2B/B2C" zegt niets over
waar het juridisch om draait. Eén etiket op dezelfde plek: Consument (roze) / Eenmanszaak,
VOF, CV (roze) / BV, NV, Stichting (blauw) / Zakelijk (grijs = rechtsvorm onbekend, besluit B
dus bewust géén blauw). Kleur komt uit `ContactBrief.beperkt_aansprakelijk`, berekend met
`is_beperkt_aansprakelijk()` — dezelfde constante als de bijlage-beslissing, dus géén tweede
keywordlijst in TypeScript. Visuele controle ving twee dingen: de zijbalk zei nog "B2B" naast
een kop die "BV" zei, en de incassolijst deed hetzelfde.

**5. Taalwachter (`2d6b973`), gebouwd vólgens de nieuwe werkwijze.** Eerst de wachter, rood
bewezen tegen de ONgefixte code (wees exact de 2 regels aan), pas daarna gefixt. De
sabotage-proef vond **twee gaten in de wachter zelf**: (a) `debtor_type.toUpperCase()` zet ook
"B2B" op het scherm zonder die letters te bevatten — patroon toegevoegd én het echte geval
(stap-bereik) gefixt; (b) de eerste regex eiste `>B2B<` en liet `>B2B (bedrijf)<` door, precies
de keuzemenu-tekst — die fix stond dus onbewaakt. Ook: blokcommentaar wordt weggestreept,
anders rekent de wachter zijn eigen uitleg aan als overtreding.

### Gewijzigde bestanden
- `backend/scripts/kvk_backfill_legal_form.py` — wederpartij-filter
- `backend/app/collections/compliance.py` — `find_debtor_type_mismatch` + `is_beperkt_aansprakelijk`
- `backend/app/workflow/scheduler.py` — `daily_debtor_type_check` (06:50 UTC)
- `backend/app/notifications/service.py` — `debtor_type_mismatch`-melding
- `backend/app/cases/schemas.py` + `incasso/{schemas,service}.py` — rechtsvorm + aansprakelijkheid in de API
- `backend/tests/test_debtor_type_mismatch.py`, `test_partij_etiket.py`, `test_debtor_type_display_guard.py` (nieuw)
- `frontend/src/lib/status-constants.ts` — `partijEtiket()` + `DEBTOR_SCOPE_LABELS`
- `frontend/src/app/(dashboard)/zaken/[id]/components/{DossierHeader,DossierSidebar}.tsx`, `incasso/page.tsx`, `zaken/nieuw/page.tsx`, `components/cases/wizard/Step1Zaakgegevens.tsx`
- `frontend/package.json` + lock, `.github/workflows/ci.yml`
- `WAARHEDEN.md` — 32/5/2 → **34 ✅ / 4 ⚠️ / 2 ❓**

### Verificatie
100 tests groen op de kruispunt-run; `uvx ruff` schoon; `tsc --noEmit` schoon; `next build`
compleet. **CI groen op alle 10 commits**, inclusief de nu-blokkerende frontend-audit.
Gedeployd via SSH, containers healthy, prod draait aantoonbaar op `2d6b973` en Next 15.5.22.
Visueel gecontroleerd op prod (eigen account, token in localStorage — géén wachtwoord getypt,
géén inlog als Lisanne): dossierkop + zijbalk op 4 dossiers (BV / Eenmanszaak / onbekend /
consument), incassolijst, stappenscherm, de melding op de bel, en de relatiekaart.

### Bekende issues / lessen
- **Een wachter die niet rood kán worden is geen wachter.** Twee keer vandaag bleek de eerste
  versie niet te bijten (de afzender-les uit S254 herhaalde zich letterlijk). De sabotage-proef
  is geen formaliteit — hij vond in beide gevallen een echt gat.
- **"Bekend rood" is de gevaarlijkste toestand.** De npm-audit stond maanden rood en werd
  daarom niet gelezen; er zaten 8 echte adviezen in. Een niet-blokkerende controle die nooit
  groen is, is dood gewicht — beter scherp instellen (alleen runtime) én laten blokkeren.
- **Twee schermen over hetzelfde gegeven lopen uit elkaar.** Kop zei "BV", zijbalk "B2B",
  lijst ook "B2B" — alleen de visuele controle ving dat; geen enkele test keek ernaar.
  Daarom nu één functie + een broncode-wachter voor de SOORT.
- **Reviewvondst in mijn eigen commentaar:** ik had `npm audit --exclude` als ontsnappingsroute
  gedocumenteerd; die optie bestaat niet. Gecorrigeerd naar `overrides` (`3713a30`).
- Openstaand voor **Lisanne**: KvK-nummer 72908475 op de contactkaart van Kaandorp (IN100077).
  Staat als melding op de bel; bewust niet zelf ingevuld (dossierwerk).
- **VvE** krijgt de rentebijlage (leden zijn voor hun aandeel aansprakelijk). 1 wederpartij,
  0 lopende zaken — verdedigbaar, niet aangepast.
- **Roze = privé aansprakelijk**, dus een eenmanszaak krijgt dezelfde kleur als een consument.
  Bewust; hover-tekst legt het verschil uit. In de praktijk bij Lisanne toetsen.

### Volgende sessie
S256 — Arsalan kiest uit de 4 resterende ⚠️'s (griffierecht/nakosten-actualiteit,
sjabloonmenu per stap, TOKEN_ENCRYPTION_KEY, kennisregels admin-only) of keuze C (ontwerp).
Zie `docs/sessions/PROMPT-S256.md`.

## Sessie 254 (30 juli 2026, Fable-oogst → Opus-bouw — waarhedenlijst compleet + 4 wachters + echte verzendfout, LIVE)

### Samenvatting
Startpunt PROMPT-S254. **Modelfout aan het begin, door Arsalan gecorrigeerd:** de oogst
(lezen/wegen/aanvullen) is denkwerk → Fable; ik was op Opus begonnen. Oogst daarna op Fable,
wachters gebouwd op Opus.

**1. De oogst — `WAARHEDEN.md` van startlijst naar compleet (`6ffdebf`).** Bronnen zelf
gelezen (geen subagents): archief S200-S253, `SESSION-NOTES.md`, het compliance-hart,
`breed-testen`, roadmap. **Elke status tegen de echte testbestanden gecheckt, niet gegokt.**
13 ✅/7 ⚠️/3 ❓ → 28 ✅/9 ⚠️/2 ❓. Vijftien waarheden bleken al lang bewaakt maar stonden
nergens (rentetabel-veroudering, fail-closed betaald-guard, dubbelklik-slot, verwijderde
betalingen tellen nergens mee, sjabloon-sandbox, dossiernummer-hergebruik, migratie-drift).
**Eén ✅ was onterecht en is gecorrigeerd:** "nieuwe mailroutes passeren de verzendregels" —
er zijn per-deur-tests, maar niets betrapte een NIEUWE deur. Twee nieuwe gaten benoemd:
afzender-regel (M1) en actualiteit griffierecht/nakosten-tarieven. Nieuwe ❓: de
verjaringsteller kent geen stuiting (S242-meting), keuze Arsalan/Lisanne.

**2. ECHTE FOUT gevonden bij het bouwen van wachter 1 (`68c9e97`).** De batch-knop
(`batch_execute`, action generate_document) genereerde én **verstuurde** een sommatie op een
betaald/afgesloten dossier — `emails_sent=1`, rood bewezen tegen de oude code via `git stash`.
`execute_recommendation` (follow-up 'Uitvoeren') deed hetzelfde. Alleen de wachtrij van
'Verstuur later' controleerde dit (S246-nacht); de twee knoppen ernaast waren toen vergeten —
exact het zijdeur-patroon van de 14-dagenbrief-gate (S204, S224). Fix: gedeelde poort
`check_case_closed_gate` in `collections/compliance.py`, naast de dagenbrief-gate; de twee
bestaande eigen controles in `scheduled_service` lopen er nu ook doorheen. Handmatig mailen
op een gesloten dossier blijft bewust toegestaan (S237: debiteur vroeg update op een
afgewikkelde zaak).

**3. Vier wachters, elk bewezen bijtend.** Niet alleen groen gemaakt maar per stuk de regel
gesloopt om te zien of de test rood wordt:
- `test_closed_case_never_sends.py` (9) — gedrag per route + de poort zelf.
- M3-drift: **nieuwe verzenddeur zonder 14-dagenbrief-gate valt rood** (allowlist mét
  motivering: gedeeld kanaal, classificatie-antwoord, factuur aan opdrachtgever).
- M1-drift: elke verzendroute vertrekt vanaf incasso@. **Eerste versie beet niet** — die keek
  of de instelling meegegeven werd, niet of hij AAN stond; `=False` glipte erdoor. Aangescherpt
  naar de letterlijke `True` (of eigen `resolve_office_channel`), daarna wél rood bij sabotage.
- `test_notification_labels.py` (2) — meldingsoorten uit de backend (AST, ook de
  ternary-variant in de deadline-job) tegen de bel-config, én of elk icoon/kleur echt bestaat.
  Getoetst met de échte S252-fout teruggezet (`bik_above_staffel` weg, `sparkles` weg): beide rood.

### Gewijzigde bestanden
- `WAARHEDEN.md` — oogst + 4 statussen naar ✅
- `backend/app/collections/compliance.py` — `check_case_closed_gate` (gedeelde poort)
- `backend/app/incasso/service.py` + `ai_agent/followup_service.py` — poort toegepast (de fix)
- `backend/app/email/scheduled_service.py` — 2 eigen controles op dezelfde poort
- `backend/tests/test_closed_case_never_sends.py` + `test_notification_labels.py` (nieuw)
- `backend/tests/test_send_route_drift_guard.py` — M1 + M3 + gesloten-poort erbij
- `docker-compose.dev.yml` — `frontend/src` alleen-lezen in de testcontainer (anders zou de
  meldingen-natelling lokaal stil overgeslagen worden; in CI staat de hele repo naast elkaar)

### Verificatie
375 tests groen op de kruispunt-run (send/compose/followup/incasso/scheduled/notification/
advance/dagenbrief/closed) en **volledige suite 1693 passed / 0 fouten** (lokaal, schone run);
`uvx ruff` schoon; **CI groen** op `68c9e97` (Backend Tests, lint,
typecheck, build, security — alleen de bekende niet-blokkerende sharp-CVE-audit rood).
Gedeployd via SSH: containers healthy, login 200, de poort aantoonbaar in de draaiende
container (`incasso/service.py` 2×, `followup_service.py` 2×, `scheduled_service.py` 4×).

### Bekende issues / lessen
- **Twee eigen misstappen, beide gecorrigeerd:** (a) het eerste "rood bewijs" was een kapotte
  testopzet (`title=` bestaat niet op `Case`, verkeerde argumentvolgorde) — opnieuw en echt
  rood bewezen via `git stash`; (b) ik verklaarde CI "45 min, afwijkend" op een rekenfout —
  het was 24 min, binnen bereik.
- **Testgereedschap in de lokale dev-container was met de hand geïnstalleerd** (niet in het
  bouwrecept) en verdween toen ik de container hercreëerde voor de nieuwe mount. Opnieuw
  geïnstalleerd in `~/.local`; **verdwijnt weer bij de volgende hercreatie** — kandidaat voor
  een dev-stage in de Dockerfile.
- **Les herbevestigd (S246):** een afgebroken achtergrond-testrun blijft ín de container
  doordraaien → twee pytest-runs op dezelfde testDB gaven spookfouten. Altijd `pkill -f pytest`
  vóór een nieuwe run; volledige suite via `docker compose exec -d`.
- Resterende ⚠️ (5): etiket vs rechtsvorm (438 KVK), griffierecht/nakosten-actualiteit,
  sjabloonmenu per stap, TOKEN_ENCRYPTION_KEY, kennisregels admin-only.
- Lokale volledige suite ná de afsluiting alsnog schoon binnengekomen: **1693 passed, 0 fouten**
  (27:57, één run tegelijk) — bevestigt CI en ontkracht de eerdere spookfouten.

### Volgende sessie
S255 — Arsalan bepaalt. Sterkste kandidaat: de 438 KVK-opzoekingen (eerst het
wederpartij-filter in `backend/scripts/kvk_backfill_legal_form.py`) + de etiket-vergelijking;
dat dicht de dikste ⚠️. Zie `docs/sessions/PROMPT-S255.md`.

## Sessie 253 (30 juli 2026, Opus ↔ Fable — KVK live + werkwijze-omslag naar waarhedenlijst)

### Samenvatting
Geen bouwsessie in de klassieke zin: één koppeling live gezet, daarna de manier van
werken zelf aangepakt naar aanleiding van Arsalans vraag "duurt het niet veel te lang,
klopt mijn manier van werken wel?".

**1. KVK-koppeling live (`fb0235b`, CI groen).** De sleutel kwam binnen bij Lisanne
(mail 28-7). Eerst rechtstreeks bij KVK getest met het eigen KvK-nummer (88601536 → 200),
daarna `KVK_API_KEY` doorgegeven aan de backend-container en de sleutel in `.env` op de VPS.
Vanuit de applicatie geverifieerd: Kesting Legal → "Eenmanszaak", Kaandorp (72908475) →
"Eenmanszaak" — precies wat S252 handmatig uit 27 dossiermails afleidde. Login 200.
**Omvang gemeten voor de backfill:** 726 relaties met KvK-nummer en lege rechtsvorm, maar
slechts **438 zijn wederpartij** (33 op open dossiers, 405 op gesloten) — de overige 288
zijn opdrachtgevers e.d. Arsalan corrigeerde de eerste telling terecht; advies werd 438
(±€9) i.p.v. 726, GO gegeven maar bewust uitgesteld. **Script mist nog het
wederpartij-filter** (`backend/scripts/kvk_backfill_legal_form.py` loopt nu álle contacts af).

**2. Onderzoek `/last30days` (nieuwe skill geïnstalleerd) — twee vragen.**
*(a) Zijn grote CLAUDE.md-bestanden nog relevant bij Claude 5?* Anthropic schrapte 24-7
ruim 80% van Claude Code's systeemprompt zonder eval-verlies; advies verschoof naar korte,
altijd-ware instructies + echte valkuilen, gedrags-coaching eruit, situationeel werk naar
skills. *(b) Klopt de bouwwijze (test → fix → test)?* De "vibe cycle" is de bekende valkuil;
92% dagelijkse AI-adoptie tegenover 29% vertrouwen; de aanbevolen uitweg is ontdekkingen
vastleggen als blijvende afspraken + wachters (60-80% minder regressies gemeld).
Ruwe rapporten: `~/Documents/Last30Days/*.md`.

**3. CLAUDE.md naar het nieuwe recept (`e15e7b8`).** 250 → 139 regels. Eruit: generieke
coaching (verifieer alles, geen aannames, elegantie) en afleidbare stack-opsommingen.
Behouden: álle harde regels, de S183-securityregels, quirks, koersregel toegevoegd.
`future-modules.md` (9,5 KB) niet meer elke sessie geladen; dode `@DECISIONS.md` weg.

**4. Drie tekstregels → echte sloten (`4190830`).** `.claude/hooks/bash-guard.py`:
blokkeert `git add -A`/`git add .` (S203-oorzaak) en weigert `git push` als ruff rood staat
— maar alleen als er Python onder `backend/app/` wijzigde (0,2 s als er niets te linten valt).
Notificatiegeluid nu automatisch via hooks bij vragen/plan-modus en beurt-einde.
5 testgevallen: `-A` en `.` blokkeren, expliciete paden en `./pad` gaan door.

**5. Werkwijze-omslag: `WAARHEDEN.md` als definitie van "af" (`d53f809`).** Startlijst met
13 ✅ bewaakt / 7 ⚠️ onbewaakt / 3 ❓ open, met een bewuste zeef (alleen geld, reputatie of
juridische fouten verdienen een wachter). Vier werkafspraken in `WERKWIJZE.md`; harde regel
in CLAUDE.md (fout = waarheid + wachter). "Af" = lijst zonder ⚠️/❓ + twee weken gebruik
zonder nieuwe schending.

**6. Omgeving opgeruimd (`/doctor`, buiten de repo).** 59 ongebruikte marketing-skills +
12 agents naar een uit-map (±7.500 tokens/sessie), Telegram-plugin uit, 6 dode
MCP-verbindingen gewist (reservekopie: `~/.claude.json.doctor-backup`), oude WinGet-installatie
2.1.49 verwijderd, auto-modus als standaard. Nieuw: contextmeter in de statusregel
(`~/.claude/statusline.ps1`, balk + percentage + kleur).

### Gewijzigde bestanden
- `docker-compose.prod.yml` — `KVK_API_KEY` doorgeven aan de backend
- `CLAUDE.md` — 250 → 139 regels, waarheden-regel, hook-blok
- `WAARHEDEN.md` (nieuw), `WERKWIJZE.md` — nieuwe werkmethode
- `.claude/hooks/bash-guard.py` (nieuw), `.claude/settings.json` — hooks
- `docs/sessions/PROMPT-S254.md` (nieuw)
- Buiten de repo: `~/.claude/settings.json`, `~/.claude/statusline.ps1`, skills/agents-uit

### Bekende issues
- **438 KVK-opzoekingen nog niet gedraaid** (GO er wél); backfill-script mist het
  wederpartij-filter — eerst inbouwen, anders draait hij 726 keer (±€6 te veel).
- Mobiele controle sjabloonmenu (390×844) nog steeds niet gelukt/gedaan (3e sessie op rij).
- ⚠️-punten uit `WAARHEDEN.md` (gesloten dossier verstuurt niets, meldingstypen-natelling,
  TOKEN_ENCRYPTION_KEY, kennisregels admin-only) staan open.
- Hooks + statusregel werken pas vanaf een NIEUWE sessie.

### Volgende sessie
S254 — de oogst: `WAARHEDEN.md` compleet maken uit archief/compliance/huisregels, per
kandidaat de zeef, 3-5 gevaarlijkste ⚠️'s dichtzetten met een wachter per soort. Wachtrij
(438 KVK + etiket-vergelijking, mobiel-check, keuze C/D) staat in `docs/sessions/PROMPT-S254.md`.

## Sessie 252 (30 juli 2026, Opus-bouw ↔ Fable-plan/review — bel-labels + sjabloonmenu + IN100077, LIVE)

### Samenvatting
Startpunt PROMPT-S252. Drie sporen: twee kleine restjes uit S251, een dossiercorrectie
die groter bleek dan gedacht, en taak A (sjabloonmenu) volledig gepland op Fable en
gebouwd op Opus.

**1. Bel-labels (`70cf7c7` + `fe5d88c`, beide CI-groen).** De backend kent 12
meldingstypen, de bel maar 10: `scheduled_email_failed` en `bik_above_staffel` vielen
terug op grijs "Systeem" met info-icoon — juist de twee die moeten opvallen. Beide
toegevoegd (rood mail-x / amber alert-triangle). **Tijdens de live-controle een tweede
gat van dezelfde soort gevonden:** `ai_draft_ready` toonde óók het grijze vangnet,
omdat `ICON_MAP` de sleutel `sparkles` en `COLOR_MAP` de kleur `violet` niet kenden.
Ook gefixt (+ `tag`). Alle 21 config-typen daarna machinaal nageteld tegen beide
kaarten: nul gaten. Live geverifieerd met twee tijdelijke echte meldingen (daarna
verwijderd, teller terug op 56).

**2. IN100077 (Kaandorp) — het etiket was fout, niet de rente.** Vraag uit S251 ("wettelijke
i.p.v. contractuele rente, bewust?"). Arsalan: eenmanszaak, moet contractueel. Doorgevoerd,
en toen **de tegenspraak gevonden**: het 13-juli-besluit (`revert_b2c_rente.py`, akkoord
Arsalan) zette 79 consumentenzaken juist wég van 2%/mnd — ambtshalve toetsing Richtlijn
93/13 vernietigt ≥1%/mnd bij consumenten, en dan vervalt zelfs de wettelijke rente.
Direct teruggezet naar de veilige stand en voorgelegd. **Daarna de 27 dossiermails gelezen:**
Kaandorp is zakelijk klant van Incassocenter (incasso-abonnement € 1.815/jaar voor zijn
eenmanszaak), Incassocenter labelt het dossier zelf "(B)", het kantoor schreef in jan-2026
"gebruikelijk in een B2B aangelegenheid", en de eerste sommatie rekende al 15%. Plus KvK
72908475 in de dossieromschrijving. Oorzaak van het foute etiket: de import zette
debtor_type op b2c zodra de wederpartij een PERSOON was (`scripts/basenet/mapping.py:278`)
— een eenmanszaak is precies het blinde gat van die regel. Na GO Arsalan: b2b +
contractueel 2%/mnd samengesteld + 15% met bodem 40. Rente € 1.277,88 → € 6.732,00,
kosten € 900,19 → € 1.877,86 (beide onafhankelijk nageteld). Volledige terugdraai-set
in `_s252_interest_backup_cases` mét toelichting.
**Omvang gemeten:** slechts 3 actieve b2c-dossiers (1 = testdossier, 1 = IN100077, 1 =
IN100345 Saltik met lopende regeling → bewust niet aangeraakt), 78 gesloten. Wél signaal
voor later: bij 105 gesloten dossiers zegt de BaseNet-fasenaam "B2C" terwijl ons etiket
"zakelijk" is → etiket-controle hoort in de fase-heropening van de 406.

**3. Taak A — sjabloonmenu gelijkgetrokken (`c7eaf10`, CI groen).** S251-vondst op
IN100602: de brief "Tweede sommatie (standaard herhaling)" is intern `wederom_sommatie_kort`
= het anker van de DERDE sommatie (S234-families + `incasso_pipeline_steps.template_type`,
allebei op prod nagemeten). De machine had gelijk, het menu loog. Menu nu 0-5 conform de
stappen: 14-dagenbrief eigen groep bovenaan, groep 3 "Derde sommatie" nieuw, groepen 4/5
hernoemd naar hun stapnaam. **`wederom_sommatie_inhoudelijk` (BaseNet L11) weer
bereikbaar** — renderer bestond, stond in geen enkel menu (GO Arsalan: bij BaseNet had
Lisanne hem wel). Alle 3 de plekken waar dit brieftype een naam krijgt gelijkgetrokken.
Verouderde GRENS-toelichting bij `STEP_TEMPLATE_FAMILIES` bijgewerkt (noemde stappen
zonder anker die er inmiddels wel een hebben).

**Fable-review op alles (geen reparaties).** Machinaal bewezen dat de backend-hunk
uitsluitend commentaar raakt (nul logicaregels), alle 23 menukeuzes een label én renderer
hebben, en geen test/scherm meer naar de oude labels verwijst. Doorwerking nagelopen:
de Word-documentenknop toont alleen de 8 échte DOCX-sjablonen die de backend aanlevert →
naamlijst-uitbreiding kan daar niets toevoegen; Incasso-filter + documentenlijst tonen
dezelfde brief onder de nieuwe naam (1 bestaand document, bestand onaangeraakt).

### Gewijzigde bestanden
- `frontend/src/hooks/use-notifications.ts` — 2 meldingstypen + labels
- `frontend/src/components/layout/app-header.tsx` — ICON_MAP (sparkles, tag) + COLOR_MAP (violet)
- `frontend/src/components/email-compose-dialog.tsx` — TEMPLATE_LABELS + TEMPLATE_GROUPS 0-5
- `frontend/src/hooks/use-documents.ts` + `use-managed-templates.ts` — brieflabels gelijkgetrokken
- `backend/app/incasso/service.py` — alleen toelichting bij STEP_TEMPLATE_FAMILIES
- Data (prod): IN100077 b2b + contractueel 2% + 15%/bodem 40; back-up `_s252_interest_backup_cases`
- Memory: `feedback_stabiliseren_boven_bouwen.md` — koersregel geen nieuwbouw (30-7)

### Bekende issues / bewust niet gedaan
- **Mobiele controle (390×844) van het sjabloonmenu niet gelukt** — het testbrowservenster
  weigerde te verkleinen (viewport 0x0, extensie viel om). Laag risico (standaard
  keuzelijst, geen layoutwijziging), maar formeel niet afgevinkt → 30 seconden werk S253.
- **Voor Lisanne (inhoudelijk, niet technisch):** hoort 'aanmaning' (het prod-anker van
  stap 2, nu onder "Overig") en de losse 'tweede_sommatie' in groep 2?
- **"Verstuur later" met verse bedragen: GESCHRAPT** (besluit Arsalan — rente van het
  inplanmoment is prima, scheelt nagenoeg niets en je ziet wat je verstuurt).
- **Logregel bij rente-/typewijziging: bewust NIET gebouwd.** De app logt alleen
  statuswissels, dus zo'n wijziging laat geen spoor in het dossier. Advies: pas bouwen bij
  een tweede kantoor of derde gebruiker; met 2 mensen dekt de huidige werkwijze het af.
- **Fase-heropening 406 (optie B): niet gestart** op verzoek Arsalan.
- Kaandorp betwist alles fel (groepsrechtszaak tegen Incassocenter, FTM/BOOS) en ziet een
  dagvaarding "met vertrouwen tegemoet" — context voor Lisanne vóór het dagvaarden.

### Volgende sessie
S253 — zie `docs/sessions/PROMPT-S253.md`.

## Sessie 251 (29 juli 2026, Fable-onderzoek → Opus-bouw → Fable-review×2 — geld-audit + 4 fixes, LIVE)

### Samenvatting
Startpunt PROMPT-S251, maar de sessie werd volledig overgenomen door een melding van
Arsalan: IN100602 toonde in Financieel € 2.840,12 incassokosten, de verstuurde sommatie
€ 964,34. Op zijn verzoek een **volledige geld-audit** (alles, tot de cent) vóór er
gebouwd werd — rapport: `docs/audits/geld-audit-2026-07-29.md`.

**Audit-kernvondsten (alles op prod gemeten):**
1. **Briefmachine deed zijn eigen som** — alle briefroutes bouwden een eigen
   financiële aanroep zónder de zaakinstellingen: kosten-afspraak genegeerd
   (altijd kale staffel) én rente altijd t/m vandaag (stopdatum genegeerd).
   Zat er vanaf de eerste versie in. 6 verstuurde brieven fout: € 10.304,71 te
   weinig gevorderd bij 4 debiteuren (grootste IN100598 € 5.470), € 232,75 te
   veel bij IN100605. Rente-bewijs IN100612: tabblad € 58,41 vs brief € 202,79.
2. **Twee 15%-afspraken liepen door elkaar**: provisie-15% (stond goed op alle 6
   kaarten) vs incassokosten-15% richting debiteur (stond als standaard op 1 van
   6 kaarten; Incassocenter zelfs 14,97 = typefout). Besluit Arsalan: **alles 15%.**
3. Gezond: hoofdsommen 627 dossiers 0 afwijkingen; staffel op de cent; 0 B2C boven
   staffel; Financieel-tab/betalingen/dashboard/facturen/AI-concepten rekenden al goed.

**Gebouwd + LIVE (4 commits, alle CI groen):**
- `f31bc39` briefmachine op de gedeelde rekenroute (`case_calc_kwargs`) — kosten-
  afspraak + rente-stopdatum in ALLE brieven; waakhond ziet nu ook percentages.
  Natelling: **43/43 actieve dossiers brief == Financieel-tabblad.**
- Instellingen: 6 klantkaarten op 15% + bodem € 40; IN100602 + IN100605 op 15%
  (back-up: `_s251_bik_backup_contacts`/`_cases`).
- `360a8e3` (Fable-review 1): **b2c-grendel** — de klant-afspraak lekte naar
  consumentendossiers (erving zonder debiteurtype-check; percentage kwam langs de
  AUDIT-23-blokkade). Bewezen op het echte pad vóór de fix; nu één gedeelde grendel
  (vast+percentage+bodem, ook bij wissel naar b2c), nieuw-scherm belooft het niet
  meer bij particulier. Live geweigerd op prod met nette melding (IN100540-toets).
- `b0ca0dd` (Fable-review 2): **intake-erving** — het intake-pad (de normale route!)
  erfde de kosten-afspraak helemaal niet; dáárom miste IN100602 zijn 15%. Nu via
  dezelfde resolver (b2b wél, b2c niet). Bodem-wijziging triggert nu ook de grendel.
- 22 nieuwe wachters totaal, elk eerst rood bewezen via git stash; 886 tests groen.

**Onafhankelijke eind-natelling (Fable):** alle 45 actieve dossiers op 5 punten tot
de cent geverifieerd met een eigen som naast de app — 0 afwijkingen.

**Verder in de sessie:** uitleg verweer-stap (IN100606/IN100607 blijven bewust op
"Verweer beantwoorden" staan — handmatige vervolgkeuze); sjabloon-naamgeving-vondst
("Tweede sommatie (standaard herhaling)" is intern de dérde-sommatie-brief → stap
schoof niet door op IN100602, voorstel blijft liggen); geplande mail IN100606 door
Arsalan geannuleerd (geverifieerd); IN100612-verschil = bekende status-kwestie
(heropeningsplan 406, 153 met rentemeter op openingsdatum).

**Incident (hersteld):** bij het live toetsen van de grendel koos ik eerst een
dossier (testdossier 2026-00009, € 80) waar 15% onder de bodem bleef — de "poging"
werd terecht toegestaan en schreef dus echt; direct teruggezet naar leeg en
geverifieerd. Les: een weiger-toets doe je op een dossier waar de grens écht
overschreden wordt.

### Gewijzigde bestanden
- `backend/app/collections/service.py` — `case_calc_kwargs` (gedeelde bron brief+betaling)
- `backend/app/documents/docx_service.py` + `documents/service.py` — brief-context via gedeelde route
- `backend/app/collections/compliance.py` — waakhond ziet percentage + bodem
- `backend/app/cases/service.py` — `resolve_client_bik_defaults` (b2c erft niets) + `assert_bik_within_staffel`
- `backend/app/ai_agent/intake_service.py` — intake erft kosten-afspraak
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — geen valse belofte bij particulier
- tests: `test_brief_bedragen_gelijk_aan_scherm.py`, `test_b2c_kosten_grendel.py`, uitbreidingen sweep+intake
- `docs/audits/geld-audit-2026-07-29.md` — volledig auditrapport

### Bekende issues / bewust niet gedaan
- **"Verstuur later" bevriest bedragen op het inplanmoment** — dagen later klopt de
  rente in de mail net niet meer. Voorstel, wacht op GO.
- **IN100077** (Incassocenter, actief): wettelijke i.p.v. 2%/mnd contractuele rente — vraag Lisanne.
- **Bel-labels-taak uit PROMPT-S251 niet gedaan** (sessie ging op aan de audit).
- Sjabloonmenu-naamgeving vs stap-koppeling (voorstel S251, niet gebouwd).
- Voor Lisanne: 4 dossiers te-weinig-gevorderd herstellen zichzelf bij de volgende
  brief; IN100605 vroeg toevallig het juiste bedrag (afspraak was 0, nu 15%).

### Volgende sessie
S252 — zie `docs/sessions/PROMPT-S252.md`.

## Sessie 250 (27 juli 2026, Opus 5-bouw — mail-conventie gespreksregels + 2 veegpunten, LIVE)

### Samenvatting
Startpunt PROMPT-S250. Bouwlijst 1-3 gebouwd, gedeployd en live nagekeken; punt 4
na meting bewust niet gebouwd.

**1. Gespreksregels correspondentie op conventie-niveau (hoofdtaak).** Het gesprek
toonde één richting-pijl van het LAATSTE bericht: na "sommatie uit → antwoord binnen"
zag je alleen inkomend, alsof er nooit iets uitging. Nu de Gmail/Outlook-conventie in
béide regelvarianten (breed `md:flex` + smalle/mobiele):
- **Deelnemers** i.p.v. pijl (`threadParticipants`) — namen in volgorde van opkomst,
  eigen berichten als "ik" ("ik, Incasso Kesting Legal (2)"); alleen-verstuurd gesprek
  toont "Aan: <ontvanger>". Aantal "(n)" verhuisde mee naar de namen.
- **Voorbeeldregel** — grijze snippet van het laatste bericht achter het onderwerp.
- **Datum** — nagemeten: `formatDateTime(..,"short")` gaf altijd "17-02-2026 14:30".
  Hergebruikt wat er al was: `formatRelativeTime` (dezelfde notatie als de mailwerkbank)
  → "Vrijdag 00:14" / "17 jul" / oudere volledige datum. Geen tweede datumhelper erbij.
- Behouden: vet + blauwe stip ongelezen, paperclip, Review-badge, datum rechts,
  nieuwste bovenaan. In het geopende gesprek staat de per-bericht-pijl er nog (correct,
  daar is het één bericht per regel).

**2. "X dagen te laat" weg bij afgeronde taken.** Afgerond/overgeslagen toont de kale
vervaldatum; open taken houden het relatieve label. Eén regel op de enige aanroep van
`getRelativeDateLabel` (gegrepped: geen andere plek toont dit).

**3. Faalmelding geplande mail kantoorbreed.** Ging naar precies één persoon — wie hem
inplande. Werd die inactief, dan zag niemand het; bestond de gebruiker niet meer, dan
viel de melding zelfs hélemaal weg (het pad "gebruiker weg" meldde niets). Nieuwe
`create_scheduled_email_failed_notification` → `_notify_all_tenant_users` (alle actieve
gebruikers, dedup 60 min op titel+dossier), zelfde keuze als de bak-melding S240. Alle
vijf faalroutes lopen door één functie, dus blokkade, verzendfout, mislukte nazorg,
vastgelopen claim én "gebruiker weg" erven hem in één keer. Wachter-test (kruispunt-
discipline): melding bereikt de collega, NIET de inactieve collega en NIET een ander
kantoor — eerst rood bewezen via `git stash`, daarna groen.

**4. Kostenblokje — NIET gebouwd (besluit Arsalan).** Eerst gemeten op prod: 453 rijen
in `ai_usage`, alleen 20-25 juli, $6,53 totaal waarvan >de helft eigen testverkeer
(`testronde_*`, `s238_natelling_*`). Echt gebruik ≈ $3,50/week ≈ €13/maand. Advies
"nu niet bouwen, opnieuw bekijken bij een echte maand" — overgenomen.

**Deploy-hobbel:** de eerste `docker compose up -d` botste op een restcontainer van een
eerdere mislukte hercreatie (`9ccf0730aafe_luxis-backend`, status Created). Opgeruimd;
backend + frontend draaien op HEAD (`b108ce1`), code in de container geverifieerd.

**Nagekomen — Fable-review (verse ogen, óók visueel op prod, `e135bf0`).** Diff herlezen
+ echt dossier bekeken (IN100458): de conventie doet daar precies wat bedoeld was —
"ik, Office (2)" op de sommatie-plus-antwoord-draad, "Aan: …" op alleen-verstuurd,
relatieve datums. Twee vondsten, beide direct gefixt en live geverifieerd:
- **Geplette Van/Aan-kop (bestond al sinds S244):** in een smal leesvenster met de
  AI-antwoord-knop erbij werd de kop van een geopend bericht één letter per regel.
  Oorzaak: kolom/rij-keuze hing aan de viewport (`sm:`), terwijl de paneelbreedte van
  het geopende gesprek afhangt. Nu flex-wrap + minimumbreedte; knoppen zakken eronder.
- **"(n)" kon mee-afkappen** in de brede regel (zat ín de truncate-span) → erbuiten
  gezet, Gmail houdt het aantal altijd zichtbaar.
Niet gefixt, wel gezien (klein/data): voorbeeldregel kan het onderwerp herhalen als de
brieftekst met het onderwerp begint (Gmail doet hetzelfde); ingeklapte uitgaande
berichtregel in een smal paneel kapt hard af ("Aa…"); reply-aan-onszelf-testdraad toont
"Incasso Kesting Legal, ik" (testdata). CI reviewfix: alles groen behalve de bekende
sharp-audit.

### Gewijzigde bestanden
- `frontend/src/app/(dashboard)/zaken/[id]/components/CorrespondentieTab.tsx` — deelnemers,
  voorbeeldregel, mail-datum (beide varianten)
- `frontend/src/app/(dashboard)/taken/page.tsx` — kale datum bij afgeronde taken
- `backend/app/notifications/service.py` — `create_scheduled_email_failed_notification`
- `backend/app/email/scheduled_service.py` — `_notify_failure` kantoorbreed + melding op
  het pad "gebruiker weg"
- `backend/tests/test_scheduled_emails.py` — wachter kantoorbrede melding (24 tests groen)

### Bekende issues / bewust niet gedaan
- **Voorstel, niet gebouwd (scope-hek):** de bel kent de typen `scheduled_email_failed`
  en `bik_above_staffel` niet (`NOTIFICATION_TYPE_CONFIG` in `hooks/use-notifications.ts`)
  → ze vallen terug op grijs "Systeem" met info-icoon. Twee regels werk, apart te doen.
- Punt 3 is live geverifieerd via tests + code-in-container, niet via een échte mislukte
  verzending op prod (dat zou een testmail vereisen).
- Kostenblokje uitgesteld (zie boven).

**Nagekomen 2 — eerste Impeccable-doorlichting van de live app (GEEN code).** Op verzoek
Arsalan de hele app door de ontwerp-tool gehaald: dashboard, dossierlijst, incassolijst en
een echt dossier, op 1440x900 én 390x844, met de kleuren gemeten op de échte pagina.
**Cijfer 28/40** (eerste meting, snapshot in `.impeccable/critique/`).
- **Kern:** geen AI-slop (geen verlopen/glas/hero), maar géén vormtaal eronder — 877 rauwe
  kleurklassen naast het tokensysteem, 15 families met dubbelingen (emerald+green,
  slate+gray, violet+purple); badge-component bestaat maar wordt in 3 bestanden gebruikt,
  de rest knutselt ze met de hand. Dát is waarom het "simpel" leest.
- **5 gemeten contrastfouten** (norm 4,5): amber-tekst 3,19 · groen 3,77 · wit-op-rood 3,76 ·
  lichtrood-op-roze 2,13 · grijze telling 4,39.
- **Echte bug gemeten:** de zwevende Timer-knop staat altijd in beeld en dekt op het
  dashboard de AI-suggesties-balk af, in de incassolijst een bedrag in de tabel.
- Verder: dashboard = 15 kaarten over 2,8 schermhoogtes met een ragged 5e KPI-kaart
  (raster staat op 4, er zijn er 5) en twee lege staten die 260px kosten; alarmmoeheid
  (3 permanent rode tellers in de zijbalk + rode bedragen/dagen/datums).
- **Onderzoek gedaan** (Radix 12-stappenschaal: alleen tint 11-12 zijn tekstkleuren, amber
  nooit met wit; Linear "attention distribution" + "structure felt not seen"; Carbon/ISA:
  rood alleen voor storing). Onze fout is exact de Radix-regel: tint ~6 als tekst.
- **Plan geschreven, NIET gebouwd:** `docs/plans/ONTWERP-kleur-en-leesbaarheid-S250.md`
  (doorgerekende statuskleuren, badge-component, rood-beleid, timer-fix; stap 0 = eerst een
  oud-naast-nieuw voorbeeldpagina). Arsalan: richting akkoord (kleur + leesbaarheid eerst),
  maar "ik ga hier nu niks mee doen" → ligt klaar, geen actie.

### Volgende sessie
S251 — zie `docs/sessions/PROMPT-S251.md`. Ontwerpspoor ligt klaar maar is niet gestart.

## Sessie 249 (27 juli 2026, Fable — doorlichting kennisregel-keten + uitleg Lisanne, GEEN code)

### Samenvatting
Startpunt PROMPT-S249. Geen bouwsessie: uitleg + doorlichting op verzoek Arsalan.

**1. Uitleg aan Arsalan (gewone taal) — wat moet Lisanne doen voor de kennisregels.**
Scherm eerst in de bron geverifieerd (`knowledge-rules-section.tsx` + `ai-leren-tab.tsx`):
Instellingen → "Slim leren" → blok "Juridische kennisregels" → "Nieuwe regel"; 2 keuzes
(verweer-type + geldt-voor als veiligheidsklep) + 4 velden; concept → groen vinkje keurt goed.

**2. Doorlichting kennisregel-keten (kernvraag Arsalan: "werkt 'Bij welk verweer?' echt,
en hoe matcht dat met de incassostappen?").** Hele keten in code gevolgd + op prod gemeten:
- **Matchsleutel = dezelfde 13-type-woordenschat** (`defense_types.py`) die de mail-
  classificatie gebruikt; géén aparte herken-machine. Regel-dropdown = die lijst minus 'overig'.
- **Koppeling met stappen:** binnenkomend verweer op een hoofdpad-stap → auto-switch naar
  "Verweer beantwoorden" + concept; kennisregels gaan ALLEEN in die verweer-prompt mee,
  via de gedeelde `build_knowledge_rules_text` in alle 3 de draft-paden. Twee harde poorten:
  type-match + `rule_applies` (zakelijk/consument vs `Case.debtor_type`), fail-closed.
- **Prod-meting:** 332 verweer-classificaties; élke verse mail sinds 6 juli krijgt een type
  (94/94 op open dossiers, 0 gemist — de 238 typeloze zijn één oude bulk van 3 juli). Alle
  5 dossiers in "Verweer beantwoorden" hebben een bruikbaar type. Alle 627 dossiers hebben
  debtor_type (546 b2b / 81 b2c, 0 leeg) → veiligheidsklep blokkeert nergens onnodig.
- **Grenzen benoemd (geen bug):** één type per mail (max 3 regels); alleen de NIEUWSTE mail
  telt bij auto/verweer-knop (op IN100458 verschoof de debiteur van av-vernietiging naar NCNP
  → oude regel vuurt niet meer, correct); gesloten dossiers doen niet mee (10 verse mails op
  afgesloten zaken onbeoordeeld, o.a. IN100492/IN100582). **Oordeel: geen los eiland, machine
  klopt; ontbreekt alleen INHOUD (0 regels). Niets bijbouwen tot Lisanne's eerste regels.**

**3. Werkregel vastgelegd (memory `feedback_standaard_conventies_eerst`).** Naar aanleiding
van de gespreksregel die alleen een richting-pijl van het laatste bericht toont: bij lang-
bestaande functionaliteit (mail/lijst/agenda) eerst onderzoeken hoe gevestigde partijen het
oplossen en het COMPLETE beeld in één keer bouwen — niet elke mini-feature apart laten vragen.

**4. Modelnieuws:** Arsalan wees erop dat Opus 5 bestaat (uit 24 juli — ná mijn kennisstop);
webcheck bevestigd. Claude Code al up-to-date (2.1.220); Opus 5 verscheen niet in de picker
(plan-/uitrolkwestie, buiten wat Claude kan zien). Bouwen kan op Opus 4.8 of 5.

### Gewijzigde bestanden
Geen code. Memory: `feedback_standaard_conventies_eerst.md` (nieuw). Docs: deze entry +
roadmap-kop + `docs/sessions/PROMPT-S250.md`.

### Bekende issues / bewust niet gedaan
- Geen bouwwerk — expliciet een onderzoeks-/uitlegsessie.
- Bouwlijst S250 staat in de kop + PROMPT-S250; gespreksregels eerst (conventie-niveau).
- Kennisregels: 0 regels, wacht op Lisanne (inhoud = haar werk, rolverdeling S240).

### Volgende sessie
S250 (Opus) — bouwlijst uit de kop, gespreksregels correspondentie eerst.
Zie `docs/sessions/PROMPT-S250.md`.

## Sessie 248 (24 juli 2026, Fable-ontwerp → Opus-bouw → Fable-review + live end-to-end — juridische kennisregels GEBOUWD + LIVE)

### Samenvatting
Startpunt PROMPT-S248. Model-cyclus netjes gevolgd: ontwerp-verfijning op Fable,
bouw op Opus, verse-ogen-review + live-proef op Fable. Arsalan koos kandidaat 1
(juridische kennisregels, restant S247) en gaf GO om te bouwen.

**Ontwerp verfijnd op Fable (gemeten in bron + prod).** Twee harde keuzes tegen het
S247-voorstel in: (1) trigger = het bestaande 13-type verweer-vocabulaire
(`defense_types.py`), géén eigen trefwoord-machinerie — op prod gevalideerd dat de
IN100458-betwisting exact als `av_toepasselijkheid` is geclassificeerd. (2) De
toepasbaarheids-poort loopt op `Case.debtor_type` (b2b/b2c), NIET op `legal_form` —
dat veld is op het ijkgeval leeg gemeten (KvK-verrijking uit). Doc bijgewerkt naar
GEBOUWD + LIVE (`docs/plans/ONTWERP-juridische-kennisregels-S247.md`).

**Gebouwd (`350f8c7`).** Aparte tabel `legal_knowledge_rules` (TenantBase, RLS in
dezelfde migratie s247). Service `ai_agent/knowledge_rules.py` met de harde poort
`rule_applies` (alle/zakelijk/consument vs debtor_type, fail-closed op onbekend) +
`build_knowledge_rules_text` (één gedeelde functie voor álle 3 de draft-paden:
automation_service verweer-stap, draft_service, unified_draft_service). Endpoints
`/api/ai-agent/learning/rules*` (CRUD + goedkeuren/uitzetten/verwijderen). Dashboard-
sectie `knowledge-rules-section.tsx` in "Slim leren" (aanmaken/bewerken/goedkeuren),
met een oranje waarschuwing zodra 'alleen consument' wordt gekozen. Framing in de
prompt is conditioneel ("pas ALLEEN toe als de debiteur deze stelling voert"), géén
toon-voorbeeld zoals de geleerde antwoorden. **Nul gedragsverandering tot een regel
is goedgekeurd** (lege string bij 0 regels).

**Kruispunt-poort (het scherpste risico, ontwerp §4).** Een zakelijke regel (art.
6:235 BW, "de B.V. kan de AV niet vernietigen") mag NOOIT op een consument — die mág
de AV juist wél vernietigen. De poort zit hard in de gedeelde functie; alle 3 de
routes erven hem. 5 wachters (zakelijk niet op consument, type-match, kandidaat-gate,
consument-scope, validatie).

**Fable-review — 3 vondsten, alle gefixt (`6f8d399`, +3 wachters, rood-eerst):**
1. Een weerlegging langer dan het promptbudget gaf alléén de aankondigingskop zonder
   één regel (prompt-ruis) en bereikte de AI stil nooit → injectie dan leeg + warning.
2. Type 'overig' kon via de API een stil-dode regel opleveren (matcher slaat 'overig'
   bewust over) → validatie weigert met duidelijke melding.
3. Geen wachter op "kennisregels alléén in de verweer-stap-prompt" → toegevoegd.

**Live end-to-end bewezen op prod (GO-scope, wegwerp-testdossier 2026-00006).** Op een
tijdelijk nagebouwd verweer-scenario (zakelijke debiteur "wij vernietigen de AV") met
een goedgekeurde test-kennisregel door álle 3 de draft-routes een échte AI-brief laten
genereren: (A) verweer-knop → concept weerlegt letterlijk met art. 6:235; (C) AI-
antwoord-op-mail → idem; (B) automatische route → kennis zat aantoonbaar in de prompt,
maar de AI gebruikte hem niet omdat de vernietigings-claim in díe route alleen als
korte mailsamenvatting meekomt en die in de testopzet de claim niet bevatte (correct
gedrag: "alleen toepassen als de debiteur het echt voert" — bij een echte mail staat
de claim wél in de samenvatting). 3 AI-calls, samen **$0,09** nageteld. Alles exact
teruggedraaid: testdossier terug op Tweede sommatie, classificatie/mailtekst hersteld,
testregel + testconcepten + testtaak verwijderd, prod weer **0 kennisregels**.

### Gewijzigde bestanden
Backend: `ai_agent/models.py` (LegalKnowledgeRule), migratie
`s247_legal_knowledge_rules.py`, `ai_agent/knowledge_rules.py` (nieuw),
`ai_agent/router.py` (rules-endpoints), `incasso/automation_service.py`,
`ai_agent/draft_service.py`, `ai_agent/unified_draft_service.py`,
`ai_agent/incasso_email_prompts.py` (injectie). Frontend:
`instellingen/knowledge-rules-section.tsx` (nieuw), `instellingen/ai-leren-tab.tsx`
(sectie + labels geëxporteerd). Tests: `test_knowledge_rules.py` (8 wachters).
Commits `350f8c7` (feature) + `6f8d399` (reviewfixes); doc `48b7505`/`350f8c7`.

### Verificatie
8 wachters groen + RLS-drift-guard (nieuwe tabel) + 59 pipeline-tests groen; ruff +
tsc schoon; CI van beide commits volledig groen (alleen de al bestaande, niet-
blokkerende sharp-CVE-dependency-audit rood — stond al rood op de docs-only commit
ervoor). Prod: migratie gedraaid (RLS FORCE + policy geverifieerd), login 200,
endpoint `[]`. Live poortproef op prod (b2b injecteert/6:235, b2c leeg, ander type
leeg). Visueel bekeken (desktop + mobiel 390×844): sectie + formulier + consument-
waarschuwing + create/delete-flow.

### Bekende issues / bewust niet gedaan
- **Wacht op INHOUD Lisanne:** er staat nog géén enkele echte regel. Tot Lisanne
  regels intikt + goedkeurt verandert er niets aan de AI-output. Vragenlijst per
  regel staat in §7 van het ontwerp-doc; ijkpunt = IN100458 (Studio Hartzema B.V.).
- Route B (automatische conceptgeneratie) neemt de debiteur-claim alleen mee via de
  mailsamenvatting — dat is by design, niet live per-pad met een echte AI-brief
  bevestigd behalve via de prompt-inhoud.
- Endpoints niet rol-beperkt (spiegelt learned_answers; 2 vertrouwde gebruikers +
  tenant-isolatie) — kan later naar advocaat/admin.

### Nagekomen — Kimi-security-scan + 7 fixes (Fable, GO Arsalan)
Arsalan: "laat Kimi (mijn API, ~$13 tegoed) een grote security-scan doen — waar kan
hij inbreken — zodat we het kunnen fixen." Kimi kan geen PII zien (S159), maar een
CODE-scan mag: alleen broncode gestuurd, nooit `.env`/secrets/data.

**Aanpak:** onderzoek vooraf → beste model = **Kimi K3** (vlaggenschip, 1M-context) voor
de kroonjuwelen (auth/tenant + geld-routes); **Kimi k2.7-code** (coding-specialist, snel
genoeg om binnen de 600s-voorgrondlimiet te blijven → geen kill) voor de 4 overige
domeinen. 6 domeinen gescand, ~$4,31 (saldo $9,13). Scanner-script + rapporten in de
scratchpad (`kimi_scan.py`, `BEVINDINGEN-SECURITY-S248.md`). **Élke vondst door Claude
tegen de echte code + prod geverifieerd** (Kimi overrapporteert — cross-check verplicht,
memory `feedback_verify_own_research`).

**Kernoordeel:** kroonjuwelen (tenant-isolatie, RLS, auth) houden stand; de meeste
"critical/high" van Kimi waren al afgeschermd door eerder werk (SEC-21/22, AUDIT-H3,
config-hardening). 11 vals-alarm/al-dicht bevestigd (OAuth-CSRF = HMAC+nonce, Next.js-docs
uit in prod, XFF-bypass, path traversal = whitelist, e-mail-XSS = DOMPurify SEC-24,
achtergrond-taken = expliciete tenant_id, cross-case IDOR = kantoor-brede autorisatie, ...).

**7 echte fixes gebouwd + getest + live (4 commits `3b58cac`/`84f4e0d`/`2b27a93`/`34e720c`):**
- **SEC-25 (zwaarst, latent-kritiek):** docxtpl + oud HTML-pad renderden geüploade
  sjablonen zonder Jinja-sandbox → SSTI/RCE. Nu `SandboxedEnvironment`. Tegenproef: oude
  env rendert de `__globals__`-escape wél, sandbox blokkeert; 112 sjabloon-tests groen.
- **SEC-26:** refresh-token-rotatie was SELECT→check→UPDATE (TOCTOU). Nu atomair
  (`UPDATE ... WHERE is_used=false RETURNING`); gelijktijdigheidstest (2 sessies, 1 token).
  Live bewezen: hergebruik oude token → 401 + alles ingetrokken.
- **SEC-27:** `get_current_user` checkte alleen `user.is_active` → geschorst kantoor hield
  toegang. Nu ook `Tenant.is_active`. Prod: 1 kantoor is_active=t (geen lockout).
- **SEC-28:** RLS-rol-grendel in tenant.py was fail-open (`== "production"`) → nu
  default-secure (dev/test-lijst uit config; typefout/lege APP_ENV faalt hard).
- **SEC-29:** `_is_blocked_host` mist 169.254/16 (cloud-metadata) + IPv4-mapped IPv6 → toegevoegd.
- **SEC-30:** max wachtwoordlengte 128. **SEC-31:** rate-limits op change-password + email/test.

**Bewust NIET gedaan (aanbeveling, kost iets — Arsalan beslist):** aparte
TOKEN_ENCRYPTION_KEY (verbreekt Lisanne's mailkoppeling → herverbinden), kennisregel-
endpoints admin-only. Fixes deed Claude zelf (Kimi kan niet fixen; wij sturen geen code naar
Moonshot). Deploy backend via SSH; login/`/me`/refresh/hergebruik live 200/200/ok/401; alle
CI-jobs groen behalve de al bestaande niet-blokkerende sharp-CVE-frontend-audit.

### Volgende sessie
S249 — Arsalan bepaalt de hoofdtaak. **START met de uitleg-opdracht van Arsalan:**
in gewone taal precies vertellen wat Lisanne moet doen om de kennisregels in te
vullen. Zie `docs/sessions/PROMPT-S249.md`.

## Sessie 247 (24 juli 2026, Fable-review → Opus-bouw → Fable-eindreview — nachtdiff-review + placeholder-bug + kennisregels-ontwerp, LIVE)

### Samenvatting
Startpunt PROMPT-S247. Model-cyclus gevolgd: deel A (verse-ogen-review nachtdiff)
op Fable, deel B onderdeel 1 (placeholder-fix) op Opus, daarna Fable-eindreview.

**Deel A — verse tegenlezing van de nachtdiff (`90aa57f`+`8ef2d88`, gebouwd én
getest door dezelfde Fable-instantie). 4 vondsten, alle gefixt (`4ffa184` backend,
`45e2ca1` voorkant):**
1. **Verkeerde brief kon blind vertrekken (zwaarste).** Follow-up "goedkeuren nu,
   uitvoeren later" maakt APPROVED langlevend, maar de stapwissel-opruiming
   (`supersede_open_recommendations`) raakt alleen PENDING. Wisselde de stap tussen
   inplannen en uitvoeren buitenom, dan verstuurde de bezorger de brief van de OUDE
   stap. Rood bewezen; stap-anker in `execute_recommendation` zelf (dekt ook de
   directe "Uitvoeren"-knop). De onjuiste "statusmachine dekt dit"-toelichting op 3
   plekken rechtgezet.
2. **Menu onzichtbaar op prod (visueel gezien).** Batch-venster tilt zich naar
   z-[60]; het "Verstuur later"-menu bleef op z-50 → presets verdwenen erachter.
   → `z-[70]` in het gedeelde component.
3. **Batch-nazorg-fout verdween stil** (mail weg, doorschuiven faalde) → melding
   "de mail IS verstuurd" + echte redenen.
4. **Faalmelding zei "verstuur zelf" ook bij onzekere verzending** (dubbel-risico)
   → wijst eerst naar de map Verzonden; alleen bewuste pre-send-blokkades houden
   hun stellige "niets verstuurd". 3 nieuwe wachters, alle rood-eerst.

**Deel B onderdeel 1 — placeholder-bug IN100606 (Opus, `ba7a388`; echte oorzaak
Fable, `0d5c227`).** De verweer-conceptprompt STAP 4 is een bewust vangnet
(onbekend verweer → invulregel voor Lisanne, geen verzonnen argument). De AI
kopieerde de invul-aanwijzing `<kernverweer letterlijk uit incoming_defense>`
letterlijk. Opus: prompt-instructie verduidelijkt + getrouwheids-poort vangt de
meta-mal (regenereren/markeren). **Fable groef dieper en vond de ECHTE oorzaak:**
de betwisting-mail was HTML-only (body_text én snippet leeg, in de bron gemeten) →
de AI kreeg een LEEG verweer en kón de invulregel niet vullen. Fix op het gedeelde
punt: `_defense_text()` hergebruikt de HTML-strip van de bibliotheek-backfill,
gebruikt door beide routes. **Live bewezen:** verse AI-generatie op het echte
IN100606-verweer (4263 tekens binnen) → inhoudelijke weerlegging, geen mal, poort
schoon; niets opgeslagen (2 AI-calls, $0,33).

**Deel B onderdeel 2 — juridische kennisregels: alleen ONTWORPEN, niet gebouwd.**
Nieuwe feature → vereist goedkeuring + inhoud van Lisanne; ontwerp hoort op Fable.
Voorstel: aparte tabel `legal_knowledge_rules` die de goedkeur-flow van
`learned_answers` hergebruikt (niet de empirische backfill), met een harde
toepasbaarheids-conditie. Scherpste risico: art. 6:235 BW omgekeerd toepassen op
een consument. Doc: `docs/plans/ONTWERP-juridische-kennisregels-S247.md`.
**Bron-correctie:** de "132 kandidaten wachten op Lisanne" is achterhaald — 103
goedgekeurd, 28 afgewezen, 1 kandidaat (memory bijgewerkt).

### Gewijzigde bestanden
Backend: `ai_agent/followup_service.py` (stap-anker), `ai_agent/followup_router.py`,
`email/scheduled_service.py`+`scheduled_models.py` (meldingen), `incasso/automation_service.py`
(`_defense_text` + guard), `ai_agent/incasso_email_prompts.py` (STAP 4).
Frontend: `components/verstuur-later-menu.tsx` (z-[70]). Tests: `test_scheduled_emails.py`
(+3), `test_incasso_pipeline.py` (+4). Docs: `ONTWERP-juridische-kennisregels-S247.md`.
Commits `4ffa184`, `45e2ca1`, `ba7a388`, `c93c629`, `0d5c227`, `5459672`. Alle CI groen;
4× backend + 1× frontend via SSH; login 200.

### Verificatie
23 wachtrij-tests + 59 pipeline-tests + 20 kimi-structured-tests groen; ruff + tsc schoon.
Guard bewezen tegen ECHTE IN100606-body (issue vuurt). Visueel op prod: batch- +
follow-up "Verstuur later"-presets zichtbaar, "Weghalen" op mislukte rij (wegwerp-rij
op 2026-00006, daarna gewist), IN100606-concept bekeken (toont nog de kapotte placeholder).

### Bekende issues / bewust niet gedaan
- **Oud IN100606-concept** toont nog de kapotte placeholder → weggooien + opnieuw
  genereren levert nu een echte weerlegging (Lisanne — inhoudelijk).
- **Kennisregels niet gebouwd** — wacht op akkoord ontwerp + regels van Lisanne.
- Melding mislukte geplande mail nog steeds alleen naar de inplanner (klein, 2 gebruikers).

### Volgende sessie
S248 — Arsalan bepaalt de hoofdtaak. Kennisregels bouwen kan zodra het ontwerp
akkoord is. Zie `docs/sessions/PROMPT-S248.md`.
