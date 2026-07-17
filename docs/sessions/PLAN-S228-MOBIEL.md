# PLAN S228 — Luxis perfect werkbaar op telefoon en tablet

**Datum onderzoek:** 17 juli 2026 (S228, Fable). **Bouwer:** Opus, direct na dit plan.
**Doel:** Lisanne werkt straks dagelijks vanaf haar telefoon. Alles wat zij doet moet
op een telefoon (voorrang) en tablet netjes, snel en zonder gepriegel werken.
**Scope:** alleen frontend + 2 kleine statische bestanden (app-icoon/manifest). Geen
backend-wijzigingen, geen migraties, geen prod-DB-mutaties.

---

## 1. Hoe er gemeten is (bewijs)

Live op productie (luxis.kestinglegal.nl) ingelogd via Playwright op **telefoonformaat
390×844** (iPhone 14/15) en **tabletformaat 820×1180** (iPad Air staand). Van 19
pagina's + 3 vensters (mail opstellen, AI-antwoord, meldingen) + het uitklapmenu is
per pagina de **horizontale overloop gemeten** (`document.documentElement.scrollWidth`
vs. 390) en een schermafbeelding beoordeeld. Aangevuld met code-metingen (grep op
responsive-classes, dialoog-maten, knophoogtes).

### Meetresultaten telefoon (390 px breed; >390 = pagina schuift horizontaal = fout)

| Pagina | Gemeten breedte | Oordeel |
|---|---|---|
| Dashboard | **567** | Overloop onderin (kaartenrij `lg:col-span-3` → 551px breed) |
| Dossierlijst /zaken | **622** | Kaartweergave goed, maar filterbalk duwt de pagina breed |
| Dossier-detail, tab Overzicht | **814** | Ernstig: inhoudskaart 798px breed, hele pagina schuift |
| Dossier-detail, tab Financieel | 390 ✅ | Tabellen scrollen netjes bínnen hun kader (`min-w-[600px]` + overflow-container) |
| Dossier-detail, tab Correspondentie | 390, maar **kapot** | Vaste splitsing lijst 2/5 + leesvenster 3/5 zónder responsive-klassen → beide kolommen ~150/220px, onleesbaar (CorrespondentieTab.tsx r107/118/125/477) |
| Mail /correspondentie | **867** | Lijst + "Terug naar lijst"-patroon bestaat al (r448-468, breekpunt `lg`), maar chips/zoekbalk erboven overloopt; meta-blok in maildetail wringt |
| Incasso werkstroom | 390 ✅ | Tabel scrollt binnen kader, maar op telefoon zie je ~2 kolommen en de rij-acties staan buiten beeld — werkstroom feitelijk onwerkbaar |
| Taken | 390 ✅ | Goed (kaarten) |
| Follow-up | 390 ✅ | Lijst goed; detailpaneel niet apart getest |
| Betalingen | **404** | Kleine overloop (chips-rij) |
| Facturen | 390 ✅ | Goed (kaarten) |
| Agenda | 390 ✅ | Goed (daglijst) |
| Relaties | 390 ✅ | Goed (kaarten) |
| Rapportages | 390 ✅ | Werkt; grote bedragen/periodeknop vallen krap |
| Uren | **404** | Kleine overloop; weekbalk-tekst breekt lelijk |
| Derdengelden | 390 ✅ | Goed |
| Intake | 390 ✅ | Goed |
| Instellingen | 390 ✅ | Goed (subnav stapelt) |
| Nieuw dossier | 390 ✅ | Goed (formulier stapelt, stappenindicator werkt) |
| Login | 390 ✅ | Goed |

### Vensters en vaste elementen (telefoon)

- **E-mail opstellen (compose-dialoog): KAPOT.** Onderste knoppenrij (Bijlage /
  Annuleren / Open in Outlook / **Verstuur**) past niet — de Verstuurknop valt half
  buiten beeld. CC/BCC-knoppen en de Betreft-regel lopen tegen de rand.
