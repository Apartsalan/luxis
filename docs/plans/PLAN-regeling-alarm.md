# PLAN — Alarm op gemiste betalingsregeling-termijnen

**Rang: 2 — direct uitvoerbaar, TIJDGEVOELIG: eerste termijn vervalt 9 juli (IN100019),
daarna 12/13/15/18/19 juli.** Zonder dit plan wordt een gemiste termijn nergens zichtbaar
behalve als iemand toevallig het juiste dossier opent.

## Vastgesteld gat (audit 7 juli)

- De dagelijkse job (06:30 UTC) `daily_installment_overdue_check` zet termijnen op
  `overdue` — **maar niemand ziet dat**: `app/notifications/service.py` heeft geen enkele
  installment-referentie en het dashboard telt alleen overdue *taken*.
- 121 pending termijnen op prod (13 actieve regelingen), eerst vervallende: 2026-07-09.
- 12 van de 13 regelingen hangen aan zaken die (nu nog) 'afgesloten' zijn — het alarm
  moet dus NIET filteren op zaakstatus.

## Te wijzigen bestanden

1. `backend/app/collections/service.py` — `mark_overdue_installments` (regel ~941):
   retourneer naast de count ook de gemarkeerde installments (of een lijst met
   case_id/case_number/bedrag/due_date), zodat de scheduler er notificaties van kan maken.
2. `backend/app/workflow/scheduler.py` — `daily_installment_overdue_check` (regel ~572):
   na het markeren per installment een notificatie aanmaken via
   `create_notification_if_not_exists` (zelfde patroon als `daily_deadline_notifications`,
   regel ~412 — kopieer de dedup-aanpak van daar, 24u-dedup).
3. `backend/tests/` — nieuwe test naast de bestaande collections-tests (bekijk
   `test_payment_*.py`-bestanden voor de fixture-stijl).

## Stappenplan

1. Lees `mark_overdue_installments` en `daily_deadline_notifications` volledig.
2. Rode test eerst: termijn met `due_date` gisteren + status pending → job draait →
   status overdue ÉN notificatie bestaat (titel bevat zaaknummer + bedrag). Tweede run →
   géén tweede notificatie (dedup).
3. Implementeer minimaal: notificatie per overdue-termijn, gericht aan de
   `assigned_to_id` van de zaak, val terug op alle actieve users van de tenant als die
   leeg is (afgesloten zaken hebben er meestal wél een; check het).
4. Notificatietekst in het Nederlands, met zaaknummer, termijnbedrag en vervaldatum,
   bv. "Betalingsregeling IN100019: termijn van € 500,00 (vervallen 9 juli) is niet
   gemarkeerd als betaald."
5. `uvx ruff check app/` + relevante pytest lokaal (VPS of dev-container), commit, push,
   deploy backend via SSH (deploy-regels-skill), health check.

## Randgevallen (die een sneller model zou missen)

- **Betaling-registratie is handmatig**: de bankimport/payment-matching koppelt betalingen
  NIET aan termijnen (geverifieerd: `payment_matching_service.py` bevat geen
  installment-logica; `payment_arrangement_installments.paid_amount/payment_id` worden
  alleen via de dossier-UI gezet). Een "gemiste" termijn kan dus gewoon betaald zijn maar
  nog niet afgevinkt. Formuleer de notificatie daarom als "niet gemarkeerd als betaald",
  niet als "debiteur heeft niet betaald".
- De job draait voor ALLE tenants zonder tenant-filter in de huidige query — houd dat zo,
  maar zet `tenant_id` correct op de notificatie (haal 'm van de installment, kolom
  bestaat).
- Dedup: `create_notification_if_not_exists` bestaat al (service regel ~43) — gebruik die,
  bouw geen eigen dedup.
- Termijn wordt overdue de dag NÁ de vervaldatum (`due_date < today`) — 9 juli-termijn
  geeft dus op 10 juli 06:30 UTC het eerste alarm. Dat is bedoeld gedrag.
- Geen e-mail sturen — alleen in-app notificatie (bel-icoon). E-mail-notificaties bestaan
  niet in dit systeem; niet bijbouwen.

## Optioneel vervolg (apart houden, NIET in deze wijziging)

Automatische koppeling goedgekeurde payment-match → openstaande termijn van dezelfde
zaak. Pas overwegen als Lisanne het handmatig afvinken vervelend blijkt te vinden.

## Acceptatiecriteria

1. Nieuwe test groen; bestaande collections/scheduler-tests groen; ruff schoon.
2. Gedeployed; `docker compose logs backend` toont de job zonder errors bij de eerstvolgende
   06:30-run (of forceer via een handmatige aanroep in een python-shell op de container).
3. Zodra een termijn echt vervalt (10 juli): notificatie zichtbaar onder het bel-icoon
   voor Lisanne's account — screenshot of beschrijving in SESSION-NOTES.
4. Twee opeenvolgende dagelijkse runs geven geen dubbele notificatie voor dezelfde termijn.
