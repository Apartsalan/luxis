# Financiële samenhang Luxis — betalingen · facturen · derdengelden · Exact

*Onderzoek sessie 158 (10 juni 2026). Vraag: hoe hangen de drie geldstromen samen, klopt het, en is het facturen-stuk af? Code-trace van alle schakels + beoordeling als advocaat/PMS-product.*

---

## 1. De drie administraties (zo zit het nu)

Luxis voert **drie gescheiden financiële administraties** — dat is juridisch correct, want het zijn ook echt drie verschillende werelden:

| Administratie | Tabel | Wat het bijhoudt | Wie betaalt wie |
|---|---|---|---|
| **Vorderingsadministratie** | `payments` (collections) | Wat de debiteur op de vordering betaalt (art. 6:44 BW verdeling: kosten → rente → hoofdsom) | Debiteur → cliënt (via stichting) |
| **Derdengelden** | `trust_transactions` | Geld dat fysiek op de stichtingsrekening staat (deposit / disbursement / offset / reversal) | Debiteur → stichting → cliënt of kantoor |
| **Declaratie-administratie** | `invoices` + `invoice_payments` | Wat het kantoor aan de cliënt factureert en wat daarop betaald is | Cliënt → kantoor |

### De verbindingen (allemaal aanwezig)

```
                    BANKIMPORT (stichtingsrekening, CSV)
                          │ match (AI + regels)
                          ▼
            ┌─ TrustTransaction (deposit) ──────────┐
 execute_match ─┤                                       │ saldo per dossier
            └─ Payment (6:44-verdeling, gecapt        │
               op openstaand; overschot blijft saldo)  │
                          │                            ▼
              dossier auto → "betaald"        DerdengeldenTab / saldolijst
                          │
                          ▼
        FACTUUR NAAR CLIËNT (facturen/nieuw?case_id=X)
        IncassoKostenPanel: BIK + rente + provisie voorgerekend,
        dubbel-factureren-detectie, uren-import, verschotten-import
                          │ approve → send (PDF + e-mail via provider)
                          ▼
        VERREKENING (offset_to_invoice, Voda 6.19 lid 5)
        consent verplicht → vier-ogen → InvoicePayment
        (method "verrekening") → factuurstatus paid/partially_paid
        + automatische bevestigingstaak aan cliënt
                          │
                          ▼
        UITBETALING REST AAN CLIËNT (disbursement)
        vier-ogen → SEPA pain.001 export → bank
```

Concrete code-ankers:
- Bankimport → beide boeken: `ai_agent/payment_matching_service.py::execute_match` (regel ~672) — maakt trust-deposit én `create_payment_for_case(cap_to_outstanding=True)`.
- Incassokosten → factuur: `invoices/service.py::get_incasso_invoice_preview` (regel ~1116) — BIK (3 modi), rente (uit `get_financial_summary`), provisie (2 grondslagen, minimumtarief, vaste kosten), al-gefactureerd-detectie.
- Derdengelden → factuur: `trust_funds/service.py::create_offset_to_invoice` + `_book_offset_payment` — zelfde-cliënt-check, saldo-cap, openstaand-cap, consent, vier-ogen; boekt pas na 2e goedkeuring een `InvoicePayment`.
- FinancieelTab toont alle drie: grand_total / betaald / openstaand / `derdengelden_balance` in één scherm (`collections/service.py::get_financial_summary` regel ~905).

**Conclusie architectuur: de samenhang is goed ontworpen.** Drie gescheiden boeken met expliciete, gecontroleerde overgangen — precies wat NOvA/Voda vereist en wat Clio/Smokeball ("trust-to-office transfer") ook zo doen.

## 2. Wat aantoonbaar af en goed is

1. **Debiteur betaalt → dossier bijgewerkt + derdengelden kloppen** — bankimport met dedup (S157), match, 6:44-verdeling identiek aan handmatige betaling (AUDIT-B3), overbetaling gecapt, dossier gaat automatisch naar "betaald" (workflow-hook).
2. **Factuur maken vanuit dossier** — knop op DossierHeader/DocumentenTab/ProvisieSettings → `facturen/nieuw?case_id=` met voorgerekende incassokosten, onbefactureerde uren-import, verschotten-import (DF-12), voorschotnota's (DF-13) met verrekentype.
3. **Factuur-lifecycle** — concept → approved → sent (échte PDF + e-mail, DF117-13) → partially_paid/paid/overdue; credit-nota's; debiteuren-aging op facturen-pagina (`get_receivables`).
4. **Verrekening juridisch correct** — consent per transactie, vier-ogen (tenant-setting, hard bij 2+ users), bevestigingstaak (6.19 lid 5), storno-mechanisme, alles S157.
5. **Uitbetaling** — disbursement met begunstigde+IBAN (mod-97), vier-ogen, SEPA-export, saldo-guard.
6. **NOvA-verantwoording** — mutaties.csv + saldolijst.csv per peildatum.

