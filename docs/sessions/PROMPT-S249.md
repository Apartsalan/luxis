cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 249 — Arsalan bepaalt de hoofdtaak

## Model
Start op **Fable** (`/effort max`) voor onderzoek/plan/review. Wissel naar **Opus**
zodra er gebouwd/geklikt wordt, en meld die wissel zelf. Bouwen op Fable en plannen
op Opus zijn allebei fout — memory `feedback_model_choice`.

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant
modules, laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak
die Arsalan bij start kiest.

## EERSTE opdracht van Arsalan (uit S248): leg uit wat Lisanne moet doen
Arsalan vroeg om aan het begin van deze sessie in **gewone taal** (geen jargon,
verhaal-stijl — harde regel) precies uit te leggen wat Lisanne moet doen om de nieuwe
**juridische kennisregels** in te vullen. De machine is af en live (S248); alleen de
inhoud ontbreekt nog. Vertel hem concreet dit (en pas het aan als de bron intussen
gewijzigd is — verifieer het scherm/de velden vóór je het uitlegt):

1. **Waar:** Instellingen → tabblad "Slim leren" → blok "Juridische kennisregels" →
   knop "Nieuwe regel".
2. **Wat ze per regel invult** (4 velden + 1 keuze):
   - *Bij welk verweer?* — kies het type verweer dat de debiteur voert (bv.
     "Toepasselijkheid voorwaarden").
   - *Geldt voor* — Iedereen / Alleen zakelijk (B2B) / Alleen consument (B2C). DIT is
     de veiligheidsklep: kies "zakelijk" voor regels die alleen tegen bedrijven gelden
     (zoals art. 6:235 BW). Bij "consument" verschijnt bewust een waarschuwing.
   - *Korte titel* — herkenbare naam voor haarzelf.
   - *Welke stelling voert de debiteur?* (optioneel) — de smoes in gewone woorden.
   - *Standaard-weerlegging* — waarom de stelling onjuist is, zoals zij het zou
     schrijven; dit is wat de AI mag gebruiken.
   - *Wetsartikel* (optioneel) — bv. "art. 6:235 lid 1 BW".
3. **Daarna:** de regel staat eerst als concept; ze klikt op het groene vinkje om hem
   goed te keuren. Pas dán gebruikt de AI hem. Uitzetten/bewerken/verwijderen kan altijd.
4. **Beste startpunt (ijkpunt):** dossier IN100458 (Studio Hartzema B.V. — "wij
   vernietigen de algemene voorwaarden"). Haar weerlegging daarvan wordt regel #1.
   De vragenlijst per regel staat in §7 van
   `docs/plans/ONTWERP-juridische-kennisregels-S247.md`.

**Rolverdeling (S240):** de INHOUD (welke verweren onjuist zijn, met welk artikel) is
juridisch werk van Lisanne — niet zelf verzinnen. Claude/Arsalan mogen de velden
technisch invullen namens haar, maar zij keurt goed. Bied niet aan het inhoudelijk
zelf te schrijven.

Extra taak-context (alleen als de gekozen hoofdtaak dat raakt):
- **Kennisregels-detail:** `docs/plans/ONTWERP-juridische-kennisregels-S247.md`
  (status: GEBOUWD + LIVE). Injectie in alle 3 de draft-paden via de gedeelde functie
  `build_knowledge_rules_text`; poort `rule_applies` in `ai_agent/knowledge_rules.py`.
- **Fase-heropening per groep:** `docs/plans/BASENET-STATUS-HERSTEL.md` (406 dossiers,
  GO per groep, draaiboek-checks éérst).

## Security (S248-nagekomen — context)
Kimi-security-scan gedaan (6 domeinen), 7 fixes live (SEC-25..31: SSTI-sandbox,
refresh-TOCTOU, kantoor-actief, RLS-default-secure, IMAP-SSRF, wachtwoordlengte,
rate-limits). Details: nagekomen-sectie entry S248 in SESSION-NOTES; rapport
`scratchpad/BEVINDINGEN-SECURITY-S248.md` (scratchpad, niet in repo). **Twee open
aanbevelingen — Arsalan beslist, ze kosten iets:**
- Aparte `TOKEN_ENCRYPTION_KEY` op de VPS zetten (nu valt tokenversleuteling terug op
  SECRET_KEY). LET OP: aanzetten verbreekt Lisanne's e-mailkoppeling → ze moet opnieuw
  verbinden. Laag risico (SECRET_KEY is sterk).
- Kennisregel-endpoints (`/api/ai-agent/learning/rules*`) admin/advocaat-only maken
  (nu get_current_user, spiegelt learned_answers). Laag (2 vertrouwde gebruikers).

## Taak
Arsalan bepaalt de hoofdtaak bij start. Sterke kandidaten uit de roadmap:
1. Losse punten (afgeronde-taak-"X dagen te laat", melding mislukte geplande mail
   alleen naar inplanner, DMARC, kostenblokje, sharp-CVE frontend-dep-audit).
2. Fase-heropening volgende groep uit BASENET-STATUS-HERSTEL.
3. Twee open security-aanbevelingen hierboven (indien Arsalan ze wil).
4. Eventueel: kennisregels-verfijning ná Lisanne's eerste regels (bv. rechtsvorm-
   filter via `legal_form` als de KvK-verrijking ooit aangaat — nu leeg, ongeschikt).

**Signaleren, niet oppakken (rolverdeling S240 — inhoudelijk werk = Lisanne):**
kennisregels-inhoud (zie boven), oud IN100606-concept opnieuw genereren, IN100592 3e
betwisting, regeling-taken IN100281/IN100537, IN100127, 2 open mails
(IN100128/IN100586), IN100492-vraag, 4 review-mails ongesorteerde bak + intake Ram
Charan Sukhdai.

## Verificatie
- Backend: `docker compose exec backend python -m pytest tests/ -k "<relevant>"` (één run tegelijk).
- Lint: `uvx ruff check backend/app/`  ·  Frontend: `cd frontend && npx tsc --noEmit`.
- Kruispunt-check skill `breed-testen` bij elk gedeeld effect (mail/stap/concept/geld/zaak).
- Bij prompt-wijziging: verse AI-output op het echte geval verifiëren (niets versturen), kosten natellen.
- Deploy via SSH; login 200; CI groen natrekken.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; testverzendingen alleen op testdossiers
  (2026-00006/…-00015, gmail Arsalan) en netjes terugzetten.
- Kostenbewust testen (ai_usage natellen).
- Geen inhoudelijk dossierwerk — signaleren, niet oppakken (Lisanne).
- Nieuwe feature → eerst plan + goedkeuring, niet autonoom bouwen.
- KvK: niet naar vragen.  ·  Nooit `git add -A` — expliciete paden.

## Commit
Per onderdeel een conventional commit + push. Deploy automatisch via SSH.
Afsluiten met `/sessie-einde` (volgende prompt = PROMPT-S250).
