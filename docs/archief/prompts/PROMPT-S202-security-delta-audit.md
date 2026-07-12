# Sessie-prompt S202 — Security- & consistentie-audit van de delta sinds S183

**Model: Fable. 100% read-only (prod-queries mogen, mutaties niet). Output = bevindingen
met bewijs + ernst + fix-recept; repareren gebeurt in een latere Opus/Sol-sessie.**

Aanleiding: de laatste volledige security-audit was S183 (8 juli). Sindsdien zijn er
~16 sessies aan wijzigingen live gegaan (S184–S199) die als geheel nooit door de
security-bril zijn bekeken. Scope = de delta: `git log sessie-183..HEAD` (of de dichtstbij
zijnde tag) bepaalt welke code onder de loep gaat.

## Te auditen (per blok: meten in code + prod, niet redeneren vanaf notities)

1. **Nieuwe/gewijzigde endpoints sinds S183** — dump de route-lijst, diff tegen S183:
   elk nieuw endpoint: auth aanwezig? juiste rol? tenant-scoped in de query zélf (niet
   alleen via middleware)? Denk aan: bulk-status (S199), PowerSearch-zoekroutes (S198),
   afwikkelflow FIN-2, termijn-vooruitblik, mail-compose/send-routes (S185-S187),
   instellingen-routes (mailslot-knop S197).
2. **Het mail-pad (S185-S187)** — versturen als incasso@ via BaseNet-SMTP:
   header/injectie-risico's, is de mailslot-vlag écht fail-safe dicht (DB weg → dicht?),
   wie mag versturen (rollen), lekken logs adressen/inhoud, IMAP-koppeling read-only?
3. **PowerSearch (S198)** — tsquery/SQL-injectie via de zoekterm, tenant-isolatie van de
   zoekindex (kan tenant A snippets van B zien?), rechten (mag élke rol alle 6.500 mails
   + stukken doorzoeken — ook privileged correspondentie?), performance-DoS (pathologische
   zoektermen).
4. **RLS-drift op prod** — élke tabel met tenant_id: RLS aan? (meet op prod, vertrouw niet
   de test); nieuwe tabellen sinds S183 expliciet langslopen.
5. **Rollen-realiteit** — S194 zette alle accounts op admin. Wat betekent dat nu Lisanne's
   eigen account bestaat (S175b)? Matrix `docs/security/rollen.md` vs praktijk; wat kan
   een toekomstige 'medewerker'-rol zien/doen dat niet zou moeten?
6. **Secrets-sweep** — bekende open punt: `.codex/config.toml` met leesbare sleutels
   (untracked, niet in .gitignore). Verder: grep repo + prod-container-env op sleutels/
   wachtwoorden in code, logs, error-messages, frontend-bundles (NEXT_PUBLIC_*).
7. **Stil-falen op de geldpaden sinds S183** — nieuwe betaal/afwikkel/rente-code:
   worden fouten geslikt? (overlap met S200-audit-4 is oké: hier alleen de geldpaden,
   dieper.)

## Verificatie-eisen
- Elke bevinding: bewijs uit déze sessie (query, code-regel, curl-respons met testtoken).
- Exploit-achtige checks alleen niet-destructief en alleen op eigen tenant/testdata;
  géén data wijzigen, niets versturen.
- "Niet geverifieerd" is een geldig label — expliciet gebruiken.

## Output
- `docs/security/S202-delta-audit.md`: bevindingen gerangschikt op ernst
  (kritiek/hoog/middel/laag), elk met fix-recept + geschatte fix-grootte.
- SESSION-NOTES + roadmap bijwerken via `/sessie-einde`.

## Constraints & parallel-protocol
- GEEN mutaties, GEEN mail, GEEN fixes bouwen (ook geen "kleine" — alles naar het rapport).
- Sessies 200 en 201 draaien mogelijk parallel: commit + push NIETS tussendoor;
  `/sessie-einde` pas op het allerlaatst, vlak daarvoor `git pull origin main`;
  bij merge-conflict op SESSION-NOTES/roadmap: eigen entry toevoegen, niets weggooien.
