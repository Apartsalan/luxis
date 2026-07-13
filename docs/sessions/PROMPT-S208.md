cd Documents\luxis && claude

# Luxis — S208 (waar we gebleven zijn na 13 juli)

**Lees eerst, in deze volgorde:**
1. `HANDOVER-NIEUWE-MACHINE.md` — alleen als dit een nieuwe computer/nieuw account is (wat
   installeren, wat weglaten).
2. `WERKWIJZE.md` — hoe je hier communiceert en werkt (harde regel: gewoon Nederlands, geen
   computertaal; meet in de bron; spreek jezelf tegen; blijf binnen de opdracht; rond af met bewijs).
3. `SESSION-NOTES.md` — de entries "S207c" en "S207d" bovenaan = de meest actuele stand.
4. `LUXIS-ROADMAP.md` — de prioriteit-sectie.

## Wat er op 13 juli LIVE is gezet (klaar, niet opnieuw doen)
- Renteberekening gereviewd; klopt op de cent met BaseNet.
- 79 consumentenzaken teruggezet van 2%/maand naar wettelijke rente (juridisch veiliger).
- Alle 580 gesloten zaken hebben een rente-stopdatum gekregen (spookrente −€531k).
- Elke zaak toont nu zijn BaseNet-herkomst ("Nog te openen" vs "archief") én werkfase.

## Hoofdtaken S208 (in deze volgorde)

1. **KRITISCHE HER-AUDIT VAN DE BASENET-EXPORT (hoge prio, Arsalan).** Bij het vorige werk bleek
   twee keer dat de import velden liet liggen of verkeerd las (de rentedatum; de werkstatus
   "Procedure loopt" die onder de verkeerde hoofdgroep hing). Arsalan: *"er is blijkbaar toch veel
   wat niet mee is genomen."* → Ga **veld voor veld** door het exportbestand
   `Xml_02-07-2026_2400.zip` (staat in de projectmap) langs wat Luxis ervan heeft overgenomen.
   Meet in de bron, neem niks aan. Breng in kaart: wát is niet geïmporteerd, en is dat nodig?
   Bron-parser: `scripts/basenet/parse.py`; mapping: `scripts/basenet/mapping.py`; bestaande
   matrix: `docs/research/S201-volledigheidsmatrix.md`. Lever een overzicht op, geen bulk-import
   zonder akkoord.

2. **WIK-rentebijlage bij de eerste sommatie** (alleen VOF/eenmanszaak/particulier). Plan ligt klaar;
   **wacht op de KvK-API-koppeling** (Arsalan vraagt aan). Bouwen kan al beginnen zónder de koppeling
   (rechtsvorm dan voorlopig handmatig per zaak). Zie SESSION-NOTES voor de aanpak.

3. **Invoer van nieuwe zaken** = verse BaseNet-export nodig + een kleine aanpassing zodat nieuwe
   zaken als actieve werkvoorraad binnenkomen in plaats van als archief.

**Voorstel (klein, nog niet gebouwd):** filter "Nog te openen" bovenaan de dossierlijst voor de
fase-heropening.

## Grenzen
- Prod-datamutaties (imports, correcties): eerst een proefdraai zonder opslaan + reservekopie +
  akkoord Arsalan, per geval.
- Mailslot staat DICHT — niet openzetten.
- Taal naar Arsalan: gewoon Nederlands, geen vaktermen (harde regel — zie `WERKWIJZE.md`).
