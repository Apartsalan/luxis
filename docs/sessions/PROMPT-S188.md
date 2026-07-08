cd Documents\luxis && claude --dangerously-skip-permissions

# Sessie 188 — Mailfunctie live-verificatie + heropening werkvoorraad

## Model + werkwijze
Mailwerk triggert het Fable-veiligheidsfilter het hardst → wisselt vaak naar Opus. Dat is
een filter aan Anthropic-kant, niet in onze code (zie memory `feedback_model_choice`). Doe
het live-doorklikwerk gewoon **op Opus** (`/effort max`); dat vereist inloggen op prod en
raakt live data. 4-stappen-werkwijze; niets verzenden zonder akkoord.

## Context laden bij start
Gebruik de luxis-researcher subagent:
"Lees de S187-entry in SESSION-NOTES.md en het openstaande deel van de S186-entry.
Geef een compacte samenvatting van wat live geverifieerd is en wat nog open staat."

## Taak 1 — VERPLICHT EERST: de twee openstaande verificatiegaten dichtklikken
S187 bouwde één gedeeld leesvenster (`EmailDetailPanel`) voor zowel "Alle e-mails" als
"Ongesorteerd". "Alle e-mails" is live doorgeklikt; **deze twee NIET**:
1. **Ongesorteerd-tab**: open een ongesorteerde mail, controleer lezen/bijlagen/beantwoorden/
   doorsturen/koppelen én dat de bulk-selectie (checkboxes) nog werkt.
2. **"Maak dossier van deze mail" met een ECHT nieuw dossier**: kies een niet-gekoppelde mail
   van een opdrachtgever, klik "Maak dossier van deze mail" → controleer dat de aanvraag in
   "Nieuwe aanvragen" verschijnt met AI-uittreksel, en dat "Maak dossier" een dossier aanmaakt
   dat klopt (cliënt = opdrachtgever, debiteur/hoofdsom uit de mail). Ruim de testaanvraag
   daarna op (afwijzen) als het puur een test was.
Login: seidony@kestinglegal.nl / Hetbaken-KL-5 (prod). Bij een fout: rode test → fix → groen.

## Taak 2 — Heropening werkvoorraad (hoofdtaak zodra input er is)
Zie `docs/plans/PLAN-heropening-werkvoorraad.md` + recept `docs/sessions/S181-werkvoorraad-recept.csv`.
Starten met LegalWork B.V.; IN100166 weer openzetten (innen); rentetype per opdrachtgever
checken. De 11 twijfel-regelingen = beslissing Lisanne. Alleen doorpakken met input Lisanne/Arsalan.

## Openstaand meenemen (niet de hoofdtaak)
- **DMARC/DKIM voor kestinglegal.nl** (Gmail-aflevering; geen Luxis-code) — flaggen aan Arsalan.
- Testspoor opruimen: "Luxis diagnose SELF" in incasso@-INBOX dismissen.
- Fable-filter: knop "auto-wissel uit" staat in claude.ai-accountinstellingen (Instellingen →
  Capabilities), niet betrouwbaar in de terminal. Arsalan gaf al `/feedback`.

## Afsluiten
`/sessie-einde`: SESSION-NOTES + LUXIS-ROADMAP bijwerken, PROMPT-S189, git tag.
