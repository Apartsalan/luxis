# Audit-opdracht — Code ↔ Roadmap opnieuw op elkaar leggen (Fable)

```
cd Documents\luxis && claude --dangerously-skip-permissions
```

## Waarom deze audit
De roadmap is dé bron van waarheid, maar loopt aantoonbaar uit de pas met wat er écht in de
code zit. Voorbeeld (sessie 171): we stonden op het punt een compleet nieuw "kennisbank"-
systeem te bouwen, terwijl er al een volledige **geversioneerde algemene-voorwaarden-upload
per cliënt** (S140, `ContactTerms` + `case.contact_terms_id`) in de code zat, inclusief
AI-injectie. Bijna dubbel werk. Dit soort drift kost tijd én credits. Deze audit legt één
keer grondig vast wat er is, wat er ontbreekt, en waar plan en werkelijkheid botsen.

## Model + kosten (belangrijk — Arsalan let op credits)
- **Fable = het redeneerwerk** (verbanden, gaten, aanbevelingen). Dat is de waarde.
- **NIET elke regel code lezen.** Dat veroudert meteen en verbrandt credits. Werk zo:
  1. **Goedkope structuur-scan met grep/glob** (routers, models, services, templates, hooks)
     → een platte inventaris. Grep is goedkoop, ongeacht model.
  2. **Diep lezen alleen bij een vermoeden van mismatch** — niet standaard.
  3. **Cap jezelf:** als een module "aanwezig + in roadmap" is, één regel noteren en door.
- Doe het onderzoek **zelf** (geen zwerm subagents — die timen uit en verdubbelen de kosten).
- **Verifieer je eigen bevindingen** vóór je ze als feit opschrijft (cross-check in de code) —
  precies de fout die we eerder maakten was "aannemen zonder checken".

## Context vooraf lezen (zelf, kort)
- `LUXIS-ROADMAP.md` — de claim (source of truth).
- `PRODUCT.md` — wat het product wíl zijn (de lat "zou een willekeurig kantoor dit willen?").
- `SESSION-NOTES.md` (bovenste ~3 sessies) — recentste stand.
- `CLAUDE.md` + `backend/CLAUDE.md` — architectuur + module-patroon.

## Op te leveren (in `docs/audit/inventaris-{datum}.md`)
1. **Feature-inventaris** — per module (backend router/service + frontend pagina): wat kan het,
   in één regel. Dit is het overzicht dat nu ontbreekt (er wordt in `docs/future-modules.md`
   naar een `FEATURE-INVENTORY.md` verwezen die niet bestaat).
2. **"Al gebouwd maar vergeten"** — features die in de code zitten maar niet (goed) in de
   roadmap staan. (Zoals `ContactTerms` dit keer.)
3. **"Beloofd maar afwezig/half"** — wat de roadmap claimt maar niet (volledig) bestaat.
4. **Parallelle/dubbele systemen** — plekken waar twee patronen naast elkaar leven en er één
   op moet ruimen. Bekend startpunt: **AV-injectie zit dubbel** — `automation_service.py`
   gebruikt de nieuwe geversioneerde `ContactTerms`, maar `ai_agent/draft_service.py` leest
   nog het oude losse `Contact.terms_file_path`-veld. Zoek meer van dit soort.
5. **Concreet aandachtspunt "Slim leren" (verweer-types):** de classificatie kent maar
   **5 vaste verweer-types** (`ai_agent/defense_library.py`, letterlijk 5 oude BaseNet-mails
   uit 8 april 2026). Daardoor valt **~93% van Lisanne's echte weerleggingen in "Overig"**
   (meting S171: 110 van 118 kandidaten = "overig"). De ~20 ingebouwde sjablonen
   (`email/incasso_templates.py`) en 6 DB-sjablonen (`response_templates`) gaan over de
   **uitgaande sommatie-/aanmaan-reeks**, niet over inhoudelijke weerleggingen — die hebben
   geen sjabloon. **Subtaak:** analyseer de 110 "Overig"-weerleggingen en stel een uitgebreide,
   realistische verweer-type-woordenschat voor die past bij hoe Lisanne écht antwoordt
   (bijv. betwist hoogte, beweert al betaald aan opdrachtgever, betwist opdracht/overeenkomst,
   verjaring, opschorting/wanprestatie, ...). Dat maakt de groepering in "Slim leren" bruikbaar
   én laat de AI een nieuw verweer aan de juiste cluster goedgekeurde voorbeelden koppelen.
6. **Herziene roadmap-voorstel** — een korte lijst wijzigingen om `LUXIS-ROADMAP.md` weer
   kloppend te maken (niet zelf de hele roadmap herschrijven zonder overleg).

## Werkwijze
Presenteer eerst de bevindingen (Plan Mode) vóór je iets in de roadmap wijzigt. Geen code
bouwen in deze sessie — dit is inventariseren + herijken. Kesting-specifieke kennis (art. 9.3,
opdrachtgever-namen) hoort in **data**, niet in code — flag het als je het in code tegenkomt.

## Kostenbesparende voorbereiding (optioneel, door Opus vooraf)
Opus kan vooraf de goedkope mechanische inventaris (stap 1) al produceren als los document,
zodat Fable alleen nog het dure redeneerwerk (2–6) op een kant-en-klare kaart hoeft te doen.
Scheelt een flink deel van de Fable-sessie.
