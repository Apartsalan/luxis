# Sessieprompt S176 — Livegang-spoor: proefzaken + Lisanne's beoordeling

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Opus** (uitvoering, klein werk). Lees vooraf: `docs/ARCHITECTUUR-KAART.md` + de
S174/S175/S175b-entries in `SESSION-NOTES.md` (S175b = het livegang-plan in 5 blokken!).

## Status na S175+S175b (6 juli 2026)
Review S174 → **GO** (must-fix cap→200 live, commit `5fa4592`). Daarna livegang-koers
bepaald (zie S175b-entry): Lisanne heeft een eigen account (lisanne@kestinglegal.nl, rol
advocaat) en **3 proefzaken staan open op haar naam** (IN100215, IN100040, IN100521 —
status 'nieuw', GEEN pijplijnstap = geen automatisering, saldi nog NIET gecorrigeerd,
PROEFZAAK-notitie in het dossier). Geen open bugs.

## Hoofdtaak — livegang-spoor, afhankelijk van waar Arsalan mee komt

### Spoor 0 (meest waarschijnlijk): proefzaken afmaken
1. Arsalan/Lisanne leveren per proefzaak: loopt nog? / wat is al betaald? / welke fase?
2. Zet per zaak: juiste status + pijplijnstap + corrigeer het openstaande saldo
   (betaling registreren met datum uit BaseNet). LET OP: pijplijnstap zetten = automatisering
   AAN voor die zaak — check de stap-deadline vóór je 'm zet (geen onbedoelde batch-mail).
3. Vergelijk zij-aan-zij met BaseNet (bedrag, volgende actie) en laat Lisanne bevestigen.
4. Mail-blok: als Arsalan de M365-mailbox incasso@kestinglegal.nl heeft aangemaakt +
   BaseNet-doorstuur staat → Lisanne koppelen via Instellingen → E-mail, teststuur.
5. Werkt de proef → recept vastleggen voor de overige ~370 (incl. fase 1b betalingen-import).

### Spoor A: Lisanne's beoordeling is (deels) gedaan → resultaat verwerken
1. Check de uitkomst: `SELECT status, defense_type, count(*) FROM learned_answers GROUP BY 1,2;`
2. Steekproef 3-5 nieuw goedgekeurde teksten op PII (namen/bedragen — moet `[bedrag]` zijn).
3. Genereer een testconcept op een verweer-dossier waarvan de nieuwste inbound een
   `defense_type` heeft → verifieer in de log/use_count dat het MATCHENDE type vooraan gaat.
   (Let op: testartefacten opruimen — draft verwijderen, use_count terugzetten.)
4. Rapporteer aan Arsalan: hoeveel goedgekeurd per type, welke groepen leeg bleven.

### Spoor B: K2-meting — GESCHRAPT (besluit Arsalan + Fable, 6 juli 2026, ná S175)
De met/zonder-uitsplitsing van de edit-rate is onderzocht en bewust NIET gebouwd:
(1) volumes zijn te klein — gesplitst duurt het maanden voor het cijfer iets zegt;
(2) zodra Lisanne's goedkeuringen live zijn krijgt vrijwel elk verweer-concept voorbeelden
mee → geen eerlijke "zonder"-groep meer; (3) de bestaande edit-rate-meting (S160, in
"Slim leren") toont de trend over tijd al. NIET alsnog bouwen zonder nieuw gesprek met
Arsalan — stabiliseren gaat vóór bijbouwen. Onderzoeksdetail: S175-entry SESSION-NOTES.

## Openstaand (achtergrond, alleen op verzoek)
- Consolidatie 3→minder draft-services (opruimklus, latere sprint).
- `language`-parameter in `get_learned_examples` is dood — meenemen bij die opruimklus.
- V4.3 (type-voorrang statische `DEFENSE_EXAMPLES`) bewust niet gebouwd — alle 5 passen
  binnen de cap, geen inhoudelijk effect.
- Unipile-key-rotatie (Recruit) staat los van Luxis — negeren.

## NIET doen
- Geen her-classificatie van oude mails (kost AI-calls; oude dossiers zijn afgehandeld).
- CLAUDE.md + `.claude/commands/*` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in repo-root niet committen.

## Kaart-discipline + sessie-einde
Wijzig je een systeemkoppeling → `docs/ARCHITECTUUR-KAART.md` bijwerken (zelfde sessie).
Sessie-einde: SESSION-NOTES + LUXIS-ROADMAP bijwerken, git tag `sessie-176`,
PROMPT-S177 schrijven.
