# S235 — Ontwerp: betalingsregeling herkennen + flexibel termijnschema

**Status:** ontwerp, wacht op akkoord Arsalan (nachtsessie 21→22 juli, Arsalan sliep).
**Fable-review 22 juli:** ontwerp tegen de bron gehouden; 3 correcties verwerkt (Gat B-meting
was te rooskleurig — er gebeurt automatisch niets bij een regeling-mail; Gat C zou letterlijk
gebouwd nooit werken door de hold-stap-blokkade in de doorschuif-guard; wanprestatie kent twee
routes + twee verplichte velden vergen een keuze bij flexibel schema). Gat A en Deel 0 vraag 2
klopten volledig op de bron.
**Bron:** alles hieronder is deze sessie zelf in de code/DB-modellen gemeten, niet uit
geheugen of roadmap overgenomen.

---

## Deel 0 — De twee openstaande vragen uit S234

### Vraag 2: auto-afsluiten bij volledige betaling — **BESLIST (Arsalan, 22 juli)**

**Besluit:** automatisch afsluiten blijft zoals het is, MAAR er komt een melding wanneer een
dossier zo automatisch sluit: "Dossier volledig betaald en afgesloten — wil je de cliënt
factureren?" (te bouwen, akkoord gegeven). Zo is het afsluiten zichtbaar én word je eraan
herinnerd je eigen declaratie naar de cliënt te sturen. Dit is een toevoeging bovenop het
afsluiten, niet een wijziging ervan.

**Concreet te bouwen (volgende sessie):**
- Nieuw meldingstype `case_closed_invoice` in de meldingen-laag (`notifications/service.py`,
  zelfde patroon als `installment_overdue`/`invoice_overdue`, met `case_id` zodat het én in
  de bel én in de dossier-actiefeed verschijnt).
- Aangeroepen ná het automatisch afsluiten in `workflow/hooks.py::on_payment_received`.
- Frontend: type registreren in `use-notifications.ts` (`NOTIFICATION_TYPE_CONFIG`, bv. icoon
  `check-circle`, kleur `emerald`) + doorklik naar de facturen-tab van het dossier
  (`notificationTab` in `app-header.tsx`).
- Wachter-test: ná auto-afsluiten bestaat precies één `case_closed_invoice`-melding; geen
  melding als de zaak niet volledig betaald is.

---

*Onderstaande onderbouwing waarom het afsluiten zelf blijft, blijft geldig:*

### Waarom auto-afsluiten zelf blijft — **laten zoals het is**

**Wat het systeem nu doet** (`workflow/hooks.py::on_payment_received`, gemeten):
bij een betaling die het openstaande saldo op €0 brengt, zet het de zaak in één keer op
'betaald', zet de sluitdatum, **bevriest de rente op de laatste betaaldatum**, gooit open
AI-concepten weg en trekt open follow-up-adviezen in. Het vuurt alleen bij écht €0
(inclusief alle zaakinstellingen zoals een BIK-correctie), en nooit op een al-afgesloten zaak.

**Waarom niet vervangen door een taakje "Volledig betaald — afsluiten?":**
1. Je oorspronkelijke keuze kwam voort uit de aanname dat er níéts gebeurde. Die aanname
   klopte niet — het systeem doet al het verstandige. Daarmee vervalt de reden voor de wijziging.
2. Drie correctheidsgaranties hangen nú aan het automatisch afsluiten: de rente wordt
   bevroren, weglopende concepten worden opgeruimd, en verouderde adviezen worden
   ingetrokken. Zet je er een taakje tussen, dan gebeuren die pas als Lisanne klikt — en
   in de tussentijd loopt de rente door op een feitelijk betaalde zaak (precies de
   spookrestant-bug die in S207 is gefixt, IN100350) en kan er een concept de deur uit gaan
   op een zaak die eigenlijk klaar is.
3. Het zit op een gedeeld, gevoelig pad (alle vier verzendroutes, betalingskoppeling,
   dashboard). Het veranderen is een regressierisico dat we niet nodig hebben.
4. Het is niet onomkeerbaar: een per ongeluk afgesloten zaak kan heropend worden (status
   "Heropend" bestaat sinds S230).

