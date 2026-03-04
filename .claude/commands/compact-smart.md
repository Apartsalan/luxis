Perform a smart context compaction by detecting the current focus area.

## Steps

1. **Detect current focus**: Look at:
   - Recent tool calls (which files were read/edited?)
   - Current todo list (what task is in progress?)
   - Git diff (what's changed?)
2. **Identify the module/feature**: e.g., "incasso pipeline", "E2E tests zaken", "email sync"
3. **Build focus string**: Create a concise summary:
   - Current task
   - Key files involved
   - Decisions already made
   - Next steps remaining
4. **Output the compaction directive**: Print the focus string formatted for `/compact`

## Example Output

```
/compact Focus op E2E tests voor zaken module. Key files: frontend/e2e/zaken.spec.ts, frontend/e2e/helpers/api.ts. Al gedaan: lijst pagina tests, create basis dossier. Nog te doen: create incasso dossier, detail pagina, status wijzigen, verwijderen. Helpers createCase/deleteCase zijn af.
```

NOTE: This command CANNOT trigger compaction directly. Copy the output and paste it into `/compact`.
