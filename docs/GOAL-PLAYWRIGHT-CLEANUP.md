# Goal: Playwright stale specs herschrijven

**Doel:** De 12 geskipte E2E specs uit `backend/tests/KNOWN_BUGS.md` KNOWN-005
herschrijven tegen de huidige UI, zodat ze weer slagen i.p.v. skipped.

Smalle scope. GEEN backend werk. GEEN coverage doorpushen. Alleen Playwright.

---

## FASE 0 — VERPLICHTE CONTEXT (eerste turn)

LEES voor je 1 spec aanpast:

1. `CLAUDE.md` + `frontend/CLAUDE.md` — Playwright conventions
2. `backend/tests/KNOWN_BUGS.md` — sectie KNOWN-005 met de 12 stale specs
3. `.claude/projects/C--Users-arsal-Documents-luxis/memory/MEMORY.md` + in het
   bijzonder `feedback_test_recipient_safety.md` + `feedback_geen_caveman.md`
4. `SESSION-NOTES.md` — laatste 4 sessies om te zien hoe UI is geëvolueerd
5. `frontend/playwright.config.ts` + `frontend/e2e/auth.setup.ts` +
   `frontend/e2e/helpers/auth.ts` + `frontend/e2e/helpers/api.ts`
6. `frontend/e2e/regression.spec.ts` + `frontend/e2e/edge-cases.spec.ts` +
   `frontend/e2e/ui-rendering.spec.ts` — patroon voor moderne specs
7. `frontend/src/components/confirm-dialog.tsx` — nieuwe React confirm-dialog
   (vervangt window.confirm patroon)

---

## DEFINITION OF DONE

### Alle 12 stale specs herschreven of bevestigd-niet-meer-relevant

Per spec uit KNOWN-005:
- Óf herschrijven tegen huidige UI zodat test slaagt → `test.skip` weghalen
- Óf bevestigd dat het concept niet meer bestaat → entry markeren in
  `KNOWN_BUGS.md` als `STATUS: NIET MEER RELEVANT — vervangen door [test_X]`
- Óf dekking is al in regression.spec.ts / edge-cases.spec.ts / ui-rendering.spec.ts
  → markeren als `STATUS: GEDEKT IN [andere file]`

### Verificatie

```bash
cd frontend && npx playwright test --reporter=list
```

Exit 0, met:
- Minimaal 80 passed (was 71 — dus minstens 9 nieuwe slagen)
- Maximaal 12 skipped (was 35 — dus minstens 23 minder)
- Geen failed

Plus:
- `grep -c "STATUS:" backend/tests/KNOWN_BUGS.md` toont minstens 12
  (een STATUS-regel per spec in KNOWN-005)

### TypeScript blijft groen

```bash
cd frontend && npx tsc --noEmit
```

Exit 0.

---

## DE 12 SPECS (uit KNOWN-005)

Werklijst. Pak één per iteratie, commit per spec.

1. **`auth.spec.ts::A4`** — Logout-button heeft `aria-label="Uitloggen"`,
   geen `title`. Selector: `page.getByRole('button', { name: 'Uitloggen' })`.

2. **`agenda.spec.ts::A2`** — Dialog-flow veranderd. Open agenda, klik
   "Nieuwe afspraak", check moderne dialog-modal verschijnt.

3. **`correspondentie.spec.ts`** — Empty-state tekst veranderd. Run pagina,
   verifier huidige tekst (kijk in `frontend/src/app/(dashboard)/correspondentie/page.tsx`).

4. **`dashboard.spec.ts`** — Greeting heading veranderd (was "Goede
   morgen/middag/avond"). Check huidige heading in `app/(dashboard)/page.tsx`.

5. **`documenten.spec.ts`** — Page structure veranderd. Run + verifier
   nieuwe structuur.

6. **`facturen.spec.ts::F2`** — Wizard flow veranderd. Check huidige stappen
   in `app/(dashboard)/facturen/nieuw/page.tsx`.

7. **`facturen.spec.ts::F7`** — Delete-confirm is nu custom React
   `<AlertDialog>`, geen `window.confirm`. Patroon:
   ```ts
   await page.getByRole('button', { name: 'Verwijderen' }).click();
   await page.getByRole('alertdialog').waitFor();
   await page.getByRole('button', { name: 'Verwijderen', exact: true })
     .last().click();
   ```

8. **`incasso-pipeline.spec.ts`** — Pipeline steps hernoemd naar "Eerste
   sommatie", "Tweede sommatie", "Derde sommatie", "Sommatie laatste
   mogelijkheid", "Verzoekschrift faillissement". Update selectors.

9. **`instellingen.spec.ts`** — Tab-structure veranderd. Run + verifier
   tab-buttons in `app/(dashboard)/instellingen/page.tsx`.

10. **`sidebar.spec.ts`** — Dashboard greeting check faalt in beforeEach.
    Vervang met andere stabiele identifier (sidebar item Dashboard zichtbaar).

11. **`relaties.spec.ts::R5`** — Delete-confirm React component. Zelfde
    patroon als F7.

12. **`tijdregistratie.spec.ts::T5`** — Zelfde delete-confirm issue.

13. **`zaken.spec.ts::Z3`** — Wizard client-search input is verplaatst naar
    latere stap. Navigeer eerst door stap 1 (type kiezen) voor je naar client-
    selector kunt. Check `app/(dashboard)/zaken/nieuw/page.tsx` voor stap-volgorde.

(Voetnoot: KNOWN-005 noemt 12+ specs, dit is de werklijst van 13 concrete items.)

---

## MOCKING / VEILIGHEID

- Recipient bij mail-test ALTIJD `arsalanir@hotmail.com`
- E2E target: `http://localhost:3000` — NIET productie
- Geen echte mails, AI-calls, externe APIs

## CONSTRAINTS — NIET DOEN

- GEEN backend tests aanraken
- GEEN backend coverage opvoeren
- GEEN nieuwe productie-features
- GEEN nieuwe E2E groepen toevoegen (geen scope-creep)
- GEEN dependencies toevoegen
- GEEN docker-compose wijzigen
- GEEN caveman-stijl in commits — normale taal
- Bij UI-bug ontdekt tijdens herschrijven: documenteer in `tests/UI_BUGS.md`
  + ga verder met volgende spec. NIET fixen — uitscope.

## WERKWIJZE PER SPEC

1. Pak één spec uit lijst hierboven
2. Run de huidige skipped versie: `npx playwright test --grep "X" --headed`
   om te zien wat er feitelijk gebeurt
3. Update selectors/assertions tegen huidige UI
4. Verwijder `test.skip` of `test.describe.skip`
5. Run lokaal, check groen
6. Commit: `test(e2e): herschrijf [spec naam] tegen huidige UI` + Co-Authored-By
7. `git push origin main`
8. Update KNOWN_BUGS.md met STATUS-regel
9. Volgende iteratie

## CONTEXT

- Werkmap: `C:\Users\arsal\Documents\luxis`
- Dev stack starten: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
- Frontend dev: `http://localhost:3000`
- Auth: gebruik bestaande `e2e-test@kestinglegal.nl` uit auth.setup.ts