**Het één scenario dat mijn advies zou kantelen** (kan ik 's nachts niet verifiëren):
als afsluiten werk verbergt dat er ná de betaling nog moet gebeuren — bijv. derdengelden
uitbetalen aan de cliënt. Als dat speelt, is de nette oplossing níét "taak in plaats van
automatisch", maar "automatisch afsluiten laten staan + een zichtbaar lijstje 'deze week
automatisch afgesloten' ter controle". Dat is een toevoeging, geen wijziging — voorstel,
niet gebouwd. Zeg maar of je dat wilt.

**Gedaan vannacht:** niets aan het afsluitpad gewijzigd of gedeployd. Bewust — "laten
staan" betekent geen code.

### Vraag 1: IN100613 (afgesloten, maar op stap 'Tweede sommatie')
Ligt bij Lisanne. Zodra zij antwoordt: zaak-data rechtzetten met dry-run + jouw GO +
natelling. Niet zelf aangenomen wat er moet gebeuren.

---

## Deel 1 — Wat al bestaat (gemeten, niet bouwen)

De regeling-laag is al fors gebouwd. Vóór elk "we moeten X maken" heb ik dit gecheckt:

| Onderdeel | Waar | Status |
|---|---|---|
| Model regeling + termijnen (elke termijn eigen **bedrag + datum**) | `collections/models.py` (`PaymentArrangement`, `PaymentArrangementInstallment`) | ✅ bestaat |
| 8 knoppen: aanmaken / lijst / detail / wijzigen / termijnbetaling boeken / wanprestatie / annuleren / termijn kwijtschelden | `collections/router.py` + `service.py` | ✅ bestaat |
| Binnenkomende betaling automatisch aan volgende open termijn(en) koppelen | `_auto_link_payment_to_installments` (DF-11) | ✅ bestaat |
| Regeling automatisch op 'compleet' als alles betaald/kwijtgescholden | `_check_arrangement_completion` | ✅ bestaat |
| Achterstand-alarm + notificatie bij gemiste termijn | `mark_overdue_installments` | ✅ bestaat |
| Dashboard-vooruitblik komende/achterstallige termijnen | `list_upcoming_installments` (B4/A8) | ✅ bestaat |
| UI-blok op het dossier | `frontend/.../incasso/BetalingsregelingSection.tsx` | ✅ bestaat |
| Pijplijnstappen "Treffen van regeling" (actief) + "Bijhouden regeling" (hold) | `incasso/service.py` seed | ✅ bestaat |
| Mail-classificatie herkent een regeling-verzoek → escaleren + ontvangstbevestiging | `ai_agent` (`betalingsregeling_verzoek` → ESCALATE) | ✅ bestaat |
| 13 echte regelingen in productie | prod-DB (uit S196-notities) | ✅ bestaat |

---

## Deel 2 — De echte gaten (dit is S235)

### Gat A — flexibel termijnschema bij het aanmaken
**Meting:** `create_arrangement` genereert alleen **gelijke** termijnen (bedrag-per-termijn ×
frequentie, alleen de laatste afgerond). De opslag kan per termijn een eigen bedrag/datum
aan, maar het aanmaakscherm en het aanmaak-schema (`ArrangementCreate`) bieden dat niet.
Een schema als "2× €200, daarna €1.000" kun je nu dus niet invoeren.

**Voorstel (minimaal, leunt op wat er al is):**
- Schema `ArrangementCreate` krijgt een optioneel veld `installments: [{due_date, amount}]`.
  Meegegeven → letterlijk overnemen (na controle: som van de termijnen = totaalbedrag, op de
  cent, in Decimal). Niet meegegeven → de bestaande gelijke-termijnen-weg blijft zoals hij is.
- UI (`BetalingsregelingSection`): een schakelaar "handmatig schema" die rijen laat toevoegen
  (datum + bedrag), met een lopende telling die vergelijkt met het totaal.
- Wachter-test: som-mismatch wordt geweigerd; flexibel schema wordt exact opgeslagen; de
  gelijke-weg blijft werken.

**Bewust niet:** een volledige naderhand-bewerken-editor voor termijnen. Niet nodig voor
de gevraagde flexibiliteit; kan later.

### Gat B — regeling-mail → concept/taak (nu stopt het bij escaleren)
**Meting (GECORRIGEERD, Fable-review 22 juli):** een binnenkomende "ik wil een
betalingsregeling"-mail wordt herkend (`betalingsregeling_verzoek`), maar daarna gebeurt er
automatisch NIETS: de classificatie belandt met status PENDING in een beoordelingswachtrij
die in de praktijk niemand afwerkt (S229: 22 wachtend). De ontvangstbevestiging
(`ontvangst_regeling_verzoek`) wordt bij deze categorie nooit verstuurd — die hangt aan de
actie `send_template`, maar de prompt stuurt op `escalate` (prompts.py:58). De escalatie-taak
("URGENT: Escalatie email beoordelen", service.py `execute_classification` escalate-tak)
ontstaat pas als iemand de classificatie handmatig goedkeurt + uitvoert. Het gat is dus
gróter dan eerst beschreven: er is geen automatische bevestiging én geen automatische taak.

**Voorstel (minimaal):**
- Direct bij classificatie `betalingsregeling_verzoek` (in `classify_email`/event-handler,
  NIET in de dode goedkeur-wachtrij): één taak aanmaken "Betalingsregeling vastleggen —
  {zaak}" (als er nog geen open staat), met doorklik naar het regeling-blok. Hergebruik het
  bestaande taak-patroon (`_ensure_followup_decision_task`).
- **Dedupe over beide routes** (kruispunt): als iemand later alsnog de classificatie
  goedkeurt + uitvoert, maakt de escalate-tak een tweede taak op dezelfde mail — de nieuwe
  taak en de escalate-taak moeten elkaar zien (zelfde bron-kenmerk in action_config).
- **Geen** automatisch ingevulde regeling uit de mailtekst. De classificatie zégt zelf al
  "escaleren, advocaat bepaalt voorwaarden" — de AI de bedragen/looptijd laten raden en
  vastleggen is juist fout (juridische beoordeling). Concept = een taak, geen ingevulde regeling.

### Gat C — pijplijn schuift niet mee met de regeling
**Meting:** `create_arrangement` raakt de pijplijn niet. De stappen "Treffen van regeling"
(actief) en "Bijhouden regeling" (hold) bestaan, maar een nieuwe regeling zet de zaak daar
niet automatisch naartoe.

**Voorstel (minimaal, met de bestaande waarborgen — GECORRIGEERD, Fable-review 22 juli):**
- Regeling aangemaakt → zaak naar "Bijhouden regeling" (hold). **LET OP: NIET via
  `advance_guard_reason` zoals eerder beschreven** — die guard verbíédt juist elke
  verplaatsing naar een hold-stap (`target_step.is_hold_step` → blok, bewust sinds S234).
  Letterlijk gebouwd zou de zet dus altijd geweigerd worden. Juiste vorm: rechtstreeks
  `move_case_to_step` (trigger_type bv. "arrangement") met alléén de checks "zaak
  gesloten?" en "verweer open?" ervoor — de hold-check geldt hier bewust niet, want de
  hold-stap ís het doel.
- Regeling verbroken (wanprestatie) → geen automatische sprong naar faillissement, maar een
  taak "Regeling verbroken — vervolg bepalen" (zelfde lijn als de b2c-guard uit S234).
  **Kruispunt:** er zijn TWEE routes naar 'defaulted' (`default_arrangement` én
  `update_arrangement` met status="defaulted") — de taak-aanmaak moet op een gedeeld punt
  zitten dat beide routes raken, plus wachter-test per route.
- **Twee verplichte velden bij een flexibel schema:** `installment_amount` en `frequency`
  zijn NOT NULL op het regeling-model. Keuze: vul `installment_amount` met het bedrag van
  de eerste termijn en laat `frequency` op de gekozen/default waarde; de UI toont bij een
  flexibel schema de termijnentabel i.p.v. "€ X per maand" (het samenvattingsveld op regel
  345 van `BetalingsregelingSection.tsx` verbergen of vervangen).

---

## Deel 3 — Premortem (3 faalredenen, waarom toch deze aanpak)

1. **"Flexibel schema laat de som niet kloppen met het totaal."** → harde Decimal-controle
   bij aanmaken (som termijnen = totaalbedrag), wachter-test die een mismatch weigert. Zelfde
   precisie-regel als de rest van de geldlaag.
2. **"De regeling-taak wordt spam."** → precies één open taak per zaak (idempotent, zoals de
   bestaande follow-up-taak); geen taak als er al een regeling loopt.
3. **"De automatische stap-verschuiving botst met een verweer of een gesloten zaak."** →
   expliciete gesloten/verweer-checks vóór de zet (NIET de volledige `advance_guard_reason`
   — die blokkeert hold-doelstappen en zou de zet zelf weigeren; zie Gat C-correctie).

---

## Deel 4 — Volgorde als je akkoord geeft
1. Gat A (flexibel schema) — meest afgebakend, direct waarde.
2. Gat C (pijplijnkoppeling) — kleine, geguarde zetten.
3. Gat B (mail → taak) — raakt de AI-classificatieroute; kruispunt-check (skill breed-testen)
   omdat meerdere routes een taak kunnen maken.
Elke stap: bouwen → test → (bij prod-data) dry-run + jouw GO + natelling → deploy via SSH.