- **AI-antwoord-dialoog: GOED.** Past netjes, leesbaar, knoppen volledig zichtbaar.
- **Meldingen-klok: KAPOT.** Popover hangt links buiten beeld (anker `absolute
  right-0` aan de bel + breedte `calc(100vw-2rem)`, app-header.tsx r188); tekst
  afgekapt.
- **Zwevende Timer-knop: HINDERT OVERAL.** `fixed bottom-20 right-4` (floating-timer.tsx
  r193/211/226) ligt op elke pagina over inhoud/knoppen heen.
- **Uitklapmenu (hamburger): GOED.** Lade schuift netjes in, alle items + tellers
  bereikbaar.
- **Zoeken: ONTBREEKT op telefoon.** Het zoekveld in de balk is `hidden sm:flex`
  (app-header.tsx r156) en het menu heeft geen zoekitem → op telefoon is er géén
  ingang naar het globale zoeken (Ctrl+K is toetsenbord-only).
- **Dossier-detail kost 2 schermen "kop"** voordat de inhoud begint (kop + stapblok +
  3 bedragen + 7 actieknoppen + tabbalk).

### Tablet (820×1180 staand)

Grotendeels goed: dossier-detail netjes, mail-pagina gebruikt het terug-naar-lijst-
patroon. Restpunten: bovenbalk mail-pagina overloopt (875 breed, Sync-knop buiten
beeld), incasso-tabel vergt horizontaal scrollen (acceptabel), tabbalk dossier valt
net buiten beeld (Tijdlijn). Liggend (1180 breed) = desktopweergave, geen werk.

### Structurele oorzaken uit de code

1. Geen `min-w-0`/truncate-discipline in flex/grid-rijen → brede kinderen duwen de
   hele pagina breed (dashboard, overzicht-tab, filterbalken).
2. Twee mail-weergaven: de losse Mail-pagina ís responsive gemaakt, de dossier-tab
   niet — zelfde functie, andere code (kruispunt-fout, klasse "route mist huisregel").
3. Dialogen zijn vaste gecentreerde vensters (`max-w-lg/2xl/5xl`); ~30 stuks. Op
   telefoon horen grote dialogen schermvullend te zijn met vaste voet.
4. Aanraakdoelen: standaardknop 36px, klein 32px, icoonknop 36px — onder de 44px-
   richtlijn van Apple/Google.
5. `select`-elementen hebben 14px-letters → iOS zoomt het scherm in bij focus
   (bekende Safari-regel; input/textarea zijn al 16px op mobiel en dus veilig).
   *Niet op fysiek toestel geverifieerd; wel vaste iOS-gedragsregel.*
6. Geen PWA-manifest, geen app-iconen, geen theme-color, geen safe-area-marges
   (iPhone-balk onderaan kan over knoppen vallen). "Zet op beginscherm" geeft nu een
   kaal browserscherm zonder icoon.

---

## 2. Keuzes (één aanbeveling per punt — zo gebouwd tenzij Arsalan anders zegt)

1. **Responsive verbouwen, géén aparte app of aparte mobiele routes.** Alles blijft
   één codebase; per scherm mobiele varianten via Tailwind-breakpoints.
2. **Breekpunt-afspraak:** telefoon = `< md` (768), tablet staand = `md–lg`, desktop =
   `≥ lg` (1024). Sluit aan op wat er al staat (sidebar en mail-split zitten al op `lg`).
3. **Onderste navigatiebalk op telefoon: JA (aanbevolen).** 5 vaste items: Dashboard,
   Dossiers, Mail, Taken, Menu (opent de bestaande lade). Dit is wat Clio/moderne
   SaaS-apps doen en scheelt Lisanne elke handeling twee tikken. Alleen zichtbaar
   `< md`. (Wil Arsalan dit niet: blok 6 overslaan, hamburger blijft de ingang.)
