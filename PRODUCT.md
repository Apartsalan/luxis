# Product

## Register

product

## Users

- **Primair:** Lisanne Kesting — advocaat (incasso/insolventie), eenpersoonskantoor Kesting Legal, Amsterdam. Geen techneut. Werkt 8 uur per dag in de app naast Outlook. Context: dossiers beheren, brieven/e-mails versturen, termijnen bewaken, betalingen verwerken.
- **Secundair (toekomst):** andere kleine Nederlandse advocatenkantoren (1-10 fte). Luxis is een product, geen maatwerk.
- **Beheer:** Arsalan — eigenaar/beheerder, geen developer.

## Product Purpose

Practice management systeem voor Nederlandse advocatenkantoren: dossiers (zaken), relaties, documenten, e-mailcorrespondentie, urenregistratie, facturatie, derdengelden en een incassomodule met juridisch correcte renteberekening (art. 6:119/119a BW), WIK-staffel en betalingstoerekening (art. 6:44 BW). Succes = Lisanne werkt volledig in Luxis in plaats van BaseNet, met minder klikken en minder fouten.

## Brand Personality

Kalm, professioneel, efficiënt. Werkgereedschap in Gmail/HubSpot-stijl: data-dens maar nooit overweldigend. De interface dient het werk en vraagt geen aandacht voor zichzelf. UI volledig in het Nederlands; juridisch jargon alleen binnen vakmodules (incasso), nergens anders.

## Anti-references

- Flashy SaaS-marketing-esthetiek: gradients, glassmorphism, hero-metrics, gradient-tekst. Dit is een werkapp, geen landingspagina.
- Herkenbare "AI-slop" patronen: paarse accenten overal, side-stripe borders, identieke card-grids.
- Legacy juridische software (BaseNet-gevoel): schermen vol velden zonder hiërarchie, verouderde dichte tabellen zonder lucht.
- Consumenten-app speelsheid: confetti, mascottes, joviale toon. Toon blijft zakelijk-vriendelijk.
- Parallelle UI-systemen naast elkaar (oud + nieuw tegelijk zichtbaar).

## Design Principles

1. **Zou een willekeurig advocatenkantoor dit willen?** — elke scherm-beslissing langs deze lat. Kesting-specifiek mag niet inbakken.
2. **Data-dens, niet druk** — veel informatie per scherm is de waarde; hiërarchie en witruimte houden het rustig.
3. **Minder klikken dan BaseNet** — elke workflow gemeten in handelingen; de standaardroute is de snelste.
4. **Vertrouwen door precisie** — bedragen, datums en juridische termen exact en consistent; financiële output op advocatenkantoor-niveau.
5. **Techniek onzichtbaar, resultaat prominent** — AI- en automatiseringsresultaten in beeld, de machinerie erachter niet.

## Accessibility & Inclusion

Niveau: **goede basis** (bewuste keuze, geen formele WCAG-certificering):
- Leesbaar contrast: body-tekst ≥ 4.5:1, geen lichtgrijs-op-wit dat na 8 uur vermoeit.
- Volledig toetsenbord-bedienbaar: Tab-volgorde logisch, focus zichtbaar, formulieren zonder muis invulbaar.
- `prefers-reduced-motion` gerespecteerd (staat al in globals.css).
- Skip-to-content link aanwezig (bestaat al).
- Formele WCAG AA-audit pas wanneer verkoop aan grotere kantoren/overheid concreet wordt.
