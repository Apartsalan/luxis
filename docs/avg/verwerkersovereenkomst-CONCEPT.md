# Verwerkersovereenkomst — CONCEPT (ter toetsing door mr. L. Kesting)

> Status: concept, opgesteld 7 juli 2026. Dit is een werkdocument, geen getekend
> contract. Lisanne (advocaat) toetst en past aan; daarna tekenen beide partijen en
> vervangt een PDF-versie dit bestand als bron.

## Partijen

1. **Verwerkingsverantwoordelijke:** Kesting Legal, gevestigd IJsbaanpad 9, 1076 CV
   Amsterdam, KvK 88601536, vertegenwoordigd door mr. L. Kesting ("Kantoor").
2. **Verwerker:** [Arsalan Seidony / rechtsvorm en KvK invullen], leverancier en
   beheerder van het praktijksysteem "Luxis" ("Verwerker").

## 1. Voorwerp en duur

Verwerker verwerkt persoonsgegevens uitsluitend ten behoeve van het Kantoor in het
kader van het leveren, hosten, onderhouden en ondersteunen van Luxis
(praktijkmanagement- en incassosysteem, productie: luxis.kestinglegal.nl). De
overeenkomst duurt zolang de dienstverlening loopt.

## 2. Aard, doel en categorieën

- **Doel:** dossierbeheer, incassoworkflow (aanmaningen, sommaties), betalings- en
  derdengeldenadministratie, e-mailkoppeling, documentgeneratie, AI-ondersteunde
  conceptcorrespondentie (altijd onder menselijke goedkeuring van het Kantoor).
- **Betrokkenen:** cliënten/opdrachtgevers, debiteuren (incl. eenmanszaken/consumenten),
  contactpersonen, wederpartijen.
- **Categorieën gegevens:** NAW, contactgegevens, dossier- en vorderingsgegevens
  (bedragen, facturen, rente), betaalgegevens (IBAN, transacties), correspondentie
  (e-mail incl. bijlagen), procesgegevens. Géén bijzondere categorieën beoogd;
  correspondentie kan incidenteel gevoelige informatie bevatten.

## 3. Instructies

Verwerker verwerkt uitsluitend op schriftelijke instructie van het Kantoor (deze
overeenkomst + tickets/verzoeken), behoudens wettelijke verplichting. Verwerker
gebruikt de gegevens nooit voor eigen doeleinden en traint er geen AI-modellen mee.

## 4. Geheimhouding

Verwerker en ieder die onder zijn gezag werkt is verplicht tot geheimhouding; Verwerker
is zich ervan bewust dat de gegevens onder het beroepsgeheim van de advocaat
(art. 11a Advocatenwet) kunnen vallen en richt de verwerking daarnaar in.

## 5. Beveiliging (art. 32 AVG)

Passende maatregelen, waaronder ten minste: EU-hosting (Hetzner, Duitsland), versleuteld
transport (TLS), versleutelde opslag van koppel-tokens, toegangsbeveiliging met
accounts/rollen en wachtwoord-hashing, firewall en inbraakdetectie (ufw/fail2ban),
dagelijkse backups met geteste restore-procedure, foutmonitoring zonder
persoonsgegevens (Sentry EU, PII uitgeschakeld), audit trail op financiële mutaties en
vier-ogen op derdengelden-uitbetalingen. Backups worden uitsluitend binnen de EU/EER
opgeslagen [ACTIE: zie subverwerkers.md — off-site backup wordt gemigreerd naar
EU-regio en versleuteld vóór upload].

## 6. Subverwerkers

Toegestaan met de lijst in `subverwerkers.md` (bijlage 1). Wijzigingen meldt Verwerker
vooraf; het Kantoor kan redelijk bezwaar maken. Verwerker sluit met elke subverwerker
een verwerkersovereenkomst met gelijkwaardige waarborgen.

## 7. Doorgifte buiten de EER

Alleen met passende waarborgen (adequaatheidsbesluit zoals EU-VS Data Privacy Framework,
of SCC's). Actueel: zie bijlage 1 per subverwerker.

## 8. Bijstand

Verwerker helpt het Kantoor bij verzoeken van betrokkenen (inzage, rectificatie,
wissing), bij DPIA's en bij vragen van toezichthouders, tegen redelijke termijnen.

## 9. Datalekken

Verwerker meldt een inbreuk **zonder onredelijke vertraging en uiterlijk binnen 24 uur
na ontdekking** aan het Kantoor (zie `datalek-procedure.md`), met alle informatie die
het Kantoor nodig heeft voor de eventuele melding aan de AP binnen 72 uur.

## 10. Audit

Het Kantoor mag naleving (laten) controleren; Verwerker verstrekt daartoe redelijke
informatie en medewerking.

## 11. Einde overeenkomst

Bij beëindiging levert Verwerker alle gegevens in een gangbaar formaat aan het Kantoor
en verwijdert daarna alle kopieën (inclusief backups na afloop van de backup-rotatie
van 90 dagen), tenzij wettelijke bewaarplicht anders vereist.

---
*Bijlage 1: `subverwerkers.md` · Bijlage 2: `verwerkingsregister.md` ·
Bijlage 3: `bewaarbeleid-CONCEPT.md`*