4. **Dialogen: twee sporen.** (a) Generiek vangnet in `components/ui/dialog.tsx`:
   onder `sm` schermvullend (`h-dvh`, inhoud scrollt, kop en voet vast) — alle ~30
   dialogen worden daarmee in één klap bruikbaar. (b) Voor de meest gebruikte snelle
   acties de **shadcn Drawer (Vaul)** als onderschuif-paneel — zie §2b.
5. **Tabellen:** lijsten die Lisanne dagelijks aanraakt (incasso-werkstroom) krijgen
   op telefoon een **kaartweergave**; overige tabellen behouden horizontaal scrollen
   bínnen hun kader met zichtbare scroll-hint. Niet elke tabel wordt herbouwd.
6. **PWA-licht: JA** — manifest + iconen + theme-color zodat Luxis als app-icoon op
   het beginscherm staat en zonder browserbalk opent. **GEEN** service worker, geen
   offline-modus, geen pushmeldingen (bewust; kan later, zie §6).
7. **Timer** verhuist op telefoon naar een kleine knop in de onderbalk-zone die de
   inhoud niet afdekt (minimized chip boven de navbalk, met safe-area-marge).

---

## 2b. Van de plank (GitHub-onderzoek 17 juli, op verzoek Arsalan)

Onderzocht wat de beste bestaande bouwstenen zijn voor telefoon-webapps in onze
stack (Next 15 / React 19 / Tailwind 3.4 / shadcn+Radix). Uitkomst:

**WEL gebruiken:**
- **Vaul / shadcn "Drawer"** (github.com/emilkowalski/vaul, ~8,5k sterren,
  React 19-ondersteuning sinds v1.1.1, laatste release dec 2024; is de officiële
  onderbouw van het shadcn Drawer-component dat Luxis' eigen componentenset al
  volgt). Dit is hét ecosysteem-standaardpatroon "Dialog op desktop, onderschuif-
  paneel met veeggebaar op telefoon" (responsive-dialog-patroon uit de shadcn-docs).
  Toepassen op de snelle acties: notitie, telefoonnotitie, uren loggen, taak,
  filters (dossierlijst), AI-antwoord (mag — was al goed, wordt hiermee néts
  natuurlijker). Installatie: `npx shadcn@latest add drawer` (voegt `vaul` toe) +
  één wrapper `components/ui/responsive-dialog.tsx` met de bestaande
  `useIsMobile`-aanpak. Grote formulier-dialogen (compose) blijven schermvullend
  via het vangnet uit keuze 4a.
- **Next.js ingebouwde PWA-ondersteuning** — géén extra pakket: `app/manifest.ts`
  (Next genereert de webmanifest) + `metadata.appleWebApp` + `icons.apple` in
  `app/layout.tsx`. Let op uit de Next-docs: **iOS negeert manifest-iconen
  volledig** → apple-touch-icon 180×180 en `apple-mobile-web-app-title` zijn
  verplicht, anders toont iOS een schermafdruk-miniatuur als "icoon".
- **Safe-area**: gewoon CSS `env(safe-area-inset-*)` — geen plugin nodig.

**Overwogen en AFGEWEZEN (bewust, geen actie):**
- **Konsta UI** (iOS/Material-componenten op Tailwind, v5.2 juni 2026): mooi voor
  pure mobiele apps, maar het zou een twééde componentenbibliotheek naast shadcn
  betekenen — dubbele stijl, grote verbouwing, desktop-risico.
- **Ionic / Framework7 / React Native**: volledige app-frameworks; veel te zwaar
  voor "bestaande webapp responsive maken".
- **Serwist/next-pwa** (service workers): alleen nodig voor offline/push — bewust
  buiten scope (§6).

Netto: **één nieuwe dependency (vaul)**, de rest is ingebouwd of handwerk dat er
al ligt.

Bronnen: shadcn Drawer-docs (ui.shadcn.com/docs/components/radix/drawer), Vaul-repo
en releases (github.com/emilkowalski/vaul), Next.js PWA-guide
(nextjs.org/docs/app/guides/progressive-web-apps), Konsta UI (konstaui.com).

