cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 182 — Opus-bouwsprint: livegang-plannen uitvoeren

## Model + rol
**Opus, /effort max.** Bouwen volgens de kant-en-klare plannen in `docs/plans/` —
elk plan is self-contained (exacte bestanden, ID's, SQL, randgevallen, acceptatie-
criteria) en op 7 juli in prod/code geverifieerd (Fable, S181-F). Volg ze letterlijk;
wijk je af, noteer waarom. Lees vóór het bouwen de skill `bekende-fouten`.

## Context laden bij start
`docs/plans/README.md` (rangorde) + SESSION-NOTES kopregels (S181-F delen 1-4) +
`docs/sessions/RAPPORT-S181F-heropeningsaudit.md` alleen bij twijfel over een bevinding.

## Taken, in deze volgorde

1. **`PLAN-regeling-alarm.md`** — URGENT: eerste regeling-termijn verviel 9 juli
   (IN100019); zonder dit ziet niemand een gemiste termijn. Bouwen → testen → deployen.
2. **`PLAN-timeout-regels-opschonen.md`** — code-guard + rode test eerst, dán de
   data-fix op prod (4 regels deactiveren, met vóór/ná-query als bewijs).
3. **`PLAN-followup-hold-steps.md`** — twee-regel-guard + test + eventuele
   pending-ruis opruimen (alleen status='pending'!).
4. Tijd over? **Getrouwheids-poort** uit `PLAN-wet-en-regelgeving-livegang.md` §1
   actie B (concept moet totaalbedrag/hoofdsom/dossiernummer/rente% uit de context
   bevatten; anders regenereren; blijft fout → reviewtaak markeren, nooit stil).

Per taak: relevante pytest lokaal + `uvx ruff check app/` vóór push; commit + push +
SSH-deploy + health check (skill `deploy-regels`); daarna pas de volgende taak.

## GEBLOKKEERD — niet aan beginnen, wel melden als input er ineens is
- **Heropening werkvoorraad** (`PLAN-heropening-werkvoorraad.md`): wacht op Lisanne's
  akkoord. Arsalan heeft het Word-bestand (`docs/sessions/Lisanne-beslispunten-
  heropening.docx`, ook op zijn Desktop) — vraag of het al bij haar ligt.
- **Backup-migratie VS→EU** (🔴, stappen in `docs/avg/subverwerkers.md`): wacht op
  Arsalans nieuwe Backblaze-EU-account. Aanmelden faalde 7 juli met HTTP 400 —
  laat hem opnieuw proberen (andere browser/incognito, werkadres
  seidony@kestinglegal.nl); blijft het falen → plan B: Hetzner Storage Box (zelfde
  console als de VPS; versleuteling via rclone crypt blijft gelijk). Zodra de codes
  er zijn: rclone crypt + backup.sh ompointen + testrun + RESTORE-TEST (runbook!),
  US-data pas wissen na 2 dagen bewezen EU-runs.
- **14-dagenbrief-sjabloon**: wacht op Lisanne's tekstkeuze (H6).
- **Account tweede stichtingsbestuurder**: wacht op naam + e-mail via Arsalan.

## Vragen aan Arsalan bij sessiestart (in één keer, geen verhoor)
1. Word-bestand al naar Lisanne / al antwoord?
2. Backblaze-EU gelukt of Hetzner-route?
3. Naam + mail tweede bestuurder?
4. Anthropic-DPA al geaccepteerd op het API-account?

## NIET doen
Geen nieuwbouw buiten de plannen ("stabiliseren boven bouwen"). Geen heropening zonder
akkoord. D-Break (IN100555) blijft dicht. Geen zips committen. Auto-draft-vlag blijft UIT
(dat is PLAN-automatisering-aanzetten, pas weken later).

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, tag `sessie-182`, PROMPT-S183.
