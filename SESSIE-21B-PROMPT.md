# Sessie 21B — QA Vervolg: Agenda, Instellingen, Shortcuts, Cross-cutting

## Lees ALLEEN dit bestand. Lees andere bestanden pas als je ze nodig hebt.

## Context

Sessie 21A heeft Uren, Facturen en Documenten getest — alles PASS behalve document preview (context vol).
Resultaten staan in `QA-SESSIE-21A-RESULTATEN.md`.
Bug gevonden: BUG-25 (floating timer FAB z-index overlapt knoppen).

## Login

- **URL:** https://luxis.kestinglegal.nl
- **Email:** seidony@kestinglegal.nl
- **Wachtwoord:** Hetbaken-KL-5

## BELANGRIJK: Alleen bugs NOTEREN, NIET fixen!

Schrijf gevonden bugs naar `QA-SESSIE-21B-RESULTATEN.md`. We fixen alles in sessie 21C.

## Tests voor deze sessie (20 tests)

### 1. Document preview (1 test — overgebleven uit 21A)
- T96: Open een dossier → Documenten tab → genereer document → klik 👁 preview → PDF modal opent

### 2. Agenda /agenda (5 tests)
- T97: Agenda laadt (maand/week view)
- T98: Navigeren tussen weken/maanden
- T99: Deadlines van taken zichtbaar als events
- T100: Nieuw event aanmaken (als beschikbaar)
- T101: Event aanklikken → detail/navigatie

### 3. Instellingen /instellingen (5 tests)
- T102: Kantoorgegevens laden en bewerken
- T103: Opslaan kantoorgegevens
- T104: E-mail tab — verbindingsstatus tonen
- T105: Modules tab — toggles zichtbaar (incasso, tijdschrijven, facturatie, wwft, budget)
- T106: Module aan/uitzetten → sidebar items verschijnen/verdwijnen

### 4. Keyboard shortcuts op dossierdetail (4 tests)
- T107: `1-9` → tab switching
- T108: `T` → timer start/stop
- T109: `N` → notitie (switch naar overzicht + focus textarea)
- T110: Shortcuts NIET actief bij typing in input/textarea

### 5. Cross-cutting checks (5 tests)
- T111: Page refresh → geen errors, data blijft (test op dashboard)
- T112: Lege states → nette "geen data" berichten (niet crashes)
- T113: Loading spinners bij data ophalen
- T114: Toast meldingen bij succes/fout acties
- T115: Console errors checken op meerdere pagina's
- T116: 404 pagina testen (navigeer naar /onzin)

## Sla resultaten op in:
`QA-SESSIE-21B-RESULTATEN.md` — zelfde format als QA-SESSIE-21A-RESULTATEN.md

## Tips om context te sparen:
- Gebruik `browser_snapshot` i.p.v. `browser_take_screenshot` (kleiner)
- Noteer resultaat direct na elke test, ga snel door
- Geen lange code-analyse — alleen testen en noteren
