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

> ✅ **S170-oplossing — de source-mount is WEG (was een lek, geen bedoeling).**
> De bind-mounts `./backend/app` + `./backend/alembic` stonden in de basis
> `docker-compose.yml` (dev-config) en lekten via de compose-merge (union op mount-target)
> naar prod, ondanks dat `docker-compose.prod.yml` de backend-volumes bewust zónder die
> mounts herdefinieert. In S170 uit de basis gehaald (staan nog in `docker-compose.dev.yml`
> voor lokale hot-reload). **Prod draait nu image-baked code** (`docker inspect luxis-backend`
> toont enkel `/app/templates` + de named volumes generated_docs/uploads — geen `/app/app`).
> Gevolgen voor de deploy:
> 1. **Code wijzigen vereist nu een rebuild** — `git pull` alleen ververst de code NIET meer
>    (geen mount). De deploy-commando's doen `build` altijd al, dus dat is goed.
> 2. **`docker compose up -d` hercreëert de backend gegarandeerd bij een codewijziging**
>    (image verandert → nieuwe container). De handmatige `docker restart`-dans van S168 is
>    niet meer nodig; verifieer `StartedAt` nog wel als goedkope check.
> 3. **`templates/` blijft wél bind-mounted** (prod.yml `:ro`) — templates worden bij render
>    van schijf gelezen, dus een `git pull` ververst ze live zonder rebuild (bedoeld).
> 4. Draaiende code == de build == git HEAD → reproduceerbaar, geen VPS-werkkopie-drift meer.

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
