cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 187 — Mailfunctie AFMAKEN (blok A + B)

## Model + werkwijze
**Op Opus bouwen** (`/effort max`). Dit is een AFMAAK-klus, geen nieuwe functionaliteit:
de mailmodule is half af (kijk-lijstjes zonder leesvenster, verborgen intake-machine).
4-stappen-werkwijze; verzenden blijft naar buiten gericht → proefmail alleen met akkoord.

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees `docs/plans/PLAN-mail-afmaken.md` volledig en de S186-entry in SESSION-NOTES.md.
Geef een compacte samenvatting van blok A, blok B en wat bewust NIET moet (blok C)."

Kern: het volledige plan + onderbouwing staat in **`docs/plans/PLAN-mail-afmaken.md`**.
S186 leverde al: versturen als incasso@, "Alle e-mails"-tab (data werkt, geen leesvenster),
zoeken door alle mail, beantwoorden/doorsturen (vanuit dossier + Ongesorteerd), huisstijl-
aankleding onder alle uitgaande mail.

## Taak 0 — VERPLICHT EERST: onafhankelijke review van al het S186-mailwerk
Voordat je iets bouwt: een verse, tegensprekende review van alles wat S186 opleverde
(versturen als incasso@, Verzonden-kopie, blok 2, huisstijl-aankleding). Dit is het
vaste vangnet (zoals de S175-review) — de waarde zit in de vérse blik, niet in het model.
- **Start op Fable** (`/effort max`, read-only past bij Fable + de discipline-skills).
  Schuift de beveiliging je naar Opus → prima, ga door op Opus; de onafhankelijkheid blijft.
- Adversarieel: probeer elke claim te weerleggen. **Bewijs elke bevinding tegen de code
  én de productieserver** (SSH + DB, read-only) — niet op het woord van de vorige sessie.
- Scope: commits `4d47fb1`, `4a5896e`, `f5ef4d7`, `ee41b72`, `8a98315`, `3b26a37`,
  `9aebb45`, `fd4ea8f`. Let extra op: huisstijl-aankleding (dubbel aankleden? kale mail
  ontsnapt?), reply-threading, bijlage-pad, `already_branded`-signaal.
- Must-fix bevindingen → eerst fixen (rode test → groen), dán pas blok A+B.

## Taak — blok A (mailbasis afmaken)
1. **Mails openen in "Alle e-mails"**: hang het bestaande leesvenster (zoals Ongesorteerd:
   `correspondentie/page.tsx` detail + `EmailDetailPanel`) aan de "Alle e-mails"-lijst —
   lezen, bijlagen, beantwoorden/doorsturen, koppelen aan dossier.
2. **Verder bladeren** voorbij de nieuwste 200 ("meer laden"; endpoint `/api/email/all`
   ondersteunt al `limit`+`offset`).
3. **Ongelezen-status** echt laten werken: IMAP `\Seen`-vlag meelezen in dezelfde fetch
   (`imap_provider._fetch_from_imap` zet nu hard `is_read=True`).
4. **Sjabloonkiezer begrijpelijk**: in `email-compose-dialog.tsx` de volgorde "kies eerst
   een dossier → dan sjabloon" zichtbaar maken (kiezer is nu disabled zonder dossier, zonder uitleg).
5. **Ophaalvenster verruimen** (`_fetch_from_imap` `since_days=14` → ruimer, bv. 90).

## Taak — blok B ("Nieuwe aanvragen"-map via bestaande intake)
De intake-detectie bestaat al (`ai_agent/intake_service.py`, draait elke 7 min, 2 wachten op
review op prod) maar is onzichtbaar vanuit de mailpagina.
1. Tab **"Nieuwe aanvragen"** op `correspondentie/page.tsx` (naast Alle e-mails/Ongesorteerd),
   met teller — gevuld door `intake_requests` (status pending_review).
2. Per aanvraag: AI-uittreksel tonen + knoppen **"Maak dossier"** / **"Afwijzen"** (bestaande
   intake-router-acties; controleer `intake_router.py`).
3. Herkenning verbreden: **domein-match** op de 7 opdrachtgevers (nu alleen exact contact-adres —
   zie `detect_intake_emails`: `sender not in client_contacts`). Match ook op e-maildomein.
4. Op elke mail een actie **"Maak dossier van deze mail"** (handmatige intake-trigger).

## Constraints (wat NIET doen — blok C)
- **GEEN vrije mappenstructuur** (Outlook-stijl). Luxis leest/koppelt/verstuurt; mailbox-beheer
  blijft bij BaseNet. Dossier = de map; aanvragen-wachtrij = de triage.
- Niet de bestaande sjablonen/huisstijl aanraken (S186 af).
- Geen losse koppelingen: alles moet meteen werken in het huidige systeem.

## Verificatie (4-stappen-loop)
- Backend: `docker compose exec backend pytest tests/ -k "email or intake" -v`
- Lint: `uvx ruff check app/` (ruff zit niet in de runtime-container, S162)
- Build: `cd frontend && npx tsc --noEmit`
- Functioneel: klik door in de browser (login seidony@kestinglegal.nl / Hetbaken-KL-5).

## Commit + deploy
Commit + push per afgerond onderdeel; deploy automatisch via SSH (skill `deploy-regels`).

## Openstaand meenemen (niet de hoofdtaak)
- **DMARC/DKIM voor kestinglegal.nl** (Gmail-aflevering; nu geen DMARC-record) — instelling bij
  BaseNet/registrar, geen Luxis-code. Flaggen aan Arsalan.
- Testspoor S186 opruimen: "Luxis diagnose SELF" in incasso@-INBOX dismissen.
- Reply-citaat staat vóór de handtekening (cosmetisch, evt. verfijnen).
- **Onafhankelijke Fable-review van al het S186-mailwerk** aanraden (verse subagent).

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, PROMPT-S188, git tag.
