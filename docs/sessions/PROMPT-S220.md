cd Documents\luxis && claude --dangerously-skip-permissions

Sessie 220 — Bouwsprint demolijst (Opus) — volgens onderzoek S219

## Start
Draai eerst `/sessie-start` (leest roadmap + sessienotities via subagent, scant modules,
laadt de verbindingskaart). Ga daarna zonder te wachten door met de taak hieronder.
Extra taak-context: **`docs/sessions/S219-onderzoek.md`** (alle oorzaken + vindplaatsen,
gemeten) en `docs/sessions/DEMOLIJST-S218.md` (status per punt). NIET opnieuw uitzoeken
wat daar al staat — de vindplaatsen (bestand:regel) staan in het rapport.

## ⚠️ Voorrang-check EERST
Vraag Arsalan: **is de KvK-productiesleutel binnen?** (15 juli: "nog ~een week".)
JA → eerst de rechtsvorm-backfill (draaiboek `docs/archief/prompts/PROMPT-S217.md`),
daarna dit. NEE → direct door.

## Werkwijze
Blokken in deze volgorde (aflopend risico/waarde), per blok: bouwen → tests → deploy →
visueel checken. Kom je niet door alles heen: netjes afronden waar je bent, rest is S221.
Bij elk blok geldt de S219-les: **fix het patroon op ALLE routes, niet alleen de gemelde.**

### Blok 1 — Verzendpad-fundament (hoofdvondst N1 + punten 1/2/3/4/5/25)
1. **Afzender-vangrail**: compose-send (`compose_router.py` /send) én documents-send
   (`documents/router.py:512`) versturen voortaan via het kantoor-account
   (`get_tenant_send_account`, patroon B13 zoals batch/followup), met terugval op het
   eigen account als er geen kantoor-account is.
2. **Logging op compose-send**: EmailLog + SyncedEmail + CaseActivity, zoals
   `send_with_attachment` dat doet (overweeg de route er gewoon doorheen te leiden —
   één gedeelde verzendfunctie is het doel). Daarmee wordt de verstuurde mail zichtbaar
   op dossier-tijdlijn + Correspondentie (basis voor punt 17).
3. **Punt 1/25 — brieftype zonder sjabloonkeuze**: bij een VERSE dossier-mail aan de
   debiteur zonder template_type het brieftype afleiden uit de huidige pijplijnstap
   (ontwerp in SESSION-NOTES S218: antwoord/doorsturen blijft zonder bijlage;
   recipient-check op debiteur; GEEN factuur-auto-attach op deze route). Renteoverzicht
   + (bij verzoekschrift-stap) concept-verzoekschrift gaan dan automatisch mee (punt 12).
   Ook het documentenroute-gaatje: 'sommatie'-brieftype toevoegen aan de bijlage-typeset.
4. **Punt 2 — bijlagen zichtbaar**: compose-venster toont vóór verzending welke bijlagen
   automatisch meegaan (rente-PDF, facturen, verzoekschrift) — serverlogica spiegelen of
   een preview-endpoint.
5. **Punt 4 — CC/BCC**: (a) CC-invoerveld commit een getypt adres automatisch bij
   verzenden (nu alleen op Enter/komma → stil verlies, email-compose-dialog.tsx:865/664);
   check het To-veld op hetzelfde patroon; (b) BCC toevoegen over de hele keten
   (ComposeRequest + outlook.py + imap_provider.py + .eml-route + dialog). Test die
   bewijst dat CC/BCC daadwerkelijk op de mail staan.
6. **Punt 5 — één onderwerp-bouwer**: gedeelde functie "{klant} / {debiteur} — {brieftype}
   — {dossiernummer}", aanroepen op alle 5 routes (S219-rapport noemt de 5 huidige formaten).

### Blok 2 — Stap-teksten & sjablonen saneren (punten 6-11 + 12-rest)
1. **De 6 stap-mailteksten in `incasso_pipeline_steps`** (DB!) herschrijven: handtekening/
   adres via kantoor-context i.p.v. hardcoded IJsbaanpad/kesting@ (of: handtekening bij
   generatie centraal aanhaken en uit de stap-teksten strippen — kies wat de AI-prompt
   "footer nooit wijzigen" heel laat), aanhef vast erin (3 missen er een), lege
   BaseNet-onderwerp-slots vullen via de onderwerp-bouwer. Dit fixt ook ALLE toekomstige
   AI-concepten. Migratie/seed-script zodat het reproduceerbaar is.
2. **BV-naam uit de aanhef**: `vaststellingsovereenkomst` + `faillissement_dreigbrief`
   (incasso_templates.py:1038/1109) + `verzoekschrift_faillissement.docx`.
3. **Klant-kenmerk ("Uw kenmerk")** uit de 5 DOCX-debiteurbrieven + e-mail-basislayout.
4. **Aanhef-stijl** gelijktrekken (kies "Geachte heer/mevrouw," — met Arsalan afstemmen).
5. **Opmaak**: AI-concepten échte HTML-tabellen laten maken (geen spatie-uitlijning);
   DOCX document-default Courier → Calibri (styles.xml, `_generate_templates.py`).
6. **verzoekschrift_bijlage** vervangen door de juiste PDF uit de projectmap
   ("CONCEPT VERZOEKSCHRIFT FAILLISSEMENT (aangepast 1612).pdf").
