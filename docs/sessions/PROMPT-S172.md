# Sessieprompt S172 — Fable-audit: code ↔ roadmap herijken

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Model
**Fable** (redeneren/onderzoek). Zie de kostenbewuste werkwijze in de audit-opdracht zelf.

## Hoofdtaak
De volledige opdracht staat in **`docs/sessions/PROMPT-AUDIT-code-vs-roadmap.md`** — lees en
volg die. Kort: inventariseer wat er écht in de code zit, leg het naast `LUXIS-ROADMAP.md`,
lever op: feature-inventaris + "al gebouwd maar vergeten" + "beloofd maar afwezig" + dubbele
systemen + een bredere verweer-type-woordenschat uit de 110 "Overig"-weerleggingen. **Beantwoord
daarna (stap 7) persoonlijk en met bewijs Arsalans strategische vraag** (wordt dit één
samenhangend product; "elke sessie nieuwe medewerker"; Obsidian/vault; wat mist hij).

## Optioneel vooraf (goedkoper): laat Opus de mechanische inventaris maken
Eén Opus-sessie kan stap 1 (grep-inventaris van routers/models/services/templates) als los
document produceren, zodat Fable alleen het dure redeneerwerk hoeft te doen. Scheelt credits.

## Stand na S171 (context)
- **AV live** voor alle 7 opdrachtgevers via de al bestaande `ContactTerms` (S140) — de "kennisbank"
  (K1) hoeft niet nieuw gebouwd, alleen gevuld (dat is gebeurd + end-to-end geverifieerd).
- **K0-gate**: poot 2 (voorwaarden) rond; poot 1 = Lisanne's review loopt (S171: 12 goedgekeurd).
- Geparkeerde bouwitems (na de audit, met Opus): permanente leerstroom-filter (vaste opdrachtgevers),
  `draft_service.py` op geversioneerde `ContactTerms` zetten, Collection Company-AV koppelen.

## Constraints
- Geen code bouwen in de audit-sessie — inventariseren + herijken, bevindingen eerst (Plan Mode).
- Geen zwerm subagents (timen uit); Fable doet het zelf en verifieert eigen bevindingen.
- CLAUDE.md + `.claude/commands/*.md` staan ongecommit gewijzigd (niet van ons) — met rust laten.
- 4 AV-PDF's in de repo-root zijn cliëntdocumenten — **niet committen**.

## Sessie-einde
SESSION-NOTES + LUXIS-ROADMAP bijwerken + git tag `sessie-172` + PROMPT-S173.
