# Plan — WIK-rentebijlage bij eerste sommatie (met KvK-rechtsvorm-koppeling)

**Status:** goedgekeurd (S210, 14 juli 2026). Bouwen = Opus, tegen de KvK-**testomgeving**;
productie-sleutel volgt ~16 juli (2 werkdagen na aanvraag). Backfill pas met de echte sleutel.

## Doel
Bij de **eerste sommatie** automatisch het bestaande renteoverzicht (regel-voor-regel
renteberekening) als **PDF-bijlage** meesturen — maar **alleen** wanneer de schuldenaar
privé aansprakelijk is (particulier, eenmanszaak, VOF, maatschap, CV). Voor een BV/NV/
stichting: geen bijlage. De rechtsvorm komt uit de **KvK-API** (Basisprofiel) en wordt
opgeslagen op de relatie, zodat de verzendbeslissing nooit live de KvK hoeft te raadplegen.

## Gemeten uitgangspunten (S210, in de bron geverifieerd)
- **Renteoverzicht bestaat al** als DOCX-sjabloon (`template_key=renteoverzicht`) met de
  regel-voor-regel berekening (motor: `calculate_monthly_compound_interest`, cent-exact op IN100197).
- **PDF-bijlage-pad bestaat al**: `documents/pdf_service.py::docx_to_pdf` + `send_with_attachment`;
  gebruikt in `ai_agent/followup_service.py` en `incasso/service.py` (DOCX-route, o.a. dagvaarding).
- **"Eerste sommatie" = eigen pijplijnstap** `sort_order=1`, `template_type=sommatie_drukte`
  (e-mailsjabloon, geen DOCX-brief). Dit is een e-mailroute → de renteoverzicht-PDF wordt als
  **bijlage** aan die mail gehangen (nu is de bijlagenlijst leeg).
- **Doelgroep-data prod:** 80 b2c-zaken (particulier, altijd bijlage); 528 b2b-zaken waarvan
  441 met KvK-nummer op de wederpartij, 87 zonder. 596 unieke wederpartijen, 438 met KvK.
- **BaseNet-export bevat GEEN rechtsvorm-veld** op Company/Person (velden geteld) → KvK-koppeling
  echt nodig, niet uit de import te halen.
- **KvK-koppeling bewezen werkend** (S210, gratis testomgeving): `GET /basisprofielen/{kvk}`
  levert `_embedded.eigenaar.rechtsvorm` + `uitgebreideRechtsvorm` (bv. "Besloten vennootschap",
  "Eenmanszaak"). Test-key + endpoints: zie §Technisch.

## Juridische kadering (eerlijk)
Er is **geen wet** die letterlijk een meegestuurde renteberekening eist. Wel hard: de
14-dagenbrief (consument) moet exacte bedragen noemen (gate staat live sinds S205), en een
rechter eist een deugdelijke rente-onderbouwing bij procedure. De bijlage is dus **verstandige
kantoorpraktijk die Lisanne wil**, geen wettelijke plicht. Niet mooier voorstellen dan het is.

## Goedgekeurde beslissingen (S210, Arsalan akkoord op aanbevelingen A–D)
- **A. Rechtsvormen die de bijlage triggeren:** particulier + eenmanszaak + VOF + **maatschap**
  + **commanditaire vennootschap** (allen privé aansprakelijk). NIET: BV, NV, stichting, coöperatie.
- **B. Zakelijke partij, rechtsvorm onbekend:** **wél** de bijlage (veilige kant — te veel info is
  onschuldig, te weinig niet).
- **C. Ook bij de 14-dagenbrief** (`sort_order=0`, gaat per definitie naar consumenten): **ja**.
- **D. Eenmalige backfill** van de 438 wederpartijen met KvK-nummer zodra de echte sleutel er is:
  **ja** (± €9 aan bevragingen; droogloop + akkoord + natelling, recept-aanpak zoals S209).

