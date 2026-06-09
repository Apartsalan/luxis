# Derdengelden — regels, industriestandaard en hoe Luxis het implementeert

*Onderzoek sessie 157 (9 juni 2026). Drie sporen: juridisch (primaire bronnen), concurrenten (Clio/Smokeball/Actionstep/LEAP/BaseNet/Kleos), code-audit Luxis.*

---

## 1. Juridisch kader (VERPLICHT)

Kernregeling: **afdeling 6.5 Verordening op de advocatuur (Voda), art. 6.19–6.23.**
Modellen staan in de Regeling op de advocatuur (Roda, art. 33-34, bijlagen 5-6).

| Regel | Bron | Wat het betekent voor software |
|---|---|---|
| Derdengelden gaan rechtstreeks naar rechthebbende óf naar de stichtingsrekening | art. 6.19 lid 1 | Debiteur-betalingen komen binnen op de stichtingsrekening (bankimport) |
| Administratie: bedrag, datum + wijze van ontvangst, datum overmaking, begunstigde, behandelend advocaat | art. 6.19 lid 2 | Velden op `trust_transactions` + mutatie-export |
| Doorbetalen "zodra de gelegenheid zich voordoet" / "onverwijld" na opdracht | art. 6.19 lid 2 / 6.23 | Talmen is tuchtrechtelijk riskant — saldo-ouderdom in de gaten houden |
| Derdengelden nooit als zekerheid (ook niet voor eigen honorarium) | art. 6.19 lid 4 | Geen "vasthouden tot factuur betaald is" |
| Verrekening met eigen declaratie alleen met expliciete schriftelijke instemming; bevestiging achteraf per verrekening; vervalt bij betwisting | art. 6.19 lid 5 | Consent-velden verplicht + automatische bevestigingstaak na elke verrekening |
| Stichting derdengelden verplicht ter beschikking (vrijstelling mogelijk, zie §3) | art. 6.21 | — |
| **Vertegenwoordiging door twee gezamenlijk handelende bestuursleden, van wie ten minste één advocaat** | art. 6.22 lid 8 | Vier-ogen op elke uitbetaling is een wettelijke eis, geen feature |
| Tweede bestuurder mag geen eigen ondergeschikte/kantoormedewerker zijn | art. 6.22 lid 6 | Eenpitter: tweede bestuurder is extern (collega-advocaat, accountant) |
| Boekhouding zodanig dat rechten/verplichtingen "te allen tijde" kenbaar zijn | art. 6.5 | Saldolijst per peildatum + mutatie-export |
| Bewaartermijn administratie | art. 2:10 BW / 52 AWR | 7 jaar |

### Rente en kosten
Rentedragend uitzetten is sinds 2017 niet meer verplicht; rente (positief én negatief)
komt de rechthebbende toe; bank-/transactiekosten mag de stichting inhouden (modelniveau).

### Toezicht
Deken (art. 45a Advocatenwet) + unit FTA. Jaarlijkse CCV-vragenlijst bevat vragen over
derdengeldrekening en stichting; periodieke kantoorbezoeken controleren het beheer.
De mutatie- en saldolijst-exports in Luxis zijn hierop gericht.

## 2. Eenpitter-specifiek (Kesting Legal)

- **Vrijstelling mogelijk** (art. 6.21 lid 2): wie geen derdengelden ontvangt hoeft geen
  stichting — wel schriftelijk melden aan de deken én publiekelijk kenbaar maken.
  Voor een incassopraktijk niet realistisch: geïncasseerde bedragen zíjn derdengelden.
- Derdengelden op de kantoorrekening ontvangen is **onder geen enkele omstandigheid**
  toegestaan; per abuis ontvangen geld direct doorstorten.
- Vier-ogen bij een eenpitter: de twee stichtingsbestuurders autoriseren elke betaling
  **bij de bank** (tweehandtekeningen-regime). In Luxis is self-approval daarom bij
  1 actieve gebruiker toegestaan (instelling, default aan) — de wettelijke autorisatie
  vindt dan plaats op bankniveau. Bij 2+ actieve gebruikers dwingt Luxis vier-ogen
  altijd af (instelling wordt genegeerd).

### Incasso-geldstroom
Door debiteuren betaalde bedragen zijn derdengelden **van de cliënt**. Doorbetalen
minus provisie = verrekening ex art. 6.19 lid 5: vereist vooraf expliciete (generieke
mag, sinds 2017) schriftelijke instemming + onderliggende declaratie + schriftelijke
bevestiging per verrekening. Zonder instemming: volledig doorbetalen, apart declareren.