## 3. De gaten (genummerd op ernst)

### FIN-1 · Twee deuren naar dezelfde boeking, één deur boekt maar half — **HOOG**
- **a)** BetalingenTab (dossier) heeft betaalmethode **"Via derdengelden"** — maar `collections/service.py::create_payment` maakt **géén** trust-deposit. Label suggereert dat het in de derdengelden-administratie komt; gebeurt niet. Handmatig zo geregistreerde stichtingsontvangsten ontbreken in saldo + NOvA-export.
- **b)** Factuur-detail laat handmatige betaling met methode **"Verrekening"** toe (`facturen/[id]/page.tsx` regel ~1357) — zonder trust-offset. De échte verrekening hoort via DerdengeldenTab → OffsetToInvoiceDialog (consent + vier-ogen + saldoafboeking). Zelfde woord, twee betekenissen: voorschot-verrekening (terecht zonder trust) vs derdengelden-verrekening (móét via trust). Eén verkeerde klik = derdengelden-saldo klopt niet meer én de Voda-waarborgen (consent, vier-ogen) zijn omzeild.
- **Fix-richting:** (a) methode "derdengelden" bij handmatige betaling → ofwel automatisch trust-deposit meeboeken, ofwel blokkeren met verwijzing naar bankimport/DerdengeldenTab. (b) "verrekening" op factuur-detail splitsen in "verrekening voorschot" (toegestaan, advance-balance-check) en derdengelden-verrekening (alleen via offset-flow; hier blokkeren).

### FIN-2 · Geen afwikkel-flow en geen sluit-guards — **HOOG (product)**
Dossier "betaald" → daarna moet de advocaat zelf weten: factureer provisie → verstuur → verreken → keer rest uit → sluit. Niets rekent **"uit te betalen aan cliënt = saldo − verrekening"** voor; dossier kan gesloten/gearchiveerd worden met trust-saldo ≠ 0 (`cases/service.py::delete_case` — geen guard; status-transities checken 14-dagenbrief/verjaring maar geen financiën). Voda 6.19: doorbetalen "zodra de gelegenheid zich voordoet" — talmen is tuchtrechtelijk riskant. Dit is hét verschil tussen "alle features bestaan" en "het werkt".
- **Fix-richting:** "Dossier afwikkelen"-wizard op betaalde dossiers: (1) toont voorstel-factuur (preview bestaat al), (2) verrekening-voorstel, (3) uitbetaling restant, (4) sluiten. Plus harde guard: sluiten/archiveren blokkeert bij trust-saldo ≠ 0 of pending trust-transacties. Plus dashboard-signaal "saldo staat al X dagen stil" (ouderdom).

### FIN-3 · Betalingen op eigen facturen = handmatig — **MIDDEL (bewuste keuze nodig)**
Bankimport leest alleen de **stichtingsrekening** en matcht op dossiers. Cliëntbetalingen op declaraties komen op de **kantoorrekening** binnen — die wordt nergens geïmporteerd. Factuurstatus loopt dus achter tot Lisanne handmatig boekt. Geen bug, wel een regime-keuze: (a) handmatig accepteren (prima bij laag volume), (b) later MT940/CSV-import kantoorrekening met match op factuurnummer, (c) terug-sync uit Exact (complex, afraden). **Advies: (a) nu, (b) als volume groeit.**

### FIN-4 · Exact payment-sync = dubbeltelling-risico — **MIDDEL**
`exact_online/sync_service.py::sync_payment` boekt elke factuurbetaling als **losse bankboeking** in Exact. Als Lisanne's Exact een echte bankkoppeling heeft (standaard bij Exact), komt dezelfde ontvangst twee keer in de administratie. Verrekening-betalingen als "bankboeking" pushen is bovendien boekhoudkundig fout (er stroomt geen geld op de kantoorbank — het komt van de stichting).
- **Fix-richting:** payment-sync standaard uit / verwijderen uit `sync_all`. Alleen facturen pushen.

### FIN-5 · BTW hardcoded 21% op BIK/rente-regels — **MIDDEL (juridische vraag, bekend als #54)**
IncassoKostenPanel zet 21% op alle drie de regels. Of dat klopt hangt af van het honorarium-model (zie §4). Rente die je als kantoor *doorbelast als onderdeel van je dienst* is belast; rente die *van de cliënt is* hoort niet op de factuur maar in de uitbetaling. Wacht op het antwoord op Lisanne-vraag 2 (verrekenclausule).

### FIN-6 · Dubbel-factureren-detectie op tekstmatch — **LAAG**
`get_incasso_invoice_preview` herkent al-gefactureerd via `"provisie" in description.lower()`. Wie de regelomschrijving aanpast, verliest de waarschuwing. Acceptabel (het is een waarschuwing, geen blokkade); robuuster = regel-type-veld op InvoiceLine.

