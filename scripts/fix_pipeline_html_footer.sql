-- Vervang HTML-versie van oude voetnoot in Eerste sommatie.
-- Gebruik dollar-quoted strings + PostgreSQL regex met POSIX classes.

BEGIN;

UPDATE incasso_pipeline_steps
SET email_body_template_html = regexp_replace(
    email_body_template_html,
    $re$Heeft u financiële zorgen[\s\S]{0,800}om uw problemen op te lossen$re$,
    $new$Heeft u financiële zorgen en ziet u geen uitweg meer? Wij informeren u graag over uw rechten als schuldenaar: <a href="https://kestinglegal.nl/debiteuren">kestinglegal.nl/debiteuren</a>. Voor schuldhulpverlening kunt u terecht bij uw gemeente. Heeft u dringend emotionele steun nodig? Bel dan gratis en anoniem met Stichting 113 Zelfmoordpreventie via 0800-0113 of kijk op <a href="http://www.113.nl">www.113.nl</a>.$new$,
    'n'
)
WHERE id = 'b45261b0-2fed-438e-bee2-a27242d715b7';

-- Verifieer geen "Neem contact" meer
SELECT name,
       position('Neem contact' IN email_body_template_html) AS pos_old_html,
       position('Neem contact' IN email_body_template) AS pos_old_plain
FROM incasso_pipeline_steps
WHERE name = 'Eerste sommatie';

COMMIT;
