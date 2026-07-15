# S219 — Demolijst-onderzoek (15 juli 2026, Fable, read-only)

Onderzoeksrapport bij `DEMOLIJST-S218.md`. Elke claim hieronder is deze sessie zelf
gemeten (prod-DB read-only, code, logs, live API-render); waar iets een hypothese is
staat dat erbij. Bouwdraaiboek: `PROMPT-S220.md`.

---

## HOOFDVONDST (nieuw, buiten de demolijst) — de compose-verstuurknop

De primaire "Versturen"-knop (`POST /api/email/compose/send` — dé route van de eerste
échte sommatie, IN100613/Bayar, 15-07 12:24) heeft twee gaten:

1. **Verstuurt via het persoonlijke account van wie klikt.** `get_email_account()`
   prefereert 'outlook' → Arsalans klik verstuurt als seidony@kestinglegal.nl i.p.v.
   incasso@. De vangrail "altijd via het kantooraccount" (B13) bestaat alleen op het
   batch- en follow-up-pad (`send_as_tenant_account=True`). Bewijs: de Bayar-mail staat
   nérgens in synced_emails en niet in incasso@'s INBOX.Sent (die map wordt elke 5 min
   gelezen, logregels "IMAP: 3/6 berichten uit 'INBOX.Sent'"). Vrijwel zeker — sluitstuk
   is één blik in Arsalans M365 Verzonden-map.
2. **Legt niets vast**: geen EmailLog, geen SyncedEmail, geen CaseActivity (de route
   eindigt direct na `provider.send_message`). Gemeten: IN100613 heeft alleen
   pipeline-activiteiten; email_logs van 15-07 bevat alleen de follow-up-test van 11:12.
   De Outlook-sync leest bovendien alleen de Inbox → de mail komt óók nooit via de
   sync binnen. **De verstuurde sommatie is onvindbaar in Luxis.**

Zelfde vangrail-gat zit op het document-verzendpad (`documents/router.py:512` —
`send_with_attachment` zónder `send_as_tenant_account`; logging is dáár wel op orde).

## Verzendroute × waarborg-matrix (patroon "route-asymmetrie")

| Waarborg | batch | follow-up | compose-send | compose-.eml | documents-send |
|---|---|---|---|---|---|
| 14-dagenbrief-gate | ✓ | ✓ | ✓ | — (Outlook verstuurt) | ✓ |
| Mailslot | ✓ | ✓ | ✓ | — | ✓ |
| Afzender incasso@ | ✓ | ✓ | **✗** | ✗ | **✗** |
| Logging (EmailLog+SyncedEmail+Activity) | ✓ | ✓ | **✗ niets** | alleen "opgesteld" | ✓ |
| Rente-bijlage (S212) | ✓ | ✓ | ✓ | ✓ | ✓ |

S220-principe: afzender-vangrail + logging horen in één gedeelde verzendfunctie,
niet per route herhaald.

---

## Blok 1 — Sjablonen (punten 5-12)

