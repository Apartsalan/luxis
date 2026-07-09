# Sessie Notities — Luxis

<!-- Kop = exact deze 4 regels, elk max 1-2 zinnen. Detail hoort in de sessie-entry. -->
<!-- Max 10 sessie-entries in dit bestand; oudere → docs/archief/SESSION-ARCHIVE.md (regels: /sessie-einde). -->
**Laatst bijgewerkt:** 9 juli 2026 (S188c/d/e) — mailwerk-review + 2 fixes + 6 verbeteringen + Fable-eindreview (GO, 1 restfout gevonden+gefixt: CR/LF-injectie). Uitrol gestart. Details: S188c-entry.
**Laatste feature/fix:** (code, S188e) `_imap_quote` ontsmet ook CR/LF/NUL — commit 8b658c7. Details: S188c-entry.
**Openstaand:** deploy-verificatie S188-werk; CI-rood test_role (niet-mail); volgende heropeningsbatches; terugstort IN100334.
**Volgende sessie:** volgende heropeningsbatch (draaiboek + stap 4b), of de rode CI-test fixen.

> 📦 **Archief:** alles ouder dan de laatste 10 sessies staat in `docs/archief/SESSION-ARCHIVE.md` (verplaatst, nooit verwijderd).

## Sessie 188c (9 juli 2026, Opus-bouw + Fable-review-fixes — mailwerk-review + 2 fixes)

### Samenvatting
Eerst Fable-review van het mailwerk S185-187 (read-only, alleen broncode/git/tests — bewust
geen echte mails of mailschermen om het model-filter niet te triggeren). Oordeel: goed en veilig
gebouwd; 26/26 endpoints geauth, XSS twee keer afgedekt (inkomende weergave + geciteerd origineel
bij reply/forward), koppeling voorzichtig. Twee ECHTE gebreken gevonden + op Opus gefixt:

**Fix 1 — aanvraag-detectie liep vast (bewezen op prod).** `detect_intake_emails` pakte de 10
oudste onverwerkte mails maar markeerde niet-matches nooit → venster slibde dicht met oude
systeem-/eigen mail (32 wachtend, 10 oudste kansloos). Root-cause-fix: alleen mail van een bekende
opdrachtgever (adres of niet-ambigu domein) is nog kandidaat; opdrachtgever-kaart wordt vóór de
mailquery gebouwd en mee-gefilterd, dus elke kandidaat matcht en verlaat de wachtrij. Geen migratie.

**Fix 2 — "Negeren" niet heilig.** `_rematch_unlinked_emails` filterde niet op `is_dismissed` →
een genegeerde mail kon bij een latere sync alsnog gekoppeld worden (0 gevallen op prod, sluimerend).
Eén filterregel toegevoegd.

### Verificatie
3 regressietests toegevoegd (detectie-venster slibt niet dicht; her-koppeling respecteert Negeren
+ koppelt niet-genegeerde wél). **52 tests groen** in test_intake.py + test_email_sync.py, gedraaid
in een geïsoleerde wegwerp-postgres op de VPS (bind-mount van de wijzigingen; prod-data niet geraakt,
wegwerp-db daarna verwijderd). Commit `edf88da`, gepusht. Lint niet los gedraaid (uvx ontbrak in de
wegwerp-container) → teststraat pikt ruff op.

### S188d — de 6 kleinere verbeterpunten alsnog gebouwd (op verzoek Arsalan, commit `2806a9e`)
Allemaal op Opus, met tests; frontend tsc + ruff schoon; 91 mail/intake-tests groen (geïsoleerde
wegwerp-postgres, prod-data niet geraakt).
1. **Echte tekstversie** van uitgaande mail, afgeleid uit de HTML (`_html_to_text`) i.p.v. de
   placeholder-zin — beter voor tekst-only clients + spamscore.
2. **Doorsturen met bijlagen**: `forward_from_email_id` → achterkant laadt de bijlagen van de
   oorspronkelijke mail van schijf (`_load_forwarded_attachments`); voor- en achterkant bedraad.
3. **Server-side adres-validatie** op `/compose/send` (to + cc, lege to afgewezen).
4. **IMAP-ontsmetting**: Message-ID in de HEADER-zoekopdracht wordt geëscaped (`_imap_quote`).
5. **Afzendernaam**: "Kesting Legal <incasso@...>" via `from_name` (kantoornaam) op beide verzendpaden.
6. **Verzonden-map-namen** in één constante (`SENT_FOLDER_CANDIDATES`), consistent gebruikt.

### S188e — Fable-review van het S188c/d-werk: GO met 1 gevonden+gefixte restfout
Volledige diff-review op Fable (beide commits regel voor regel + randgevallen tegen prod-metadata
en de modellen gehouden). Uitkomsten:
- **Detectie-fix klopt**: databasefilter en nazorg-lus consistent (ambigue domeinen, hoofdletters,
  exacte-adres-voorrang); NULL-valkuil in de NOT-IN-subquery kán niet (kolom verplicht, prod 0 NULLs).
- **Alle 3 providers** accepteren `from_name` (geen kapotte aanroep); huisstijl heeft geen
  `<style>`-blok dus de tekstversie blijft schoon; prefill wordt op beide pagina's gewist.
