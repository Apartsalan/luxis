# Premortem — Autonome AI Incasso-agent (Luxis)

*10 juni 2026 · methode: Gary Klein premortem (prospective hindsight) · 7 faalmodi, 7 parallelle onderzoekers.*

## Context

- **Wat:** Autonome AI Incasso-agent in Luxis met gelaagde autonomie — L0 uit / L1 suggereren / L2 auto-routine + escaleren / L3 ruim autonoom. Per-tenant instelbaar + globale kill switch. Harde grenzen: pipeline-op-schema autonoom; inbound debiteur-mail-reactie altijd mens; geld/derdengelden nooit autonoom (vier-ogen, Voda 6.22); alle autonome acties gelogd + omkeerbaar + op dashboard.
- **Voor wie:** Lisanne Kesting, solo-advocaat (incasso/insolventie, Amsterdam), tuchtrechtelijk + civiel aansprakelijk. Luxis = óók product voor andere advocatenkantoren.
- **Succes:** agent draait routine autonoom, Lisanne reviewt alleen uitzonderingen, bespaart echte tijd, geen aansprakelijkheidsincident, per-tenant veilig verkoopbaar.
- **Bouwstenen die al bestaan (assistent):** e-mailclassificatie, concept-antwoorden (nooit auto-versturen), intake-AI, follow-up-advies, betalingsmatching, tool-framework + orchestrator. De autonome lifecycle-agent moet nog gebouwd worden.

## Frame

> Het is 6 maanden later. De autonome AI Incasso-agent is gebouwd en gelanceerd. Het is mislukt. We kijken terug en leggen uit waaróm.

## Rauwe faalredenen

1. Autonome actie op foute grond (rente/bedrag/al-betaald/misclassificatie) → tuchtklacht/aansprakelijkheid.
2. Lisanne blijft op L1 hangen → geen ROI, dure ongebruikte feature.
3. Scheidslijn "pipeline=auto / inbound=mens" houdt niet (verborgen offline-context).
4. Toggle-complexiteit → niemand weet wat aanstaat → onverwachte actie.
5. Te vroeg geproductiseerd → incident bij vreemd kantoor → Luxis-reputatie.
6. Bouwkosten ≫ waarde voor 1 advocaat (opportunity cost).
7. "Omkeerbaar" is juridisch een mythe (termijnen/brieven al ingetreden).

---

## Synthese

**Meest waarschijnlijke mislukking — Lisanne schaalt nooit op voorbij L1.** Voor een persoonlijk aansprakelijke solo-advocaat is de afweging asymmetrisch: tijdwinst diffuus, fout staat met háár naam eronder. De volledige ROI zit in L2+, en daar komt ze nooit. Autonomie-machinerie gebouwd, getest, ongebruikt.

**Gevaarlijkste mislukking — autonome actie op foute grond, onomkeerbaar, → tuchtklacht.** Sommatie/14-dagenbrief autonoom verstuurd terwijl debiteur al betaalde of er offline iets speelde. Brief ontvangen, termijn loopt; software-undo zet alleen het record terug. Raakt Lisanne's aansprakelijkheid én Luxis-reputatie.