---

## 3. Bouwblokken (volgorde = prioriteit; telefoon eerst)

> Werkwijze per blok: bouwen → `npx tsc --noEmit` → visuele check op 390 én 820
> (Playwright) → volgende blok. Deploy via SSH na elk samenhangend geheel.
> Kruispunt-regel (skill `breed-testen`): elke fix van een fout-SOORT krijgt een
> wachter — hier is dat de overloop-wachter uit blok 7 die ALLE pagina's dekt.

### Blok 0 — Fundament (klein, raakt alles)
- `app/layout.tsx`: `viewport`-export met `viewportFit: "cover"`, `themeColor`;
  koppeling `manifest.webmanifest`; `apple-touch-icon`.
- `public/`: `manifest.webmanifest` (naam "Luxis", `display: "standalone"`,
  start_url "/", iconen 192/512 + apple-touch-icon 180 — genereer uit het bestaande
  Luxis-logo, vierkant met achtergrondkleur).
- `app/globals.css`: safe-area-variabelen (`env(safe-area-inset-*)`) voor onderbalk,
  timer en schermvullende dialogen.
- `components/ui/select.tsx`: triggertekst `text-base md:text-sm` (iOS-zoom weg).
  Controleer óók losse zoek-inputs die niet het Input-component gebruiken.
- `components/ui/button.tsx`: op touch-formaat grotere tikdoelen — default `h-11`
  onder `md`, `h-9` daarboven (`h-11 md:h-9` in de size-varianten; idem `icon`).
  Visueel nalopen dat desktop niet verandert.
- `components/floating-timer.tsx`: positie `bottom-20 right-4` → op telefoon boven de
  nieuwe onderbalk mét safe-area (`bottom-[calc(4rem+env(safe-area-inset-bottom))]`),
  kleinere minimized chip; mag inhoud nooit blokkeren op de laatste regel van pagina's.
- `components/layout/app-header.tsx`:
  - Meldingen-popover (r188): op telefoon `fixed inset-x-4 top-14` (volle breedte
    onder de balk) i.p.v. `absolute right-0`; desktop ongewijzigd.
  - Zoekknop óók op telefoon tonen (icoon) die het bestaande commando-palet opent.

### Blok 1 — Dialogen (vangnet + Drawer + compose)
- `components/ui/dialog.tsx`: onder `sm` wordt `DialogContent` schermvullend:
  `inset-0 h-dvh max-w-none rounded-none translate-x-0 translate-y-0 grid-rows-[auto_1fr_auto]`,
  inhoud scrollbaar, `DialogFooter` vast onderin met safe-area-padding. Boven `sm`
  exact het huidige gedrag. Alle ~30 dialogen liften mee.
- `npx shadcn@latest add drawer` (dependency `vaul`) + wrapper
  `components/ui/responsive-dialog.tsx` (Dialog ≥`md`, Drawer <`md`); de snelle
  acties uit §2b stapsgewijs omzetten (notitie, telefoonnotitie, uren, taak,
  filters, AI-antwoord). Elke omgezette dialoog visueel checken op 390 én desktop.
- `components/email-compose-dialog.tsx`: voetknoppen herschikken voor telefoon
  (Verstuur volle breedte bovenaan de voet, secundaire knoppen eronder of achter een
  ⋯-menu); Aan/CC/BCC en Betreft stapelen; ontvanger-chips mogen wrappen.
- Steekproef daarna op de 5 meest gebruikte dialogen: AI-antwoord (was al goed —
  mag niet verslechteren), notitie, taak, uren loggen, renteoverzicht (bevat tabel →
  scroll binnen dialoog).

### Blok 2 — Dossier-detail (belangrijkste pagina)
- **Correspondentie-tab** (`CorrespondentieTab.tsx` r107/118/125/477): zelfde
  responsive patroon als de Mail-pagina — onder `lg` toont óf de lijst óf het
  leesvenster met "Terug naar lijst" (r448-468 van `correspondentie/page.tsx` als
  voorbeeld; overweeg de lijst/detail-wissel als gedeelde component zodat dit
  kruispunt niet opnieuw kan ontstaan).
