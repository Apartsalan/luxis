# UX Research — E4: Documenten uploaden in dossier

**Datum:** 20 februari 2026
**Status:** Onderzoek afgerond, wacht op goedkeuring

---

## 1. Huidige situatie

### Wat er nu is
De documents module doet **alleen template-generatie**:
- DOCX templates (14-dagenbrief, sommatie, renteoverzicht) → Word-bestanden genereren per dossier
- Gegenereerde documenten worden opgeslagen in `generated_documents` tabel (metadata + template snapshot)
- Documenten tab op dossierdetail: templates kiezen → Word downloaden
- Geen upload-mogelijkheid

### Wat er mist
Lisanne ontvangt dagelijks documenten die bij een dossier horen:
- Vonnis van de rechtbank
- Contracten van cliënten
- Correspondentie van wederpartij
- Bewijsstukken
- Dagvaardingen
- Betalingsbewijzen

Deze worden nu buiten Luxis opgeslagen (Outlook, lokale mappen, Basenet). **Kernfunctie voor een PMS.**

---

## 2. Concurrentie-analyse

### Clio
- **Upload:** Drag & drop of "New → Upload files" knop
- **Organisatie:** Folder-structuur per matter, document categories (tags)
- **Metadata:** Bestandsnaam (aanpasbaar), ontvangstdatum, document category
- **Zoeken:** Op matter, category, en bestandsnaam
- **Extras:** Clio Drive (Dropbox-achtige sync), versiegeschiedenis

### PracticePanther
- **Upload:** Directe upload of integratie met Google Drive/Dropbox/OneDrive/Box
- **Organisatie:** Gekoppeld aan Contact en/of Matter
- **Metadata:** Custom tags voor filteren, versiegeschiedenis
- **Zoeken:** Tags + matter + contact
- **Extras:** Client Portal voor veilige document-deling, auto-populate templates

### Smokeball
- **Upload:** Upload-knop met folder-selectie, import van lokale bestanden
- **Organisatie:** Automatische folder-structuur per matter
- **Metadata:** Bestandsstatus iconen, import-status tracking
- **Zoeken:** Binnen matter, bestandsnaam
- **Extras:** Microsoft Office integratie, automatische activiteiten-tracking

### Gemeenschappelijke patronen
1. **Drag & drop is standaard** — elke concurrent ondersteunt het
2. **Documenten zijn altijd gekoppeld aan een dossier/matter**
3. **Metadata is minimaal maar nuttig:** naam, datum, type/categorie
4. **Chronologische lijst** is de standaard weergave (nieuwste eerst)
5. **Geen complexe folder-structuren** bij kleine kantoren — flat list met filters

---

## 3. Aanbevolen aanpak voor Luxis

### Ontwerpprincipes
- **Eenvoudig voor een solopraktijk** — geen complexe folder-hiërarchieën
- **Snelle upload** — drag & drop + klik-upload
- **Minimale metadata** — alleen wat écht nodig is
- **Integratie met bestaande Documenten tab** — uploads naast gegenereerde documenten

### UI op dossierdetail (Documenten tab)

De bestaande Documenten tab wordt uitgebreid met twee secties:

**Sectie 1: "Document genereren"** (bestaand, ongewijzigd)
- Template-knoppen voor Word-generatie

**Sectie 2: "Bestanden"** (nieuw)
- Upload-zone bovenaan: drag & drop area met "Sleep bestanden hierheen of klik om te uploaden"
- Lijst van geüploade bestanden (chronologisch, nieuwste eerst)
- Per bestand: icoon (op basis van bestandstype), naam, uploaddatum, grootte, type badge, verwijder-knop
- Download door op het bestand te klikken