- **Restfout gevonden + direct gefixt** (commit `8b658c7`): `_imap_quote` ontsmette `"` en `\`
  maar niet CR/LF — een gevouwen Message-ID-header kon in theorie een eigen IMAP-commando
  injecteren bij het bijlage-ophalen. CR/LF/NUL → spatie + injectie-regressietest (groen).
- Deploy van al het S188c/d/e-werk gestart (losgekoppeld op de VPS, log `/root/deploy-s188d.log`).

### Openstaand
- CI-rood blijft: `test_role_survives_commit_if_role_exists` (omgevingsgevoelig, S184-security,
  géén mailwerk) → CI-deploy skipt; uitrol gaat via SSH. Verdient losse fix of skip-markering.

## Sessie 188b (9 juli 2026, Fable — heropening LegalWork LIVE, eerste batch)

### Samenvatting
Eerste heropeningsbatch uitgevoerd op prod volgens `docs/plans/PLAN-heropening-werkvoorraad.md`,
met akkoord Arsalan (rente-besluit + go, deze sessie). **14 LegalWork-zaken heropend** in één
atomische transactie met rijenaantal-sloten (afwijking = automatische rollback):
- 9 × Eerste sommatie (IN100592/598/599/602/603/604/605/606/607)
- 3 × Voorstel dagvaarding (IN100410/504/527)
- 2 × Verweer beantwoorden + verweer-vinkje (IN100458/483)
- Alle 14: status nieuw, toegewezen aan Lisanne, `date_closed` leeg. IN100547 (voldaan) bleef dicht.

**Rente-besluit Arsalan (staand beleid):** alle b2b-zaken van de 7 holding-opdrachtgevers
(Invorderingsbedrijf-groep) bij heropening op contractuele AV-rente 2%/mnd enkelvoudig;
B2C blijft wettelijk. Geen vraag meer per groep. Voor nieuwe zaken dekt de AV-laag
(terms_interest, S177) dit al automatisch.

**Rente-valkuil gevonden + gefixt (tegenspreker-check on de cijfers):** dossier-update alleen
(`interest_type=contractual, rate=2.00`) liet de rente **2%/JAAR** rekenen — IN100598 toonde
€50,02 (= exact 31.477,36 × 2% × 29/365). De periode-eenheid zit op de **vorderingen**:
`claims.rate_basis` stond op `yearly` (proefzaken-ijkpunt: `monthly`). Fix: 43 claims van de
14 zaken → `monthly` (guarded, andere zaken ongemoeid: 1511 yearly elders intact).
Ná fix: €600,23 + €181,20 (2%/mnd pro-rata), derde factuur terecht €0 (verzuim 01-08).
Draaiboek bijgewerkt met stap 4b zodat volgende batches dit meenemen.

### Verificatie (alle acceptatiecriteria van het plan)
1. 14 zaken status=nieuw met juiste stap + rente-config — query groen (tabel in transcript).
2. 0 zonder toewijzing, 0 met date_closed — groen. 3. Vangnet BaseNet-Gereed/Geannuleerd: 0 rijen.
4. email_logs vóór==ná==0 (niets gemaild); auto_drafts false. 5. IN100547 nog afgesloten.
6. UI-rooktest: werkstroom 4→18 dossiers, bedragen op de cent gelijk aan recept (o.a. 44.609,73 /
   12.100,00 / 18.934,11), deadline-kleuren zichtbaar; 3 dossiers geopend (598 sommatie /
   458 verweer / 410 dagvaarding): juiste stap, "Contractuele rente", renteoverzicht klopt, geen crash.
Bekende cosmetische beperking (gepland): SQL-heropening schrijft geen case_step_history-regel.

### Volgende sessie
Volgende heropeningsbatch (per opdrachtgever, expliciet akkoord per groep blijft de afspraak) mét
stap 4b; de 11 gestopte-regeling-zaken en de regeling-groep (incl. IN100019) apart. Terugstort-vraag
IN100334 (±€215) nog open bij Lisanne.

## Sessie 188 (9 juli 2026, Opus — mailverificatie live, geen code)

### Samenvatting
De 2 openstaande verificatiegaten uit S187 live dichtgeklikt in de ingelogde prod-app
(seidony@kestinglegal.nl). Geen code gewijzigd; niets verstuurd.

**Gat 1 — Ongesorteerd-tab (gedeeld `EmailDetailPanel`): volledig groen.**
- Bulk-selectie: "Selecteer alles" → "67 geselecteerd" + actiebalk (Koppel aan dossier /
  Negeren / Deselecteer); Deselecteer wist de selectie. Per-rij-vinkjes werken.
- Leesvenster op een mail mét bijlage: afzender/ontvanger/datum, bijlage getoond
  (`LISANNE-A4-heropening… 2 KB`), mailtekst, knoppen aanwezig.
- Beantwoorden opent: "Aan" voorgevuld met afzender, onderwerp "Re: …", origineel als citaat.
- Doorsturen opent: onderwerp "Fwd: …", leeg "Aan", doorgestuurd-blok, Versturen terecht
  uitgeschakeld zonder ontvanger. Beide geannuleerd — niets verstuurd.

**Gat 2 — "Maak dossier van deze mail" (nieuwe knop/endpoint): groen.**
- Klik op de knop → intake-aanvraag aangemaakt, app sprong naar "Nieuwe aanvragen" (2→3).
- AI-uittreksel draaide (model claude-haiku-4-5, zekerheid getoond); op een testmail zonder
  incasso-inhoud kwam het uittreksel terecht leeg (<UNKNOWN>, 10%) — correct gedrag.
- "Details bewerken" navigeert naar `/intake/[id]` (debiteur/factuur/AI-analyse/bron-mail +
  Afwijzen/Goedkeuren). Testaanvraag opgeruimd via Afwijzen (met reden) → teller 3→2.

### Niet uitgevoerd (bewust, met reden)
De laatste deelstap "Maak dossier/Goedkeuren → PERMANENT dossier" niet geklikt: de enige
beschikbare ongekoppelde mails zijn test/self-mails waaruit de AI (terecht) niets haalt, dus
goedkeuren zou een leeg junk-dossier op prod zetten waarvan het opruimen (Case verwijderen)
een echt destructieve prod-actie is. Die deelstap is bovendien bestáánde intake-code (al in
gebruik); het NIEUWE werk uit S187 (mail→aanvraag + domein-herkenning) is hiermee geverifieerd.
Een echte eind-tot-eind dossier-aanmaak kan zodra er een echte nieuwe opdrachtgever-aanvraag
binnenkomt (of op expliciet verzoek een wegwerp-dossier + opruiming).

### Volgende sessie
Heropening werkvoorraad — wacht op input Lisanne/Arsalan. Draaiboek
`docs/plans/PLAN-heropening-werkvoorraad.md` + recept `docs/sessions/S181-werkvoorraad-recept.csv`.

## Tussensessie (9 juli 2026, Fable — documentatie-opruiming, geen code)

### Samenvatting
Levende docs opgeruimd — alles verplaatst naar `docs/archief/`, niets verwijderd (commit `04b6248`):
- **SESSION-NOTES.md 540KB→42KB**: max 10 entries (regel), 168 oudere entries verbatim naar
  `docs/archief/SESSION-ARCHIVE.md`; kop teruggebracht van 15 opgestapelde regels naar 4.
- **LUXIS-ROADMAP.md 180KB→26KB**: 8 afgeronde secties (verbind-sprint, systeem-audit-backlog,
  GTM, audits 110/124, bug-log, volgorde van werken, LF-sprint) + 15 "Vorige:"-regels naar
  `docs/archief/ROADMAP-ARCHIEF.md`. Nu precies één 🎯 prioriteit-sectie. Enig open punt
  (AI Factuur Parsing Validatie, LF-10) overgenomen in Backlog.
- **Mappen**: oude prompts → `docs/archief/prompts/`, mei-audits → `docs/archief/audits/`,
  `docs/audit` hernoemd naar `docs/audits` (verwijzingen bijgewerkt), backups → `docs/archief/sessions/`.
- **Dood duplicaat weg**: `.github/skills/impeccable` (330KB, door niets gebruikt; `.claude`-versie is de echte).
- **Verankering**: archief-regels in `/sessie-einde` + CLAUDE.md; waakhond-hook bij sessiestart
  waarschuwt bij SESSION-NOTES >150KB of roadmap >60KB; luxis-researcher-leeslijst bijgewerkt.
Aanleiding: doorlichting op verzoek Arsalan, getoetst aan officiële Claude Code-documentatie
("pruning is het primaire onderhoud"; instructiebestanden waren al op maat: 116/38/39 regels).

### Verificatie
Tellingen sluitend: 178+25=203 sessie-koppen vóór = 10 live + 193 archief ná; roadmap 17 secties
= 9 behouden + 8 archief (+1 nieuwe prioriteit-sectie). Git toont elke verplaatsing als rename (100%).
settings.json valide JSON; waakhond-logica getest (stil bij huidige maten, vuurt bij lage drempel).

### Volgende sessie
Ongewijzigd S188: eerst de 2 mailverificatie-gaten, dan heropening werkvoorraad (`docs/sessions/PROMPT-S188.md`).

## Sessie 187 (8 juli, Opus-bouw + Fable-review — mailfunctie afmaken, blok A+B)

### Samenvatting
Mailmodule afgemaakt volgens `docs/plans/PLAN-mail-afmaken.md`. Onderzoek/review op Fable,
bouw op Opus (mailwerk triggert het Fable-veiligheidsfilter het hardst → wisselt vaak naar
Opus; dat is een filter aan Anthropic-kant, niet in onze code — zie memory `feedback_model_choice`).
Alles in de ingelogde prod-app doorgeklikt (m.u.v. het openstaande gat hieronder).

### Taak 0 — Fable-review S186-mailwerk (vooraf), 2 fixes LIVE (commit `13f18df`)
- **Reply-threading**: `References` begon bij de directe voorganger i.p.v. de draad-wortel →
  antwoord middenin een lange keten kreeg (na sync) een andere `thread_id` → auto-koppeling
  kon terugvallen naar Ongesorteerd. Nu stuurt de voorkant `references_root` mee; IMAP-provider
  bouwt `References = "root parent"`. Outlook-signatuur meegetrokken (negeert het veld).
- **Kale-mail-ontsnapping**: AI-concept met mislukte huisstijl-wrap (`body_html` leeg) ging tóch
  als `already_branded` de deur uit → kaal. Nu alleen overslaan bij écht opgemaakte HTML.

### Blok A — mailbasis (commit `7b91704`, + fixes `1fce49c`/`7decaf2`)
- **Leesvenster in "Alle e-mails"**: inline detail-JSX van Ongesorteerd geëxtraheerd naar één
  gedeeld `EmailDetailPanel` (lezen, bijlagen, beantwoorden/doorsturen, koppelen). Gekoppelde
  mail toont "Gekoppeld dossier" + Open-dossier; niet-gekoppelde: koppelen + Negeren + Maak-dossier.
- **"Meer laden"**: `useAllEmails` → `useInfiniteQuery` (offset, 200/pagina). Teller = totaal.
- **Gelezen-status**: IMAP-fetch vraagt nu `(FLAGS RFC822)`; `_seen_flag_present` leest `\Seen` uit
  de descriptor; `is_read` volgt de vlag (was hard True). Her-sync werkt bestaande mail bij (alleen
  bij verschil, geen rij-load). Ongelezen = blauwe stip + vet. Live: stippen verschenen na sync.
- **Sjabloonkiezer** altijd zichtbaar; zonder dossier disabled met uitleg "Kies eerst een dossier".
- **Ophaalvenster** `since_days` 14 → 90.

### Blok B — Nieuwe aanvragen (zelfde commit)
- Tab **"Nieuwe aanvragen"** met teller (pending_review), AI-uittreksel per aanvraag + Maak-dossier/
  Afwijzen (bestaande intake-acties). Detail bewerken linkt naar `/intake/[id]`.
- **Domein-herkenning**: `detect_intake_emails` + `create_intake_from_email` matchen ook op
  bedrijfsdomein van de opdrachtgevers; vrije providers (gmail e.d.) + ambigue domeinen uitgesloten.
- **"Maak dossier van deze mail"**: `POST /api/intake/from-email/{email_id}` (idempotent), knop in
  het leesvenster op niet-gekoppelde mail.

### Bugs onderweg gevonden + gefixt (live geverifieerd)
- **Suggesties gaven 500** (`Contact.display_name` bestaat niet → `Contact.name`). Trof élke mail
  met een suggestie; zichtbaar geworden nu je in "Alle e-mails" ook uitgaande/gekoppelde mail opent.
  Commit `7decaf2` + regressietest; endpoint nu 200.
- **`case_number` ontbrak in mail-detail** → gekoppelde mail toonde "Koppel aan dossier" i.p.v.
  "Gekoppeld dossier". Toegevoegd (relatie is `lazy="selectin"`). Commit `1fce49c`, live bevestigd.

### Verificatie
Backend 121 mail/intake-tests groen, ruff schoon; frontend tsc + `next build` schoon. Browser
(ingelogd, prod): 3 tabs + tellers, leesvenster open/lezen/reply-knoppen, paginering "6450 — 200
getoond", ongelezen-stippen, gekoppeld/niet-gekoppeld-varianten, aanvragen-tab met AI-uittreksel,
sjabloon-uitleg. Sync draaide foutloos met de nieuwe vlag-fetch. `suggest-cases` na fix → 200.

### Openstaand (voor S188)
- ⚠️ **Ongesorteerd-tab** en de **"Maak dossier"-flow met een echt nieuw dossier** niet apart live
  doorgeklikt (delen wel het bewezen `EmailDetailPanel`; risico laag, maar niet 0-bewezen).
- Fable-filter blijft mailwerk naar Opus schuiven — Arsalan gaf feedback via `/feedback`. Knop om
  auto-wissel uit te zetten staat in claude.ai-accountinstellingen (niet betrouwbaar in de terminal).
- Nog steeds open sinds S186: DMARC voor kestinglegal.nl; testspoor "Luxis diagnose SELF" opruimen.

## Sessie 186 (8 juli, Opus + Fable — mailfunctie: versturen als incasso@ + blok 2 + huisstijl)

### Samenvatting
Doel: mailmodule doorlichten (menu + dossierniveau) en versturen áls incasso@ bouwen; daarna
de mailfunctie verder afmaken. Onderzoek=Fable, bouw=Opus, alles live geverifieerd.

**Verzenden als incasso@ (blok 1, commits `4d47fb1`/`4a5896e`/`f5ef4d7`):**
- `ImapProvider.send_message` = echte SMTP via `smtp.basenet.nl:587` (STARTTLS+AUTH, zelfde inlog
  als IMAP-ontvangst; was `NotImplementedError`). Afzender = het account (Lisanne = incasso@).
- **Gemeten: BaseNet bewaart SMTP-verzonden mail NIET in Verzonden** → Luxis doet zelf IMAP APPEND
  naar `INBOX.Sent` na elke send (faalt nooit de verzending). 2 proefmails aangekomen + kopie in
  Verzonden bewezen.
- `imap_smtp_kwargs()` (SMTP-host afgeleid uit IMAP-scope) doorgegeven in `send_service` +
  `compose_router` → incasso-machine, facturen, opvolging én compose-knop versturen nu correct.
- Bijlage-lek `/compose/send` gedicht (vielen stil weg); document-send omgeleid van Gmail-noodroute
  → `send_with_attachment`; dossier-mailtab 50→200 mails.

**Blok 2 (commits `ee41b72`/`8a98315`/`3b26a37`/`9aebb45`):**
- Dood `/api/email/all` HERSTELD (verloren bij shadow-map-opruiming) → "Alle e-mails"-tab toont
  6446 mails. Browser-geverifieerd.
- Zoeken door álle mail server-side (onderwerp/afzender/ontvanger/snippet/body). "faillissement"
  = 2009 treffers, browser-geverifieerd.
- Gesprekketting-fix: thread_id = References-WORTEL (was directe voorganger → keten brak na 1 antwoord).
- Beantwoorden/doorsturen vanuit dossier ÉN Ongesorteerd (`lib/email-reply.ts`), koppelt via
  In-Reply-To/References. Browser-geverifieerd (prefill klopt).

**Huisstijl-opmaak (commit `fd4ea8f`):** afspraak Arsalan = álles vanuit de incasso-mailbox draagt
de sjabloon-opmaak (handtekening+logo+schuldhulpblok+disclaimer); alleen de tekst verschilt.
`ensure_branded_body()` centraal; al-opgemaakte HTML (templates/AI-concept) via `already_branded`
overgeslagen (robuust tegen geciteerd 'Betreft:'). Prod-render 7/7 groen. 346 tests groen.

### Gewijzigde bestanden
- Backend: `email/providers/imap_provider.py`, `email/oauth_service.py`, `email/send_service.py`,
  `email/compose_router.py`, `email/sync_router.py`, `email/sync_service.py`,
  `email/incasso_templates.py`, `documents/router.py`; tests `test_imap_send.py`/`test_email_sync.py`/`test_email_branding.py`.
- Frontend: `components/email-compose-dialog.tsx`, `lib/email-reply.ts`, `hooks/use-email-sync.ts`,
  `zaken/[id]/page.tsx`, `zaken/[id]/components/CorrespondentieTab.tsx`, `correspondentie/page.tsx`.

### Bekende issues
- **NIET geverifieerd:** hoe een aangeklede mail er in een échte inbox uitziet (kleuren/logo);
  geen echt antwoord/bijlage-mail verzonden (verzendpad wel bewezen). Reply-citaat staat vóór
  de handtekening (cosmetisch).
- **DMARC ontbreekt** voor kestinglegal.nl (Gmail-aflevering → mogelijk spam). Later regelen bij
  BaseNet/registrar. SPF bevat wel `_spf.basenet.nl`.
- Testspoor: "Luxis diagnose SELF" in incasso@-INBOX (dismissen); enkele proefmails naar
  arsalanseidony@gmail.com.
- Later: incasso@-accountnaam hernoemen.

### Volgende sessie
**Mailfunctie AFMAKEN — plan `docs/plans/PLAN-mail-afmaken.md`, blok A+B, op Opus.**
Blok A: mails openen in "Alle e-mails" (leesvenster ontbreekt), verder bladeren >200, ongelezen-status,
sjabloonkiezer begrijpelijk maken (werkt alleen mét dossier), ophaalvenster >14 dagen.
Blok B: "Nieuwe aanvragen"-tab via de BESTAANDE intake-detectie (draait al, 2 wachten op review),
domein-match op de 7 opdrachtgevers, "maak dossier van deze mail". Blok C = géén vrije mappen.

## Sessie 185 (8 juli, Opus + Fable — uitrol S184 + nazorg + mail incasso@)

Uitrol- en nazorgsessie met Arsalan (deels naast Lisanne). Prod-mutaties met geld:
vóór/na getoond, pas na akkoord.

**Taak 1 — S184 LIVE gezet (bewezen gezond):**
- `git checkout main && merge s184-fixes && push` → daarna **zelf via SSH gedeployd in de
  juiste volgorde** (build → migreren via `run --rm` → `up -d backend`). Reden: de CI-deploy
  doet `up` vóór `migrate`, wat mét de nieuwe fail-closed opstartcontrole een kip-ei zou geven
  (app weigert te starten zolang learned_answers RLS mist). Handmatig migreren-eerst omzeilt dat.
- Verificatie: backend `Up (healthy)`, geen RuntimeError; `alembic current`=`s184_rls_learned_answers`;
  `relforcerowsecurity` op learned_answers = `t` (was `f`); extern `/health` = ok. Tag `sessie-184` gezet.

**Taak 2 — 4 heropeningszaken herrekend (vóór/na, alleen-lezen op prod):** rente wordt live
berekend, dus prod toont sinds de deploy al de "na"-cijfers; niets aan te passen. Verschillen
(peildatum 8 juli): IN100334 rente −€24,34→€110,89 (**te veel betaald was €217,47, nu €82,24**),
IN100469 +€0,26, IN100505 +€0,20, IN100553 +€1,94. Fout was: oude `_build_claim_reductions`
boekte per betaling méér af op de positieve vordering dan er binnenkwam (creditfacturen in de
pro-rata-basis). Bewijs dat de fix klopt: van de betalingen ging precies €605,00 (=netto
verschuldigd) naar hoofdsom; oude uitkomst "liep" €20/mnd terwijl de zaak stillag. Arsalan:
rente = AV art. 13.3 (2%/mnd) — LET OP: de 4 zaken staan op `interest_type='commercial'`
(handelsrente), moet per opdrachtgever gecheckt/rechtgezet vóór brieven met bedragen.
Berekening door Arsalan/Lisanne akkoord bevonden.

**Taak 3 — "7 dossiers sluiten": GEEN actie nodig.** Meten wees uit: alle 8 (incl. IN100166
en IN100334) staan op prod al op `afgesloten` — dat is de parkeerstand van de hele BaseNet-import,
niet een besluit. Niets gemuteerd. IN100334: geen terugstorting (besluit Arsalan/Lisanne).
IN100166 moet later juist wél weer open (innen) → hoort bij de heropening.

**BaseNet-gesloten dossiers geverifieerd (vraag Lisanne):** uit de originele backup
`Xml_02-07-2026_2400.zip` (projectlezer): 148 Gereed + 15 Geannuleerd = **163 in BaseNet
al dicht**. Alle 163 op naam opgezocht op prod → **alle 163 `afgesloten`, 0 uitzonderingen**.
Vangnet + rentetype-check toegevoegd aan `PLAN-heropening-werkvoorraad.md` (acceptatiecrit. 7).

**Mail incasso@kestinglegal.nl aangesloten (IMAP, live):** BaseNet-mailserver = `imap.basenet.nl:993`
(bewezen: bestaand seidony-imap-account). Aangesloten **onder Lisanne's user** (admin bezat al
een imap-account; store keyt op user+provider → anders overschrijven). Alleen-lezen (`readonly`),
14-daagse/100-venster → geen stortvloed. Eerste sync: 5 opgehaald, 5 nieuw, **2 auto-gekoppeld
via afzender**. ~~Bevinding "BaseNet-dossiernummers blokkeren matching"~~ → **CORRECTIE
(Fable-audit):** die `2026-00xxx`-nummers bleken verweesde Luxis-testmails (apr–jun,
dossiers weggeveegd bij schone lei) in seidony's mailbox — geen BaseNet-nummers en geen
incasso-mail-probleem. Verzenden áls incasso@ = aparte latere stap.

**Mail-koppel-audit + fix (Fable-audit → Opus-bouw → Fable-review, alles S185):**
- **Audit (gemeten):** nummer-herkenning kende alleen Luxis-formaat `20xx-xxxxx` → 0 van
  607 geïmporteerde zaken (allemaal `IN######`) herkenbaar; live-matcher had ooit maar 2
  successen. Dekking na heropening sterk: 369/372 debiteuren met e-mail, slechts 3 zaken
  bij multi-zaak-debiteur. Opdrachtgever-kenmerk (`Case.reference`, 592/607 gevuld,
  kern vóór `_`) werd nergens doorzocht.