- **Overzicht-tab overloop** (pagina 814px): oorzaak opsporen in de kaarten
  (`min-w-0` + `truncate`/`break-words` op flex/grid-kinderen, lange e-mailadressen
  en bedragen); pagina moet exact 390 meten.
- **Kop compacter op telefoon:** bedragenrij als 3 compacte tegels naast elkaar;
  actieknoppen (7 stuks) op telefoon in één horizontaal scrollende chip-rij of
  achter "Acties ⌄"; stapblok blijft (dat is de kern) maar zonder dode ruimte.
  Doel: inhoud van de actieve tab begint binnen ~1,5 schermhoogte.
- **Tabbalk:** horizontaal scrollen behouden maar met vervaag-rand (scroll-hint) en
  actieve tab automatisch in beeld (`scrollIntoView` bij tabwissel).
- Overige tabs (Facturen/Documenten/Uren/Tijdlijn): zelfde tabel-in-kader-check als
  Financieel; geen herbouw, wel overloop-vrij.

### Blok 3 — Mail-pagina
- Chips-/zoekbalk (r~400): laten wrappen (`flex-wrap`) i.p.v. de pagina breed duwen;
  zoekveld volle breedte op eigen regel op telefoon. Zelfde fix op tablet (875-meting).
- Maildetail-meta ("Van/Aan/Datum"): op telefoon gestapeld zonder kolomgrid dat per
  woord afbreekt; onderwerp mag 2 regels met truncate daarna.
- Beantwoorden/Doorsturen/AI-antwoord-knoppen: bereikbaar zonder scrollen (sticky
  actierij bovenaan het leesvenster op telefoon).
- HTML-briefinhoud: in een kader met `overflow-x-auto` en `max-width:100%` op
  afbeeldingen zodat een brede brief nooit de pagina breekt.

### Blok 4 — Incasso-werkstroom + lijstpagina's
- **Incasso** op telefoon: kaart per dossier (nummer, cliënt→wederpartij, stapbadge,
  hoofdsom, dagen) met checkbox; batch-actiebalk als vaste balk onderaan zodra ≥1
  aangevinkt. "Per stap"-weergave idem kaarten. Tabel blijft voor `≥ md`.
- **Dossierlijst**: filterbalk op telefoon achter één "Filters"-knop (opent de
  (nu generiek responsive) dialoog of wrapt); exportknop onderaan; overloop naar 390.
- **Dashboard**: overloop-oorzaak in de kaartenrij fixen (`min-w-0`/truncate);
  takenregels truncte al goed.
- **Betalingen/Uren**: de 404-overlopen (chips-rij, weekbalk) → wrap/truncate; de
  uren-weekweergave op telefoon als verticale daglijst i.p.v. 7-koloms grid.

### Blok 5 — Restpagina's polijsten
- Rapportages: bedragen laten schalen (kleiner lettertype op smal scherm of
  `tabular-nums` met truncate-vrije kaart), periodeknoppen wrappen; grafieken
  containerbreedte laten volgen (check bestaande chart-lib instellingen).
- Follow-up detailpaneel, intake-detail, relatie-detail, facturen-detail, agenda
  maand-raster (maand → week/agenda-lijst op telefoon als het raster wringt),
  instellingen-tabs met tabellen (sjablonen/producten): overloop-vrij maken; geen
  herontwerp.

### Blok 6 — Onderste navigatiebalk (telefoon)
- Nieuw `components/layout/mobile-nav.tsx`: 5 items (Dashboard, Dossiers, Mail,
  Taken, Menu→opent bestaande lade), alleen `< md`, safe-area-padding, actieve
  status, badge-tellers hergebruiken uit de sidebar-data. Content-container krijgt
  op telefoon onderruimte zodat de balk niets afdekt (samen met de Timer-positie
  uit blok 0).

