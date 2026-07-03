---
name: deploy-regels
description: Deployment regels en commando's voor de Luxis VPS
---

# Deploy Regels

## SSH Toegang
- **Host:** root@46.225.115.216
- **Key:** `~/.ssh/luxis_deploy` (passphrase-vrij)
- **SSH commando:** `ssh -i ~/.ssh/luxis_deploy root@46.225.115.216`
- **Productie URL:** https://luxis.kestinglegal.nl
- **App pad op VPS:** `/opt/luxis`
- `COMPOSE_FILE` staat in `.env` → gewoon `docker compose` werkt

## Autonome deploy (Claude doet dit zelf)

Na commit + push → deploy automatisch via SSH. Geen commando aan gebruiker geven.

### Alleen frontend:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build frontend && docker compose up -d frontend && docker image prune -f"
```

### Alleen backend:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend && docker compose up -d backend && docker image prune -f"
```

### Backend + migraties:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend && docker compose run --rm backend python -m alembic upgrade head && docker compose up -d backend && docker image prune -f"
```

### Alles:
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && git pull && docker compose build backend frontend && docker compose run --rm backend python -m alembic upgrade head && docker compose up -d && docker image prune -f"
```

**VOLGORDE CRUCIAAL: eerst `build`, dán migreren.** `alembic upgrade` vóór de build kan op een oude toestand draaien → migratie stil overgeslagen (S167 live tegengekomen). De CI-auto-deploy (`deploy.yml`) doet het goed: build → up → exec migrate.

> ⚠️ **S168-correctie — er IS wél een source-mount (i.t.t. wat hier eerder stond).**
> `docker inspect luxis-backend` toont bind-mounts: `/opt/luxis/backend/app → /app/app` en
> `/opt/luxis/backend/alembic → /app/alembic`. Gevolgen die je moet kennen:
> 1. **`git pull` ververst de codebestanden in de container meteen** — géén rebuild nodig om
>    de *bestanden* te wijzigen.
> 2. **Maar uvicorn draait ZONDER `--reload`** → het draaiende proces houdt de oude code in
>    geheugen. Een codewijziging wordt pas actief na een **herstart** van de container.
> 3. **`docker compose up -d` herstart NIET altijd** (als het image niet wijzigt, is het een
>    no-op). In S168 bleef het proces na de deploy op de oude code draaien.
> 4. **Praktijkregel: verifieer ná elke code-deploy dat het proces echt herstartte** —
>    `docker inspect luxis-backend --format '{{.State.StartedAt}}'` moet ná je push liggen.
>    Zo niet: `docker restart luxis-backend` (veilig bij mount + geen nieuwe migratie).
>    Verifieer dat de nieuwe code draait, niet alleen dat het bestand gewijzigd is.
> 5. **Los script draaien** (bv. import) importeert altíjd verse code (los python-proces),
>    dus dat merkt de niet-herstart niet — alleen de scheduler/webserver wel.
>
> **Open vraag (S169):** is deze source-mount in prod bedoeld of een dev-override die per
> ongeluk draait (zie bekende-fouten #28, `COMPOSE_FILE`)? Uitzoeken — het bepaalt of de
> "code in image"-aannames elders kloppen.

## `--no-cache` — wanneer wel / niet

**Standaard: GEEN `--no-cache`.** Docker's layer cache is betrouwbaar met onze Dockerfiles (deps eerst, code pas daarna). Sessie 120 incident: elke sessie met `--no-cache` bouwt ~20-30GB aan build-cache die niet wordt opgeruimd → na 4 sessies was de VPS 143GB vol en Postgres crash-loopte.

**Alleen `--no-cache` bij:**
- `pyproject.toml` of `package-lock.json` gewijzigd EN je wilt 100% zekerheid dat deps opnieuw geïnstalleerd worden
- Base image upgrade (FROM-regel)
- Cache-corruption debugging

**Na deploy altijd `docker image prune -f`** (zonder `-a`) — ruimt alleen dangling images van vorige builds op. Nooit tagged rollback-images.

## Disk-pressure bewaking

- `scripts/disk_guard.sh` draait elk uur via cron. Bij >85% safe prune, bij >95% emergency prune (cache + dangling only, nooit tagged images).
- Weekly cron zondag 04:00: `docker builder prune -f --filter "until=168h"`.
- Log: `/var/log/luxis-disk.log` — check bij twijfel of het WARNING/ALERT regels heeft.
- `df -h /` handmatig bij vreemd deploy-gedrag om vroege diagnose.

## Verificatie na deploy
```bash
ssh -i ~/.ssh/luxis_deploy root@46.225.115.216 "cd /opt/luxis && docker compose ps && docker compose logs backend --tail 5"
```

## Veiligheidsregels
- **Autonoom:** git pull, logs, disk check, ps, deploy (na groene tests)
- **ALTIJD bevestiging vragen:** volumes verwijderen, database wissen, rm -rf, rollback migraties
- Na deploy altijd vermelden: welke service(s), of er migraties gedraaid zijn

## Valkuilen
- **Alembic: `run` niet `exec`** als backend crashed
- **POSTGRES_PASSWORD:** werkt alleen bij eerste volume-init. Later wijzigen via `ALTER USER`
- **Na ELKE commit ALTIJD `git push origin main`** — anders bereikt het de VPS niet
