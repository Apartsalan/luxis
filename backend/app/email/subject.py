"""Gedeelde onderwerp-bouwer voor uitgaande incasso-mail (S220 punt 5).

Eén formaat op alle verzendroutes:
    "{klant} / {debiteur} — {brieftype} — {dossiernummer}"

Voorheen liepen vijf verschillende formaten door elkaar ("... inzake dossier ...",
"... - ...", getitelde sjabloonsleutels, lege BaseNet-slots). Ontbrekende klant of
debiteur worden weggelaten zodat het onderwerp nooit met lege delen of losse
streepjes begint.
"""


def build_email_subject(
    *,
    client_name: str | None,
    debtor_name: str | None,
    letter_type: str,
    case_number: str,
) -> str:
    """Bouw het gestandaardiseerde mail-onderwerp.

    Args:
        client_name: Naam van de opdrachtgever (klant), of None/leeg.
        debtor_name: Naam van de debiteur (wederpartij), of None/leeg.
        letter_type: Menselijke naam van de brief/stap (bv. "Eerste sommatie").
        case_number: Dossiernummer.
    """
    parties = " / ".join(p.strip() for p in (client_name, debtor_name) if p and p.strip())
    prefix = f"{parties} — " if parties else ""
    return f"{prefix}{letter_type} — {case_number}"
