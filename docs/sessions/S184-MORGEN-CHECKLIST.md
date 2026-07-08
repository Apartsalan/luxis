# S184 — Morgen-checklist (fix-sprint af, wacht op jouw deploy-go)

*Opgesteld nacht 8 juli 2026 (Opus bouwde, Fable reviewde). Alles staat op branch
`s184-fixes` — **NIET gedeployed**. Een push naar `main` deployt automatisch, daarom
heb ik het bewust op een branch gehouden zodat jij eerst kijkt.*

## Wat er gebouwd is (alle 6 werkorder-punten)

1. **[HOOG] Rekenfout creditfacturen opgelost** — betalingen worden nu alleen over
   positieve vorderingen verdeeld; een creditfactuur telt niet meer dubbel.
2. **[LAAG] Betaling op/vóór verzuimdatum** — verlaagt nu de hoofdsom i.p.v. genegeerd.
3. **Beveiligingsvangnet dicht** — de tabel die het miste (geleerde antwoorden) krijgt het
   vangnet via een migratie; plus een **opstartcontrole die in productie weigert te starten
   als een tabel het vangnet mist** (faalt zichtbaar i.p.v. stil lekken) + een test die
   drift vangt.
4. **Vangnet valt niet meer weg na tussentijds opslaan** — structureel gefixt op één plek
   i.p.v. 31.
5. Trage-deploy-instelling (`--no-cache`) verwijderd.
6. Beveiligingsregels + rollen-overzicht vastgelegd (`docs/security/rollen.md`).

## Fable-review: 1 must-fix gevonden én opgelost
Fable (verse, onafhankelijke lezing) keurde fixes 1, 3 en 4 goed, maar vond dat mijn
verzuim-fix (2) per ongeluk de **negatieve rente van een creditfactuur op nul zette** —
dat zou de debiteur op elke credit-zaak te veel rente laten betalen. **Direct gecorrigeerd**
(clamp draait nu alleen bij een echte vroege betaling) + rode test toegevoegd. Zelf
nagerekend: creditrente is weer −€12,00 zoals hoort, de andere randgevallen kloppen.

## Teststatus
- Volledige suite: **1147 groen** (vóór de review-fix; die fix zit in de rekenkern).
- Na de review-fix: **152 groen** op alle rente/betaling-suites (dekt de gewijzigde code).
- Ruff schoon. Migratieketen: één head (`s184_rls_learned_answers` bovenop `s177`).

## Deploy-go (als jij akkoord bent)
De veiligste weg — merge de branch, dat triggert de automatische deploy (build → up →
migratie → healthcheck):
```
cd Documents\luxis && git checkout main && git merge s184-fixes && git push origin main
```
> **Let op — nieuw gedrag:** de app **weigert nu te starten in productie** als een
> tenant-tabel het RLS-vangnet mist. Dat is bedoeld (fail-closed bij PII), maar het
> betekent: als de migratie om welke reden niet draait, faalt de deploy zichtbaar (geen
> stille livegang met een gat). De deploy draait de migratie automatisch vóór de app start,
> dus normaal gaat dit goed. Bij twijfel: check na de deploy
> `ssh ... "cd /opt/luxis && docker compose logs backend --tail 20"`.

## Nog open (jouw beslissing / mensenwerk)
1. ~~CLAUDE.md security-sectie niet gecommit~~ → **AFGEROND** (8 juli, met Arsalan
   afgestemd): security-regels + de eerdere "geen-aannames"-regel zijn vastgelegd in
   CLAUDE.md (commit `743e471`); de regeleinde-ruis in de 8 `.claude/commands/`-bestanden is
   teruggedraaid (was geen inhoud).
2. **7 dossiers sluiten** (Lisanne akkoord: alle behalve IN100166). Bewust NIET 's nachts
   autonoom gedaan (prod-mutatie). Kleine, omkeerbare actie — zeg het woord, dan doe ik het.
3. **IN100334 ±€215 te veel betaald** — terugstorten? Vraag aan Lisanne (staat in het A4).
4. **De 4 heropeningszaken herrekenen** (IN100334/IN100469/IN100505/IN100553) ná de deploy:
   de creditfactuur-fix verandert hun rentebedrag. Ik laat eerst een vóór/na-vergelijking
   zien; bedragen pas aanpassen met jouw akkoord.
5. **~10 juli:** Backblaze US-bucket wissen — check of `/var/log/luxis-backup.log` op 8+9
   juli twee geslaagde EU-runs toont.

## Daarna
Heropening werkvoorraad = aparte sessie (S185, draaiboek
`docs/plans/PLAN-heropening-werkvoorraad.md`), ná de deploy en de herrekening.
