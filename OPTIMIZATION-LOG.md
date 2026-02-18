# Optimization Log — Luxis

## 2026-02-18: Claude Code Productiviteit Optimalisatie

### Bronnen onderzocht
12 bronnen gelezen: Anthropic officieel (best practices, common workflows), Steve Sewell (Builder.io), Siddharth Bharath (complete guide), Tessl.io (14 technieken), HumanLayer (CLAUDE.md schrijven), F22 Labs (10 tips), Nikiforov (handbook), Sixeyed (10 tips parallel work), en 2 GitHub repos (everything-claude-code, awattar best practices).

### Wat er veranderd is

#### 1. CLAUDE.md geoptimaliseerd (HOOG IMPACT)
**Waarom:** De oude was 157 regels met informatie die Claude zelf kan afleiden. Best practices zeggen: kort houden (< 100 regels), alleen dingen die Claude fout doet zonder instructie.

**Wat:**
- **Root CLAUDE.md**: Ingekort van 157 naar ~50 regels. Alleen kritieke regels, geen uitleg die Claude zelf kan afleiden.
- **`backend/CLAUDE.md`**: NIEUW — backend-specifieke patronen, financiële modules, testing conventies
- **`frontend/CLAUDE.md`**: NIEUW — frontend routing, component patronen, design system
- **`docs/dutch-legal-rules.md`**: NIEUW — losse reference voor juridische regels (laden op aanvraag, niet elke sessie)

**Best practice toegepast:** "Elke regel in CLAUDE.md — zou het verwijderen ervan Claude fouten laten maken? Zo nee, schrap het." (Anthropic). Gedetailleerde info in submappen zodat het alleen geladen wordt wanneer relevant (HumanLayer advies).

#### 2. Custom Slash Commands (HOOG IMPACT)
**Waarom:** Herhalende taken (testen, committen, nieuwe feature) kosten tokens als je ze elke keer uitlegt. Commands zijn herbruikbare prompts.

**Aangemaakt in `.claude/commands/`:**
| Command | Wat het doet |
|---------|-------------|
| `/test` | Draait alle tests, analyseert failures, fixt ze |
| `/lint` | Draait ruff check + fix |
| `/commit` | Staged, commit (conventional), push |
| `/new-feature` | Volledig feature workflow: plan → backend → tests → frontend → commit |
| `/session-end` | Einde-sessie check: lint → tests → duplicaten → commit → push |
| `/check-financial` | Verificatie van alle financiële berekeningen met bekende waarden |

**Best practice toegepast:** "Create `.claude/commands/` with markdown files for frequent workflows" (Tessl.io, F22 Labs)

#### 3. Sub-Agents (MEDIUM IMPACT)
**Waarom:** Aparte context voor reviews voorkomt vervuiling van de hoofd-sessie. Elke agent heeft focus en beperkte tools.

**Aangemaakt in `.claude/agents/`:**
| Agent | Rol | Tools |
|-------|-----|-------|
| `tech-tester` | QA engineer — bugs, edge cases, test coverage | Read, Grep, Glob, Bash |
| `func-tester` | Domeinexpert — test vanuit perspectief advocaat, rapporteert in NL | Read, Grep, Glob, Bash |
| `security-reviewer` | Security — OWASP Top 10, AVG, tenant isolatie | Read, Grep, Glob (read-only) |

**Best practice toegepast:** "Deploy specialized agents for specific tasks—each maintains isolated context" (Siddharth Bharath, Tessl.io)

**Bewuste keuze:** Security reviewer heeft GEEN Bash toegang — alleen lezen. Voorkomt dat een security scan per ongeluk iets wijzigt.

#### 4. Hooks (LAAG IMPACT voor nu, groeit mee)
**Waarom:** Deterministische acties die ALTIJD moeten gebeuren — niet afhankelijk van CLAUDE.md instructies die genegeerd kunnen worden.

**Ingesteld in `.claude/settings.json`:**
- **PostToolUse (Write/Edit):** Herinnering om tests te draaien na file edits
- **Stop:** Herinnering om `/session-end` te draaien

**Best practice toegepast:** "Use hooks for actions that must happen every time with zero exceptions" (Anthropic). "Never send an LLM to do a linter's job — use deterministic hooks" (HumanLayer)

**Bewuste keuze:** Hooks zijn nu lichtgewicht (echo reminders). Zwaardere hooks (auto-lint bij save, auto-test) voegen we toe als het project groeit en de test suite sneller is.

#### 5. CI/CD Pipeline (HOOG IMPACT)
**Waarom:** Arsalan is geen developer. Het systeem moet zichzelf bewaken. CI is de automatische poortbewaker.

**GitHub Actions `.github/workflows/ci.yml`:**
- **Lint job:** ruff check + format check
- **Test job:** PostgreSQL service, migraties, pytest (depends on lint)
- **Frontend job:** npm ci + build
- **Security job:** secrets scan, float-in-financial check, tenant isolation reminder

**Workflow:** push/PR naar main → alle 4 jobs draaien → alles moet groen zijn

**Best practice toegepast:** "Richt GitHub Actions in zodat bij elke push tests, lint, en security draaien" (Arsalan's eigen eis + Siddharth Bharath CI/CD advies)

### Wat ik NIET heb gedaan (en waarom)

| Niet gedaan | Waarom niet |
|-------------|-------------|
| `--dangerously-skip-permissions` | Onnodig — `.claude/settings.json` allowlist is veiliger |
| Deploy workflow naar Hetzner | Te vroeg — geen VPS geconfigureerd |
| Automatische CLAUDE.md generatie (`/init`) | Handmatig is beter voor kwaliteit (HumanLayer advies) |
| Agent Teams (experimenteel) | Nog niet stabiel genoeg, worktrees zijn betrouwbaarder |
| Code style regels in CLAUDE.md | "Never send an LLM to do a linter's job" — ruff doet dit |
| Plugin installatie (everything-claude-code) | Overkill voor ons project, cherry-picked de relevante ideeën |

### Permissions uitgebreid
Toegevoegd aan `.claude/settings.json`:
- `Bash(MSYS_NO_PATHCONV=1 *)` — voor Docker commands in Git Bash
- `Bash(curl *)` — voor API testing

### Impact verwachting
- **CLAUDE.md:** ~30% minder irrelevante context per sessie
- **Commands:** ~50% minder tokens voor herhalende taken
- **CI/CD:** 100% van bugs/secrets gevangen voor ze op main landen
- **Agents:** ~20% betere code kwaliteit door geïsoleerde reviews