## Bouwstappen (Opus, tegen testomgeving)
1. **Relatie-veld `legal_form`** op `contacts` (String, nullable) + herkomst-velden
   `legal_form_source` ("kvk"/"handmatig") en `legal_form_checked_at`. Migratie additief; contacts
   heeft al RLS → geen aparte apply_rls (zie s209/s210-precedent). Model + schemas (Create/Update/
   Response) + UI op de relatiekaart (tonen + handmatig aanpasbaar, patroon = rechtsvorm-veld).
2. **KvK-client** `backend/app/integrations/kvk_service.py`: `async get_rechtsvorm(kvk_number) ->
   str | None`. Basis-URL + apikey uit `app.config` (env: `KVK_API_KEY`, `KVK_API_BASE`).
   Timeout + faalt zacht (return None, log). NOOIT in het verzendpad aanroepen.
3. **Auto-vullen bij relatie-aanmaak/-update**: als `kvk_number` gezet wordt en `legal_form` leeg
   is → KvK bevragen, `legal_form` + source="kvk" + checked_at zetten. Mislukt = leeg laten.
4. **Beslisregel** `should_attach_rente_bijlage(opposing_party) -> bool` in één helper
   (`collections/compliance.py` of naast de dagenbrief-gate). Leest **alleen** `legal_form` (+
   `debtor_type=b2c`). Kernwoord-match op de vormen uit besluit A; onbekend zakelijk → True (besluit B).
5. **Bijlage aanhaken** op de e-mailroute van stap `sort_order in (0,1)` (14-dagenbrief + eerste
   sommatie): render renteoverzicht → `docx_to_pdf` → aan `attachments` toevoegen. Ook opslaan als
   `GeneratedDocument` zodat het in het dossier terugkomt. Raakt zowel `followup_service` (Uitvoeren-
   knop) als `incasso/service` (batch) — één gedeelde helper, beide paden gebruiken 'm.
6. **Backfill-script** `scripts/kvk_backfill_legal_form.py` (droogloop-modus verplicht): loopt de 438
   wederpartijen met KvK-nummer af, vult `legal_form`. Pas draaien met de ECHTE sleutel (testdata =
   nepbedrijven). Tel-verificatie achteraf.
7. **Tests:** beslisregel per rechtsvorm (A/B/C-gevallen), auto-vullen bij create, KvK-client met
   gemockte respons, en dat het verzendpad NIET faalt als KvK onbereikbaar is.

## Premortem (3 faalrisico's + waarom aanpak toch juist)
1. **KvK-storing blokkeert verzending** → beslisregel leest alleen het opgeslagen veld; KvK enkel
   bij aanmaak + backfill. Verzendpad raakt de KvK nooit.
2. **KvK schrijft de vorm nét anders** ("Besloten Vennootschap" / "Vennootschap onder firma" /
   uitgebreide varianten) → kernwoord-match, niet exacte string; test per variant.
3. **Bijlage ontbreekt bij wie 'm moest krijgen** (erger dan andersom) → besluit B: bij twijfel wél
   meesturen.

## Technisch — KvK-API (getest S210)
- Gratis test-key (openbaar, geen geheim): `l7xx1f2691f2520d487b902f4e0b57a0b197`
- Test-endpoints: `https://api.kvk.nl/test/api/v2/zoeken`, `.../test/api/v1/basisprofielen/{kvk}`
- Header: `apikey: <key>`. Rechtsvorm-pad in respons: `_embedded.eigenaar.rechtsvorm` (+ `uitgebreideRechtsvorm`).
- Productie (na sleutel): base wordt `https://api.kvk.nl/api/...`; alleen `KVK_API_KEY` + `KVK_API_BASE` omzetten.
- Kosten prod: €6,40/mnd vast + zoeken €0,00 + basisprofiel €0,02/bevraging (BTW-vrij).

## Wat NIET in scope
- Landregel op dagvaarding/faillissementsverzoek (los klusje, S210 bewust niet gedaan).
- De 87 zakelijke wederpartijen zónder KvK-nummer: blijven leeg → vallen onder besluit B (wél bijlage);
  handmatig invulbaar op de relatiekaart.