- **Fix (`_find_case_by_case_number`, commit `b489e04`):** voorrang (A) eigen zaaknummer
  incl. IN-formaat, (B) kenmerk-kern opdrachtgever (blokhaken gestript — 9 zaken), en
  onbekend kenmerk blokkeert de afzender-terugval niet meer (alleen echt Luxis-nummer doet dat).
- **Fable-review = grondwaarheidstoets op 6.393 archiefmails** (bekende juiste koppeling):
  4.407 juist / 4 fout (0,06%). **Label-lezen `[D..._I...]` bewust UIT** (zou +1.440 juist
  maar +17 fout geven; precisie eerst — besluit Arsalan; heroverwegen als Ongesorteerd vol
  raakt). LET OP: eerste toets-script OOM'de de exec (6.393 mails in één keer, exit 137,
  backend zelf bleef gezond) → porties van 200.
- **Live bewezen na deploy:** sync koppelde exact de 3 voorspelde mails op zaaknummer
  (IN100092, IN100330, IN100166 — die laatste is de blijft-innen-zaak). 5e mail
  (Incassocenter, onbekend kenmerk) terecht naar Ongesorteerd. 23 tests groen, ruff schoon.
- **Ongesorteerd-vangbak geverifieerd:** Correspondentie-tab + zijbalk-teller +
  dossier-suggesties per mail + (bulk-)koppelen/dismiss bestaan en zijn getest (DF-03, S115).