### Metadata per document (minimaal)
| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `original_filename` | String | Ja | Oorspronkelijke bestandsnaam |
| `file_size` | Integer | Ja | In bytes, automatisch |
| `content_type` | String | Ja | MIME type, automatisch |
| `document_direction` | Enum | Nee | `inkomend` / `uitgaand` (standaard: inkomend) |
| `description` | Text | Nee | Korte omschrijving |
| `uploaded_by` | FK User | Ja | Automatisch |
| `uploaded_at` | DateTime | Ja | Automatisch |

**Bewuste keuze: geen folders.** Voor een solopraktijk met één advocaat is een flat list met zoek/filter voldoende. Folders toevoegen als er vraag naar komt.

---

## 4. Backend plan

### Nieuw model: `CaseFile`

```python
class CaseFile(TenantBase):
    __tablename__ = "case_files"

    case_id: UUID          # FK → cases.id, indexed
    original_filename: str  # String(500)
    stored_filename: str    # String(500), UUID-based unique naam
    file_size: int          # Integer, bytes
    content_type: str       # String(100), MIME type
    document_direction: str # String(20), "inkomend"/"uitgaand", nullable
    description: str | None # Text, nullable
    uploaded_by: UUID       # FK → users.id
    is_active: bool         # Soft delete
```

**Naamkeuze:** `CaseFile` i.p.v. `CaseDocument` om verwarring met bestaande `GeneratedDocument` te voorkomen.

### File storage

- **Locatie:** `/app/uploads/{tenant_id}/{case_id}/{stored_filename}`
- **Docker volume:** Nieuw `uploads` volume naast bestaand `generated_docs`
- **stored_filename:** `{uuid4}.{extensie}` — voorkomt conflicten en path traversal
- **Max bestandsgrootte:** 50 MB per bestand (configureerbaar)
- **Toegestane types:** PDF, DOCX, DOC, XLSX, XLS, JPG, JPEG, PNG, GIF, TXT, MSG, EML

### API endpoints

| Methode | Pad | Beschrijving |
|---------|-----|--------------|
| `POST` | `/api/cases/{case_id}/files` | Upload bestand (multipart/form-data) |
| `GET` | `/api/cases/{case_id}/files` | Lijst bestanden voor dossier |
| `GET` | `/api/cases/{case_id}/files/{file_id}/download` | Download bestand |
| `DELETE` | `/api/cases/{case_id}/files/{file_id}` | Soft-delete bestand |

**Upload endpoint detail:**
- Accepteert `multipart/form-data` met `file` (UploadFile) + optionele `description` en `document_direction`
- Valideert bestandsgrootte en MIME type
- Slaat bestand op schijf op met UUID-naam
- Maakt `CaseFile` record aan
- Retourneert CaseFileRead schema

### Pydantic schemas

```python
class CaseFileRead(BaseModel):
    id: UUID
    case_id: UUID
    original_filename: str
    file_size: int
    content_type: str
    document_direction: str | None
    description: str | None
    uploaded_by: UUID
    created_at: datetime
    uploader: UserBrief  # naam van uploader

class CaseFileCreate(BaseModel):
    document_direction: str | None = None
    description: str | None = None
```

### Waar te plaatsen

Twee opties:

**Optie A: In bestaande `documents/` module**
- Pro: documenten-gerelateerd, logisch
- Con: de documents module is al complex (deprecated HTML + docx + generatie)

**Optie B: In `cases/` module** (aanbevolen)
- Pro: het zijn case-bestanden, endpoint is `/api/cases/{case_id}/files`
- Pro: simpele toevoeging, cases module is al de juiste scope
- Con: cases/models.py wordt groter

**Aanbeveling: Optie B** — nieuw bestand `cases/files_service.py` en endpoints in `cases/router.py`.

---

## 5. Frontend plan

### Bestaande Documenten tab uitbreiden

De `DocumentenTab` component in `zaken/[id]/page.tsx` wordt uitgebreid:

