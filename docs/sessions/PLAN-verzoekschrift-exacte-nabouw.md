# Plan — verzoekschrift-bijlage: Lisanne's exacte opmaak nabouwen (per zaak ingevuld)

**Beslissing (Arsalan, 15-07 / S221):** de faillissement-bijlage moet EXACT de opmaak van
Lisanne's PDF hebben (crème-balk + KESTING LEGAL-logo + lay-out), maar per zaak ingevuld.
Aparte, verse sessie afgesproken (niet haastig aan het eind van S221). Onderzoek hieronder
is al gedaan — niet opnieuw uitzoeken.

## Bron & doel
- **Doelbeeld (blanco):** `templates/lisanne/CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf`
  (5 pagina's, crème-balk met logo, elegant). Bevat 6 afbeeldingen (logo + handtekening-placeholder).
- **Bron-DOCX (blanco + OUD adres):** `templates/lisanne/Template Verzoekschrift Bijlage.docx`.
  Dit is een **BaseNet-merge-sjabloon** (Velocity-taal), GEEN docxtpl. Logo's zitten in de
  headers (`word/header1/2.xml`, image2.png = KESTING LEGAL-logo, image1.jpg = handtekening-
  placeholder "basenet_image_0"). Hardcoded OUD adres "IJsbaanpad 9" in de body → moet naar
  huidig adres of `{{ kantoor.* }}`.

## Wat er nu (S221) LIVE staat als tussenoplossing
`templates/verzoekschrift_faillissement.docx` (managed_template key `verzoekschrift_faillissement`,
door compose auto-bijgevoegd — zie `email-compose-dialog.tsx:513-524`) = het WERKENDE invulbare
Luxis-sjabloon + KESTING LEGAL-logo in het briefhoofd (rechtsboven, wit). Vult correct per zaak
(bedragen/namen/huidig adres), één lettertype (Calibri). NIET Lisanne's crème-balk-lay-out.
De exacte nabouw VERVANGT dit bestand (zelfde key) of komt als aparte key.

## De klus: BaseNet-velden → Luxis docxtpl-velden
Lisanne's DOCX heeft **38 unieke BaseNet-markers** (`«...»`), o.a. `#foreach` (vorderingen +
kosten), `#if/#else/#end`, `#set` (berekeningen via `$func`), en `$image.registerImage(...)`.
De Luxis render-service levert echter al de EINDwaarden — dus de `#set`/`$func`-berekeningen
kunnen weg; alleen de DISPLAY-velden omzetten + één regel-loop opnieuw opbouwen.

**Doel-variabelen (exact die de render-service voor `verzoekschrift_faillissement` levert —
overnemen uit het huidige `templates/verzoekschrift_faillissement.docx`):**
`{{ kantoor.naam/adres/postcode_stad }}`, `{{ wederpartij.naam/adres/postcode_stad }}`,
`{{ client.naam/postcode_stad }}`, `{{ zaak.zaaknummer }}`, `{{ vandaag }}`,
`{{ totaal_openstaand }}`, loop `{%tr for v in vorderingen %}` met
`{{ v.beschrijving/factuurnummer/verzuimdatum/hoofdsom }}` `{%tr endfor %}`,
`{{ totaal_hoofdsom }}`, `{{ totaal_rente }}`, `{{ subtotaal }}`, `{{ bik_bedrag }}`,
`{{ btw_regel_label }}`, `{{ btw_regel_bedrag }}`, `{{ totaal_verschuldigd }}`.

**Marker→var (concept, controleren bij bouw):**
- `«…linkedEntity.wederpartij…»` (recipient-blok, 4×) → `{{ wederpartij.naam/adres/postcode_stad }}`
- `«…relation.aanhef»` → vaste aanhef "Geachte heer, mevrouw," (keuze S220)
- `«#if…»«…relationName»«#else»…«#end»` (bedrijf/persoon) → `{{ client.naam }}` (data geeft direct)
- `«…pcode»` / client-locatie → `{{ client.postcode_stad }}`
- `«…openBedrag»` → `{{ totaal_openstaand }}`
- `«…ledate.format.longdate»` → `{{ vandaag }}`  ·  `«…lesubject»` → Betreft/Inzake
- `«#foreach($vordering…)»…«#end»` → `{%tr for v in vorderingen %}…{%tr endfor %}`
- `«$vordering.inclinvnr»`→`{{ v.factuurnummer }}` · `inclamount.format.money`→`{{ v.hoofdsom }}`
  · `inclduedate`→verzuim/vervaldatum · `inclsenddate`→factuurdatum
- amounts `hoofds/incass/incinc/vatPer/totaal` → `{{ totaal_hoofdsom/bik_bedrag/… }}`
- `«$image.registerImage("basenet_image_0",…)»` (handtekening) → laten vallen of vaste
  handtekening-afbeelding; LOGO houden via het briefhoofd (image2.png, zoals de tussenoplossing).

## Valkuilen (gemeten)
- **Markers zijn over runs gesplitst** in de OOXML → een simpele string-replace op document.xml
  vindt ze niet. Eerst per paragraaf de runs samenvoegen (merge-fields normaliseren) vóór replace.
- **LibreOffice behoudt briefhoofd-logo's** (getest: Lisanne's origineel rendert mét 10 afbeeldingen)
  → het logo overleeft de DOCX→PDF-render. `docx_to_pdf` gebruikt `soffice`.
- **PNG-transparantie**: image2.png (logo) is palette+transparant → op WIT compositen vóór insert
  (anders zwart blok). Zie de S221-aanpak.
- **docxtpl-render bewijst**: getest met testdata → alle velden vullen + logo blijft (S221).

## Verificatie (verplicht — juridisch stuk met bedragen)
Render met testdata → PDF → **elk veld visueel controleren** (vooral de bedragentabel: hoofdsom,
rente, BIK, BTW, totaal, per-factuur-regels) → naast de doel-PDF leggen (lay-out) → pas dan reseed
(`scripts/reseed_builtin_templates.py`) + prod byte-check. Back-up managed_templates vóór reseed.

## Aanpak-volgorde
Fable: velden/mapping definitief maken + testdata-context bepalen. Opus: bouwen (run-merge +
marker-replace + loop + adres-fix + logo-briefhoofd) → testrender → veld-voor-veld-controle →
reseed. Fable: review.
