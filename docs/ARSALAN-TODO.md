# Arsalan — openstaande acties

Dingen die wachten op **jou** (of op Lisanne via jou). Vink af wat klaar is.
Bijgewerkt: 10 juni 2026 (na sessie 160).

---

## 🔴 Jij zelf — technisch (uit sessie 159, blokkeert niks maar belangrijk)

### 1. Sentry instellen (crash-meldingen)
- [ ] Gratis account + DSN-sleutel in de server zetten.
- **Waarom:** nu worden serverfouten in productie **nergens** gemeld — je weet pas dat er iets stuk is als een gebruiker klaagt.
- **Hoe:**
  1. Ga naar **sentry.io** → gratis account → nieuw project, kies **Python / FastAPI**.
  2. Kopieer de **DSN** (ziet eruit als `https://xxxx@xxxx.ingest.sentry.io/xxxx`).
  3. Geef die DSN aan mij → ik zet `SENTRY_DSN=...` in `/opt/luxis/.env` op de server en herstart de backend.
- *Het enige dat ik niet kan: het account aanmaken. De rest doe ik.*

### 2. Outlook opnieuw koppelen
- [ ] In Luxis → **Instellingen → E-mail → Outlook opnieuw verbinden**.
- **Waarom:** in sessie 159 is de versleutelingssleutel (`TOKEN_ENCRYPTION_KEY`) gewijzigd. Daardoor zijn de oude opgeslagen Outlook-tokens onleesbaar → e-mailsync werkt pas weer ná opnieuw koppelen.
- **Hoe:** login op **luxis.kestinglegal.nl** (met `seidony@kestinglegal.nl`) → Instellingen → E-mail → opnieuw inloggen bij Microsoft.

### 3. Backblaze B2-bucket regio = EU bevestigen
- [ ] Controleren dat de off-site backup-bucket in een **EU-regio** staat.
- **Waarom:** AVG — debiteur-/cliëntgegevens mogen niet buiten de EU opgeslagen worden.
- **Hoe:** log in op **Backblaze** → bucket → check de **Region/Endpoint** (moet EU zijn, bv. `s3.eu-central-...`). Staat 'ie buiten de EU → meld het mij, dan maken we samen een EU-bucket + passen de backup-config aan.

---

## 🟡 Vragen aan Lisanne (jij stelt ze; nodig vóór livegang)

### 4. Derdengelden — 3 vragen (vóór de derdengeldenmodule live mag)
- [ ] Wie is de **2e stichtingsbestuurder**, en wie wordt de "tweede-paar-ogen"-goedkeurder in Luxis?
- [ ] Staat er een **verrekenclausule** in de opdrachtbevestiging (mag Kesting derdengelden verrekenen met openstaande facturen)?
- [ ] Betalen debiteuren **rechtstreeks op de stichting-derdengeldenrekening**?
- *Achtergrond: `docs/research/derdengelden-regels.md` §5.*

### 5. 14-dagenbrief (H6)
- [ ] Lisanne moet een knoop doorhakken — er staan tegenstrijdige juridische instructies in.

### 6. BaseNet-export klaarzetten
- [ ] Lisanne exporteert haar BaseNet-data (relaties, dossiers, documenten, boekhouding) — nodig voor de migratie naar Luxis. Zij heeft de toegangsrechten, jij/ik niet.

---

## 🟢 Product-input (later, geen haast)

### 7. Algemene voorwaarden per cliënt
- [ ] Voorwaarden van elke **cliënt** (niet van Kesting zelf) aanleveren. De AI valt hierop terug bij betwistingen. Wordt relevant bij de AI-incasso-agent.

### 8. AI-antwoordtemplates fine-tunen
- [ ] Jouw feedback op de 6 standaard AI-antwoordsjablonen (basisversie staat klaar sinds sessie 112).

---

*Optionele tooling-experimenten (Graphify, grill-me skill) staan apart in mijn geheugen — geen actie nodig, alleen als je tijd over hebt.*
