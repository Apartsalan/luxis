Start een nieuwe werksessie.

Stappen:

1. **`/effort max`** — zet reasoning op maximum voor deze sessie (voorkomt 0-reasoning beurten door adaptive thinking)
2. **Lees** via `luxis-researcher` subagent: SESSION-NOTES.md (wat vorige sessie deed + volgende stap) en LUXIS-ROADMAP.md (status + prioriteiten). NIET zelf lezen — subagent houdt context schoon.
3. **Module + route scan** — draai deze 2 commando's en bewaar output in werkgeheugen voor de hele sessie:
   - Frontend pagina's: `Glob` met pattern `frontend/src/app/(dashboard)/**/page.tsx`
   - Backend modules: `Glob` met pattern `backend/app/*/router.py`

   **Doel:** voorkom advies "bouw X" voor iets dat al bestaat. Vóór elk "X ontbreekt"-advies: check deze lijst eerst.
4. **NIET** de hele codebase inhoudelijk lezen. Wel weten WELKE pagina's/modules bestaan, niet WAT erin staat. Detail pas bij specifieke taak.
5. **Geef korte samenvatting**:
   - "Vorige sessie: [wat er gedaan is]"
   - "Volgende stap: [wat er nu moet gebeuren]"
   - "Bestaande modules: [aantal] backend, [aantal] frontend pagina's"
   - "Klaar om te beginnen."
6. **Wacht op gebruiker** voor prioriteit deze sessie.

## Harde regel tijdens sessie

Voordat je adviseert "bouw X" / "X ontbreekt" / "we moeten Y maken":
- ALTIJD eerst Glob of Grep om te checken of het bestaat
- Bij twijfel: zeg "weet niet, ga checken" — nooit gokken
- Niet vertrouwen op samenvatting van roadmap/memory voor existence-checks; alleen op code