### Blok 7 — Wachters en bewijs (verplicht sluitstuk)
- **Playwright mobiel project** in `frontend/playwright.config.ts`: project "mobile"
  (viewport 390×844, touch) naast bestaand chromium.
- **Overloop-wachter** `frontend/e2e/mobile-overflow.spec.ts`: loopt álle routes uit
  de pagina-inventaris af en asserteert `scrollWidth === clientWidth` op 390 én 820
  (de wachter voor deze fout-SOORT — elke toekomstige brede pagina valt hierop).
- **Kernflow-tests mobiel** (zelfde spec of apart): inloggen → dossier openen →
  tab Correspondentie → mail lezen → AI-dialoog openen/sluiten → taak-lijst →
  compose-dialoog openen: Verstuurknop volledig in beeld (bounding box check) →
  annuleren. Niets écht versturen.
- `npx tsc --noEmit` schoon; bestaande desktop-e2e blijven groen; CI groen na push.
- **Visuele einddoorloop** op 360 (smalle Android), 390, 820: schermafbeeldingen per
  pagina vergelijken met de startfoto's van dit onderzoek.
- **Live doorklikken door Arsalan op zijn eigen telefoon** (echte iOS/Android-check,
  o.a. de iOS-zoom-aanname en het beginscherm-icoon) — kan pas na deploy.

---

## 4. Definitie van "klaar"

1. Geen enkele pagina meet breder dan het scherm op 360/390/820 (wachter bewijst het).
2. Compose: Verstuurknop en alle voetknoppen volledig zichtbaar en tikbaar op 390.
3. Dossier-tab Correspondentie is op telefoon leesbaar met lijst↔lezen-wissel.
4. Meldingen, zoeken en timer werken op telefoon zonder iets af te dekken.
5. Luxis staat met eigen icoon op het beginscherm en opent schermvullend.
6. Aanraakdoelen ≥ 44px voor knoppen op touch-formaat.
7. tsc + volledige e2e (desktop + nieuw mobiel project) + CI groen; live doorgeklikt
   op prod (testdossier 2026-00006).

## 5. Constraints (blijven gelden)

- MAILSLOT OPEN: niets écht versturen behalve via testdossier 2026-00006 na GO.
- Bayar IN100613 niet aanraken. Geen `git add -A`. Geen prod-DB-mutaties (dit plan
  heeft er geen nodig). Deploy via SSH na commit+push.
- Desktopweergave mag nergens zichtbaar veranderen (alle mobiele klassen onder
  breakpoints; steekproef op 1440 na elk blok).

## 6. Bewust NIET in dit plan (voorstellen voor later, geen actie)

- Service worker / offline-modus / pushmeldingen (pas zinnig als Lisanne erom vraagt;
  vergt ook backend-werk voor push).
- Swipe-gebaren (swipe om te archiveren e.d.) en pull-to-refresh.
- Aparte native app (App Store) — responsive + beginscherm-icoon dekt de behoefte.
- Herontwerp van de agenda-maandweergave tot volwaardige mobiele kalender.
- E-mail-HTML-sanering server-side; hier alleen de weergave-container.

## 7. Bekende beperkingen van dit onderzoek

- Gemeten in desktop-Chrome met mobiele viewport, niet op fysiek toestel: échte
  iOS-Safari-eigenaardigheden (zoom bij focus, 100vh/dvh-gedrag, safe-area) zijn op
  regels-kennis meegenomen maar pas bewezen na de einddoorloop op Arsalans telefoon.
- Follow-up-/intake-detailpanelen en het instellingen-tabblad Sjablonen zijn niet
  individueel geschermafdrukt; ze vallen onder de generieke wachter uit blok 7.
- Schermafbeeldingen van het onderzoek staan in `C:\Users\arsal\m-*.jpeg` /
  `t-*.jpeg` (lokaal, niet in de repo).
