Plan and implement a new feature for Luxis: $ARGUMENTS

Steps:
1. **Understand**: Read relevant existing code to understand current patterns
2. **Plan**: Create a detailed implementation plan covering:
   - Which files need to change
   - Database changes needed (new migration?)
   - API endpoints (router + service + schemas)
   - Frontend pages/components
   - Tests needed
3. **Implement backend**: Models → Migration → Service → Router → Schemas
4. **Write tests**: Unit tests for business logic, integration tests for API
5. **Run tests**: `MSYS_NO_PATHCONV=1 docker compose exec backend pytest tests/ -v`
6. **Implement frontend**: Hook → Page → Components
7. **Verify**: Check everything works together
8. **Commit**: Using conventional commit format
