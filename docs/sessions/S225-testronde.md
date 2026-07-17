# S225 — Testronde batch-verzending + bouwwerk (Fable, 17 juli 2026)

Opdracht Arsalan: "20 zaken aanklikken, verstuur de sommatie, en alles moet
overal kloppen — bedragen, namen, brief, fase, follow-up, alle pagina's, alle
vervolgstappen." Getest met 13 verse testdossiers (debiteur = Arsalans gmail),
via de échte UI-route (aanvinken → Verstuur brief), niets naar echte debiteuren.

## 1. Testopzet

| Set | Dossiers | Doel |
|-----|----------|------|
| Mini-batch (3) | 2026-00007 (BV €250), -00008 (eenmanszaak €100), -00009 (particulier b2c €80) | varianten: rechtsvorm, consument-blokkade |
| Grote batch (10) | 2026-00010 t/m -00019, 10 verschillende bedrijfsnamen, bedragen €60–€2.500, verzuim maart–juni | schaal + per-zaak-correctheid |
| Word-tak (1) | 2026-00017 via tijdelijke "TEST DOCX-stap" (sjabloon dagvaarding) | de batch-tak die op prod nooit vuurde (B6) |

Alle dossiers aangemaakt via de echte API (opdrachtgever = TEST Opdrachtgever
Fable-review), op stap Eerste sommatie gezet, batch via de incasso-pagina.

## 2. Resultaten — alles bewezen

**Batch-uitvoer:** mini-batch "2 verwerkt, 1 overgeslagen" — de particulier
(00009) correct geblokkeerd mét wettelijke reden (14-dagenbrief verplicht,
art. 6:96 lid 6 BW). Grote batch: 10/10 verwerkt, 10 mails, 10 doorgeschoven.

**Bedragen op de cent (onafhankelijk nagerekend, 4% wettelijke rente):**
- 00007: €250 + €2,11 rente (77 dgn) + €40 BIK = **€292,11** ✅
- 00008: €100 + €0,50 rente (46 dgn) + €40 BIK = **€140,50** ✅
- 00010: €150 + €1,12 rente (68 dgn) + €40 BIK = **€191,12** ✅ (ook in gmail-inhoud geverifieerd)

**Bezorging:** alle 12 batchmails **in gmail-inbox aangekomen** (via Gmail-API
gecontroleerd), juiste namen per zaak, rente-PDF als bijlage, volledige
huisstijl (logo, schuldhulpblok, disclaimer, Willem Fenengastraat, juiste
derdengelden-IBAN).

**Huisregels (matrix breed-testen):** M1 afzender incasso@ op alle 13 mails ✅;
M2 drieluik (EmailLog + SyncedEmail + CaseActivity) per zaak compleet ✅;
M3 gate blokkeert consument in batch ✅; M4 onderwerp huisformaat via de bouwer
✅; M5 rente-bijlage volgens rechtsvorm-regel ✅ (zie kanttekening 3).

**Vervolgstappen (P-regels):** alle verstuurde zaken Eerste → Tweede sommatie;
geblokkeerde zaak bleef staan; per zaak automatisch één nieuwe taak "Tweede
sommatie genereren" (toegewezen aan gebruiker, deadline +4 dagen = wachttijd);
verzending vastgelegd op de stap-historie.

**Overal zichtbaar:** incasso-lijst (nieuwe stap), dossierpagina (fasebalk
Tweede sommatie + correspondentie + tijdlijn met mail/stap/automatisering),
Mail-pagina (alle uitgaande mails), Taken-pagina (10 nieuwe taken), follow-up
(geen voorbarige of verouderde adviezen). Allemaal live doorgeklikt.

**Word-tak (B6) bewezen:** TEST-stap met dagvaarding-sjabloon → batch rendert
DOCX → PDF (38→55 kB), verstuurt via incasso@ met PDF-bijlage en
bouwer-onderwerp, document in het dossier. TEST-stap daarna verwijderd,
zaak teruggezet — pijplijn weer exact 15 originele stappen.

**B1 factuur-afzender bewezen:** testfactuur F2026-00001 (€1) → goedkeuren →
versturen → **afzender incasso@** (vóór de fix: persoonlijk account), bezorging
bevestigd via de mailsync; factuur daarna geannuleerd (nette boekhoudstatus).

## 3. Vondsten / kanttekeningen