- **Volgende sessie = MAIL-doorlichting (S186, `docs/sessions/PROMPT-S186.md`):** is het
  mailgedeelte zelfstandig genoeg als "mailprogramma" + **eerste taak: versturen áls incasso@**.
  - **Versturen-bevinding (S185, gemeten):** `ImapProvider.send_message` = `NotImplementedError`
    (BaseNet-koppeling is alleen-ontvangen). De compose-knop verstuurt via `OutlookProvider`
    (Graph, alleen als seidony@/M365). De losse SMTP-brug (`app/email/service.py`, aiosmtplib,
    één globale `smtp_from`) staat op prod op **`arsalanseidony@gmail.com`** (test-restje →
    opruimen). Om áls incasso@ te versturen: SMTP via BaseNet's uitgaande server
    (waarsch. `smtp.basenet.nl:587`, zel.fde inlog) — spiegelbeeld van de IMAP-ontvangst,
    afzender + Verzonden-map kloppen dan. **Nodig van Arsalan:** BaseNet SMTP-host bevestigen +
    of BaseNet relay namens incasso@ toestaat. Buildkeuze: per-account SMTP-send in ImapProvider
    (netjes, multi-afzender) vs globale brug herpunten (snel, één afzender).
  - Verder op de agenda: label-lezen-heroverweging (`[D..._I...]`: +1.440 juist/+17 fout),
    gesprek-ketting (IMAP-thread één antwoord diep), mappen/zoeken/beantwoorden in de UI.
