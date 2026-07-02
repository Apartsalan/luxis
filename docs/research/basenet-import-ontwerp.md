# BaseNet-import — onderzoek & ontwerp (S166)

**Datum:** 2 juli 2026 · **Status:** ontwerp, wacht op afstemming met Arsalan
**Bron-export:** `Xml_02-07-2026_2400.zip` (3,98 MB, BaseNet XML-backup van 2 juli 00:00)
**Doel:** BaseNet-data in Luxis krijgen, primair als voeding voor shadow-learning (Lisanne's echte verweer-antwoorden).

---

## 1. Wat er in de export zit

**Formaat:** 137 XML-bestanden, één per BaseNet-entiteit. Per record:
```xml
<rela.letter>
    <entityname>rela.letter</entityname>
    <systemid>529071024</systemid>
    <entrylist>
        <entry key="lesubject" value="..."/>
        ...
    </entrylist>
</rela.letter>
```
Let op: meerdere roots per bestand → **geen well-formed XML**; parsen met een simpele record-splitter (regex of iterparse met wrapper). Encoding UTF-8, entities ge-escaped (`&lt;` etc.). Grote bestanden zijn gechunkt (Letter.xml in 4 delen à 5000 records).

**Relevante entiteiten + tellingen:**

| BaseNet-bestand | Records | Wat | Relevant? |
|---|---|---|---|
| `advocatuur.entities.Incasso` | **607** | Incasso-dossiers, `inccode` = **IN**-nummer | ✅ KERN |
| `advocatuur.entities.Dossier` | 187 | Advocatuur-dossiers, `docode` = **D**-nummer | ❌ skip (afspraak Arsalan: alleen IN) |
| `rela.entities.Project` | 794 | Generieke dossier-container (607+187 = 794 ✓); projectvelden zitten al **embedded** in Incasso.xml (`pstatus`, `pdatestart`, `prcode`…) | (via Incasso) |
| `rela.entities.Company` | 815 | Bedrijven (rcode, naam, KvK, adres, email, tel) | ✅ |
| `rela.entities.Person` | 208 | Personen (firstname/lastname, titel, adres, geslacht) | ✅ |
| `rela.entities.Contact` | 145 | Contactpersonen bij bedrijven | ✅ (→ ContactLink) |
| `advocatuur.entities.IncassoLine` | **1.563** | Vorderingen per incasso: factuurnr, bedrag, verzend-/vervaldatum, berekende rente | ✅ |
| `advocatuur.entities.IncassoBetalingsRegeling` | ~180KB | Betalingsregelingen | ✅ (fase 1b/2) |
| `advocatuur.entities.IncassoBetalingAnders` | ~33KB | Betalingen buiten kantoor om | ✅ (fase 1b/2) |
| `rela.corres.Letter` (4 chunks) | **17.928** | Correspondentie-METADATA (zie §2) | ✅ KERN |
| Boekhouding (Journal, OutgoingInvoice…) | — | Gevoeligst, Exact blijft leidend | ❌ later/nooit (afspraak prompt) |

**Incasso-dossiers (607):** `pstatus`: **Lopend 372 · Wacht 69 · Gereed 148 · Geannuleerd 15 · Offerte 3**. Startjaar: 2024: 15 · 2025: 480 · 2026: 112. Velden o.a.: `inccode` (IN100000), `incwederid` (→ relatie-systemid wederpartij), `prcode` (→ rcode opdrachtgever), `pscode` ("Opdrachtgever / Debiteur"-label), `incinteresttype`/`incinterest`, `incincassocost` (BIK), `inckenmerkclient` (**cliënt-kenmerk! relevant voor backlog #1**), `cachedhoofdsom`, `cachedpayments*`, `pdatestart`/`pdateend`, `prtype` (B/P → debtor_type!… verifiëren: prtype lijkt type opdrachtgever, wederpartij-type via relatie).

**Correspondentie (Letters):** metadata per stuk: `lesubject`, `ledate`, `leinout`, `lepcode` (dossiercode!), `lefrom`/`leemail`/`lecc`/`lebcc`, `lemimetype`, `leoriginalfilename`, `lesize`, `documentstore_id`. Richting gedecodeerd (empirisch, via afzender-correlatie):
- `leinout=3` = **uitgaande e-mail** (5.912/5.913 afzender kestinglegal)
- `leinout=4` = **inkomende e-mail** (6.368)
- `leinout=6/11/1/2/5` = documenten/uploads/brieven (geen e-mail)

**Op IN-dossiers:** 3.308 uitgaande + 3.115 inkomende e-mails. Totaal e-mails in export: 12.620.

## 2. ⛔ KERNBEVINDING: de teksten ontbreken

De zip bevat **alleen metadata**. Alle 17.928 correspondentie-stukken (samen **11,51 GB**, waaronder alle .eml-e-mailbestanden) verwijzen naar een `documentstore_id` in BaseNet's documentopslag — die zit NIET in deze zip (`leremarks` overal leeg, geen body-veld). De bestandsnaam "Xml_…" + het `BackupXmlTask`-record bevestigen: dit is het **database-deel** van BaseNet's backup; documenten zijn een apart deel.

**Gevolg:** relaties, dossiers en vorderingen kunnen NU geïmporteerd worden; het shadow-learning-doel (leren van Lisanne's e-mailteksten) is **geblokkeerd tot de documenten-export er is**.

**Actie Arsalan:** in BaseNet (Onderhoud/Beheer → Backup) naast de XML-backup ook de **documenten-backup** aanvragen/downloaden. Verwacht: meerdere zips met bestanden op documentstore_id/pad. Alleen de IN-dossier-e-mails zijn strikt nodig (~6.400 .eml-bestanden), maar de download is waarschijnlijk alles-of-niets (11,5 GB).

## 3. Doelmapping BaseNet → Luxis

### Fase 1 — relaties + dossiers + vorderingen (kan nu, zonder documenten)

| BaseNet | Luxis | Opmerkingen |
|---|---|---|
| Company (`company`, `kvk_nummer`, `email`, `tel1`, `o*`/`m*`-adres) | `contacts` (contact_type='company', name, kvk_number, email, phone, visit_*/postal_*) | dedupe: zie beslispunt B |
| Person (`firstname`/`lastname`, `title`, `saluation`, `sex`, adres) | `contacts` (contact_type='person', first_name, last_name, salutation) | |
| Contact (contactpersoon bij bedrijf) | `contacts` (person) + `contact_links` (role_at_company) | |
| Incasso (`inccode`, `prcode`→client, `incwederid`→opposing, `pdatestart`, `pstatus`, rente/BIK-velden, `inckenmerkclient`) | `cases` (case_number=**IN-code**, client_id, opposing_party_id, date_opened, status, interest_type, bik_override, reference=inckenmerkclient) | statusmapping + pipeline: beslispunt C |
| IncassoLine (`inclinvnr`, `inclamount`, `inclsenddate`, `inclduedate`) | case-vorderingen (claims) | som(inclamount) ≡ `cachedhoofdsom` → dry-run-check |
| BetalingsRegeling / BetalingAnders | betalingen/notities op case | fase 1b, na kern |

- **ID-mapping:** tabel `basenet_import_map` (entity, basenet_systemid, basenet_code, luxis_id) — nodig voor idempotentie én om in fase 2 Letters aan cases te koppelen.
- **Import-runner:** script met `--dry-run` (rapport: verwacht vs te schrijven, per entiteit, incl. overlap-detectie met bestaande prod-data en financiële checks) en `--execute` (transactioneel).
- **Rente-instellingen:** `incinteresttype`-codes moeten gedecodeerd (8 = ? → steekproef tegen BaseNet-UI of afleiden uit incinterest-percentage); bij twijfel → wettelijke rente + flag in dry-run-rapport.

### Fase 2 — correspondentie (zodra documenten-export binnen is)
- .eml parsen (Python `email`-module) → `synced_emails`: direction uit `leinout`, body_html/body_text uit .eml, from/to/cc uit headers, `email_date` = ledate, `provider_message_id` = `basenet:{systemid}` (dedup), case via lepcode→import_map.
- **`email_account_id` is NOT NULL** → speciaal import-account (provider `import`, sync uit) of koppelen aan Lisanne's bestaande account — verifiëren dat de 5-min-sync-scheduler zo'n account overslaat.
- Alleen Letters met `lepcode` beginnend met `IN`. PDF's/Word-documenten: later/optioneel (niet nodig voor shadow-learning).

### Fase 3 — classificatie + backfill (het leer-doel)
De backfill-keten (`learned_answers.backfill_learned_answers`) eist per uitgaande mail:
1. outbound SyncedEmail met case_id, body, geen bounce, geen sjabloon/`XXX`, ≥40 tekens na opschonen;
2. de **recentste INBOUND mail op dat dossier vóór de verzenddatum** heeft een `EmailClassification` met category ∈ (`juridisch_verweer`, `betwisting`).

Geïmporteerde oude mails hebben géén classificaties → **gerichte AI-classificatie nodig**: eerst outbound-mails filteren (sjabloon-filter + lengte), dan alléén de bijbehorende voorafgaande inbound-mails classificeren (≤3.115, verwacht flink minder). Kostenraming vooraf + go van Arsalan (memory: cost-vs-kwaliteit).
Daarna: backfill draaien → dashboard "Slim leren" → **steekproef of geleerde teksten écht weerleggingen zijn**.

## 4. Beslispunten — BESLOTEN (Arsalan, 2 juli 2026)

- **A. Documenten-export** — ✅ Arsalan vraagt in BaseNet **"Documenten per project van alle medewerkers"** aan (mapstructuur = dossiercode → betrouwbare koppeling). ~11,5 GB, download loopt parallel aan fase 1.
- **B. Relatie-scope** — ✅ **ALLES importeren** (besluit Arsalan): er zijn maar een paar leveranciers en die staan ook in dossiernamen. Opdrachtgevers zijn o.a.: Incassocenter, INC Zakelijk, Invorderingsbedrijf, CM Zakelijk, Collect 1, The Collection Company, Legalwork, SYN Finance 1. `rinactive=true` → `is_active=false`.
- **C. Dossier-status** — ✅ **Passief archief** (akkoord): status gesloten/geen pipeline-stap, automatisering raakt de geïmporteerde dossiers niet. Activeren kan later per dossier.
- **D. Dossiernummers** — ✅ **BaseNet IN-code als `case_number`** (akkoord): herkenbaar, er zijn al betalingen binnengekomen onder die nummers, en e-mail-dossiernummer-matching herkent ze vanzelf. Luxis-nieuwe zaken blijven 2026-xxxxx.

## 5. Premortem (top-faalmodi)

1. **Dubbele data in prod.** Luxis-prod heeft al ~48 dossiers + ~44 relaties (deels dezelfde: Incassocenter-zaken!). Blind importeren → dubbele Incassocenter B.V., dubbel dossier voor dezelfde vordering. → Dry-run rapporteert overlap (naam/e-mail/KvK-match voor relaties; wederpartij+bedrag/kenmerk voor dossiers); per overlap beslissing (koppelen i.p.v. aanmaken).
2. **Import triggert automatisering.** Geïmporteerde open dossiers met pipeline-stap → scheduler genereert taken/sommaties op oude zaken; e-mail-import triggert classificatie-hook of notificaties. → Import als archief (C), e-mails via direct DB-insert zonder de sync-hooks, verifiëren dat backfill de enige consument is; alles eerst op lokale kopie.
3. **Financiële drift.** BaseNet-rente (berekend) ≠ Luxis-rente (eigen rekenkern) → verwarring over openstaand saldo. → Dossiers als archief importeren (geen live herberekening nodig); dry-run checkt som(IncassoLine) vs `cachedhoofdsom` per dossier en rapporteert afwijkingen; open dossiers pas activeren na expliciete financiële afstemming per dossier.

## 6. Volgorde van bouwen (Opus-stap, na akkoord)

1. Generieke BaseNet-XML-parser (`scripts/basenet/parse.py`) + pytest op echte samples
2. Migratie `basenet_import_map`
3. Import-runner relaties (dry-run → rapport → execute op lokale kopie → prod)
4. Import-runner dossiers + vorderingen (idem, met financiële checks)
5. [wacht op documenten-export] .eml-import → synced_emails
6. Gerichte classificatie (kostenraming eerst) → backfill → steekproef-verificatie