### FIN-7 · Trust-deposit ↔ Payment alleen via PaymentMatch gelinkt — **LAAG**
Bankimport-paren zijn via `PaymentMatch.trust_transaction_id/payment_id` traceerbaar; handmatig aangemaakte paren niet. Voor een eenpitter werkbaar; bij audit-vragen ("welke storting hoort bij welke afboeking?") handig om een directe FK te hebben. Parkeren.

## 4. Het juridische model — de vraag die geen code is

BIK en rente komen juridisch **de schuldeiser (cliënt) toe** — de debiteur vergoedt ze aan de cliënt. Wat het kantoor verdient bepaalt de **opdrachtbevestiging**. Twee gangbare modellen:

1. **Provisiemodel:** kantoor factureert % over geïncasseerd (+ evt. vaste kosten, minimumtarief). Geïncasseerde BIK/rente gaan met de hoofdsom mee naar de cliënt.
2. **Kosten-voor-kantoor-model:** afspraak is dat geïncasseerde BIK + rente het honorarium zíjn ("no cure no pay op kosten van debiteur"). Kantoor factureert exact de geïnde BIK/rente (+ evt. provisie).

Luxis ondersteunt **beide** (IncassoKostenPanel: alle bedragen aanpasbaar, provisie-grondslag kiesbaar) — maar dwingt geen keuze af en de default (BIK + rente + provisie alle drie aanklikbaar) kan in model 1 tot dubbel rekenen leiden. Dit is exact dezelfde openstaande Lisanne-vraag als bij derdengelden (verrekenclausule). **Tot die beantwoord is, is dit stuk niet "af" — niet door code, maar door een ontbrekende kantoorafspraak.** Daarna eventueel: fee-model als tenant-setting zodat het paneel alleen het juiste voorstelt.

## 5. Exact Online — moet het verbonden zijn?

**Nee, niet voor het primaire proces. Wel voor de boekhouding, en dan precies zó:**

| Stroom | Bron | Advies |
|---|---|---|
| Facturen (omzet, BTW-aangifte) | **Luxis** | Push naar Exact (module bestaat: sessie 112, OAuth + GL-mapping per product uit DF120-08). Activeren zodra Lisanne haar Exact koppelt. |
| Betalingen kantoorrekening | **Exact** (bankkoppeling) | NIET vanuit Luxis pushen (FIN-4). Exact reconcilieert zelf; in Luxis handmatig afvinken. |
| Derdengelden | **Luxis** (mutaties/saldolijst CSV) | NOOIT naar kantoor-Exact — de stichting is een aparte rechtspersoon met eigen administratie. Luxis-exports zijn die administratie. Hooguit een aparte Exact-administratie voor de stichting, maar voor een eenpitter is de CSV genoeg. |

Status: module gebouwd en idempotent (sync-log), settings-UI aanwezig (`instellingen/exact-tab.tsx`), handmatige sync-knop, **geen live koppeling in productie** (0 connecties; triage #93/#94 bevestigde latente randgevallen). Activatie = sessie van ~½ dag mét Lisanne erbij (OAuth-login + journaal/GL-codes kiezen + proeffactuur).

## 6. Antwoord op "is het af?" + volgorde

**Architectuur: ja.** Drie boeken, juiste scheiding, gecontroleerde overgangen, juridische waarborgen. Beter dan BaseNet dit doet.

**Werkend voor Lisanne: bijna.** Vier dingen staan tussen "features bestaan" en "het werkt":

| # | Actie | Omvang | Waarom eerst |
|---|---|---|---|
| 1 | FIN-1 dichten (twee halve deuren) | klein (½ sessie) | Voorkomt dat de administraties úít elkaar lopen zodra Lisanne echt boekt |
| 2 | FIN-2 afwikkel-flow + sluit-guard | middel (1–1,5 sessie) | Maakt de keten bruikbaar zonder handleiding; tuchtrechtelijke talm-bescherming |
| 3 | Lisanne-vragen beantwoorden (fee-model + verrekenclausule + 2e bestuurder) | gesprek | Bepaalt BTW (FIN-5), paneel-defaults, en of verrekening überhaupt mag |
| 4 | Exact activeren (facturen-push only, FIN-4 eerst strippen) | ½ sessie mét Lisanne | Pas zinvol na 1–3; boekhouding volgt het proces, niet andersom |

FIN-3 (kantoorbank-import) en FIN-6/7: backlog, heroverwegen bij volume.

## Verwante documenten
- `docs/research/derdengelden-regels.md` — juridisch kader + Lisanne-vragen (S157)
- `docs/research/14-dagenbrief-advies.md` — H6-beslispunten (S157)
- `.audit/TRIAGE-S157.md` — #53/#54/#57/#58/#94 (BTW/credit-nota-cluster, latent)
