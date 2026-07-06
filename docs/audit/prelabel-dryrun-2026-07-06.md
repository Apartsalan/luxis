# Dry-run verweer-pre-labeler op de 102 prod-kandidaten — 6 juli 2026 (Fable)

**Vraag van Arsalan:** hoe gaat "Slim leren" werken voor de grote bak "Overig"-kandidaten?
Hoe weet Lisanne wat ze moet goedkeuren? Is hier goed over nagedacht?

**Aanpak:** alle 102 open kandidaten (94 overig) van prod gedumpt en de voorgestelde
13-types-woordenschat (audit S172 §5.c) er als trefwoord-regels droog op losgelaten
(`scratchpad/prelabel_test2.py`, niets gewijzigd aan prod).

## Kernbevinding 1 — de woordenschat klopt op echte data

Verdeling na pre-labeling (102 kandidaten):

| Type | aantal |
|---|---|
| afwikkeling_intrekking | 20 |
| **overig (restant)** | **15** |
| verlenging_opzegging | 12 |
| reeds_betaald_verrekening | 8 |
| betalingsregeling_schikking | 7 |
| consumentenbescherming_b2b | 6 |
| opschorting_tegenvordering | 6 |
| derde_partij | 5 |
| betwisting_ongemotiveerd | 5 |
| ncnp_gerechtelijke_fase | 5 |
| klacht_dienstverlening | 4 |
| vertegenwoordiging | 4 |
| av_toepasselijkheid | 3 |
| kosten_rente_hoogte | 2 |

85% krijgt een zinvol label; steekproef op de toewijzingen klopt (9.3-afwikkelingen,
verlenging/opzegging, 3:61-vertegenwoordiging, 6:74/reflexwerking allemaal correct
herkend). Dit spiegelt de audit-schatting goed.

## Kernbevinding 2 — VALKUIL: eerst geciteerde AV-blokken strippen

Eerste poging faalde stil: 22 kandidaten belandden in `betalingsregeling_schikking`
omdat het **geciteerde art. 9.3-blok** zelf de woorden "betalingsregeling treft" en
"schikking treft" bevat. De pre-labeler MOET dus eerst de geciteerde
voorwaarden-blokken (9.3 / 20.4 / NCNP-clausule / disclaimer) uit de tekst knippen en
alleen op Lisanne's **eigen** tekst matchen. Vangnet daarna: citeert de mail 9.3/20.4
maar matcht de eigen tekst nergens op → `afwikkeling_intrekking`.

**Voor de bouwer (S174 V3):** neem deze quote-stripping op in de pre-labeler; de
geteste regels + prioriteitsvolgorde staan in `scripts/prelabel_dryrun_s174.py`.

## Kernbevinding 3 — het restant "Overig" (15) is vooral WEGGOOI-materiaal

De 15 die overblijven zijn bijna allemaal korte procedurele mails ("stuur bijlage
opnieuw", "verwijs naar bijlage", "wie is cliënt?", "cliënte houdt vast aan de
vordering") — géén herbruikbare modelantwoorden. Advies aan Lisanne: deze groep in
bulk afwijzen op 2-3 na. "Overig" wordt daarmee wat het hoort te zijn: een kleine
restbak, geen zwart gat.

## Kernbevinding 4 — twee gaten die S174 nog niet dicht

1. **Geen type-matching bij het genereren.** `get_learned_examples` kiest op
   hoofdcategorie + spreiding over types, maar kijkt niet welk verweer de debiteur NU
   voert. Kleinste zinvolle fix: de bestaande AI-classificatie van inkomende mail ook
   een `defense_type` uit de 13 laten kiezen (één veld extra in de classificatie-prompt
   + kolom) en in `get_learned_examples` voorbeelden van dat type voorrang geven.
   Voorstel: als V4 na V3, klein werk, maakt de leer-loop pas écht "slim".
2. **Geen bron-context in het review-scherm.** Lisanne ziet alleen haar eigen oude
   tekst, niet op welke debiteur-mail/dossier het antwoord was (koppeling bestaat wél:
   `source_synced_email_id`/`source_case_id`). Eén linkje/uitklapblok toevoegen maakt
   beoordelen veel makkelijker.

## Status prod (6 juli 2026)

- 102 kandidaten open (94 overig, 7 annuleringskosten_9_3, 1 afrekening_20_4)
- 12 goedgekeurd (6 overig, 4 annuleringskosten_9_3, 2 verlengd_abonnement)
- 17 afgewezen (S173-schoonmaak)

## Wat Lisanne straks doet (na V3, beoogde werkwijze)

1. Open "Slim leren" — kandidaten staan per verweer-type gegroepeerd (13 groepen i.p.v.
   één bak van 94).
2. Per groep: lees de 2-5 kandidaten, keur de 1-2 sterkste goed (het zijn haar eigen
   teksten), wijs de rest in bulk af.
3. Restbak "Overig": vrijwel alles afwijzen.
4. Klaar in ±30-45 min. Niets goedkeuren is ook veilig: de AI valt dan terug op de 5
   vaste bibliotheek-teksten — goedkeuren voegt alleen toe, het kan niets kapotmaken.