**De verborgen aanname — Luxis bevat de hele waarheid, en undo = ongedaan.** Het ontwerp neemt aan dat (a) de volledige dossierstand ín Luxis zit op beslismoment (terwijl telefoon/Tikkie/mondelinge afspraken/cliënt-opdracht buiten het systeem leven) en (b) software-terugdraaien = werkelijkheid ongedaan maken (terwijl ontvangst door derden + wettelijke termijnen buiten software's bereik liggen). "Op schema" wordt verward met "op juiste grond".

### Herzien plan

1. **Geen autonomie eerst — bouw "shadow mode" (L1.5):** agent berekent alles wat 'ie op L2 zou doen, verstuurt niets, logt het. Wekelijks "zou-fout-zijn"-rapport. Opschalen pas bij ≈0 over weken. Meetinstrument + verkoop-bewijs ineen.
2. **Pre-send legal-check als harde gate:** 14-dagentermijn / BIK-staffel + verzuimdatum / actuele rente / debiteur niet betaald (incl. fuzzy-match). Faalt één → escaleer. Rode→groene tests.
3. **Stop-signalen buiten e-mail vangen:** handmatige betaling, agenda, notitie, telefoon-log, cliënt-instructie in laatste 14 dagen → auto-escalatie. Nooit "geen mail = ga door".
4. **Intern-omkeerbaar vs extern-onomkeerbaar scheiden:** externe acties (verstuurd, termijn gestart) nooit volledig autonoom op L2; undo weigert op `sent_at ≠ null`.
5. **3 presets, geen matrix:** "Uit / Assistent / Auto-routine" + dik "WAT STAAT NU AAN"-paneel begrijpelijk voor niet-techneut.
6. **Productiseer pas na bewijs:** kantoor #2 pas bij maanden incidentvrij + verplichte shadow-start + per-tenant template-/staffel-validatie.
7. **Scope-discipline:** L1 = 80% waarde; bouw klein (shadow + pre-send), niet de hele policy-engine/dashboard/reversibility. Time-box; migratie/security/livegang mogen niet stilvallen.

### Checklist vóór livegang

- [ ] Shadow-mode + wekelijkse "zou-fout-zijn"-rapportage; opschalen bij ≈0 over X weken.
- [ ] Pre-send legal-check blokkeert elke niet-100%-gevalideerde autonome verzending (met tests).
- [ ] Undo weigert op `sent_at ≠ null`; "extern verzonden" = aparte niet-autonome categorie.
- [ ] "Wat staat nu aan"-paneel; test: Lisanne voorspelt 5 scenario's correct.
- [ ] Reconciliatie-metric vóór L2 live: % autonoom binnen 7 dagen teruggedraaid; boven drempel → auto terug naar L1.

---

## Diepteonderzoek per faalmodus

### 1 — Autonome actie op foute grond → tuchtklacht
B2C-dossier: debiteur betaalde dag 12 met tikfout in kenmerk + €0,84 te laag (bankkosten). Matching faalde, geen "betaling-in-behandeling"-status → dag 14 autonome sommatie mét verse WIK + rente over een al voldane hoofdsom. Dreigbrief ná betaling → Deken-klacht. BIK bovendien niet verschuldigd (14-dagenbrief-termijn fout). Keten: matching-miss → geen tussenstatus → autonome juridische stap → onterechte kosten.
- **Aanname:** "op schema = veilig" i.p.v. "kloppen de feiten op verzendmoment".
- **Signalen:** niet-auto-match % > 5–10% · sommaties binnen X dagen ná binnenkomende betaling/inbound-mail.

### 2 — Lisanne blijft op L1 (meest waarschijnlijk)
L1 doet wat er al was; opschalen = risico zónder zichtbaar voordeel. Afgevangen rente-fout in maand 2 bevestigde "goed dat ik kijk", niet "de check werkt". Eén verzonden fout weegt zwaarder dan 100 bespaarde klikken. Slider bleef op L1; L2/L3 ongebruikt.
- **Aanname:** opschalen is vertrouwen-dat-vanzelf-groeit; werkelijk een blijvende aansprakelijkheids-asymmetrie.
- **Signalen:** na 4 weken nog L1 + >95% blind goedgekeurd · shadow-foutmarge daalt niet naar 0.

### 3 — Scheidslijn pipeline/inbound houdt niet
Debiteur belde + Tikkie €500 ("rest deze week"), niet in Luxis → agent stuurde volledige sommatie. B2B: cliënt zei telefonisch "wacht, we onderhandelen" → agent duwde dagvaarding-voorbereiding door. 4 van 11 autonome escalaties hadden een offline stop-reden.
- **Aanname:** "geen inbound mail = geen reden om te stoppen".
- **Signalen:** >10% autonome escalaties binnen 7 dagen teruggedraaid · dossiers met betaling/notitie/agenda maar zónder inbound mail vóór autonome stap.

### 4 — Toggle-complexiteit
4 niveaus × 8 vinkjes × tenant × kill switch. "Pipeline op schema" aangevinkt zonder te beseffen dat het óók 14-dagenbrief + sommatie verstuurde. Sommatie tijdens onderhandeling; "dat stond uit". Config klopte, mentaal model niet. Bij kantoor #2 won niemand wist welke laag. Geen bug, wél vertrouwensbreuk → L0.
- **Aanname:** niet-technische gebruiker kan 4 orthogonale assen mentaal simuleren.
- **Signalen:** test-voorspelling >1 op 5 fout · "ik dacht dat dat uitstond"-tickets vroeg.

### 5 — Te vroeg geproductiseerd
Kantoor #2 koopt op "draait al maanden autonoom" — gold voor Lisanne's templates/data/bijsturing. #2 paste 14-dagenbrief-template + verzuimdatum aan, zette L2 aan → honderden sommaties met BIK op verkeerde staffel zonder geldige 14-dagenbrief → ACM-klacht + screenshots → "die AI van Luxis stuurt verkeerde sommaties". Prospects haken af.
- **Aanname:** "bewezen bij Lisanne" is overdraagbaar (geldt voor háár setup, niet de agent).
- **Signalen:** nieuw kantoor binnen 30 dagen op L2/L3 met lage review-historie · autonome sommaties zonder pre-send template-/staffel-check (moet 0).

### 6 — Bouwkosten ≫ waarde
Omkeerbaarheidspaden → correctielaag op gedeelde financiële code → test bij elke berekening; test-dekking > feature. Audit-log + dashboard = nieuwe tabellen + RLS-scoping + 2e frontend-view bovenop 57 te refactoren bestanden. Migratie/M365/security stil. Maand 5 race-condition → aanmaning op betaald dossier → kill switch → terug naar L1. 6 maanden voor een knop die "uit" stond.
- **Aanname:** "mens keurt goed → agent handelt zelf" is een logische kleine stap; die klik was juist de goedkoopste verzekering.
- **Signalen:** test+omkeerbaarheid : feature-code > 2:1 binnen 2–3 sessies · BaseNet/M365 0 commits over 3+ sessies.

### 7 — "Omkeerbaar" juridisch een mythe
Autonome 14-dagenbrief; cliënt: "al betaald, géén harde brief naar deze relatie". "Terugdraaien" zette record terug, maar brief lag 3 dagen gelezen → relatie kapot. Autonome stuitingsbrief op deels verjaarde vordering erkende lager bedrag → wederpartij citeert in procedure. Twee tegenstrijdige 14-dagenbrieven → BIK betwist. Dashboard groen, buitenwereld niet.
- **Aanname:** "ongedaan maken" = record terugzetten; onomkeerbaar is ontvangst-door-derde + wettelijke termijn.
- **Signalen:** undo toegestaan op `sent_at ≠ null` (moet 0) · eerste telefoon van cliënt/debiteur over autonoom verstuurde brief binnen eerste ~20 verzendingen.

---

## Rode draad

Vier van de zeven faalmodi (1, 3, 5, 7) komen uit dezelfde wortel: **de agent handelt op onvolledige of verouderde kennis en kan de gevolgen niet terugnemen.** De twee adoptie-faalmodi (2, 6) zeggen hetzelfde van de andere kant: omdat dat risico reëel is, durft niemand op te schalen en blijkt de hele bouw verspilling. De rode draad-fix is daarom niet "meer features" maar **shadow-mode + pre-send legal-check + harde scheiding intern/extern** — pas autonomie aanzetten als de agent bewezen op volledige, kloppende grond handelt. Bouw klein, bewijs eerst, productiseer als laatste.
