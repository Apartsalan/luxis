cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 139 — Aanhef-veld op contactpersoon + bulk-delete + sort-persistence

## Context laden bij start

Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Demo Feedback Lisanne sessie 138') en SESSION-NOTES.md (sessie 138). Geef compacte samenvatting van wat er in 138 is gebouwd en welke 3 items nog open staan (DF138-04 aanhef, DF138-bulk-delete, DF138-sort-persist). <300 woorden."

## Taak

Drie samenhangende UX-verbeteringen uit Lisanne's demo. Eén tegelijk uitvoeren, bij elk: backend → frontend → live verificatie via Playwright (login `seidony@kestinglegal.nl` / `Hetbaken-KL-5`) voordat door naar de volgende.

### A) DF138-04 — Aanhef-veld "De heer / Mevrouw / Onbekend" op contactpersoon

**Doel:** Wanneer Lisanne bekend is met aanhef → gebruikt in mail. Bij onbekend → "Geachte heer/mevrouw" zonder naam.

**Werk:**
1. Migratie: nieuwe kolom `salutation` (enum varchar `mr|mrs|unknown`, default `unknown`) op `contacts` tabel (alleen `contact_type=person` zinvol, maar veld op alle rows OK)
2. SQLAlchemy model + Pydantic schemas (ContactCreate, ContactUpdate, ContactResponse, ContactSummary)
3. Frontend Contact type + ContactCreateInput type
4. UI: dropdown "Aanhef" naast last_name in `relaties/nieuw/page.tsx` + `ContactInfoSection.tsx` edit-mode (alleen tonen bij person)
5. AI-prompt update in `backend/app/ai_agent/incasso_email_prompts.py`: regel 50-52 — gebruik `debtor_data.salutation` om "Geachte heer Seidony," (mr) / "Geachte mevrouw Seidony," (mrs) / "Geachte heer/mevrouw," (unknown — zonder naam)
6. `gather_case_context` in `automation_service.py` voegt `salutation` toe aan `debtor_data` dict
7. `_resolve_contact_person` retourneert tuple (achternaam, salutation) of houd ze gescheiden

**Verificatie:** maak nieuw concept-mail in dossier 2026-00062 (J.H.Verkeer&Security BV / Arsalan Seidony) — zet salutation op `mr` → mail moet "Geachte heer Seidony," tonen.

### B) DF138-bulk-delete — Bulk-actie toolbar op dossiers + relaties

**Doel:** Selecteer meerdere items via bestaande checkboxes → "Verwijder X geselecteerde" knop. Loop sequential delete; gebruik bestaande endpoints.

**Werk:**
1. `frontend/src/app/(dashboard)/zaken/page.tsx`: selectie-state al aanwezig (Selecteer alle dossiers / per dossier). Voeg toolbar toe boven tabel die zichtbaar wordt bij selectedIds.length > 0 met "Verwijder geselecteerde" knop.
2. `frontend/src/app/(dashboard)/relaties/page.tsx`: zelfde patroon (eerst checkboxes per rij toevoegen indien niet aanwezig)
3. Hooks: `useDeleteCases({ ids })` / hergebruik `useDeleteRelation` in loop. Toon toast met `X succes, Y mislukt` als gemixt.
4. Bevestig-dialog: "X relaties verwijderen?" — destructive variant.

**Verificatie:** selecteer 2 lege test-dossiers en verwijder → lijst ververst, dossiers zijn weg.

### C) DF138-sort-persist — Sortering onthouden tussen pagina-bezoeken

**Doel:** Klikken op kolom "Aangemaakt" → ga naar dossier en terug → sortering blijft staan.

**Werk:**
1. Frontend relaties + dossiers: initialiseer `sortBy` / `sortDir` state uit URL search params (Next.js `useSearchParams`)
2. Bij `toggleSort` → `router.replace(url + ?sort_by=X&sort_dir=Y)` zodat history-back ook werkt
3. Optioneel fallback: localStorage als geen URL-param aanwezig (alleen voor dossiers en relaties, niet globaal)

**Verificatie:** sortering op "Aangemaakt desc" → klik op een relatie → terug-knop browser → sortering staat nog op Aangemaakt desc met chevron-down.

## Verificatie

- Backend: `docker compose exec backend python -c "from app.relations.models import Contact; print(Contact.salutation)"`
- Build: `cd frontend && npx tsc --noEmit`
- E2E via Playwright op productie: login + test elk fix-item zoals beschreven hierboven

## Constraints (wat NIET doen)

- Geen schema-change buiten contacts.salutation kolom — DF138-04 alleen.
- Geen UI-overhaul van dossiers/relaties-tabel — alleen toolbar toevoegen, bestaande layout behouden.
- Sort-persistence alleen voor lijsten waar sortering al werkt (DF138-10 fixte relaties). Dossiers heeft nog geen sortering — alleen toevoegen als er tijd over is.
- Tussenvoegsels in achternaam (de/van/van der) verloren bij `_last_name_from_full` — laat staan, Lisanne kan `last_name` veld expliciet invullen. Niet proberen tussenvoegsels te detecteren.

## Commit

Per fix-item een aparte commit. Conventional commit message. Push naar main. Deploy automatisch via SSH (zie skill `deploy-regels`).

## Sluit met /sessie-einde

Verplicht aan einde sessie.

## Communicatiestijl

Schrijf normaal Nederlands met volledige zinnen. Geen caveman-mode (zie `feedback_geen_caveman.md` in memory).
