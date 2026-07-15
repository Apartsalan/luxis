cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 219 — Onderzoek demolijst (Fable) — alle demo-punten van 15 juli uitpuzzelen

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context: **`docs/sessions/DEMOLIJST-S218.md`** — dé lijst met 25 demo-punten,
inclusief wat in S218 al onderzocht/beantwoord is (punten 1, 2, 3, 13, 15, 16). Lees die eerst.

## ⚠️ Voorrang-check EERST
Vraag Arsalan: **is de KvK-productiesleutel binnen?** (contractdocumenten kwamen 15 juli
al binnen per mail). JA → eerst de rechtsvorm-backfill (draaiboek in
`docs/sessions/PROMPT-S217.md`), daarna dit onderzoek.

## Taak — onderzoek, GEEN bouwwerk
Dit is een onderzoekssessie (model: Fable). Doel: elk nog-niet-onderzocht punt van de
demolijst tot op de bodem uitzoeken zodat de bouwsessie (S220, Opus) een dichtgetimmerd
draaiboek heeft. Werk de demolijst zelf bij met de bevindingen (status per punt).

**Spelregels uit de demolijst gelden:** elk punt breed checken (alle routes/schermen waar
hetzelfde kan spelen); sjabloon-punten gelden voor ALLE sjablonen (AI + vast), stuk voor stuk.

### Blok 1 — Sjablonen-audit (punten 5 t/m 12) — grootste klus
Loop élk sjabloon na (alle e-mailsjablonen uit de compose-lijst + alle vaste
DOCX-sjablonen) op élk van deze punten: oud adres (Ijsbaanpad), handtekening
(Incasso@kestinglegal.nl), aanhef aanwezig en zónder BV-naam, klant-kenmerk waar het niet
hoort, spaties/lettertype-uniformiteit, onderwerpformaat (klant/debiteur — sommatie tot
betaling — dossiernummer). Maak een matrix sjabloon × punt met goed/fout + vindplaats.
Render waar mogelijk écht (testdossier, niet versturen — mailslot staat OPEN).
Referentie: `SOMMATIE TOT BETALING _  _ voorbeel voor handtekening.eml` (projectmap) en
`CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf` (juiste verzoekschrift-PDF).

### Blok 2 — AI-keten (punten 19, 20, 21, 24)
- Meet waar de tijd zit: classificatie (planner zegt elke 6 min), conceptgeneratie
  (welk model, hoeveel tokens, hoe lang), en de klik-keten kwalificeren→goedkeuren→overzicht.
- Punt 21 (nietszeggend antwoord op "wie zijn jullie / wie is de klant" — IN100607):
  haal het concept + de bron-mail erbij, stel vast wat de prompt aan context mist
  (klantnaam, facturen) en ontwerp de prompt-/context-fix.
- Ontwerp: hoe wordt de keten "continu automatisch" zonder kwaliteitsverlies + minder klikken.

### Blok 3 — Fasebalk + concurrentie (punt 14)
IN100410 nameten (waarom staat er gerechtelijk/regeling terwijl alleen minnelijk overleg
was); uitzoeken hoe Clio/Smokeball/PracticePanther e.d. de zaakstatus/fase tonen; voorstel
maken (echte status i.p.v. vijf vaste fasen).

### Blok 4 — Kleinere punten doorlichten
- Punt 4: waarom doen CC/BCC het niet in het AI-concept-verstuurscherm (BCC ontbreekt, CC faalt).
- Punt 17/18: mail-preview vanuit tijdlijn + klikbaar zaaknummer vanuit Mail — bestaande
  bouwstenen inventariseren (preview bestaat al op de Mail-pagina?).
- Punt 23: taken terugdraaien — waar de overgeslagen taak van IN100607 ("urgent: escalatie-
  e-mail beoordelen") vandaan kwam + hoe een terugdraai-knop past in het takenmodel.
- Punt 16: beslismemo b2b/b2c voor Lisanne afmaken (105 zaken; raakt WIK/14-dagenbrief-route).
- Punt 15-inconsistentie: 7 vs 4 dagen (Eerste→Tweede) — voorstel welke wint.

### Afronding
- Demolijst bijwerken met alle bevindingen (status per punt: oorzaak + fixrichting).
- `PROMPT-S220.md` schrijven: de bouwsessie (Opus) met een geordend bouwdraaiboek —
  inclusief punt 25 (rentebijlage AI-concept-route, ontwerp staat in SESSION-NOTES S218)
  en de fixrichting van punt 13 (zombie-adviezen opruimen bij stap-wissel).
  De niet-uitgevoerde UX-sprint-punten uit `docs/sessions/PROMPT-S218.md` (follow-up
  sorteren/linken, dagen-kolom, intake ont-dubbelen, Bankimport-naam, rapportage-label,
  agenda-lege-staat, soft-delete-banner) daarin meenemen — overlap met de demolijst ontdubbelen.

## Verificatie
Onderzoek = meten in de bron (prod-DB read-only, echte renders, live API met eigen login).
Geen prod-mutaties, niets versturen, mailslot NIET aanraken. Geen deploys nodig.

## Constraints (wat NIET doen)
- NIETS bouwen of fixen — alleen onderzoeken en vastleggen (bouw = S220, Opus).
- Geen mails versturen, ook geen "testjes" — mailslot staat OPEN.
- De 12 échte follow-up-aanbevelingen niet uitvoeren/afwijzen (beoordeling = Arsalan/Lisanne).
- Geen nieuwe afhankelijkheden.

## Commit
Docs-wijzigingen committen + pushen (expliciete paden, NOOIT `git add -A`).
Sluit af met `/sessie-einde`.
