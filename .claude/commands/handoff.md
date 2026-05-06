Genereer een handoff document voor context-overdracht. Gebruik dit als alternatief voor /compact wanneer context vol raakt midden in een complexe taak.

Stappen:

1. **Analyseer huidige sessie**: wat is de taak, wat is gedaan, wat moet nog
2. **Schrijf `handoff.md`** in repo root met:
   ```
   # Handoff — [taak beschrijving]
   Datum: [vandaag]

   ## Wat is gedaan
   - [concrete wijzigingen met bestandspaden]

   ## Wat moet nog
   - [resterende stappen, in volgorde]

   ## Huidige staat
   - Build status: [groen/rood + welke errors]
   - Tests: [welke slagen, welke falen]
   - Uncommitted changes: [ja/nee + welke bestanden]

   ## Beslissingen genomen
   - [keuzes die gemaakt zijn en waarom]

   ## Bekende issues
   - [waar je tegenaan liep]
   ```
3. **Meld aan gebruiker**: "Handoff klaar. Doe `/clear` en plak dan: `Lees handoff.md en ga verder waar ik gebleven was.`"
4. **handoff.md wordt na gebruik verwijderd** — het is een tijdelijk overdracht-document, geen permanente docs.
