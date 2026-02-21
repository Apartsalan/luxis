Sluit de huidige werksessie af. Dit is VERPLICHT aan het einde van elke sessie.

Stappen:

1. **Lint check**: `MSYS_NO_PATHCONV=1 docker compose exec backend ruff check app/`
2. **Tests**: `MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -v`
3. **Frontend build**: `cd frontend && npm run build`
4. **Git status**: Check op uncommitted changes, commit als nodig
5. **Push**: Push alle commits naar origin
6. **SESSION-NOTES.md bijwerken** met:
   - Datum van vandaag
   - Laatste feature/fix naam
   - Lijst van wat er gedaan is (concrete wijzigingen)
   - Volgende stap (concrete actie, geen vage plannen)
   - Lijst van gewijzigde bestanden
   - Openstaande issues/bugs
   - Belangrijke beslissingen
7. **LUXIS-ROADMAP.md check**: Controleer of alle afgeronde features als ✅ staan
8. **Commit** de SESSION-NOTES.md update: `docs: update session notes`
9. **Push** nogmaals
10. **Rapport**: Geef een korte samenvatting aan de gebruiker + deploy-commando als er iets gedeployd moet worden
