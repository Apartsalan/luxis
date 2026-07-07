# Register van verwerkingsactiviteiten — Kesting Legal (art. 30 AVG)

Stand: 7 juli 2026 (concept, vaststellen door mr. L. Kesting).
Verwerkingsverantwoordelijke: Kesting Legal, IJsbaanpad 9, 1076 CV Amsterdam,
KvK 88601536. Geen FG aangesteld (niet verplicht bij deze omvang).
Contactpunt privacy: mr. L. Kesting.

| # | Verwerking | Doel | Betrokkenen | Gegevens | Grondslag | Bewaartermijn | Systemen/verwerkers |
|---|---|---|---|---|---|---|---|
| 1 | Dossierbeheer & incasso | Uitvoering opdracht tot incasso/rechtsbijstand | cliënten, debiteuren, wederpartijen | NAW, contact, vordering/facturen, rente, correspondentie, procesinformatie | uitvoering overeenkomst (cliënt); gerechtvaardigd belang (debiteurgegevens: incasso namens schuldeiser) | 5 jaar na sluiting dossier (zie bewaarbeleid) | Luxis (Hetzner EU) |
| 2 | Betalings- & derdengeldenadministratie | Verwerken betalingen, art. 6:44-toerekening, derdengeldenbeheer (Voda) | debiteuren, cliënten | IBAN, transacties, bedragen | wettelijke plicht (administratie/Voda) + uitvoering overeenkomst | 7 jaar (fiscaal) | Luxis; bankafschriften via handmatige CSV-upload (Rabobank) |
| 3 | E-mailkoppeling | Correspondentie koppelen aan dossiers | allen | e-mails + bijlagen | uitvoering overeenkomst / gerechtvaardigd belang | volgt dossiertermijn | Microsoft 365 (EU), Luxis |
| 4 | AI-conceptcorrespondentie | Concepten van aanmaningen/reacties; advocaat keurt elk stuk | debiteuren, cliënten | relevante dossiercontext per verzoek | gerechtvaardigd belang (efficiënte uitvoering, menselijke controle geborgd) | Anthropic bewaart API-verkeer conform DPA [instelling vastleggen]; Luxis bewaart het concept in het dossier | Anthropic (VS, DPF/SCC) |
| 5 | Backups | Continuïteit/herstel | allen | volledige database | gerechtvaardigd belang | lokaal 7 dagen, off-site 90 dagen | Hetzner (EU); Backblaze (🔴 migratie VS→EU loopt, zie subverwerkers.md) |
| 6 | Foutmonitoring | Storingen opsporen | n.v.t. (PII uitgeschakeld) | technische foutdata | gerechtvaardigd belang | 90 dagen (Sentry-standaard) | Sentry EU |
| 7 | Toegang & audit | Beveiliging, aantoonbaarheid (Voda/Wki) | gebruikers kantoor | accounts, logregels, goedkeuringen | wettelijke plicht / gerechtvaardigd belang | logs ≥ 1 jaar; financiële audit trail 7 jaar | Luxis |

**Beveiligingsmaatregelen:** zie verwerkersovereenkomst §5.
**Doorgiften buiten EER:** alleen Anthropic (DPF/SCC) en tijdelijk Backblaze
(migratie naar EU loopt) — zie `subverwerkers.md`.
**Datalekprocedure:** `datalek-procedure.md`.
