# Advies: betaalinstructies 14-dagenbrief (AUDIT-H6)

*Sessie 157 (10 juni 2026). Rechtspraak geverifieerd tegen data.rechtspraak.nl. Beslissing is aan Lisanne — dit document legt het probleem, het juridisch kader en een concreet tekstvoorstel voor.*

## 1. Wat er nu mis is

De 14-dagenbrief bestaat in twee kanalen met elk een eigen defect:

**E-mailversie** (`backend/app/email/incasso_templates.py`, `_render_14_dagenbrief`) bevat **twee tegenstrijdige betaalinstructies**:
1. "…het verschuldigde bedrag van **{hoofdsom}** binnen veertien dagen na ontvangst van deze brief te voldoen op **het rekeningnummer van onze cliënt**" *(geen IBAN vermeld)*
2. "…het totaal verschuldigde bedrag van **{totaal incl. BIK}** binnen veertien dagen … over te maken op **{stichtings-IBAN}**"

Twee bedragen, twee rekeningen, in één brief.

**Briefversie** (`backend/templates/14_dagenbrief.html`) verwijst tweemaal naar "het rekeningnummer van onze cliënt" en noemt **nergens een IBAN** — de debiteur kan letterlijk niet betalen op basis van de brief.

## 2. Juridisch kader (geverifieerd)

| Regel | Bron | Hardheid |
|---|---|---|
| 14-dagentermijn vangt aan **daags na ontvangst**; "na heden"/"na verzending" voldoet niet; ook **"verwarrende of misleidende informatie"** over de termijn is fataal | HR 25-11-2016, ECLI:NL:HR:2016:2704, rov. 3.4 + 3.6.1 | Hard (HR) |
| Niet-conforme brief = **géén BIK**, geen gedeeltelijk effect; herstel alleen met nieuwe correcte brief | idem, rov. 3.6.2 | Hard (HR) |
| Stelplicht/bewijslast ontvangst bij schuldeiser; ervaringsregel: bezorging tweede dag na verzending | idem, rov. 3.5.1–3.5.2 | Hard (HR) |
| Bij deelbetaling binnen de termijn: BIK herberekend over het restant | idem, rov. 3.8 | Hard (HR) |
| Brief die de indruk wekt dat **twee bedragen** verschuldigd zijn = verwarrend → BIK afgewezen | Rb. Rotterdam ECLI:NL:RBROT:2020:5202, rov. 4.6 | Lagere rechtspraak, vaste lijn |
| Onjuiste info (bijv. BIK over rente) = BIK afgewezen | Rb. Amsterdam ECLI:NL:RBAMS:2020:3212 | Lagere rechtspraak |
| **Exact BIK-bedrag** vermelden, en het moet kloppen met het Besluit (te hoog = fataal) | wettekst 6:96 lid 6 + Rb. Rotterdam ECLI:NL:RBROT:2020:9162 | Wettekst hard; sanctie lagere rechtspraak |
| Betaling aan incassoadvocaat/stichting voorschrijven is toegestaan (bevrijdende betaling aan gevolmachtigde, art. 6:114/3:60 e.v. BW); geen rechtspraak die betaling aan schuldeiser zélf eist | dogmatiek; geen gepubliceerde uitspraken | Onzeker maar standaardpraktijk |

**Risico-conclusie:** de huidige e-mailversie valt vrijwel zeker onder het verwarringscriterium (twee bedragen + twee rekeningen — exact het patroon van RBROT:2020:5202). Gevolg bij betwisting: **gehele BIK-aanspraak vervalt** voor dat dossier. De briefversie zonder IBAN is praktisch onwerkbaar en via hetzelfde criterium aanvechtbaar.

## 3. Voorstel nieuwe tekst (één instructie, één rekening)

Eén rekening (de stichtingsrekening — daar moet het geld toch heen, en alleen dan werkt de bankimport-matching), twee glasheldere scenario's:

