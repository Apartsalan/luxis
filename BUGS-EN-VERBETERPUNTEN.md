# Bugs en Verbeterpunten — Handmatige Test (19 feb 2026)

Gevonden tijdens handmatige doorloop van Luxis productie.

---

## NU OPPAKKEN (volgende sessie)

### BUG-1: Relatie niet automatisch gekoppeld bij nieuwe zaak

**Waar:** Relaties > klik op relatie > "Nieuwe zaak" knop
**Ernst:** UX-bug (hoog)

**Probleem:** Als je vanuit een relatiedetailpagina op "Nieuwe zaak" klikt, wordt die relatie niet automatisch als cliënt ingevuld. Je moet handmatig zoeken en selecteren — onlogisch als je de zaak vanuit die relatie opent.

**Verwacht gedrag:**
- Je zit op relatiedetail van "Jansen B.V." en klikt "Nieuwe zaak"
- In het zaakformulier is "Jansen B.V." al ingevuld als cliënt
- Je hoeft alleen nog de overige gegevens in te vullen

**Bestanden:**
- `frontend/src/app/(dashboard)/relaties/[id]/page.tsx` — regel 674: link gaat nu naar `/zaken/nieuw` zonder parameters
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — regel 19-29: form initialiseert altijd met lege `client_id`, leest geen URL params

**Fix:**
1. Relatiedetail: link wijzigen naar `/zaken/nieuw?client_id=${id}&client_name=${encodeURIComponent(relation.name)}`
2. Zaakformulier: `useSearchParams` importeren, `client_id` en `client_name` uit URL lezen, form pre-populeren
3. Suspense boundary toevoegen (Next.js vereist dit bij `useSearchParams`)

---

### BUG-2: Rente-instellingen zichtbaar bij alle zaaktypes

**Waar:** Nieuwe zaak aanmaken (`/zaken/nieuw`)
**Ernst:** UX-bug (midden)

**Probleem:** De "Rente-instellingen" sectie (rentetype, rentepercentage) is altijd zichtbaar, ook bij niet-incasso zaaktypes (advies, insolventie, overig). Rente is alleen relevant bij incassozaken.

**Verwacht gedrag:**
- Rente-instellingen ALLEEN tonen als `form.case_type === "incasso"`
- Bij ander zaaktype: sectie verbergen

**Bestanden:**
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — regels 194-238: de hele "Rente-instellingen" `<div>` wordt altijd gerenderd

**Fix:**
Wrap regels 194-238 in `{form.case_type === "incasso" && ( ... )}`. Eén regel toevoegen, één sluiten.

---

### BUG-3: Automatische renteberekening per documentdatum

**Waar:** Documentgeneratie (sommatiebrief, 14-dagenbrief, dagvaarding, renteoverzicht)
**Ernst:** Functioneel (hoog — processtukken voor de rechtbank)

**Probleem:** Bij het genereren van documenten moet de rente automatisch berekend worden tot de datum van het document. Als je in een jaar vijf brieven stuurt, is de rente in elke brief hoger.

**Huidige status na onderzoek:**
- De renteberekening in `backend/app/collections/interest.py` (functie `calculate_case_interest`) accepteert al een `calc_date` parameter en berekent correct
- `backend/app/documents/docx_service.py` (`_build_base_context`, regel 261-279) gebruikt al `calc_date=today` met `today = date.today()` bij aanroep van `get_financial_summary`
- Dit betekent: **de berekening werkt al correct voor nieuwe documenten** — rente wordt berekend t/m de huidige datum

**Wat nog gecontroleerd moet worden (volgende sessie):**
1. Worden de rente-bedragen daadwerkelijk als merge fields in de templates gezet? Check de template context keys.
2. Staan de juiste merge fields in de .docx templates? (`{{ rente_totaal }}`, `{{ rente_per_vordering }}`, etc.)
3. Is de legacy HTML service (`backend/app/documents/service.py`, regel 224-226) ook correct? (ook `today = date.today()`)
4. Overweeg: bij hergebruik van een oud document, moet `doc.created_at.date()` als `calc_date` worden gebruikt (niet `today`)

---

## NIET NU BOUWEN — WEL IN ROADMAP

### ROADMAP-4: Handmatige taken aanmaken

**Waar:** Taken-overzicht en zaakdetailpagina
**Priority:** Midden (toevoegen aan UX-VERBETERPLAN)

**Probleem:** Er is geen mogelijkheid om zelf een taak aan te maken. Taken worden alleen automatisch aangemaakt door workflow-triggers (statuswijzigingen). Een advocaat wil ook ad-hoc taken aanmaken ("Bel cliënt terug", "Stuk nakijken").

