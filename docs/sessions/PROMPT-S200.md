# Sessie-prompt S200 — "De voorkant liegt"-audit (systematische jacht op dode/lege/misleidende features)

Bedacht in S199 (11 juli, Arsalan + Fable) terwijl Sol de veegsessie bouwde. Aanleiding:
de afgelopen sessies vonden we steeds per toeval features die er werkend uitzien maar
het niet zijn (bulk-status-404, blanco fasebalk, "Geïnd €0", stille lockout-breuk,
NotImplementedError op mail-verzenden, reliek-stappen). Deze sessie jaagt op die klasse
fouten SYSTEMATISCH in plaats van incidenteel.

**Werkvorm:** Fable meet (read-only op prod!), bevindingen → lijst; fixes bouwt Opus/Sol
in een vervolgsessie. Alleen triviale fixes mogen direct. GEEN prod-data wijzigen.

**Voorwaarde:** S199 is af en gedeployed (anders meet je een tussenstand).

---

## De zes families (uit de vondsten van S161–S199)

1. **Loszittende knoppen** — frontend roept endpoint dat niet bestaat (bulk-status).
2. **Lege bronnen** — UI leest uit tabel die op prod leeg is (fasebalk ← workflow_statuses).
3. **Liegende cijfers** — getoond getal klopt niet met de data ("Geïnd €0", "1169 nieuw", 18≠18).
4. **Stil falen** — fout ingeslikt, "gelukt" gemeld (lockout S161, send-write S27).
5. **Half-af** — knop/scherm aanwezig maar NotImplementedError/no-op (mail-verzenden vóór S186).
6. **Relieken** — code/data van vóór een verbouwing nog aangesloten (status-engine, sort-100-stappen).

## Audit 1 — Contract-audit frontend ↔ backend (familie 1 + dode code)

- Backend-kant: alle routes dumpen (lokaal: FastAPI route-lijst printen, of `/api/openapi.json`).
- Frontend-kant: grep alle calls — `api.(get|post|put|patch|delete)(` in `frontend/src/`,
  plus losse `fetch(`.
- Diff beide richtingen:
  - Frontend-call zonder backend-route = **kapotte knop** (bevinding, ernst hoog).
  - Backend-route zonder frontend-caller = dode-code-kandidaat (check eerst: scheduler,
    Celery, webhooks en externe callers tellen ook als caller).
- Ook methode/pad-mismatch meenemen (PUT vs POST, trailing slash, path-params).

## Audit 2 — Lege-bronnen-audit (familie 2)

- Prod (read-only): rijaantal per tabel (information_schema + count per tabel).
- Voor elke tabel met 0 of verdacht weinig rijen: grep alle readers (backend services +
  frontend hooks/schermen). Elke reader van een lege tabel = blanco-render- of
  fout-gedrag-kandidaat. Per stuk beoordelen: hoort hij leeg te zijn (nieuwe feature) of
  leunt er UI op (bevinding)?

## Audit 3 — Cijfer-reconciliatie (familie 3)

- Inventariseer ELK getoond getal: dashboard-widgets, rapportage-cijfers, badges,
  tellers boven lijsten, bedragen in dossierkoppen.
- Reken elk onafhankelijk na met SQL op prod. Verschil = bevinding (met query als bewijs).
- Sluitregels: som van uitsplitsingen = totaal (fasen, statussen, periodes); zelfde
  grootheid op twee schermen = zelfde getal.
- Let op de S198-les: 'betaald' is nu een eindstatus — elke telling "actieve zaken" en
  "openstaand bedrag" checken op de 4-statussen-logica.

## Audit 4 — Stil-falen-audit (familie 4)

- Backend: grep `except`-blokken die alleen loggen/passen; externe calls (mail, AI,
  bank, SSH) waarvan de respons niet gecheckt wordt; `background_tasks`/Celery-taken
  zonder foutafhandeling.
- Frontend: `.catch` die niets toont, success-toasts vóór/zonder response-check,
  mutations zonder `onError`.
- Per vondst: kan Lisanne hierdoor denken dat iets gelukt is terwijl het faalde? Zo ja
  → bevinding.

## Audit 5 — Half-af-audit (familie 5)

- Grep: `NotImplementedError`, `TODO`, `FIXME`, `HACK`, `XXX`, "binnenkort", "coming
  soon", `disabled` op knoppen zonder reden, lege `onClick`/handlers, routes die
  hard-coded lege data teruggeven.
- Elke hit beoordelen: zichtbaar voor Lisanne? Dan bevinding.

## Audit 6 — Relieken-audit (familie 6)

- Prod: per tabel `max(created_at)` / `max(updated_at)` — tabellen zonder enige
  schrijfactie sinds de BaseNet-import (S168, ±eind juni) zijn reliek-kandidaten.
- Koppel aan code: leest of schrijft er nog iets serieus op? Nul levende callers →
  sloop-kandidaat voor vervolgsessie (patroon S199-taak-3).

## Audit 7 — Prod-log-audit

- Backend-logs laatste 2–4 weken: alle ERROR/WARNING doornemen, ontdubbelen, per unieke
  fout: reproduceerbaar? Raakt hij een Lisanne-flow?

## Audit 8 — Sluitstuk: de dag van Lisanne (pas NA 1–7)

End-to-end op prod doorklikken (Playwright of handmatig, netwerk-tab open, elke 4xx/5xx
en console-error noteren). Minimaal deze flows:
1. Nieuwe zaak aanmaken → eerste brief genereren → versturen-als-concept.
2. Betaling boeken op een zaak → verdeling (kosten→rente→hoofdsom) → zaak wordt
   vanzelf 'betaald' bij €0.
3. Mail komt binnen → koppelt aan juist dossier → beantwoorden als concept.
4. Betalingsregeling: termijn vervalt → vooruitblik-blok → gemiste termijn rood.
5. Maandrapportage draaien → cijfers vergelijken met audit-3-uitkomsten.
6. Bulk-actie op de werkvoorraad (status, taken) op 2 testzaken.
7. Instellingen-schermen openen: elk blok moet óf werken óf weg zijn.

## Output

- `docs/sessions/S200-BEVINDINGEN.md`: per bevinding — familie, wat er mis is, bewijs
  (query/response/screenshot), ernst (blokkeert Lisanne / misleidend / cosmetisch),
  geschatte fix-grootte.
- Gerangschikt: eerst wat Lisanne deze week raakt.
- Afsluiten met `/sessie-einde` (notities, roadmap, tag sessie-200). Fixes = S201.
