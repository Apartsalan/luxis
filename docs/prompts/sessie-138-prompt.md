cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 138 — Wix → TransIP registrar-transfer OF M365 M0b (mailbox Lisanne)

## Context laden bij start

Gebruik de luxis-researcher subagent:
"Lees LUXIS-ROADMAP.md (sectie 'Volgende grote module Microsoft 365 Email Integratie' in docs/future-modules.md) en SESSION-NOTES.md (sessie 137 en 136). Wat is de status van: (a) Wix-DNS blokkade + TransIP transfer plan, (b) M365 M0a status, (c) BaseNet mail-issue Lisanne. Geef compact in <300 woorden."

## Beslissing aan begin van sessie

Twee mogelijke hoofdtaken — kies welke:

**Optie A — Wix → TransIP registrar-transfer (DNS unlock):**
Wix-DNS blokkeert MX-wijziging. Voor finale M365-overgang moet kestinglegal.nl bij TransIP staan zodat MX, SPF en DKIM beheerd kan worden. 5-8 dagen DNS-propagatie. Werk:
1. TransIP account check (of er al een is)
2. Auth-code opvragen bij Wix
3. Domein-transfer aanvragen bij TransIP
4. Wachten op propagatie + nameservers wijzigen
5. MX/SPF/DKIM records overzetten

**Optie B — M365 M0b (Lisanne mailbox overzetten):**
Alleen samen met Lisanne. Werk:
1. Mailbox `lisanne@kestinglegal.nl` aanmaken in M365
2. IMAP-migratie van BaseNet naar M365 (gratis Microsoft tool)
3. Outlook desktop instellen (handmatige IMAP omdat auto-discover faalt)
4. MX-records wijzigen (vereist Optie A eerst, anders blijft mail naar BaseNet)
5. BaseNet email opzeggen na verificatie

**Optie C — Quick-wins backlog** (als Lisanne niet beschikbaar + transfer niet acuut):
- M3+ correspondentie tab UX verbeteringen
- AI-incasso agent prep (knowledge base research is af, kan kleine PoC bouwen)
- Performance tuning (zo nodig)

## Taak

Begin met **Optie A** tenzij Lisanne aangeeft beschikbaar te zijn voor Optie B.

Voor Optie A:
- Geen code-werk eerste 80% — proces is operationeel (auth-code, transfer aanvragen, wachten)
- Documenteer huidige DNS-staat in `docs/dns-transfer-plan.md` (NEW): MX/SPF/A/TXT/CNAME records bij Wix
- Maak terminal-script om DNS-status periodiek te checken (handig voor propagatie-monitoring)
- Geen frontend/backend code-changes nodig tenzij MX-switch dwingt iets op te lossen in mail-provider config

Voor Optie B:
- Werk via terminal + Outlook GUI samen met Lisanne
- Geen code-changes, alleen configuratie

## Verificatie

Voor DNS-werk:
```bash
nslookup -type=MX kestinglegal.nl 8.8.8.8
nslookup -type=NS kestinglegal.nl 8.8.8.8
```

Voor M365 mailbox:
- Test-mail van extern adres naar lisanne@kestinglegal.nl
- Check inbox in M365 + correspondentie-tab Luxis

## Constraints (wat NIET doen)

- Geen MX-wijziging vóórdat M365 mailbox getest is — anders bouncet productie
- Geen Wix-account afsluiten vóórdat domein-transfer compleet is (anders verlies domein)
- Geen rebuild docker images zonder reden (cache benutten, sessie 120 incident)
- Geen code-aanpassingen aan email-providers tenzij MX-switch dat dwingt

## Commit

Commit + push naar main met conventional commit message. Deploy automatisch via SSH zodra er code-changes zijn.

## Sluit met /sessie-einde

Verplicht aan einde sessie.