**Gewenst gedrag:**
- Op zaakdetailpagina: knop "+ Taak" om handmatige taak te maken
- Velden: titel, omschrijving (optioneel), deadline, gekoppelde zaak
- Op taken-overzicht: ook een "+ Taak" knop
- Handmatige taken naast workflow-taken in dezelfde lijst
- Taak afronden met één klik

**Afhankelijkheden:**
- Backend: `POST /api/tasks` endpoint bestaat al (via workflow router), maar check of het ook handmatige taken ondersteunt (zonder workflow_rule_id)
- Frontend: `taken/page.tsx` + `zaken/[id]/page.tsx` TakenTab

---

### ROADMAP-5: Agenda — events aanmaken

**Waar:** Agenda-pagina
**Priority:** Midden (toevoegen aan UX-VERBETERPLAN)

**Probleem:** De agenda is read-only. Je kunt er niets aan toevoegen. Advocaten moeten afspraken, zittingen en herinneringen kunnen inplannen.

**Gewenst gedrag:**
- Klikken op datum/tijdslot opent formulier voor nieuw event
- Velden: titel, datum/tijd, duur, zaak (optioneel), type (afspraak, zitting, herinnering, deadline)
- Events verschijnen naast workflow-deadlines in de kalender
- Bewerken en verwijderen van handmatige events

**Afhankelijkheden:**
- Backend: nieuw model + CRUD endpoints nodig (`CalendarEvent` met `title`, `start`, `end`, `type`, `case_id`, `user_id`)
- Frontend: `agenda/page.tsx` aanpassen met click handler en formulier modal

---

### ROADMAP-6: Conflict check verbeteren — warning, niet blokkeren

**Waar:** Zaak aanmaken + zaakdetailpagina (partijen)
**Priority:** Midden (toevoegen aan UX-VERBETERPLAN)

**Huidige situatie:**
- Op het zaak-aanmaakformulier (`/zaken/nieuw`) zit al een conflict check via `useConflictCheck` hook
- Als een cliënt in een andere zaak wederpartij is, toont het een amber warning box met details
- De submit wordt NIET geblokkeerd — dit is goed, want soms is een conflict gewenst/te verantwoorden
- Op de zaakdetailpagina (`/zaken/[id]`) is er GEEN conflict check bij het partijen-tab

**Gewenst gedrag:**
- **Aanmaakformulier:** Huidige warning behouden (werkt al). Eventueel: checkbox "Ik bevestig kennis van dit conflict" toevoegen zodat het bewust is.
- **Zaakdetailpagina (Partijen tab):** Ook een conflict warning tonen als cliënt of wederpartij in andere zaken een tegengestelde rol heeft
- **Visueel:** Warning sign (amber) — duidelijk zichtbaar maar niet blokkerend. De advocaat beslist zelf.
- **Audit trail:** Optioneel voor later: als een zaak wordt aangemaakt ondanks conflict, dit loggen in de activiteiten

**Bestanden:**
- `frontend/src/hooks/use-cases.ts` — `useConflictCheck` hook bestaat al
- `backend/app/cases/router.py` — `GET /conflict-check` endpoint bestaat al
- `backend/app/cases/service.py` — `conflict_check()` logica bestaat al
- `frontend/src/app/(dashboard)/zaken/nieuw/page.tsx` — regels 307-330: amber warning box (al werkend)
- `frontend/src/app/(dashboard)/zaken/[id]/page.tsx` — Partijen tab: GEEN conflict check (moet toegevoegd)

**Wat er al werkt:**
- Backend conflict detection is compleet
- Frontend warning op aanmaakformulier is compleet
- Formulier is al niet-blokkerend (submit gaat door ondanks conflict)

**Wat er nog moet:**
- Conflict warning toevoegen aan zaakdetail Partijen tab
- Eventueel: bevestiging-checkbox bij aanmaken met conflict
- Eventueel: conflict loggen in activiteiten als audit trail

---

## Samenvatting

| # | Issue | Ernst | Actie | Status |
|---|-------|-------|-------|--------|
| 1 | Relatie niet gekoppeld bij nieuwe zaak | Hoog | Nu fixen | Klaar voor implementatie |
| 2 | Rente-velden bij niet-incasso zaken | Midden | Nu fixen | Klaar voor implementatie |
| 3 | Rente per documentdatum | Hoog | Controleren + evt. fixen | Grotendeels al werkend, needs verification |
| 4 | Handmatige taken aanmaken | Midden | Roadmap | Gedocumenteerd |
| 5 | Agenda events aanmaken | Midden | Roadmap | Gedocumenteerd |
| 6 | Conflict check verbeteren (warning, niet blokkeren) | Midden | Roadmap | Gedocumenteerd — aanmaken werkt al, zaakdetail mist het |
