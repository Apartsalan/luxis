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


def build_reply_subject(
    *,
    original_subject: str | None,
    client_name: str | None,
    debtor_name: str | None,
    case_number: str,
) -> str:
    """Onderwerp voor een AI-ANTWOORD op een inkomende mail van de wederpartij.

    Keuze Arsalan (S223): houd het originele onderwerp aan met 'Re:' ervoor (zo
    blijft de mailwisseling bij de ontvanger één gesprek) en plak klant/debiteur +
    dossiernummer erachter — maar NIET als het dossiernummer al in het originele
    onderwerp staat (voorkomt dubbele vermelding).
    """
    base = (original_subject or "").strip()
    if base.lower().startswith("re:"):
        reply = base
    elif base:
        reply = f"Re: {base}"
    else:
        reply = "Re:"

    if case_number and case_number not in reply:
        parties = " / ".join(
            p.strip() for p in (client_name, debtor_name) if p and p.strip()
        )
        tag = f"{parties} — {case_number}" if parties else case_number
        reply = f"{reply} — {tag}"
    return reply
