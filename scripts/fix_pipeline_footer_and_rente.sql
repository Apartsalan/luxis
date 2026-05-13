-- DF138-20/21: vervang oude voetnoot + hardcoded 'Rente € 0,00' in
-- email_body_template van alle pipeline-steps. Body voor email_body_template_html
-- wordt apart aangepakt (HTML structuur).

BEGIN;

-- 1. Voetnoot: oude tekst -> nieuwe tekst (plain text body)
UPDATE incasso_pipeline_steps
SET email_body_template = REPLACE(
    email_body_template,
    'Heeft u financiële zorgen en ziet u geen uitweg meer? Neem contact op met uw gemeente voor schuldhulpverlening. Voor directe ondersteuning bij zelfmoordpreventie kunt u ook bellen met 113 (gratis en anoniem) via 0800-0113 of bezoek www.113.nl<https://www.113.nl>. Wacht niet te lang met hulp zoeken en maak gebruik van de hulp die er is om uw problemen op te lossen',
    'Heeft u financiële zorgen en ziet u geen uitweg meer? Wij informeren u graag over uw rechten als schuldenaar: kestinglegal.nl/debiteuren. Voor schuldhulpverlening kunt u terecht bij uw gemeente. Heeft u dringend emotionele steun nodig? Bel dan gratis en anoniem met Stichting 113 Zelfmoordpreventie via 0800-0113 of kijk op www.113.nl.'
)
WHERE email_body_template ILIKE '%Neem contact op met uw gemeente voor schuldhulpverlening%';

-- 2. Hardcoded 'Rente   €       0,00' verwijderen — AI vult zelf in.
-- Match de letterlijke tab-uitlijning uit Lisanne's template.
UPDATE incasso_pipeline_steps
SET email_body_template = REPLACE(
    email_body_template,
    E'\tRente\t€\t0,00',
    E'\tRente\t€\t'
)
WHERE email_body_template LIKE E'%\tRente\t€\t0,00%';

-- Variant met spaties i.p.v. tabs
UPDATE incasso_pipeline_steps
SET email_body_template = REGEXP_REPLACE(
    email_body_template,
    E'(Rente[ \t]+€[ \t]+)0,00',
    '\1',
    'g'
)
WHERE email_body_template ~ 'Rente[ \t]+€[ \t]+0,00';

-- Zelfde behandeling voor HTML-variant indien aanwezig
UPDATE incasso_pipeline_steps
SET email_body_template_html = REPLACE(
    email_body_template_html,
    'Heeft u financiële zorgen en ziet u geen uitweg meer? Neem contact op met uw gemeente voor schuldhulpverlening. Voor directe ondersteuning bij zelfmoordpreventie kunt u ook bellen met 113 (gratis en anoniem) via 0800-0113 of bezoek www.113.nl<https://www.113.nl>. Wacht niet te lang met hulp zoeken en maak gebruik van de hulp die er is om uw problemen op te lossen',
    'Heeft u financiële zorgen en ziet u geen uitweg meer? Wij informeren u graag over uw rechten als schuldenaar: kestinglegal.nl/debiteuren. Voor schuldhulpverlening kunt u terecht bij uw gemeente. Heeft u dringend emotionele steun nodig? Bel dan gratis en anoniem met Stichting 113 Zelfmoordpreventie via 0800-0113 of kijk op www.113.nl.'
)
WHERE email_body_template_html IS NOT NULL
  AND email_body_template_html ILIKE '%Neem contact op met uw gemeente voor schuldhulpverlening%';

UPDATE incasso_pipeline_steps
SET email_body_template_html = REGEXP_REPLACE(
    email_body_template_html,
    '(Rente[^0-9€]{1,40}€[^0-9]{1,10})0,00',
    '\1',
    'g'
)
WHERE email_body_template_html IS NOT NULL
  AND email_body_template_html ~ 'Rente[^0-9€]{1,40}€[^0-9]{1,10}0,00';

-- Verifiëren: kolommen waar oude voetnoot of 0,00 nog aanwezig is.
SELECT name,
       CASE WHEN email_body_template ILIKE '%Neem contact op met uw gemeente%' THEN 'OLD' ELSE 'OK' END AS footer_plain,
       CASE WHEN email_body_template_html ILIKE '%Neem contact op met uw gemeente%' THEN 'OLD' ELSE 'OK' END AS footer_html,
       CASE WHEN email_body_template ~ 'Rente[ \t]+€[ \t]+0,00' THEN 'OLD' ELSE 'OK' END AS rente_plain
FROM incasso_pipeline_steps
ORDER BY name;

COMMIT;