1. **Dossiernummer-hergebruik plakt oude post aan nieuwe dossiers** (2×
   waargenomen: 00007 en 00014 kregen een maart-testmail met datzelfde nummer
   automatisch aangekoppeld via de dossiernummer-matcher). Nummers van
   verwijderde dossiers worden hergebruikt; oude mail met dat nummer koppelt
   dan aan het verkeerde (nieuwe) dossier. Bij echte dossiers kan dit
   correspondentie-vervuiling geven. → Voorstel S226: nummer-hergebruik
   voorkomen (teller nooit terug) of matcher laten kijken naar de maildatum
   vs. dossier-aanmaakdatum.
2. **Gmail filtert de zwaarste juridische brieven stilletjes weg (patroon
   bevestigd):** 25 mails bezorgd (12 eerste sommaties, 12 tweede sommaties,
   14-dagenbrief — allemaal binnen een minuut, mét PDF-bijlagen), maar de
   dagvaarding-PDF-mail en BEIDE faillissementsdreigbrieven (zonder én mét
   verzoekschrift-bijlage) zijn nergens — ook niet in spam. Alle drie door
   smtp.basenet.nl geaccepteerd, kopie in Verzonden, geen bounce. Het ligt dus
   niet aan bijlagen maar aan de inhoud (dagvaarding/faillissement). Voor echte
   debiteuren met gmail is dit relevant: juridisch telt verzending, praktisch
   komt de dreiging niet aan. → S226: SPF/DKIM/DMARC van kestinglegal.nl op de
   BaseNet-SMTP-route controleren; bounce-logboek later nachecken.
3. **Rechtsvorm-afkorting "bv" wordt niet herkend als beperkt aansprakelijk:**
   de bijlage-regel matcht op de volledige KvK-benaming ("besloten
   vennootschap"); handmatig ingevoerde afkortingen ("bv") vallen op de veilige
   kant (bijlage mee). Correct-veilig gedrag, maar goed om te weten voor
   handmatige invoer; de KvK-backfill (volle benamingen) lost dit vanzelf op.
4. **Dubbele spatie in gmail-onderwerpen is een weergave-artefact** van
   regel-vouwen bij lange onderwerpen; in de database staat het onderwerp goed.

## 3b. Tweede ronde — alle overige brieftypen door de batch (vraag Arsalan)

Vraag: "geldt dit ook voor Tweede sommaties e.d., of moeten we dat testen?"
Antwoord: het gedeelde mechanisme is voor alle typen hetzelfde (bewezen), maar
de brief-INHOUD verschilt per sjabloon → alle resterende typen alsnog gevuurd:

- **Tweede sommatie (12 zaken):** 12/12 verstuurd, geen bijlage (correct — geen
  rente-set-type), alle 12 doorgeschoven naar Derde sommatie, bezorgd in gmail.
- **14-dagenbrief (particulier 2026-00009):** verstuurd MÉT rente-PDF (correct:
  consument → bijlage), zaak doorgeschoven naar Eerste sommatie. De batch-gate
  laat een volgende sommatie nu pas na 15 dagen toe.
- **Faillissementsdreigbrief (2026-00016):** verstuurd, zaak bleef op de stap.
  **→ VONDST 5 (M5 × batch): de brieftekst belooft "een kopie van het
  verzoekschrift treft u in de bijlage aan", maar de batch stuurde GEEN bijlage
  mee.** De brief was ontworpen voor de compose-dialoog (Lisanne voegt het
  concept-verzoekschrift daar handmatig toe). **GEFIXT (keuze Arsalan 17/7:
  automatisch meesturen, commit `20d7df9`):** de gedeelde bijlage-helper rendert
  het concept-verzoekschrift nu bij élke route (batch/follow-up/compose/.eml/
  documents); voorvertoningen kondigen hem aan; +2 wachter-tests. **Live
  herbewezen:** tweede batch-run op 2026-00016 → mail mét bijlage (08:07) +
  "Concept-verzoekschrift faillissement" als document in het dossier.
- Derde sommatie / Sommatie laatste mogelijkheid / Voorstel dagvaarding hebben
  géén briefsjabloon → batch slaat ze over met verwijzing naar de AI-conceptflow
  (bewust ontwerp, geen gat).
- Bezorging ronde 2: 13/14 direct in gmail; 1 nog onderweg (zelfde vertraging
  als de dagvaarding-PDF-mail, zie §3.2).

## 4. Testdata (opruimen later, afspraak Arsalan)

13 testdossiers 2026-00007 t/m 2026-00019 + 13 TEST-contacten + testfactuur
F2026-00001 (geannuleerd) + 12 taken "Tweede sommatie genereren". Testdossier
2026-00006 blijft actief als vast testkanaal (besluit B5).