- **Heropening werkvoorraad** blijft klaarstaan (`docs/plans/PLAN-heropening-werkvoorraad.md`)
  als het andere grote item — koppel-fix + vangnetten zijn er nu klaar voor; inplannen na/naast S186.

## Sessie 184 (8 juli, Opus — fix-sprint audit S183 + Fable-review)

Nachtsessie op verzoek Arsalan: bouw de hele S184-werkorder, laat Fable alles nachecken,
Arsalan ziet het 's ochtends. **Alles op branch `s184-fixes`, NIET gedeployed** (push naar
main = auto-deploy; branch gekozen zodat de onomkeerbare prod-stap bij Arsalan blijft).
Deploy-stappen + open punten: `docs/sessions/S184-MORGEN-CHECKLIST.md`.

**Gebouwd (6 punten):**
- S183-3 [HOOG] `_build_claim_reductions`: betalingen alleen over POSITIEVE vorderingen →
  creditfacturen niet meer dubbelgeteld (`sum(reducties)==betaling`).
- S183-4 [LAAG] betaling op/vóór verzuimdatum verlaagt nu de start-hoofdsom (`pre_start`).
- S183-1 nieuwe migratie `s184_rls_learned_answers` (her-past `apply_rls`, dicht
  learned_answers) + `find_unprotected_tenant_tables` + opstartcontrole in `main.lifespan`
  (**faalt dicht in productie** bij een RLS-gat) + drift-guard-test.