> **Wettelijke mededeling (art. 6:96 lid 6 BW)**
>
> U kunt incassokosten voorkomen. Betaalt u het verschuldigde bedrag van **{hoofdsom + verschenen rente}** binnen **veertien dagen, te rekenen vanaf de dag nadat deze brief bij u is bezorgd**, dan bent u géén incassokosten verschuldigd.
>
> Betaalt u niet binnen deze termijn, dan bent u tevens buitengerechtelijke incassokosten verschuldigd van **{BIK-bedrag}{btw-toelichting}**. Het totaal te betalen bedrag komt daarmee op **{totaal}**.
>
> Betaling kan uitsluitend op rekeningnummer **{stichtings-IBAN}** t.n.v. **{stichting-tenaamstelling}**, onder vermelding van zaaknummer **{zaaknummer}**.

Plus twee technische aanpassingen:
- **Termijnformulering** overal: "binnen veertien dagen, te rekenen vanaf de dag nadat deze brief bij u is bezorgd" (de door de HR gesanctioneerde formulering). "Binnen 14 dagen na ontvangst" telt de ontvangstdag mee en is strikt genomen één dag te kort.
- **`termijn_14_dagen`-datum** (nu: vandaag + 15): naar **vandaag + 16** (verzenddag + 2 dagen bezorging-ervaringsregel + 14 dagen), of de concrete datum weglaten en alleen de formulering gebruiken. Een te vroege datum naast een correcte formulering is zelf al fataal (rov. 3.6.1).

### Welk bedrag in scenario 1?
Wettelijk gaat het om het "verschuldigde" zonder de BIK. Rente die al verschenen is, ís verschuldigd en mag in het 14-dagenbedrag. Simpelste juridisch veilige keuze: **hoofdsom + rente t/m vandaag** als 14-dagenbedrag, totaal incl. BIK als scenario 2. (Alternatief — alleen hoofdsom — is debiteur-vriendelijker maar laat rente liggen; aan Lisanne.)

## 4. Beslispunten voor Lisanne

1. Akkoord met **één betaalinstructie op de stichtingsrekening** (instructie "rekeningnummer van onze cliënt" vervalt)?
2. 14-dagenbedrag = **hoofdsom + verschenen rente**, of alleen hoofdsom?
3. Akkoord met de HR-termijnformulering + datum op verzenddag+16 (of datum weglaten)?
4. Geldt dit ook voor de papieren/HTML-variant (zelfde tekst)? *(advies: ja, identiek houden)*

## 5. Implementatie (na akkoord — ½ sessie)

- `_render_14_dagenbrief` in `incasso_templates.py` herschrijven volgens §3 (placeholders bestaan al: hoofdsom/rente/BIK/btw_toelichting/totaal/stichtings-IBAN sinds S157).
- `templates/14_dagenbrief.html` zelfde tekst.
- `termijn_14_dagen` in `docx_service.py` naar +16 (geldt voor alle brieven die het veld gebruiken — herinnering/aanmaning/sommatie profiteren mee).
- Rode test: render bevat exact één IBAN, één 14-dagenbedrag, HR-formulering; geen "rekeningnummer van onze cliënt".

## Bronnen
- HR 25-11-2016, ECLI:NL:HR:2016:2704 (termijn, bewijslast, sanctie, deelbetaling)
- HR 13-06-2014, ECLI:NL:HR:2014:1405 (geen nadere incassohandeling vereist na correcte brief)
- Rb. Rotterdam ECLI:NL:RBROT:2020:5202 (twee bedragen = verwarrend, BIK afgewezen)
- Rb. Amsterdam ECLI:NL:RBAMS:2020:3212 (onjuiste BIK-info = afgewezen)
- Rb. Rotterdam ECLI:NL:RBROT:2020:9162 (BIK-bedrag te hoog = brief ongeldig)
- Rb. Noord-Holland ECLI:NL:RBNHO:2022:528 / Rb. Rotterdam ECLI:NL:RBROT:2020:3726 (ontvangst-bewijs in de praktijk)