7. ⚠️ **Beslispunten Lisanne vóór dit blok live gaat**: klopt de Rabo-derdengelden-
   rekening in het verzoekschrift nog (kantoor zit op KNAB)? Kloppen EUR 2.195,00 /
   € 412,61 nog? Antwoorden verwerken (bij voorkeur: uit instellingen laten komen).
8. Ná sanering: de 8 open 'generated' AI-concepten zijn verouderd (oud adres) —
   regenereren of afvoeren (met akkoord Arsalan, zie blok 3).

### Blok 3 — Zombie-opruiming (punt 13 + vondst N3/N4)
1. **Bij elke stap-wissel**: open follow-up-adviezen ÉN open AI-concepten van de oude
   stap automatisch afsluiten (reden "stap al uitgevoerd buiten follow-up"), zodat de
   scanner weer vrij is en niemand een oude sommatie dubbel verstuurt.
2. **Dedupe**: nieuwe conceptgeneratie voor dezelfde zaak+stap toont het bestaande
   concept i.p.v. een tweede te maken (IN100521 had er 2 identiek).
3. **Backfill** (met akkoord): 3 verouderde adviezen (IN100607/IN100613/IN100521) +
   verouderde concepten afsluiten; 470 pending classificaties van vóór go-live (13-07)
   bulk-afsluiten; 14 intake-ruiskandidaten afwijzen.
4. **Taken (punt 23)**: weergave voor overgeslagen taken + herstel-knop
   (skipped/completed → pending) + undo-toast direct na de pijltjes-klik.

### Blok 4 — AI-keten sneller & slimmer (punten 19/20/21/24 + 15)
1. Classificatie direct ná de mailsync triggeren (race weg; latency → ~5 min).
2. **Auto-concept weer AAN per categorie** (staat uit in orchestrator.py:78) — eerst
   kort met Arsalan afstemmen welke categorieën; nooit auto-verzenden, alleen klaarzetten.
3. Punt 21: verweer-type "identiteits-/informatievraag" + promptregel "beantwoord
   letterlijke vragen concreet (klantnaam, factuurnummers, leveringscontext)" —
   `defense_types.py` + `incasso_email_prompts.py`.
4. Punt 20: voortgangsindicator bij genereren + bestaand-concept-check (blok 3.2);
   optioneel prompt slanker.
5. Punt 15: timeout Eerste→Tweede 7 → 4 dagen (step_transitions, één UPDATE na akkoord).
6. Eén review-scherm: classificatie + concept naast elkaar, goedkeuren+uitvoeren in
   één klik (approve-and-execute-endpoint bestaat al).

### Blok 5 — Fasebalk + kleine UX (punt 14/17/18 + S218-UX-restanten)
1. **Fasebalk (punt 14)**: vervang de 5-vinkjes-balk door huidige stapnaam +
   categoriekleur + "X dagen in deze stap" (step_entered_at) + volgende stap
   (`DossierHeader.tsx`; concurrent-onderbouwing in S219-rapport).
2. Punt 18: zaaknummer klikbaar in de mail-LIJSTrij (detailpaneel heeft de link al).
3. Punt 17: tijdlijn-mailregel klikbaar → preview (kan pas na blok 1.2-logging).
4. S218-UX-restanten (uit PROMPT-S218, nooit uitgevoerd): follow-up dossiernummer-link
   in de tabel + echte dagen-kolom + sorteerbare koppen; menu-item Intake weg (Mail-tab
   "Aanvragen" is de ingang) + intake-detectie dempen; menu "Bankimport" → "Betalingen";
   rapportage-label "Incassoratio" → "Geïnd op lopende zaken" + tooltip; agenda-blok
   lege staat; soft-delete-banner op verwijderd dossier.

### Blok 6 — Beslismemo b2b/b2c (punt 16, geen code)
Memo voor Lisanne: de 105 BaseNet-B2C-spoor-dossiers (lijst per dossier uit
`Xml_02-07-2026_2400.zip`), wat er verandert bij omzetten (14-dagenbrief-plicht, BIK+BTW,
consumentenrente, WIK-bijlage), advies + vraag. Koppel aan de KvK-backfill.

## Verificatie
- Backend: `docker compose exec backend pytest tests/ -k "compose or send or draft or followup or template" -v`
  (vol alleen bij refactors); lint lokaal `uvx ruff check app/` vóór push.
- Frontend: `cd frontend && npx tsc --noEmit && npm run build`.
- Per blok visueel op prod. Verzend-tests ALLEEN naar eigen adressen (testdossier
  2026-00006, debiteur = Arsalans gmail) — mailslot staat OPEN, echte debiteuren zijn bereikbaar!
- Blok 1-bewijs: testmail via de verstuurknop → From = incasso@, mail zichtbaar op
  tijdlijn + Correspondentie + email_logs.

## Constraints (wat NIET doen)
- Geen echte debiteuren mailen; de 12 échte follow-up-aanbevelingen niet uitvoeren/afwijzen.
- Prod-data-mutaties (backfills blok 3.3, 7→4, stap-teksten): eerst dry-run/telling + GO Arsalan.
- Geen nieuwe afhankelijkheden. Geen `git add -A` (expliciete paden).
- Beslispunten (derdengelden-IBAN, kosten, aanhef-stijl, auto-concept-categorieën) niet
  zelf beslissen — vragen.

## Commit
Per blok commit + push (conventional commits, expliciete paden). Deploy zelf via SSH
(skill `deploy-regels`). Sluit af met `/sessie-einde`.