## 3. Industriestandaard (concurrent-onderzoek)

Acht minimale waarborgen die elk serieus pakket heeft, met Luxis-status na sessie 157:

| # | Waarborg | Luxis |
|---|---|---|
| 1 | Sub-ledger per dossier/cliënt die optelt tot het banksaldo | ✅ saldo per dossier + cliënt-overzicht |
| 2 | Harde negatief-saldo-blokkade | ✅ bij aanmaken én goedkeuren én storno |
| 3 | Verrekening alleen tegen definitieve factuur, gecapt op saldo | ✅ status-check + saldo-cap + consent |
| 4 | Boeken vóór bankoverboeking (SEPA-export na approval) | ✅ |
| 5 | Geen edits/deletes — alleen storno's met audit trail | ✅ sinds S157 (reversal-mechanisme) |
| 6 | Reconciliatie bank vs boek | ◐ saldolijst + mutaties; geen three-way module (bewust — eenpitter) |
| 7 | Bankimport met review-wachtrij, duplicaat-exclusie, handmatig koppelen | ✅ sinds S157 (dedup + Ongekoppeld-tab) |
| 8 | Rollen/permissies op uitbetalingen | ✅ vier-ogen + tenant-setting |

Bewust niet gebouwd (enterprise, niet nodig voor doelgroep): three-way-reconciliation-
module, protected funds/earmarking, AML-blokkades, multi-trustrekening, rente-administratie.

## 4. Luxis-implementatie (stand na sessie 157)

- **Module:** `backend/app/trust_funds/` + bankimport in `backend/app/ai_agent/payment_matching_*`
- **Storno:** `reverse_transaction()` — tegenboeking type `reversal`, origineel krijgt
  `reversed_by_id`. Storting-storno direct (met saldo-guard); debit-storno via vier-ogen.
  Verrekening-storno draait ook de factuurbetaling terug.
- **Bankimport:** dedup op IBAN+Volgnr (fallback inhouds-hash), overbetaling gecapt op
  openstaand (overschot blijft als saldo zichtbaar), bulk-verwerking per-match atomair.
- **Vier-ogen (H14):** `tenants.trust_allow_self_approval`; 2+ actieve gebruikers ⇒ altijd strikt.
- **Verrekening-bevestiging:** na finale goedkeuring automatisch taak "Bevestiging
  verrekening … aan cliënt sturen" (art. 6.19 lid 5).
- **Rapportages:** `/api/trust-funds/reports/mutaties.csv` + `saldolijst.csv` (NOvA/deken).

## 5. Openstaande vragen voor Lisanne

1. Heeft Kesting Legal een eigen stichting derdengelden, en wie is de **tweede bestuurder**?
   Wil ze die als goedkeurder in Luxis (dan vier-ogen in de app i.p.v. alleen bij de bank)?
2. Staat in de opdrachtbevestiging een **expliciete verrekenclausule** (geïncasseerd geld
   verrekenen met declaratie)? Zonder die clausule: volledig doorbetalen + apart factureren.
3. Bevestigen dat debiteuren **op de stichtingsrekening** betalen (briefpapier/templates
   vermelden het juiste IBAN — gekoppeld aan H7/H26 kantoor-IBAN-instellingen).

## Bronnen

- Voda art. 6.19 / 6.22: maxius.nl/verordening-op-de-advocatuur/artikel6.19 en .22
- NOvA — stichting derdengelden (modelstatuten 2023): advocatenorde.nl/praktijkuitoefening/voor-uw-praktijk-1/stichting-derdengelden-1
- NOvA Q&A wijzigingen derdengelden (2017): advocatenorde-middennederland.nl/40635
- D. de Wolff, *Ars Aequi* nov. 2021 (vier-ogen bevestigd): pure.uva.nl/ws/files/70399236/AA20211100.pdf
- LOTA/unit FTA — CCV: toezichtadvocatuur.nl/toezicht/centrale-controle-verordening-ccv
- Regelgeving NOvA art. 6.23: regelgeving.advocatenorde.nl/content/artikel-623-bestuurder-stichting-derdengelden
- Wijzigingsregeling derdengelden, Stcrt. 2016, 68605
- Concurrenten: Clio Trust Account Management, Smokeball Trust Accounting Overview,
  Actionstep Trust Accounting, LEAP Trust-to-Office flow, BaseNet handleiding
  derdengeldenadministratie (URL's in sessietranscript S157)
