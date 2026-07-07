# Subverwerkers Luxis (bijlage 1 bij verwerkersovereenkomst)

Stand: 7 juli 2026. Bij elke wijziging: dit bestand bijwerken + Kantoor informeren.

| Subverwerker | Doel | Locatie data | Grondslag doorgifte | Status |
|---|---|---|---|---|
| Hetzner Online GmbH | Hosting VPS (applicatie + database) | Duitsland (EU) | n.v.t. (EU) | ✅ DPA is onderdeel van Hetzner-voorwaarden — kopie archiveren |
| Microsoft Ireland | E-mail (M365/Outlook, Graph-koppeling) | EU-datacenters (M365-tenant) | n.v.t. (EU) + Microsoft DPA (standaard) | ✅ kopie DPA archiveren |
| Anthropic | AI-conceptteksten (dossiercontext wordt per verzoek meegestuurd) | VS (API) | EU-VS Data Privacy Framework / SCC's via Anthropic Commercial Terms + DPA | ⚠️ ACTIE: DPA aantoonbaar accepteren op het API-account; instelling geen-training/retentie vastleggen (screenshot in docs/avg/) |
| Backblaze Inc. | Off-site backup (dagelijkse database-dump, 90 dagen) | **VS (us-east-005) — VASTGESTELD 7 juli, moet EU worden** | tijdelijk: DPF; doel: EU-regio zodat doorgifte vervalt | 🔴 ACTIE (urgent, zie hieronder) |
| Functional Software Inc. (Sentry) | Foutmonitoring backend | EU-regio (Duitsland), `send_default_pii=False` | n.v.t. (EU) | ✅ ingericht S161 |
| GitHub Inc. | Broncode (géén persoonsgegevens; documentatie kan zaaknummers bevatten) | VS | DPF; beleid: geen persoonsgegevens in repo | ✅ beleid handhaven |

## 🔴 Backup-actie (vastgesteld 7 juli 2026, S181-F)

De off-site backup gaat nu **onversleuteld** naar een **Amerikaanse** Backblaze-regio
(`s3.us-east-005`, bewezen via de API van het account). Dat zijn dagelijkse volledige
databasekopieën met debiteur- en cliëntgegevens. Reparatie (volgorde belangrijk):

1. **Arsalan:** nieuw Backblaze-account/bucket aanmaken en bij het aanmaken expliciet
   **regio EU (eu-central-003, Amsterdam)** kiezen — de regio hangt aan het account en
   is achteraf niet te wijzigen. Nieuwe application key aanmaken (alleen die bucket).
2. **Claude (Opus):** op de VPS een **versleutelde** rclone-remote (`crypt`) over de
   nieuwe EU-bucket configureren, `backup.sh` laten wijzen naar de nieuwe remote
   (env-variabele `RCLONE_REMOTE`), en een testrun + restore-test doen (runbook
   `docs/runbooks/restore.md` volgen — versleuteling verandert de restore-stappen!).
3. Pas als de EU-backup 2 dagen aantoonbaar draait: de oude US-bucket **volledig wissen**
   (alle dumps) en de oude key intrekken; wisbewijs in SESSION-NOTES.
4. `verwerkersovereenkomst-CONCEPT.md` §5 en deze tabel bijwerken.
