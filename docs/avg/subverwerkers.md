# Subverwerkers Luxis (bijlage 1 bij verwerkersovereenkomst)

Stand: 7 juli 2026 (avond, S182 — Backblaze naar EU + versleuteld). Bij elke
wijziging: dit bestand bijwerken + Kantoor informeren.

| Subverwerker | Doel | Locatie data | Grondslag doorgifte | Status |
|---|---|---|---|---|
| Hetzner Online GmbH | Hosting VPS (applicatie + database) | Duitsland (EU) | n.v.t. (EU) | ✅ DPA is onderdeel van Hetzner-voorwaarden — kopie archiveren |
| Microsoft Ireland | E-mail (M365/Outlook, Graph-koppeling) | EU-datacenters (M365-tenant) | n.v.t. (EU) + Microsoft DPA (standaard) | ✅ kopie DPA archiveren |
| Anthropic | AI-conceptteksten (dossiercontext wordt per verzoek meegestuurd) | VS (API) | EU-VS Data Privacy Framework / SCC's via Anthropic Commercial Terms + DPA | ⚠️ ACTIE: DPA aantoonbaar accepteren op het API-account; instelling geen-training/retentie vastleggen (screenshot in docs/avg/) |
| Backblaze Inc. | Off-site backup (dagelijkse database-dump + uploads, 90 dagen), client-side versleuteld (rclone crypt: bestandsnamen + inhoud) | **EU (eu-central-003, Amsterdam)** — sinds 7 juli 2026 | n.v.t. (EU-regio; data bovendien versleuteld vóór upload) | ✅ live 7 juli (S182); restore-test geslaagd. Restpunt: oude US-bucket wissen na 2 dagen bewezen EU-runs (≈ 10 juli) |
| Functional Software Inc. (Sentry) | Foutmonitoring backend | EU-regio (Duitsland), `send_default_pii=False` | n.v.t. (EU) | ✅ ingericht S161 |
| GitHub Inc. | Broncode (géén persoonsgegevens; documentatie kan zaaknummers bevatten) | VS | DPF; beleid: geen persoonsgegevens in repo | ✅ beleid handhaven |

## ✅ Backup-actie — UITGEVOERD 7 juli 2026 (S182), één restpunt

Stappen 1-2 zijn klaar: nieuw EU-account (bucket `luxis-backup-eu`, endpoint
`s3.eu-central-003.backblazeb2.com`, lifecycle "keep only last version"),
versleutelde rclone-remote `luxis-backup-eu-crypt` (crypt over `luxis-b2-eu`),
cron omgezet, volledige testrun (db 23 MB + uploads 1,2 GB versleuteld geüpload)
én restore-test via de crypt-remote geslaagd (tellingen exact gelijk aan live:
cases 607 / contacts 1168 / payments 255). Crypt-wachtwoorden: rclone.conf op de
VPS + Arsalans wachtwoordmanager. Runbook `docs/runbooks/restore.md` bijgewerkt.

**Restpunt (≈ 10 juli):** als de EU-backup 2 dagen aantoonbaar draait (checks
8 + 9 juli in `/var/log/luxis-backup.log`): oude US-bucket `Luxis-backup`
volledig wissen, oude application key intrekken, oude rclone-remote
`luxis-backup` verwijderen; wisbewijs in SESSION-NOTES. Daarna ook
`verwerkersovereenkomst-CONCEPT.md` §5 nalopen.
