# Vooronderzoek — Lisannes eigen facturatie is nooit gemigreerd (12 juli 2026, Fable)

Aanleiding: Arsalan constateerde dat de facturen die Lisanne vanuit BaseNet aan haar
(7 vaste) klanten stuurde niet zijn meegekomen. Dit vooronderzoek hard-meet de omvang.
Bron: BaseNet-export `Xml_02-07-2026_2400.zip` (2 juli) + prod-queries (12 juli, read-only).

## Kernfeiten (gemeten, niet geschat)

1. **Prod is volledig leeg:** `invoices` = 0, `invoice_lines` = 0, `invoice_payments` = 0.
   Uren (`time_entries`) idem leeg — vandaar de dode dashboard-widgets (D-A-audit).
2. **De S168-import nam bewust alleen mee:** relaties, dossiers, vorderingen, mails,
   (later) betalingen. Lisannes eigen declaratielaag zat nooit in de scope.
3. **De export bevat alles wél:**
   | Entiteit | Records | Wat het is |
   |---|---|---|
   | OutgoingInvoice | **567** | Lisannes uitgaande facturen 2024-2026 (2024: 9, 2025: 301, 2026: 257) |
   | OutgoingInvoiceLine | 773 | de factuurregels |
   | Hour | **1.320** | urenregistraties |
   | HourToOutgoingInvoiceLine | 2.742 | koppeling uur → factuurregel |
   | HourActivity / HourlyRate / HourType | 864 / — / — | activiteiten + tarieven |
4. **Bedragen (veld `invtobepaid`/`invopenamount` op de factuurkop):** som "te betalen"
   €235.899,91; som openstaand **€21.670,52**. ⚠️ Sommige klanttotalen zijn negatief →
   de semantiek van deze velden (credit? saldo?) is NIET vastgesteld; regelsom-veld op
   OutgoingInvoiceLine nog niet gevonden (kolomnaam onbekend). → uitzoeken in sessie.
5. **Topklanten = precies de vaste opdrachtgevers:**
   Incassocenter 142 · INC Zakelijk 100 · LAVG (deurwaarders) 95 · COLLECT 1 31 ·
   Van der Kooij Besters Advocaten 24 · LegalWork 18 · Scholte de Vries 12 ·
   Reijck Credit Service 11 · Fresh Burger 7 11 · CM Zakelijk 10 · Invorderingsbedrijf 8.
6. **Open spoor:** de 12 onverklaarde bankcredits ±€21,7k (Donker/Dinc, S195, besluit
   "vervallen") liggen numeriek dicht bij het openstaande factuurbedrag €21.670,52.
   MAAR: "Donker Groep B.V." (100316) en "Donkers" (100737) zijn relaties zónder
   facturen → hypothese wankel. Wel toetsen: match de 12 credits op factuurbedragen/
   -nummers vóór hem definitief te begraven.

## Groter dan facturen: het niet-beoordeelde deel van de export

Entiteiten mét data die nooit voor migratie zijn beoordeeld (selectie, aantal records):
- **Letter ×4 bestanden: ~18.000 brieven** (rela.corres.Letter) — gegenereerde
  correspondentie; verhouding tot de 6.393 geïmporteerde mails onbekend.
- **Journal 2.954 + MemorialLine 777 + Dcinfo 1.027** — boekhouding/open posten.
- **Task 1.613 (+ TaskActivity 1.513 / TaskHistory 1.364)** — BaseNet-taken.
- **Project 794** — projecten (uren hangen hieraan).
- WorkflowEvent 1.436, LabelLink 1.375, RelationEmailAddress 940, RelationTag 729.

→ De onderzoekssessie hoort een **volledigheidsmatrix** op te leveren: élk export-
bestand met records → geïmporteerd ja/nee → hoort het alsnog mee? (ja/nee/deels + why).

## Waar het bronmateriaal staat
- Zip: `C:\Users\arsal\Documents\luxis\Xml_02-07-2026_2400.zip`
- Leescode die het formaat al aankan: `scripts/basenet/parse.py` (`iter_records`)
- Relatiecode → naam: `rcode`/`company` in `…rela.entities.Company.xml` (+ Person.xml)

## Vervolg
Zie `docs/sessions/PROMPT-S201-onderzoek-facturatie.md` — het volledige draaiboek
(Fable, read-only). Bouwen daarna door Opus/Sol op het opgeleverde recept.
