cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 181 — werkvoorraad-heropening (blok 1 livegang) — pas starten mét input

> **S181-F (7 juli, Fable-heropeningsaudit) is GEDAAN — lees eerst:**
> `RAPPORT-S181F-heropeningsaudit.md` (bevindingen C1-C9) +
> `S181-werkvoorraad-recept.csv` (alle 372 zaken met voorgestelde stap + vlaggen) +
> `LISANNE-A4-heropening.md` (de 3 vragen aan Lisanne, klaar om te sturen).
> Kern: heropenen is veilig (niets verstuurt vanzelf, vlag uit), maar vóór de
> auto-draft-vlag ooit aangaat: dubbele timeout-regel fixen (C3) en creditfactuur-rente
> beslissen (C1, −€2.781 over 32 zaken). Adviesgroep 1: LegalWork B.V. (15 zaken).

## Model + rol
**Opus** (data-actie, geen nieuwbouw). De betalingen zijn sinds S180 COMPLEET (255 op de
135 zaken die BaseNet kende) — er is geen machine-bouwwerk meer nodig vóór de heropening.
Deze sessie draait op **input van mensen**; zonder die input: niet gissen, aan Arsalan
vragen wat er al ligt.

## Benodigde input (checklist bij start)
1. **Lisanne's oordeel over de 3 proefzaken** (IN100215/IN100040/IN100521): loopt de
   proef goed genoeg om een eerste groep te heropenen? Welke pijplijnstap per zaak?
2. **Bevestiging 8 feitelijk-voldane "Lopend"-zaken** (S180-bijvangst): IN100256,
   IN100210, IN100166, IN100197, IN100547, IN100334, IN100456, IN100457 — afsluiten
   bevestigen i.p.v. heropenen.
3. Welke eerste groep heropenen (voorstel: per opdrachtgever, klein beginnen).

## Context laden bij start
Gebruik de `luxis-researcher` subagent: "Lees SESSION-NOTES.md (S180+S178) en
LUXIS-ROADMAP.md-kop. Vat samen: livegang-blokken, recept-aanpak, de 8-voldaan-lijst."

## Taak (zodra input er is)
- Heropenen per groep zoals S175b het deed (status via SQL want 'afgesloten' is terminal;
  `date_closed` NULL; toewijzen aan Lisanne) — nu MÉT pijplijnstap (deadline checken!)
  omdat de proef geslaagd is. Automatisering gaat dan aan voor die zaken: batch/followup
  filtert op `incasso_step_id IS NOT NULL` — bewuste keuze, benoem het expliciet.
- Betalingsregeling-zaken (13, o.a. IN100019 termijn 9 juli): regeling-bewaking loopt al;
  bij heropening géén aanmaan-stap zetten zolang de regeling loopt.
- Saldi hoeven NIET geverifieerd per zaak (betalingen compleet + exact-match-slot);
  steekproef van 3 in de UI volstaat.

## Parallel (mensen)
- Mail live: Arsalan maakt M365-mailbox incasso@kestinglegal.nl + BaseNet-doorstuurregel.
- Generale repetitie geldstromen: 1 echt dossier A-Z (bankimport → 6:44 → derdengeld →
  doorbetalen → afwikkelen → factuur) — plannen mét Arsalan.

## NIET doen
- Geen nieuwbouw ("stabiliseren-boven-bouwen"). Geen heropening zonder Lisanne's input.
- D-Break buiten alles (IN100555 blijft dicht). Geen zips committen.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-181`, PROMPT-S182.
