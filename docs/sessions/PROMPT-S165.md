# Sessieprompt S165 — Backlog uit de S164-demosessie (incasso-flow afmaken + shadow-learning)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

**Model:** Opus (precisiewerk). **`/effort max` aan het begin.**
**Deploy: ZELF via SSH** (memory `feedback_deploy_via_ssh` + skill `deploy-regels`) — niet wachten op CI; die skipt deploy bij rood en duurt ~11 min.

---

## Waarom deze sessie
S164 werd een lange live-demosessie mét Arsalan i.p.v. de geplande H25. Veel gefixt + gedeployd (zie S164-entry in `SESSION-NOTES.md`). Wat overblijft = concrete punten die Arsalan tijdens het testen vond + één strategisch spoor (shadow-learning Optie A, door hem goedgekeurd). H25 staat óók nog open uit de audit.

## Context laden bij start
- `SESSION-NOTES.md` — **S164-entry bovenaan** (wat net gefixt is + valkuilen: prompt-fragiliteit, XXX-flakiness, token-re-encrypt).
- Per fix: rood→groen lokaal, dan **zelf via SSH deployen** + health-check.

## Backlog (kies/prioriteer met Arsalan)

**1. Cliënt-kenmerk/dossiernummer bij factuur-upload.**
Het kenmerk van de cliënt staat vaak níét op de geüploade factuur, en we kunnen cliënten niet vragen het erop te zetten. Bedenk een manier om het tóch in Luxis te krijgen bij de upload (nu handmatig). Eerst onderzoeken (hoe lossen Clio/Basenet dit op), dan mét Arsalan afstemmen — geen aanname.

**2. Particulier-naam auto-invullen in wederpartij.**
Bij factuur-upload van een **particulier** wordt de naam niet automatisch in het wederpartij-veld gezet. Voornaam + achternaam; géén voornaam → gebruik achternaam. Zit in invoice-parse → wizard: `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` (`handleInvoiceParsed`) + parser `/api/ai-agent/parse-invoice`. NB: de auto-match-bug (verkeerde partij) is in S164 al gefixt — dit gaat om het invullen van de naam zelf voor een persoon.

**3. Stappenhistorie: verzonden brieven bijhouden.**
Je ziet wél gegenereerde concepten (en zelfs de tweede sommatie), maar een daadwerkelijk **verstuurde eerste sommatie** ontbreekt in de staphistorie. Alles wat gedaan wordt moet in `CaseStepHistory`/activity. Check de verzendpaden (incasso send + `advance-after-send`) — loggen ze de verzending wel?

**4. 14-dagenbrief bij particulier (B2C).**
Bij een particulier (B2C) is de 14-dagenbrief wettelijk verplicht/geldig, maar hij werd niet meegenomen in de gegenereerde brieven van het dossier. Zorg dat de pipeline 'm voor B2C opneemt.

**5. Verweer-escalatie: twee reacties → laatste ultimatum → volgende fase.**
Lisanne reageert doorgaans **2× inhoudelijk** op een discussie; daarna één afsluitend bericht ("we komen er niet uit, ik ga cliënt adviseren hun rechten te betrekken / procedures te starten") en dán naar de volgende fase. De agent moet dit patroon herkennen: na 2 inhoudelijke verweer-reacties → genereer de afsluitende ultimatum-brief → markeer voor de volgende fase.

**6. Shadow-learning Optie A (RAG uit Lisanne's echte antwoorden) — STRATEGISCH, goedgekeurd door Arsalan.**
Uitwerken tot **plan + premortem** (zie S164-onderzoek in de notes), dan bouwen. Kern: bij draft-generatie Lisanne's meest gelijkende **vroegere verzonden antwoorden** ophalen (op classificatie-categorie + semantische gelijkenis) en als voorbeeld injecteren i.p.v. (of naast) de hand-curated `defense_library`. Elk verzonden antwoord wordt automatisch een toekomstig voorbeeld → continu lerend, geen training. Versterkt het assistent-model, géén autonomie (besluit S160). Randvoorwaarde (in S164 gefixt): e-mailsync + dossier-koppeling werken.

**7. (uit audit, nog open) H25 — `modules_enabled` server-side afdwingen.** Bounded autonome taak; zie `docs/sessions/PROMPT-S164.md` + `.audit/AUDIT-REPORT.md` (H25).

## Verificatie
Per fix relevante test rood→groen; `npx tsc --noEmit` bij frontend-wijzigingen; `gh run list` groen houden; **zelf via SSH deployen** + `curl -sf https://luxis.kestinglegal.nl/health`.

## Constraints (NIET doen)
- Geen autonome AI-incasso-agent (besluit S160). Shadow-learning = assistent; Lisanne beslist + handelt.
- Juridische bewoording = Lisanne's oordeel; jij fixt de structuur/flow.
- Prompt-fragiliteit (S164-les): de verweer-prompt laat bij extra instructies snel de 'XXX'-plaatshouder staan → het XXX-retry-vangnet vangt dat op, maar voeg niet onnodig instructies toe.

## Sessie-einde
SESSION-NOTES.md + LUXIS-ROADMAP.md bijwerken + git tag `sessie-165` + prompt S166.
