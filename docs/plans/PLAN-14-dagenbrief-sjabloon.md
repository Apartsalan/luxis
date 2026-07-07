# PLAN — E-mailsjabloon voor de 14-dagenbrief-stap

**Rang: 4 — deels geblokkeerd: Lisanne moet de brieftekst goedkeuren (er staat al
langer een open punt "H6: tegenstrijdige juridische instructies" in ARSALAN-TODO §5).
Het voorbereidende werk kan nu; live zetten pas na haar akkoord.**

## Vastgesteld probleem (audit 7 juli)

De actieve stap "14-dagenbrief" (id `a31f9658-06ff-4b3f-893b-c806b579f49b`) heeft **geen
e-mailsjabloon en geen documentsjabloon**. In het heropeningsrecept starten **34
B2C-zaken** op deze stap, en de wet eist deze brief vóórdat incassokosten (BIK) gevorderd
mogen worden bij consumenten. Zonder sjabloon kan de draft-generator niets maken
(`generate_draft_for_step` gooit "geen email-sjabloon geconfigureerd") en toont de
opvolg-scan alleen "handmatige beoordeling nodig".

## Waar het sjabloon leeft

Kolommen `email_subject_template`, `email_body_template`, `email_body_template_html` op
`incasso_pipeline_steps`. Instelbaar via de UI: Instellingen → Workflow (StappenTab) —
géén deploy nodig. De AI-draft-generator gebruikt het sjabloon als bron via
`app/ai_agent/incasso_email_prompts.build_full_prompt`; de bedragen-context bevat al
"Incassokosten (BIK): € …" (prompt-bestand regel ~187), dus het exacte bedrag is
beschikbaar voor het concept.

## Stappenplan

1. Lees het bestaande sjabloon van "Eerste sommatie" als stijlvoorbeeld
   (`SELECT email_subject_template, email_body_template FROM incasso_pipeline_steps
   WHERE name='Eerste sommatie' AND is_active;`).
2. Stel een concepttekst op die de **wettelijke eisen** dekt (bron:
   `docs/dutch-legal-rules.md`, sectie 14-dagenbrief, art. 6:96 lid 6 BW):
   - betaaltermijn van **veertien dagen die ingaat de dag ná bezorging** — gebruik de
     Hoge Raad-veilige formulering "binnen veertien dagen vanaf de dag nadat deze brief
     bij u is bezorgd" (NIET "binnen 14 dagen na dagtekening" — dat maakt de brief
     ongeldig);
   - het **exacte BIK-bedrag** dat verschuldigd wordt bij niet-betalen (uit de
     bedragen-context; geen "circa");
   - als de cliënt niet btw-plichtig is: het btw-bedrag over de BIK apart benoemen
     (de staffelberekening in `app/collections/wik.py` levert dit al).
3. Leg de concepttekst via Arsalan aan Lisanne voor **samen met het open punt H6**
   (ARSALAN-TODO §5) — één beslismoment.
4. Na akkoord: tekst in de stap zetten via de UI (of SQL-UPDATE op de drie kolommen;
   UI heeft de voorkeur want dan is bewezen dat de beheerflow werkt).
5. Genereer op één heropende B2C-testzaak handmatig een concept (de handmatige
   trigger-endpoint bestaat; de vlag hoeft er niet voor aan) en laat Lisanne het
   beoordelen.

## Randgevallen

- **De timeout-regel "14-dagenbrief → Eerste sommatie" staat op 15 dagen** — klopt met
  de 14-dagen-termijn (+1 dag bezorgmarge), niets aan doen.
- De stap is b2c-only (`debtor_type='b2c'`) — B2B-zaken horen hier nooit te staan;
  het heropeningsrecept doet dat al goed.
- Verstuurdatum ≠ ontvangstdatum: de termijn in de brief moet aan bezorging refereren,
  niet aan verzending — dit is precies waar standaardsjablonen de mist in gaan.
- Bij deelbetaling binnen de 14 dagen mag alleen BIK over het restant — dat hoeft NIET
  in het sjabloon (te complex voor een brief), maar de zaak moet dan handmatig
  beoordeeld worden; noteer dit als werkinstructie in het sjabloon-commentaar voor
  Lisanne.
- Sla de definitieve tekst óók op in `docs/` (bv. `docs/templates/14-dagenbrief.md`)
  zodat hij versiebeheer heeft — de DB-kolom heeft dat niet.

## Acceptatiecriteria

1. Stap heeft subject + body (+ html) gevuld — query toont niet-lege kolommen.
2. Concept gegenereerd op een echte B2C-zaak bevat: exact BIK-bedrag in euro's,
   de "dag nadat bezorgd"-formulering, dossiernummer als betalingskenmerk.
3. Lisanne heeft de tekst schriftelijk (mail/appje via Arsalan) goedgekeurd.
4. Tekst gearchiveerd in de repo; SESSION-NOTES bijgewerkt.