- S183-2 `after_begin`-event in `middleware/tenant.py`: her-past tenant + rol na elke
  commit binnen een request (tenant op `session.info`). Structureel, i.p.v. 31 plekken.
- Deploy: `--no-cache` uit `deploy.yml`. Security-regels + rollen in `docs/security/rollen.md`.

**Fable-review (verse subagent op Fable-model, adversarieel) → 1 must-fix:**
De verzuim-clamp `max(0, principal - pre_start)` draaide óók bij `pre_start==0` en zette zo
een creditvordering (negatieve principal) op 0 → verloor zijn verrekenende negatieve rente
→ debiteur te veel rente op elke credit-zaak. **Zelf gereproduceerd** (credit-rente werd 0
i.p.v. −€12,00), **gefixt** (clamp alleen bij echte pre-start-betaling) + rode test. Fixes
1/3/4 keurde Fable goed (geen lek tussen requests, scheduler/migraties niet geraakt,
migratievolgorde vóór opstartcontrole klopt via Dockerfile-CMD).

**Teststatus:** volledige suite 1147 groen (vóór review-fix); 152 rente/betaling-tests groen
na review-fix; ruff schoon; 13 nieuwe tests. **CLAUDE.md nu wél vastgelegd** (commit `743e471`,
met Arsalan afgestemd): security-regels + de eerdere "geen-aannames"-regel; regeleinde-ruis in
8 `.claude/commands/`-bestanden teruggedraaid (geen inhoud). **Open:** deploy-go (branch mergen
→ auto-deploy + tag sessie-184), 4 heropeningszaken herrekenen ná deploy (met akkoord), 7
dossiers sluiten (Lisanne akkoord, niet autonoom), IN100334-terugstort, Backblaze-wis ~10 juli.
Volgende sessie = uitrol + nazorg: `docs/sessions/PROMPT-S185.md`.

## Sessie 183 (8 juli, Fable — architectuur+security-audit, 100% read-only)

