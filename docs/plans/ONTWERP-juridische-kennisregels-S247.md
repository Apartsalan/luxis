# Ontwerp — Juridische kennisregels ("standaard-onzin herkennen")

**Status:** GEBOUWD + LIVE (S248, 24 juli) — GO Arsalan gegeven, machinerie
gebouwd op Opus en gedeployd. De harde poort is live op prod bewezen (zakelijke
regel injecteert wél op b2b, NIET op b2c). **Wacht nog op de inhoud: de eerste
echte regels van Lisanne (§7)** — tot die er zijn en zijn goedgekeurd verandert er
niets aan de AI-output (0 regels → lege injectie).

Gebouwd: tabel `legal_knowledge_rules` (+ RLS-migratie s247), service
`ai_agent/knowledge_rules.py` (poort + CRUD + `build_knowledge_rules_text`),
endpoints `/api/ai-agent/learning/rules*`, injectie in alle 3 de draft-paden,
dashboard-sectie in "Slim leren". 5 wachters + live poortproef.

**Aanleiding (demo-wens IN100458):** Studio Hartzema **B.V.** wil "de algemene
voorwaarden vernietigen". Voor zo'n partij staat dat doorgaans zwak — maar let
op de precisie (S247-Fable-review): art. 6:235 lid 1 BW sluit niet élke B.V.
uit, alleen (a) rechtspersonen die hun laatste jaarrekening openbaar hebben
gemaakt en (b) partijen met ≥50 werknemers; lid 3 raakt daarnaast wie
(vrijwel) dezelfde AV in eigen contracten gebruikt. "B.V. ⇒ kansloos" mag dus
nooit als kale regel in het systeem — de voorwaarde hoort bij de regel. Dit is
precies waarom §4 de toepasbaarheids-conditie hard maakt en Lisanne de
formulering per regel vaststelt. Luxis herkent zulke standaard-zwakke
stellingen nu überhaupt niet en draagt geen gerichte weerlegging aan.

---

## 1. Wat er al is (gemeten in de bron, S247)

- **`DEFENSE_EXAMPLES`** (`ai_agent/defense_library.py`): 5 vaste voorbeeld­reacties
  uit Kesting's eigen AV (art. 20.4, 9.3, NCNP, verlengd abonnement, English).
  Dit zijn *antwoord-teksten* die de AI qua toon/structuur overneemt.
- **`learned_answers`** (shadow-learning): **empirisch** — elke rij is geknipt uit
  een écht verstuurd antwoord van Lisanne (`source_synced_email_id` +
  `source_case_id` verplicht), via backfill → anonimiseer-voorstel → goedkeur-flow
  (`kandidaat`/`goedgekeurd`/`afgewezen`). Alleen goedgekeurde voeden de AI, gematcht
  op `defense_type`.
  - **Correctie op eerdere aanname:** het zijn **132 rijen totaal**, waarvan
    **103 goedgekeurd, 28 afgewezen, 1 kandidaat** — géén 130 wachtenden. Lisanne
    heeft de wachtrij grotendeels verwerkt.

## 2. Waarom kennisregels iets ánders zijn dan `learned_answers`

| | `learned_answers` | juridische kennisregel |
|---|---|---|
| Herkomst | empirisch, uit Lisanne's echte mail | proactieve juridische kennis |
| Bronzaak | verplicht | geen |
| Kern | "zó weerlegde Lisanne dit type" (toon/tekst) | "déze stelling is onjuist — dit is waarom (art. X BW)" |
| Voorwaarde | geen | vaak conditioneel (bv. alleen bij B.V./grote partij) |

De hele `learned_answers`-machinerie (backfill, dedup, anonimisering) is gebouwd
rond *empirische* antwoorden met een bronmail. Kennisregels hebben die machinerie
niet nodig en zouden er alleen door vervuild worden.

## 3. Architectuur — verfijnd op Fable (S248, gemeten in bron + prod)

**Aparte tabel `legal_knowledge_rules`** die de goedkeur-flow van `learned_answers`
**hergebruikt**, niet de backfill (§6.3 hiermee besloten: de backfill-machinerie is
~600 regels empirisch afgestelde knip-/dedup-heuristiek — curated regels horen daar
niet doorheen, en meng je ze in één tabel, dan concurreren regels met voorbeelden om
dezelfde 3 prompt-slots met de verkeerde framing).

### 3a. Trigger = het bestaande verweer-type (géén eigen trefwoord-machinerie)

De S247-versie stelde `trigger_keywords` voor — geschrapt. Er bestaat al een
13-type-woordenschat (`defense_types.py`) die door twee kanten wordt gebruikt: de
classificatie-AI kiest er één per inkomende verweer-mail (`prompts.py`), en de
geleerde-voorbeelden-matching draait er al op (`get_learned_examples`,
voorrang op `defense_type`). Een kennisregel krijgt dus gewoon een `defense_type`
uit die lijst als matchsleutel — nul nieuwe matching-machinerie.

**Gevalideerd op het echte ijkgeval (prod, S248):** de betwisting-mail van
IN100458 (7-10-2025) is geclassificeerd als `betwisting` / **`av_toepasselijkheid`**
— de type-match raakt het ijkgeval exact. Verdeling prod: 93 verweer-mails over 12
types (top: betwisting_ongemotiveerd 21, derde_partij 16, afwikkeling_intrekking 14;
av_toepasselijkheid 7). Faalrichting bij een mis-classificatie is veilig: regel
wordt dan NIET geïnjecteerd (concept mist extra kennis — geen fout advies).

### 3b. Toepasbaarheids-poort = `Case.debtor_type`, hard in code

