# E-mail echtheidskenmerken kestinglegal.nl — SPF / DKIM / DMARC

**Doel:** voorkomen dat mail van incasso@kestinglegal.nl (verstuurd via Luxis/BaseNet)
bij debiteuren in de spam belandt. Grote ontvangers (Gmail, Outlook.com) eisen sinds
2024 dat een afzender deze drie kenmerken op orde heeft.

**Gemeten stand (8 juli 2026, via publieke DNS):**
- ✅ **SPF** aanwezig: `v=spf1 include:_spf.basenet.nl include:spf.protection.outlook.com -all`
- ❌ **DKIM** ontbreekt volledig (geen enkele selector gevonden — ook niet M365 selector1/2)
- ❌ **DMARC** ontbreekt (`_dmarc.kestinglegal.nl` bestaat niet)

Deze records staan bij de partij die het **DNS** van kestinglegal.nl beheert (BaseNet of de
domeinregistrar). Vraag daar of zij ze plaatsen, of dat jij ze zelf in het DNS-beheer zet.

---

## 1. DKIM — aanvragen bij BaseNet (kan NIET zelf verzonnen worden)

De DKIM-tekst bevat een unieke sleutel die alleen BaseNet's mailserver kan genereren.
Stuur BaseNet dit verzoek:

> "Wij versturen uitgaande e-mail namens kestinglegal.nl via jullie mailserver
> (incasso@kestinglegal.nl). Kunnen jullie **DKIM-ondertekening inschakelen** voor
> dit domein en ons het bijbehorende DNS-record (de selector + waarde) geven dat wij
> moeten publiceren? Of, als jullie ook ons DNS beheren: kunnen jullie het meteen
> plaatsen? Wij willen dat uitgaande mail met een geldige DKIM-handtekening vertrekt."

BaseNet geeft dan een record dat er ongeveer zo uitziet (voorbeeld — NIET zelf invullen,
de echte sleutel komt van BaseNet):

```
Naam:  <selector>._domainkey.kestinglegal.nl
Type:  TXT
Waarde: v=DKIM1; k=rsa; p=<lange sleutel van BaseNet>
```

> Let op: seidony@kestinglegal.nl verstuurt via Microsoft 365. Als díé mailbox ook
> extern mailt, zet dan óók DKIM aan in Microsoft 365 (admin.microsoft.com →
> Beveiliging → E-mailverificatie). Voor de incasso-mail via Luxis is BaseNet-DKIM
> het belangrijkst.

---

## 2. DMARC — dit exacte record kan wél meteen geplaatst worden

Dit is een instructie-regel (geen sleutel), dus die is kant-en-klaar. Plaats in het DNS:

```
Naam:  _dmarc.kestinglegal.nl
Type:  TXT
Waarde: v=DMARC1; p=none; rua=mailto:incasso@kestinglegal.nl
```

**Uitleg per stukje:**
- `p=none` = **monitor-stand**: Gmail e.d. blokkeren nog NIETS, ze rapporteren alleen.
  Dit is bewust veilig gekozen — het kan geen enkele echte mail tegenhouden. Het bestaan
  van dít record is al wat Gmail wil zien.
- `rua=mailto:incasso@...` = (optioneel) hierheen worden technische rapporten gestuurd
  over wie namens jouw domein mailt. Handig om te zien of alles klopt; het zijn saaie
  XML-bestandjes, dus weglaten mag ook: dan wordt de waarde simpelweg `v=DMARC1; p=none;`.

**Later aanscherpen (pas NADAT DKIM werkt):** als de rapporten een paar weken laten zien
dat alle echte mail netjes door SPF + DKIM komt, kan `p=none` worden verhoogd naar
`p=quarantine` (verdachte mail → spam) en uiteindelijk `p=reject` (verdachte mail →
weigeren). Niet eerder — anders riskeer je dat je eigen mail wordt geweigerd.

---

## Volgorde

1. BaseNet: DKIM aanzetten + record plaatsen (of aan jou geven).
2. DMARC-record `p=none` plaatsen (mag meteen, samen met of vlak na DKIM).
3. Een paar weken de rapporten/spam-plaatsing volgen.
4. Pas als alles groen is: DMARC ophogen naar `quarantine`, later `reject`.

Controleren of het gelukt is kan gratis via bv. mxtoolbox.com (zoek op "DKIM" en "DMARC"
voor kestinglegal.nl) of dmarcian.com.