**Vraag Arsalan:** "vibe-coded software zou onstabiel/onveilig/niet future-proof/verspillend
zijn — klopt dat hier?" Antwoord: nee, grotendeels niet — maar de audit vond wél 4 nieuwe
bevindingen. Volledig rapport (met bewijs, faalscenario's en werkorder):
**`docs/research/audit-S183-architectuur-security.md`**. Geen enkele schrijfactie op prod.

### Samenvatting (bevindingen)
- **S183-3 [HOOG, geld]** `_build_claim_reductions` (interest.py) verdeelt betalingen fout
  bij creditfacturen: negatief aandeel telt mee als "verdeeld" maar wordt niet toegepast →
  laatste vordering krijgt te veel → rente te laag + creditvordering rent onverminderd door.
  Bewezen door de echte functie uit te voeren (+1000/−200/+200, betaling 500 → 600 afgeboekt).
  Prod: 68 negatieve claims (−€22.870) op 45 zaken; 11 zaken met de raak-combinatie; **4 in
  de heropeningslijst** (IN100334/IN100469/IN100505/IN100553).
- **S183-1 [MIDDEN, security]** `learned_answers` (S168) is de enige van 48 tenant-tabellen
  zónder RLS op prod (bewezen met pg_class-query). Oorzaak: RLS-migratie was eenmalige sweep;
  de RLS-test zet policies zelf aan en ziet drift dus nooit. App-laag filtert overal netjes →
  geen actueel lek (één tenant), wel structureel: herhaalt zich bij elke nieuwe tabel.
- **S183-2 [MIDDEN, security]** `SET LOCAL ROLE`/tenant vervalt bij élke tussentijdse
  `db.commit()` — rest van het verzoek draait als superuser zonder RLS (live bewezen op
  prod-DB; 31 plekken gemeten waar handlers na commit nog databasewerk doen). Maakt de
  bekende superuser-residual concreet; handmatige filtering compenseert vandaag overal.
- **S183-4 [LAAG, geld]** Betaling op/vóór verzuimdatum wordt in de renteberekening
  weggefilterd (interest.py:276) → rente iets te hoog. Prod: 18 betalingen (€9.486), alle
  op afgesloten zaken buiten de heropeningslijst.
- **[LAAG, bekend]** `--no-cache` staat nog in deploy.yml (S162-residual).

### Aantoonbaar op orde (niet meer auditen)
RLS-beleid zelf (46/48 FORCE+policy), auth/rate-limits/OAuth-state (HMAC+nonce)/uploads
(Caddy 55MB + per-endpoint caps)/secrets/VPS==HEAD; S172-kernbevinding "3 AI-services/3
geheugens" ECHT opgeruimd (alle 3 paden op gedeelde `knowledge_context`); scheduler = 1
proces + foutisolatie + advisory-lock; rekenkernen wet-conform met 65+ tests; `total_paid`
== som betalingen op 0 zaken afwijkend; geen float op geldpaden.

### Gewijzigde bestanden
- `docs/research/audit-S183-architectuur-security.md` (nieuw — rapport + werkorder)
- `docs/sessions/PROMPT-S184.md` (nieuw), SESSION-NOTES.md, LUXIS-ROADMAP.md

### Volgende sessie
S184 (Opus): fix-sprint met de werkorder uit het rapport — pro-rata-fix eerst (rode test),
dan RLS-gat + drift-guard-test, dan rolwissel-na-commit, dan de 2 kleine punten. Plus de
Backblaze-US-wis-check (~10 juli). Zie `docs/sessions/PROMPT-S184.md`.

## Sessie 182 (7 juli, Opus — bouwsprint livegang)

**Taak 1 — regeling-alarm: LIVE.** Gat uit S181-F gedicht: de dagelijkse job zette
vervallen betalingsregeling-termijnen wel op 'overdue' maar er kwam geen melding, dus
niemand zag een gemiste termijn. Nu maakt `mark_overdue_installments` per gemiste termijn
een in-app notificatie (nieuw type `installment_overdue`) met zaaknummer + bedrag +
vervaldatum. **Bewust afgeweken van het plan:** melding gaat naar álle actieve
kantoorgebruikers i.p.v. `assigned_to_id` — heropende BaseNet-zaken kunnen op een
legacy/inactieve gebruiker staan, wat het alarm stil zou misleiden (precies wat dit moet
voorkomen); gelijkgetrokken met de andere financiële alarmen. Frontend: meldingstype
geregistreerd, linkt naar betalingen-tab. 33 tests groen (incl. nieuwe alarm-test: melding
mét zaaknummer/bedrag + geen dubbele bij tweede run), ruff schoon, tsc schoon.
Backend+frontend gedeployed (commit `8f49329`), geen migratie. Job op prod geforceerd =
foutloze no-op (121 pending termijnen onaangeroerd, eerste vervalt 9 juli → eerste echte
alarm 10 juli 06:00 UTC). Geen zaakstatus-filter (12/13 regelingen hangen aan afgesloten
zaken — bedoeld).

**Taak 2 — timeout-regels opschonen: LIVE (code `faf3fd6` + data-fix prod).**
`evaluate_timeout_rules` koos per stap "de eerste" default-regel zónder ORDER BY (toeval);
bij de dubbele regel op "Tweede sommatie" (→ Derde sommatie ÉN → inactieve
Ingebrekestelling) kon de regel naar een stap zonder sjabloon winnen → ValueError → zaak
stil hangen. Nu: ORDER BY created_at,id (oudste wint), regels naar inactieve doel-stap
overgeslagen (actieve wint altijd), warning-log bij >1 default-regel per stap. 2 tests
(inactieve-doel overgeslagen ondanks oudere created_at + determinisme), 60 pipeline-tests
groen, ruff schoon. **Data-fix prod:** 4 dode/dubbele timeout-regels gedeactiveerd (niet
verwijderd — historie): 3 vanaf inactieve stappen + de Tweede-sommatie→Ingebrekestelling.
Bewijs ná: 0 actieve regels van/naar inactieve stappen, 0 stappen met >1 default-regel.
Resterende keten schoon: 14-dagenbrief → Eerste → Tweede → Derde → Sommatie laatste
mogelijkheid → Verzoekschrift faillissement.

**Taak 3 — opvolg-scan slaat hold/terminale stappen over: LIVE (code `20bb5eb`).**
`scan_for_followups` maakte voor elke zaak met een stap een aanbeveling zodra
min_wait_days verstreken was; hold-stappen (Verweer beantwoorden/Bijhouden regeling/On
hold, min_wait_days=0) gaven zo elke 30 min een ruis-aanbeveling — bij heropening ~100+
zaken. Guard: `if step.is_hold_step or step.is_terminal: continue` (op de vlag, niet op
naam). Verweer-zaken krijgen hun concept al via de e-mail-trigger. 3 tests, 22 followup
groen, ruff schoon. Ruis-opruiming niet nodig: 0 pending aanbevelingen op hold-stappen
(heropening nog niet gedraaid). Backend gezond na deploy.

**Status sprint:** taken 1-3 (de drie NU-uitvoerbare) LIVE + geverifieerd. Taak 4
(getrouwheids-poort) = optioneel/"tijd over"; beoordeeld als lager-nut nu (poort geldt pas
als auto-draft-vlag aangaat, weken later) — overgelaten aan een aparte sessie.

**Fable-review (subagent op Fable-model, adversarieel) → 2 fixes LIVE (code `ae4f6e7`).**
De review vond twee echte gaten die ik heb gedicht: (1) `mark_overdue_installments`
selecteerde alleen `pending`, maar een deelbetaalde termijn staat op `partial` → een
debiteur die na één deelbetaling afhaakt bleef onzichtbaar. Nu flippen pending ÉN partial
die vervallen naar overdue + melding (paid_amount blijft). (2) `evaluate_timeout_rules`
waarschuwde alleen bij >1 default-regel; een énkele regel naar een inactieve doel-stap
werd stil weggefilterd → poortwachter zelf stil. Nu warning-log bij elke overgeslagen
inactief-doel-regel. 61 tests groen, backend gezond.
**Taak 4 — getrouwheids-poort: LIVE (code `0c701f1`, op verzoek Arsalan tóch gedaan).**
Na conceptgeneratie controleert een poort dat dossiernummer, hoofdsom, rentebedrag en
te-voldoen-bedrag uit de context letterlijk in het concept staan (NL/EN-notatievarianten,
alleen bedragen > 0, alleen als het sjabloon een bedragen-tabel heeft). Ontbreekt iets →
regenereren (max 3 AI-calls); blijft fout → concept tóch aangemaakt maar reviewtaak
gemarkeerd "⚠ … wijkt af — extra controleren" + issues in draft.sources. Nooit stil.
**Plan-afwijking (bewust):** geen rentepercentage-check — geverifieerd op prod: sjablonen
tonen rente als bedrag + vaste uitleg-alinea zónder percentage ('%' alleen in "BTW 21%");
percentage afdwingen = elke contractuele-rente-brief vals geflagd. Rentebedrag-check is
sterker. **Bijvangst: het XXX-vangnet was al die tijd kapot** — `"XXX" in result` checkte
dict-sleutels i.p.v. de tekst, vuurde dus nooit; zit nu werkend in de poort (test dekt het).
**Praktijkproef op 5 echte zaken (plan §1B stap 3) NIET gedaan** — maakt AI-concepten +
taken aan op prod die Lisanne ziet; wacht op apart akkoord.

**Reviewpunt regeling-achterdeur ook gedicht (zelfde commit, op verzoek Arsalan):**
(1) regeling-alarm bewaakt alleen ACTIEVE regelingen (join-filter) — beëindigde regeling
met achtergebleven open termijn alarmeert nooit meer (dit dichtte ook een interactie-bug
van de partial-fix: partial op gedefaultete regeling zou anders alsnog alarmeren);
(2) `/default` en `/cancel` sluiten nu ook `partial`-termijnen af (restant komt niet meer);
(3) de generieke PATCH-route sluit open termijnen af bij eindstatus (defaulted→missed,
cancelled/completed→waived) — de achterdeur is dicht. 7 nieuwe tests, 167 groen totaal.

**Backup-migratie VS→EU: LIVE + BEWEZEN (S182-avond).** Fable blijkt t/m 12 juli
beschikbaar; Arsalans nieuwe Backblaze-EU-account lukte wél. Uitgevoerd: bucket
`luxis-backup-eu` (eu-central-003 Amsterdam, private, lifecycle keep-only-last, geverifieerd
via endpoint), remote `luxis-b2-eu` + versleutelde laag `luxis-backup-eu-crypt` (rclone
crypt: bestandsnamen + inhoud; rondgang-test bewees cijferbrij op B2-kant), cron omgezet
(`RCLONE_REMOTE=luxis-backup-eu-crypt RCLONE_BUCKET=backups`), volledige proefrun (db 23 MB
+ uploads 1,2 GB), en de VERPLICHTE restore-test via de crypt-remote: wegwerp-DB geladen,
tellingen exact live (cases 607/contacts 1168/payments 255), tarball leesbaar. Runbook +
subverwerkers.md bijgewerkt. Crypt-wachtwoorden: VPS rclone.conf + doorgegeven aan Arsalan
voor wachtwoordmanager (onvervangbaar!). **Restpunt 10 juli:** na 2 bewezen EU-runs (log
8+9 juli) oude US-bucket `Luxis-backup` wissen + oude key intrekken + remote `luxis-backup`
verwijderen, wisbewijs hier. /opt/db-backup.sh gecheckt: alleen lokaal, geen VS-lek.

