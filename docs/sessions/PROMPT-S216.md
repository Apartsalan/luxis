cd Documents\luxis && claude --dangerously-skip-permissions

## STAND (15 juli, Opus) — BLOK 1 IS LIVE + GEVERIFIEERD
Commits `4dba5b3` (tabbladen) + `4ef4c0a` (inklappen), frontend gedeployd. Gedaan:
- 11/8 → 7/6 tabbladen; tabbalk past nu (0px overflow, was 5 buiten beeld).
- Financieel bundelt vorderingen+betalingen+regeling+derdengelden; lege regeling/derdengelden
  ingeklapt tot 1 regel (open-klik bewezen). Provisie → Facturen. Tijdlijn = Activiteiten +
  inklapbare stap-historie. Taken + conflictbanner op Overzicht. PartijenTab verwijderd.
- Vertaaltabel oude ?tab= getest op prod (betalingen→Financieel, staphistorie→Tijdlijn,
  partijen→Overzicht ✓). Incasso 7 tabs / advies 6 tabs (geen Financieel) beide geverifieerd.
  Klik-inventaris: alle partij-links + actieknoppen + factuurlink behouden.
**Nog open in blok 1 (bewust uitgesteld):** anker-subnav bovenin Financieel
(Vorderingen · Betalingen · Regeling) — kleinere winst nu de secties al gegroepeerd + inklapbaar.

## BLOK 2 IS OOK LIVE + GEVERIFIEERD (commit `3a927fc`, gedeployd)
- Kop: 4 statkaarten → compacte geldstrook Hoofdsom · Betaald · **Openstaand** (ontbrak eerder;
  geverifieerd IN100215 = €1.891,40 incl. rente/BIK). Kop past nu boven de vouw.
- Notitie + Telefoonnotitie → één venster `NoteDialog` (autoFocus → **cursor-bug gefixt**,
  live bewezen: `cursorInEditor:true`). Sneltoets `n` opent het venster. `phoneNoteText`-plumbing weg.
- BaseNet-waarschuwing (`[BaseNet-waarschuwing]`) → oranje balk bovenaan Overzicht
  (`BasenetWarningBanner`, parser geëxporteerd). Bewijs: IN100022 toont "PROCEDEREN …".
- Zijbalk type-afhankelijk: Debiteur/Rente alleen incasso (advies-lek dicht, bewezen op verse
  advieszaak: beide weg), OHW alleen bij uren>0.
**Next = BLOK 3 (S217, normale zaak):** agenda-blok op Overzicht (komende afspraken/zittingen van
dit dossier; `calendar_events` heeft case-koppeling), "Volgende stap"-regel in de kop (eerstvolgende
open taak+deadline i.p.v. incasso-fasebalk), geldstrook per type voor normale zaak (OHW ·
ongefactureerd · openstaand · budget — bronnen bestaan al). + evt. anker-subnav Financieel.
Plan: `docs/plans/PLAN-dossierpagina.md` §2 (tabel per type).

---

Sessie 216 — Dossierpagina 2.0, blok 1 (+2 als de sessie het toelaat)

## Start
Draai eerst `/sessie-start`. Ga daarna zonder te wachten door met de taak hieronder.
**Lees verplicht:** `docs/plans/PLAN-dossierpagina.md` — het volledige ontwerp (S215, Fable),
inclusief de 4 harde eisen van Arsalan en de klik-inventaris-verificatie. Dit prompt-bestand is
alleen de opdracht; het plan is de waarheid.

## Model
Dit is **bouwen → Opus**. Review daarna = Fable (apart moment, Arsalan zet om).

## Hoofdtaak — Blok 1: tabbladen (beide zaaktypes)
Van 11 (incasso) / 8 (normaal) naar 7 / 6 tabbladen volgens plan §2:
1. Nieuwe tablijst: Overzicht · Financieel (alleen incasso) · Facturen · Documenten ·
   Correspondentie · Uren · Tijdlijn.
2. Financieel = Vorderingen + Financieel + Betalingen + Regeling + Derdengelden met anker-subnav;
   lege secties ingeklapt (één regel + chevron, klik opent — NOOIT onzichtbaar).
   Provisie/"Facturatie-instellingen" → Facturen-tab.
3. Tijdlijn = huidige Activiteiten + staphistorie-filter (incasso).
4. Taken-tab → volledig takenblok op Overzicht (niets van de functionaliteit kwijt).
5. Partijen-tab opheffen; **conflictcontrole verhuist naar een banner op Overzicht** (zit nu ALLEEN
   in PartijenTab — niet vergeten, anders verlies je stil de conflictcheck-weergave).
6. ?tab=-vertaaltabel (6 oude waarden) + sneltoetsen bijwerken (plan §2 "Niet stuk laten gaan").

Blok 2 (kop + notitie-dialoog + waarschuwingsbanner + zijbalk) alleen starten als blok 1 af én
geverifieerd is. Blok 3 (normale zaak: agenda-blok, volgende-stap, geldstrook) = S217.

## Verificatie (plan §4 — vóór "klaar")
tsc + Playwright-doorklik op prod (IN100215 + verse advies-testzaak, daarna verwijderen) +
**klik-inventaris oud→nieuw afvinken** + vouw-check 1280×720 + alle 6 oude ?tab=-links.

## Constraints
- Harde eisen plan §0: alles klikbaar blijft klikbaar; één stijl beide types; niets onzichtbaar;
  Uren blijft volwaardig tabblad.
- Geen backend-wijzigingen verwacht; geen migraties. Mailslot: niets versturen.
- Geen `git add -A`; expliciete paden. Commit + push per afgerond onderdeel, deploy frontend via SSH.

## Los draadje (alleen melden, niet oppakken)
KvK-sleutel (PROMPT-S215) is er nog niet — als Arsalan hem meldt heeft dát voorrang
(726 kandidaten, ~€14,50 per run, dry-run kost óók geld; zie PROMPT-S215).

Werk af met `/sessie-einde`.
