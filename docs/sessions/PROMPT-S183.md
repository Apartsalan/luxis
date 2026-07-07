cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 183 — Architectuur- + beveiligings-audit (Fable, ONDERZOEK-ONLY)

## Model + rol
**Fable, /effort max** (Fable is beschikbaar t/m 12 juli). Dit is een **read-only
audit vóór de livegang** met echte cliënt-PII en €1,89M aan vorderingen. Je BOUWT
niets en wijzigt niets op prod — je levert een gewogen bevindingenlijst op. Lees de
skills `fable-diepte` (meet in de bron, niet vanaf samenvattingen) en
`fable-tegenspreker` (probeer je eigen bevinding te weerleggen vóór je 'm opschrijft;
een bevinding zonder concreet faalscenario is geen bevinding).

## Waarom deze sessie (context)
Arsalan vroeg: "vibe-coded software zou onstabiel / onveilig / niet future-proof /
verspillend zijn — klopt dat hier?" De livegang staat voor de deur. Eerdere audits
schoten hier telkens raak (S161 accountlockout stil kapot, S24 AI zag <10%
werkervaring, S182 een veiligheidsvangnet dat door een tikfout NOOIT werkte). Doel:
één frisse, kritische doorlichting mét de livegang-bril op.

## Context laden bij start
Gebruik de `luxis-researcher` subagent:
"Lees LUXIS-ROADMAP.md (kopregels + secties 'SYSTEEM-AUDIT 2026-06-01' en 'Audit 124/125')
en SESSION-NOTES.md (S182-entry + S161/S172-verwijzingen). Geef compacte samenvatting van
wat al geauditeerd is en wanneer." Zo dubbel je geen werk.

## Scope — auditeer wat NIET (recent) getoetst is, langs 4 assen
1. **Beveiliging / buitenkant.** Kan een buitenstaander of een ingelogde gebruiker van
   tenant A ergens bij data van tenant B? RLS is in S150/S161 hard gemaakt (FORCE + WITH
   CHECK) — verifieer dat het nog sluit op tabellen/edge-functies die ná S161 zijn
   toegevoegd (regeling-alarm-notificaties, getrouwheids-poort, betalingen fase 1b).
   Auth-flow, tokenopslag, upload-grenzen, secret-hygiëne. Bekende latente residual:
   app draait als DB-superuser (SET ROLE-modus) — herbevestig dat er geen lekpad is.
2. **Architectuur / houdbaarheid.** Wat breekt als Kesting Legal groeit (2e advocaat,
   meer volume)? Zwakke plekken: gedeelde functies zonder tenant-scope, N+1-queries,
   plekken die stil falen (lege except, geslikte errors), scheduler-jobs zonder lock.
   S172 vond "3 AI-services / 3 geheugens" — check of dat is opgeruimd of nog leeft.
3. **Geld-correctheid.** Elke cent-berekening onder rand-omstandigheden: rente
   (samengesteld vanaf verzuimdatum), WIK-staffel, art. 6:44-toerekening, betalingen,
   creditfacturen (S181-F: negatieve-rente-verrekening — klopt die overal?). Zoek naar
   float-gebruik waar Decimal hoort, afrondingslekken, ontbrekende tests op geldpaden.
4. **Verspilling.** Onnodige AI-calls / dubbele modellen / dode code / dubbele config /
   `--no-cache` op elke deploy (bekend residual S162). Kosten per conceptgeneratie.

## Werkwijze
- Meet in de bron: grep de code, query de prod-DB read-only (via
  `docker compose exec -T db psql`, ALLEEN SELECT), lees de echte migraties/tests.
- Per bevinding: bestand:regel + concreet faalscenario (input → fout gedrag) + severity
  (blocker / hoog / midden / laag) + of het nieuw is of een bekende residual.
- Weerleg jezelf: draai waar mogelijk de relevante test of een prod-query om te bewijzen
  dat het écht misgaat. Geen speculatie als bevinding.
- Overweeg een `general-purpose`-subagent met `model: fable` voor een parallelle
  tweede-lezing op één as (zoals S182 deed) — maar cross-check zijn bevindingen zelf.

## Deliverable
`docs/research/audit-S183-architectuur-security.md`: executive summary (staat het systeem
klaar voor livegang met echte PII? ja/nee/mits) + gewogen bevindingenlijst per as +
"wat is aantoonbaar op orde" (niet-doen-lijst). GEEN fixes bouwen — de fixes zijn een
aparte Opus-sessie (S184) met dit rapport als werkorder.

## GEBLOKKEERD / niet doen
- Geen code- of prod-wijzigingen (ook geen "kleine fix onderweg"). Puur onderzoek.
- Heropening werkvoorraad blijft wachten op Lisanne. D-Break (IN100555) blijft dicht.
- Backblaze US-bucket wissen is een APARTE actie (~10 juli, zie onder) — niet in deze audit.

## Losstaand openstaand (niet deze audit, wel bewaken)
- **~10 juli:** als `/var/log/luxis-backup.log` op 8 + 9 juli twee geslaagde EU-runs toont
  (`Off-site upload complete`), dan: oude US-bucket `Luxis-backup` volledig wissen, oude
  application key intrekken, rclone-remote `luxis-backup` verwijderen. Wisbewijs in
  SESSION-NOTES. Daarna `docs/avg/verwerkersovereenkomst-CONCEPT.md` §5 nalopen.
- Arsalan: 2 crypt-wachtwoorden in wachtwoordmanager (onvervangbaar — zonder deze zijn
  EU-backups onleesbaar).

## Verificatie (als je toch iets draait — read-only)
- Tests lokaal: `docker compose exec backend python -m alembic ... ` NIET nodig; hooguit
  bestaande tests draaien om een bevinding te bewijzen.
- Prod-DB: uitsluitend SELECT-queries.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-183`, PROMPT-S184
(Opus fix-sprint met het auditrapport als werkorder).
