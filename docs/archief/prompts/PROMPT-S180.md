cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 180 — START OP FABLE: boekhoud-matching 90 cache-only betalingen

## Model + rol
**Start op Fable.** Onderzoek/redeneren, geen bouwsessie. In S179 zijn 56 gedateerde
betalingen geïmporteerd, maar BaseNet's eigen betaal-cache laat zien dat **90 zaken méér
betalingen hebben ontvangen zonder een gedateerd `IncassoBetalingAnders`-record** (19 daarvan
lopen nog, samen €33.161). Die zaken ogen nu té open in Luxis. De vraag: zijn die betalingen
alsnog betrouwbaar te herstellen uit de boekhoud-export, of is dat niet verantwoord?
Regel (`stabiliseren-boven-bouwen`): eerst toetsen of het écht kan en nodig is — soms is
"handmatig invoeren door Lisanne" het eerlijke antwoord. Cross-check tegen prod
(`verify-own-research`).

## Context laden bij start
Lees SESSION-NOTES.md (S179- + S178-entry) en `scripts/basenet/import_payments.py` (hoe
fase 1b nu koppelt: `_uid("case", incpincassoid)` + reconciliatie tegen `cachedpayments*`).

## Hoofdtaak — haalbaarheid boekhoud-matching
Bronnen in `Xml_02-07-2026_2400.zip` (lokaal, gitignored):
- `admin.genericbankline` (425) — velden `bedrag`/`datum`/`omschrijving` (VRIJE TEKST, geen
  incasso-nummer).
- `admin.cashbankline` (425) — `cblamount`/`cbldate`/`cbldescr`.
- `admin.payment.Payment` = `admin.payment` (237) — `amount`/`insertdate` (geen dossier-FK?).
- `admin.journal` (2954) + `MemorialLine`/`OutgoingInvoice*` — grootboek.

Beantwoord, gegrond op de echte data:
1. **Is er een betrouwbare koppel-sleutel** van een bankregel naar een dossier? (dossiernr
   IN1xxxxx of klantkenmerk in de omschrijving? factuurnummer → `OutgoingInvoice` → dossier?)
   Meet de dekkingsgraad op de 90 zaken: hoeveel matchen deterministisch, hoeveel alleen fuzzy,
   hoeveel helemaal niet.
2. **Klopt de som per zaak** met BaseNet's `cachedpayments*` (na aftrek van de bekende
   dubbeltelling klant+admin)? Zo niet → niet importeren.
3. **Verantwoord?** Fuzzy-gematchte betalingen op de verkeerde zaak boeken is erger dan een
   te-open saldo. Advies: welk deel is veilig automatisch te importeren, welk deel moet
   Lisanne handmatig doen (en op welke ~19 lopende zaken concreet).

## Verificatie / werkwijze
- Lezen, meten, redeneren — GEEN productiecode, GEEN prod-mutaties (read-only queries).
- Eindproduct: kort haalbaarheidsoordeel + (indien veilig) `PROMPT-S181.md` als Opus-
  bouwopdracht voor het deterministisch-koppelbare deel. Als de conclusie "handmatig door
  Lisanne" is: zeg dat, met de concrete lijst van 19 lopende zaken + bedragen.

## Parallel openstaand (livegang, niet deze sessie)
- Blok 1: werkvoorraad-recept met de 3 proefzaken (input Lisanne) → rest van de 372 in groepen.
- Blok 2: mail live (Arsalan: M365-mailbox incasso@ + BaseNet-doorstuur + MX).
- Blok 3: generale repetitie geldstromen (1 echt dossier A-Z) — geldmodules nooit met echt geld.
- Blok 5: parallel draaien 2-4 weken → BaseNet opzeggen.

## NIET doen
- Geen prod-mutaties. Geen fuzzy-import blind uitvoeren. Geen zips committen.
- D-Break buiten voorbeelden/tests (IN100555 = D-Break, met rust laten).

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-180`, PROMPT-S181.
