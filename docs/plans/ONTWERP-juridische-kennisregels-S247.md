# Ontwerp — Juridische kennisregels ("standaard-onzin herkennen")

**Status:** VOORSTEL — nog niet gebouwd. Nieuwe feature → vereist goedkeuring
(4-stappen-werkwijze) + inhoud van Lisanne. Ontwerp-verfijning hoort op Fable
(sessieprompt S247: "Ontwerp op Fable").

**Aanleiding (demo-wens IN100458):** Studio Hartzema **B.V.** wil "de algemene
voorwaarden vernietigen". Voor een B.V. is dat juridisch kansloos — art. 6:235
BW sluit grotere partijen uit van de vernietigingsgrond die consumenten wél
hebben. Luxis herkent zulke standaard-onjuiste stellingen nu niet en zou er geen
gerichte weerlegging voor aandragen.

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

## 3. Voorgestelde architectuur (technische richting — Fable verfijnt)

**Aparte tabel `legal_knowledge_rules`** die de goedkeur-flow van `learned_answers`
**hergebruikt**, niet de backfill:

- Kolommen (voorstel): `trigger_keywords`/`trigger_description` (waaraan herken je de
  stelling), `applies_when` (bv. `debtor_type`/`legal_form` = niet-consument),
  `rebuttal_body` (de standaard-weerlegging), `legal_basis` (bv. "art. 6:235 BW"),
  `language`, `status` (`kandidaat`/`goedgekeurd`/`afgewezen`), `is_active`,
  `reviewed_at`. `TenantBase` → **RLS in dezelfde migratie** (huisregel S183).
- **Dezelfde goedkeur-flow**: elke regel is eerst `kandidaat` en voedt de AI pas na
  goedkeuring door Lisanne. Nieuwe tab in het bestaande "Slim leren"-dashboard naast
  de verweer-kandidaten.
- **Voeding**: bij de verweer-stap (en evt. de antwoord-route) krijgt de AI de
  matchende goedgekeurde regels mee, ánders geframed dan de voorbeeldteksten:
  "*Als de debiteur deze onjuiste stelling aanvoert én de voorwaarde klopt, is dit
  de standaard juridische weerlegging (art. X BW).*"

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

1. **Goedkeuring van dit ontwerp** (Arsalan) + **model naar Fable** voor de detail-verfijning.
2. **Eerste set regels van Lisanne** (minimaal het IN100458-geval als ijkpunt).
3. Beslissing: aparte tabel (dit voorstel) vs. uitbreiding van `learned_answers` met een
   `rule_type`-kolom (compacter, maar dwingt curated regels door de empirische machinerie).