### Inventaris
- 8 DOCX in `templates/` = byte-identiek (md5) aan prod `managed_templates` (9e rij =
  `verzoekschrift_bijlage`, Lisanne's origineel).
- ~21 e-mailsjablonen in code (`incasso_templates.py`), lijst in `email-compose-dialog.tsx`.
- 7 pijplijnstappen met eigen mailtekst in `incasso_pipeline_steps` (DB) — letterlijke
  BaseNet-kopieën (bron `templates/lisanne/*.eml`).
- response_templates (6) en learned_answers (131): schoon.

### Punt 6 — oud adres: bron gevonden
De tenant-instellingen zijn al correct (Willem Fenengastraat 16E, 1096 BN, 020-3086621,
incasso@, IBAN NL79KNAB…). DOCX- en code-e-mailsjablonen renderen daar vers uit —
live geverifieerd (verse render sommatie op IN100613: Willem Fenengastraat 1×,
IJsbaanpad 0×). Het oude adres zit in:
1. **De 6 stap-mailteksten in de DB** (Eerste/Tweede/Derde sommatie, Laatste mogelijkheid,
   Verzoekschrift, Verweer beantwoorden): hardcoded "IJsbaanpad 9 / 1076 CV" in de vaste
   handtekening. De AI-prompt (regel 1: "ondertekening/footer NOOIT wijzigen") kopieert
   dit trouw → **alle 10 ai_drafts dragen het oude adres, ook die van 15-07 12:50**.
   Het écht verstuurde Bayar-concept had oud adres én kesting@-handtekening.
2. **`verzoekschrift_bijlage`** (Lisanne's DOCX-origineel): hardcoded "IJsbaanpad 9".

### Punt 7 — handtekening
Code switcht al goed op zaaktype (incasso → Incasso@). Fout zit in de stap-mailtekst
"Eerste sommatie" (kesting@ hardcoded); 5/10 concepten dragen kesting@.

### Punt 8 — aanhef
Stap-mailteksten ZONDER aanhef: Sommatie laatste mogelijkheid, Verzoekschrift
faillissement, Verweer beantwoorden. De AI voegt er soms zelf één toe →
niet-deterministisch (demo zag hem wegvallen). Alle 21 code-sjablonen hebben wél een
aanhef; stijl wisselt ("heer/mevrouw" vs "heer, mevrouw").

### Punt 9 — BV-naam in aanhef: 3 vindplaatsen
`vaststellingsovereenkomst` (incasso_templates.py:1038), `faillissement_dreigbrief`
(:1109), `verzoekschrift_faillissement.docx` ("Geachte heer, mevrouw {{ wederpartij.naam }},").

### Punt 10 — klant-kenmerk
`zaak.referentie_regel` = "Uw kenmerk: {case.reference}" (= kenmerk van de OPDRACHTGEVER)
staat in alle 5 DOCX-debiteurbrieven én de e-mail-basislayout; de AI-prompt zet het
kenmerk in de Betreft-regel.

### Punt 11 — opmaak/lettertype
- DOCX: runs Calibri, maar document-default = **Courier** (styles.xml) — tekst zonder
  eigen opmaak valt terug op Courier.
- E-mails: Verdana. AI-concepten: platte tekst zonder font.
- "Spaties onder Bedrag": AI-concepten bouwen tabellen met spatie-uitlijning (gemeten in
  de verstuurde Bayar-mail) → scheef in proportioneel lettertype. Fix: écht HTML-tabellen
  (de stap-sjablonen hebben een html-variant; de AI schrijft nu platte tekst).

### Punt 5 — onderwerpregel: 5 formaten naast elkaar
1. follow-up/batch: "{stap} inzake dossier {nr}" · 2. follow-up-DOCX-route: staptemplate
of "{stap} - {nr}" · 3. compose-preview: "{Sjabloonsleutel Titlecased} inzake dossier {nr}"
(lekt "Sommatie Drukte") · 4. stap-mailteksten: "SOMMATIE TOT BETALING / / " (lege
BaseNet-slots) · 5. AI-concepten: "SOMMATIE TOT BETALING / IN100613".
Gewenst formaat (Arsalan): "klant / debiteur — sommatie tot betaling — dossiernummer"
→ één gedeelde onderwerp-bouwer.

### Punt 12 — verzoekschrift-bijlage
De dreigbrief-tekst belooft "kopie verzoekschrift in de bijlage", maar alleen de
compose-dialog met sjabloonkeuze `faillissement_dreigbrief` hangt hem automatisch aan
(email-compose-dialog.tsx:459); de AI-concept-route (geen sjabloonkeuze) niet → zelfde
wortel als punt 1. Juiste PDF staat klaar in de projectmap; huidige render verliest logo's.

### Geld-kritisch beslispunt (Lisanne):
`verzoekschrift_faillissement.docx` bevat hardcoded "IBAN NL20 RABO 0388 5065 20 t.n.v.
Stichting Beheer Derdengelden Kesting Legal" — gelijk aan de huidige
derdengelden-instelling, maar het kantoor-IBAN is inmiddels KNAB. Vraag: klopt de
Rabo-derdengeldenrekening nog? Ook hardcoded: aanvraagkosten EUR 2.195,00 / € 412,61.

---

## Blok 2 — AI-keten (punten 19, 20, 21, 24)

- Klokken: sync 5 min → classificatie 6 min (haiku) → gemeten race (classificatie draaide
  3 sec vóór de sync klaar was → mail wacht een ronde). Echte casus: mail 12:43:35 →
  concept klaar 12:50:54 ≈ **7,5 min automatisch** (worst-case ~12).
- **Auto-concept ná classificatie staat bewust UIT** (orchestrator.py:78, kwaliteitsreden);
  alleen de verweer-route maakt nog automatisch een concept. Overige categorieën =
  handmatig klikken → de "traag + zelf klikken"-beleving.
- **470 classificaties op pending** (bulk-backfill 11-07 over importmails) + 348 ongelezen
  notificaties → wachtrijen zijn onbruikbaar.
- Punt 20 gemeten: handmatige generatie = **39 s** (12:21:40→12:22:19; prompt 40.947
  tekens, in=16.891/out=1.575 tokens, $0,074, sonnet-4-6), zonder voortgang in de UI.
  IN100521 kreeg 2 identieke concepten 5 min uit elkaar (dubbelklik).
- Punt 21: vraag "Wie zijn jullie en wie is jullie klant!" → classificatie
  betwisting/betwisting_ongemotiveerd (0.95) → standaard-weerlegging; klantnaam
  (LegalWork B.V.) staat wél in de promptcontext maar wordt niet genoemd. Fix: apart
  type "identiteits-/informatievraag" + promptregel "beantwoord letterlijke vragen concreet
  (klantnaam + facturen)".
- Punt 24-ontwerp: wachtrij-cutoff op go-live + auto-draft weer aan per categorie +
  classificatie direct ná sync triggeren + één scherm met approve-and-execute
  (endpoint bestaat al).

---

## Blok 3 — Fasebalk (punt 14)

- IN100410: stap "Voorstel dagvaarding" (categorie administratief), 0 stap-historie.
  `DossierHeader.tsx`: `isPast = index < currentPhaseIndex` → alles links van de huidige
  categorie krijgt een groen vinkje, doorlopen of niet. "Administratief" (verweer/
  opvragen/voorstel/on-hold) is bovendien geen fase.
- Concurrenten: Clio (matter status = label; stages = kanban per praktijkgebied),
  Smokeball (stage = milestone-dropdown boven de zaak, per zaaktype, met tijd-in-stage).
  Niemand vinkt niet-doorlopen fasen af.
- Voorstel: huidige stapnaam + categoriekleur + "X dagen in deze stap"
  (step_entered_at bestaat) + volgende stap; het echte pad staat al in Tijdlijn.
- Bronnen: help.clio.com "Matter Stages"/"Matter Status";
  support.smokeball.com "Set up and use matter stages".

---

## Blok 4 — Kleinere punten

- **Punt 4 CC/BCC:** BCC bestaat nergens (0 treffers in backend/app/email — schema's,
  providers, UI). CC werkt backend-breed wél; de dialog verliest een getypt CC-adres
  stilletjes als je niet eerst Enter/komma drukt (email-compose-dialog.tsx:865 vs :664)
  — meest waarschijnlijke demo-oorzaak (hypothese, in S220 met test bevestigen).
- **Punt 17/18:** detailpaneel Mail heeft al een klikbare dossierlink; de lijstrij niet.
  Tijdlijn-preview vereist eerst de logging-fix (compose-send maakt geen SyncedEmail).
- **Punt 23:** "URGENT: Escalatie email beoordelen — IN100607" bestaat nog, status
  'skipped' (12:54:41 aangemaakt door de escalatie-actie, 12:55:10 per ongeluk geskipt).
  Taken-pagina toont skipped nergens en heeft geen herstelknop; 18 taken staan zo
  onzichtbaar. Fix: weergave + herstel-knop + undo-toast.
- **Punt 16:** memo-structuur klaar (impact: 14-dagenbrief-plicht, BIK/BTW,
  consumentenrente, WIK-bijlage); lijst per dossier maken kan in S220 uit de BaseNet-XML.
- **Punt 15:** timeout Eerste→Tweede staat op {"days": 7} in step_transitions;
  stap-wachttijd = 4; Lisanne's workflow = 4. **Voorstel: 7 → 4** (één UPDATE).

---

## Blok 5 — Eigen demoronde: nieuwe vondsten

1. **Zombie-concepten** (zelfde patroon als punt 13): 8 open ai_drafts, waarvan IN100613
   2× "Eerste sommatie" terwijl de zaak al op Tweede staat (versturen = dubbele sommatie
   mét oud adres) en IN100521 2× identiek verzoekschrift. Fix samen met punt 13: bij
   stap-wissel ook oude concepten sluiten + bestaand concept tonen i.p.v. opnieuw genereren.
2. **Zes stille ruis-wachtrijen** (gemeten): classificaties 470 pending · notificaties 348
   ongelezen · mail ongelinkt 79 · intake 14 (ruis) · follow-up 15 (3 verouderd) · taken
   18 skipped onzichtbaar. Ontwerpprincipe: go-live-cutoff voor import-ruis +
   auto-opruiming bij achterhaald-raken + afgehandelde items zichtbaar/herstelbaar.
3. **Hardcoded geld/kantoor-waarden**: derdengelden-IBAN + kosten in verzoekschrift-DOCX,
   "2% per maand" in VSO-sjabloon, kantoornaam/URL in code (single-tenant OK).
   kestinglegal.nl/debiteuren + logo.png: beide bereikbaar (geen vondst).

## Bewijs-status
Alle metingen deze sessie zelf gedaan (prod read-only). Niet 100% dichtgetimmerd:
(a) From-adres Bayar-mail = afleiding uit code + afwezigheid in incasso@-Sent — checken
in Arsalans M365 Verzonden-map; (b) CC-verlies = code-hypothese, in S220 testen;
(c) demo-waarneming "aanhef weggevallen bij verzoekschrift-concept" niet gereproduceerd
(de 2 huidige IN100521-concepten hébben een aanhef) — verklaring: LLM-variatie op een
sjabloon zonder aanhef.