```
┌─────────────────────────────────────────┐
│ Document genereren                      │  ← bestaand
│ [14-dagenbrief] [Sommatie] [Rente...]   │
├─────────────────────────────────────────┤
│ Bestanden                          [↑]  │  ← nieuw
│ ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│ │  📂 Sleep bestanden hierheen      │  │
│ │     of klik om te uploaden        │  │
│ └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                         │
│  📄 Vonnis_Jansen.pdf        12 KB      │
│     Inkomend · 20 feb 2026    [🗑]      │
│                                         │
│  📄 Contract_huur.docx       45 KB      │
│     Uitgaand · 19 feb 2026    [🗑]      │
│                                         │
│  Gegenereerde documenten                │  ← bestaand
│  📝 14-dagenbrief - Z-2026-001  [🗑]    │
│     18 feb 2026                         │
└─────────────────────────────────────────┘
```

### Hooks (nieuw in `use-case-files.ts` of toevoegen aan `use-documents.ts`)

```typescript
useCaseFiles(caseId)           // GET /api/cases/{id}/files
useUploadCaseFile()            // POST multipart
useDeleteCaseFile()            // DELETE
```

### Upload UI
- Drag & drop zone met `<input type="file" multiple>`
- Visuele feedback: border highlight bij drag-over, progress indicator bij upload
- Toast bij succes/fout
- Meerdere bestanden tegelijk uploaden

### Bestandstype iconen
- PDF → rode icoon
- DOCX/DOC → blauwe icoon
- XLSX/XLS → groene icoon
- Afbeeldingen → paarse icoon
- Overig → grijze icoon

---

## 6. Bouwstappen

| # | Stap | Geschatte omvang | Details |
|---|------|-----------------|---------|
| 1 | Backend: `CaseFile` model + migration | Klein | Model in cases/models.py, alembic migration |
| 2 | Backend: File storage utility | Klein | Upload/delete helper functies, path validation |
| 3 | Backend: Service + Router | Midden | CRUD + multipart upload endpoint, validatie |
| 4 | Backend: Tests | Midden | Upload, download, delete, size/type validatie |
| 5 | Docker: uploads volume | Klein | docker-compose.yml + prod |
| 6 | Frontend: hooks | Klein | useCaseFiles, useUploadCaseFile, useDeleteCaseFile |
| 7 | Frontend: Documenten tab uitbreiden | Midden | Drag & drop zone, bestandenlijst, download, delete |
| 8 | Build + test + commit | Klein | npm run build, pytest |

**Totaal geschat:** ~2-3 sessies

---

## 7. Risico-analyse

| Risico | Ernst | Mitigatie |
|--------|-------|-----------|
| Grote bestanden vullen Docker volume | Midden | Max 50 MB per bestand, monitoring van volume grootte |
| Bestands-uploads mislukken bij slechte verbinding | Laag | Frontend toont duidelijke foutmelding, retry mogelijk |
| Path traversal aanval via bestandsnaam | Hoog | UUID-based stored_filename, nooit originele naam gebruiken voor opslag |
| MIME type spoofing | Laag | Server-side validatie van content type + bestandsextensie |
| Backups missen uploads | Hoog | Uploads volume moet in backup-script van Hetzner Storage Box |
| Tenant isolatie: bestanden van andere tenant zien | Kritiek | Altijd tenant_id check in queries + storage path bevat tenant_id |

---

## 8. Toekomstige uitbreidingen (NIET nu bouwen)

- **Zoeken in bestandsinhoud** (full-text search op PDF tekst)
- **Folders/categorieën** (als er meer dan ~50 bestanden per dossier komen)
- **Versiebeheer** (meerdere versies van hetzelfde document)
- **Preview in browser** (PDF/afbeeldingen inline tonen)
- **Client Portal** (cliënt kan bestanden uploaden/bekijken)
- **Outlook integratie** (e-mail bijlagen automatisch opslaan)

---

*Dit document is het onderzoeksresultaat voor E4. Wacht op goedkeuring voordat implementatie begint.*
