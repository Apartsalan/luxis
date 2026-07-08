cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 186 — Mail-functionaliteit: doorlichting + versturen áls incasso@

## Model + rol
**Start op Fable** (`/effort max`) voor de doorlichting/ontwerp; daarna **Opus** voor de bouw,
en **Fable** weer voor de review vóór livegang. Onderzoek eerst, bouw daarna (4-stappen-werkwijze).
Versturen is **naar buiten gericht** → niets live zonder expliciet akkoord + proefmail.

## Context laden bij start
Lees de S185-entry in `SESSION-NOTES.md` (mail-koppel-audit + versturen-bevinding) en
`docs/future-modules.md` (M0/M1-M6 e-mailstrategie). Kernpunt: incasso@kestinglegal.nl komt
sinds S185 **binnen** in Luxis via IMAP (`imap.basenet.nl:993`, alleen-lezen, onder Lisanne).

## Hoofdtaak — versturen áls incasso@ vanuit Luxis (blok 1, prioriteit)
**Probleem (gemeten S185):** `ImapProvider.send_message` = `NotImplementedError`; de compose-knop
gaat via `OutlookProvider` (Graph, alleen seidony@/M365); de globale SMTP-brug
(`app/email/service.py`) staat op `arsalanseidony@gmail.com` (test-restje).

**Aanpak:** SMTP via BaseNet's uitgaande server, ingelogd als incasso@ — spiegelbeeld van de
IMAP-ontvangst. Zo klopt de afzender én komt er een kopie in BaseNet's Verzonden-map.
1. **Van Arsalan nodig (eerst vragen):** BaseNet SMTP-host + poort (waarsch. `smtp.basenet.nl:587`)
   en bevestiging dat BaseNet SMTP-AUTH-relay namens incasso@ toestaat.
2. **Buildkeuze (aan Arsalan voorleggen):**
   - (A) Per-account SMTP-send in `ImapProvider.send_message` via `aiosmtplib`, met host uit
     `account.scopes` en wachtwoord uit `access_token_enc` — netjes, multi-afzender, past in de
     bestaande provider-abstractie. **Voorkeur.**
   - (B) De globale brug (`service.py`) herpunten naar BaseNet/incasso@ — snel, maar één globale
     afzender en raakt alle SMTP-sends.
3. **Test:** proefmail naar een controleerbaar adres → afzender = incasso@, komt aan (geen spam),
   verschijnt in BaseNet Verzonden. Pas daarna als "werkend" melden.
4. **Opruimen:** de `arsalanseidony@gmail.com`-SMTP-config van prod af (of vervangen).

## Doorlichting mail-module (blok 2) — is het een volwaardig mailprogramma?
Meet in de bron (`app/email/`, `frontend/.../correspondentie/`) + toets in de UI. Beoordeel:
- **Beantwoorden/doorsturen** vanuit een dossier én vanuit Ongesorteerd — werkt de thread-koppeling
  van het antwoord? (bekende beperking S185: IMAP-thread-matching werkt maar één antwoord diep —
  `imap_provider.py` `thread_id = in_reply_to or references.split()[0]`; onderzoek of dit de
  keten breekt en of `References`-volledig meenemen het oplost).
- **Zoeken** door alle mail; **mappen/labels**; ongelezen-status; bijlagen versturen.
- **Ongesorteerd-flow** (bestaat: Correspondentie-tab + teller + suggesties + koppelen/dismiss) —
  is het snel genoeg voor dagelijks gebruik bij honderden mails?

## Openstaand meenemen (niet de hoofdtaak)
- **Label-lezen-heroverweging** (`[D..._I...]` in `_find_case_by_case_number`): gemeten +1.440
  juist / +17 fout. Nu bewust UIT (precisie eerst). Heroverwegen als Ongesorteerd te vol raakt.
- **Backblaze US-bucket wissen ~10 juli** na 2 bewezen EU-runs (log 8+9 juli) — zie project-memory.

## Andere grote item (los inplannen, niet deze sessie)
**Heropening werkvoorraad** — `docs/plans/PLAN-heropening-werkvoorraad.md`, start LegalWork B.V.
Koppel-fix (S185) + vangnetten staan klaar; alleen Lisanne's groep-go + rentetype-check nog.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, PROMPT-S187, git tag.