De S247-versie noemde `debtor_type`/`legal_form`. **Gemeten (prod, S248): het
`legal_form`-veld van de IN100458-debiteur is LEEG** (KvK-verrijking staat uit —
"KvK: niet naar vragen"). Een poort op rechtsvorm zou dus stil falen op precies het
ijkgeval. De afdwingbare poort is `applies_to` ∈ {`alle`, `zakelijk`, `consument`},
in code gematcht tegen `Case.debtor_type` (b2b/b2c — not-null, stuurt nu al
WIK/14-dagenbrief/rente/stap-guards; de grondwaarheid van het systeem voor
consument-zijn):

- `applies_to='zakelijk'` + dossier b2c → regel gaat NOOIT de prompt in. Dit doodt
  het §4-doemscenario (art. 6:235 omgekeerd op een consument) deterministisch.
- De fijnere nuance van 6:235 lid 1 (jaarrekening-publicatie, ≥50 werknemers) kent
  Luxis niet en komt dus in de REGELTEKST van Lisanne te staan; de AI krijgt hem
  conditioneel geframed en het concept passeert altijd nog Lisanne's review
  (AIDraft + nakijk-taak — het tweede net).
- Rechtsvorm-verfijning (BV/NV via `legal_form`, patroon `compliance.py`
  `EXCLUDED_LEGAL_FORM_KEYWORDS`) kan later als optioneel extra filter, zodra het
  veld gevuld raakt — nu zou hij niets filteren.

### 3c. Kolommen (definitief voorstel)

`defense_type` (String(50), matchsleutel, één van de 13), `applies_to`
(String(10), harde poort), `title` (korte naam voor het dashboard),
`claim_description` (waaraan herken je de stelling — context voor de AI),
`rebuttal_body` (de standaard-weerlegging), `legal_basis` (bv. "art. 6:235 lid 1
BW"), `language` (default 'nl'), `status` (`kandidaat`/`goedgekeurd`/`afgewezen`),
`is_active`, `reviewed_at`. `TenantBase` → **RLS via `apply_rls` in dezelfde
migratie** (huisregel S183).

- **Dezelfde goedkeur-flow**: elke regel is eerst `kandidaat` en voedt de AI pas na
  goedkeuring door Lisanne (ook als Arsalan/Claude de regel namens haar invoert).
  Nieuwe sectie in het bestaande "Slim leren"-dashboard
  (`instellingen/ai-leren-tab.tsx`), endpoints naar het patroon van
  `/learning/candidates` (ai_agent/router.py).
- **Voeding — zelfde drie injectiepunten als de geleerde voorbeelden** (gemeten:
  `automation_service.generate_draft_for_step` verweer-stap, `draft_service`,
  `unified_draft_service` — alle drie halen daar al categorie + verweer-type van de
  laatste inkomende mail op). Eén nieuwe gedeelde functie
  `build_knowledge_rules_text(db, tenant_id, defense_type, debtor_type)` ernaast,
  eigen prompt-blok met eigen framing: "*Als de debiteur deze onjuiste stelling
  aanvoert én de voorwaarde klopt, is dit de standaard juridische weerlegging
  (art. X BW)*" — dus GEEN toon-voorbeeld, maar conditionele kennis.

## 4. Scherpste risico (premortem)

Een **fout toegepaste** kennisregel produceert zelfverzekerd-onjuiste juridische
tekst naar een debiteur. Concreet gevaar bij het IN100458-voorbeeld: art. 6:235 BW
**omgekeerd** toepassen — een **consument** mág de AV juist wél vernietigen. De
`applies_when`-voorwaarde (niet-consument) is daarom geen nice-to-have maar
**hard**; zonder die conditie schaadt de regel meer dan hij helpt. Daarom:
1. Menselijke goedkeuring per regel is niet onderhandelbaar (dekt de prompt-eis
   "élke regel langs Lisanne").
2. De toepasbaarheids-conditie moet in de matching worden afgedwongen, niet alleen
   in de tekst.

## 5. Wat wie moet doen (rolverdeling)

- **Lisanne (inhoud — kan niet door Claude):** welke stellingen zijn standaard-onjuist,
  met welk BW-artikel weerlegd, onder welke voorwaarde. Claude mag geen juridische
  regels verzinnen. Optioneel later: het systeem kan kandidaat-regels *voorstellen* uit
  veelvoorkomende patronen, maar Lisanne blijft de bron van waarheid.
- **Claude/Arsalan (machinerie, ná goedkeuring van dit ontwerp):** tabel + RLS-migratie,
  goedkeur-flow-hergebruik, dashboard-tab, prompt-injectie met conditie-gate, wachters.

## 6. Openstaand vóór bouw

1. **Goedkeuring van dit verfijnde ontwerp** (Arsalan). ~~Model naar Fable~~ — verfijning
   gedaan op Fable, S248.
2. **Eerste set regels van Lisanne** (minimaal het IN100458-geval als ijkpunt).
   Vragenlijst per regel (§7).
3. ~~Aparte tabel vs. `rule_type`-kolom~~ — **besloten: aparte tabel** (onderbouwing §3).

## 7. Vragenlijst voor Lisanne (per regel — inhoud is aan haar)

1. **Welke stelling** voert de debiteur? (bv. "wij vernietigen de algemene voorwaarden")
2. **Waarom is die (meestal) onjuist**, met welk wetsartikel? (de weerlegging zoals zij
   die zou schrijven)
3. **Onder welke voorwaarde geldt de regel** — zakelijke wederpartij, consument, of
   allebei? En zit er een nuance in die in de regeltekst zelf moet (zoals bij 6:235:
   gepubliceerde jaarrekening / ≥50 werknemers / zelfde AV in eigen contracten)?
4. **Ijkgeval IN100458:** hoe zou zij het "wij vernietigen de AV"-verweer van Studio
   Hartzema B.V. concreet weerleggen? (die tekst wordt regel #1)
