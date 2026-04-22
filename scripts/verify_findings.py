"""Verifieer concrete audit-bevindingen in de gerendererde brieven."""
import re
from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "docs" / "audits" / "rendered-samples"


def extract(html: str, pattern: str, flags: int = 0) -> list[str]:
    return re.findall(pattern, html, flags)


def check_14dagenbrief():
    html = (SAMPLES / "14_dagenbrief__PRODUCTIE.html").read_text(encoding="utf-8")

    print("\n" + "=" * 70)
    print("14-DAGENBRIEF — PRODUCTIE RENDERING")
    print("=" * 70)

    # Finding #4: "dagtekening" versus "ontvangst"
    ontvangst = len(extract(html, r"na ontvangst"))
    dagtekening = len(extract(html, r"na dagtekening"))
    print(f"\n[#4] Termijn-formulering in 14-dagenbrief:")
    print(f"     'na ontvangst' komt voor:   {ontvangst}x  (correct)")
    print(f"     'na dagtekening' komt voor: {dagtekening}x  (juridisch FOUT)")
    status = "FOUT BEVESTIGD" if dagtekening > 0 else "OK"
    print(f"     Status: {status}")

    # Vind de letterlijke zinnen
    for m in re.finditer(r"binnen veertien dagen na (\w+) (?:van |van deze )?", html):
        context = html[max(0, m.start()-50):m.end()+80]
        # strip HTML tags for readability
        clean = re.sub(r"<[^>]+>", "", context)
        clean = re.sub(r"\s+", " ", clean).strip()
        print(f"     -> \"...{clean}...\"")

    # Finding template: "EUR" vs "€"
    eur_text_count = len(extract(html, r"EUR\s*\d"))
    euro_sym_count = len(extract(html, r"&euro;|€\s*\d"))
    print(f"\n[#6] Valuta-formaat:")
    print(f"     'EUR 1.234,56' formaat: {eur_text_count}x")
    print(f"     '€ 1.234,56'   formaat: {euro_sym_count}x")
    status = "FOUT BEVESTIGD" if eur_text_count > euro_sym_count else "OK"
    print(f"     Status: {status}")

    # Finding #5: BIK bedrag aanwezig, BTW bedrag aanwezig?
    print(f"\n[#5] BIK-bedrag in de brief:")
    bik_match = re.search(r"EUR\s*475[,.]00", html)
    print(f"     BIK excl BTW (475,00): {'aanwezig' if bik_match else 'niet aanwezig'}")
    btw_over_bik = re.search(r"EUR\s*99[,.]75", html)
    print(f"     BTW over BIK (99,75):  {'aanwezig' if btw_over_bik else 'NIET AANWEZIG (= bug)'}")
    print(f"     Toelichting: 'excl. BTW' in brief: "
          f"{'ja' if 'excl. BTW' in html else 'nee'}")
    status = ("FOUT BEVESTIGD: brief zegt 'excl. BTW' en toont geen BTW-bedrag, "
              "terwijl client niet-BTW-plichtig is en 21% WEL vorderbaar was") \
             if not btw_over_bik else "OK"
    print(f"     Status: {status}")

    # Finding: IBAN in de brief?
    iban_in_body = "NL20 RABO 0388 5065 20" in html
    print(f"\n[#] IBAN rendering in brief:")
    print(f"     IBAN staat in brief: {'ja' if iban_in_body else 'NEE (debiteur kan niet betalen)'}")
    # Check of de tekst "rekeningnummer van onze client" ernaast een IBAN heeft
    rek_match = re.search(r"rekeningnummer van onze cli[^.]*", html)
    if rek_match:
        window = html[rek_match.start():rek_match.start()+500]
        iban_near = "NL20 RABO" in window
        print(f"     IBAN vlakbij 'rekeningnummer van onze client'-zin: "
              f"{'ja' if iban_near else 'NEE = FOUT'}")

    # Finding: dubbel valutasymbool
    dubbel = extract(html, r"€\s*EUR|EUR\s*€")
    print(f"\n[#] Dubbel valutasymbool (€ EUR of EUR €):")
    print(f"     Aantal gevonden: {len(dubbel)}")
    if dubbel:
        for d in dubbel[:3]:
            print(f"     -> {d!r}")


def check_sommatie():
    html = (SAMPLES / "sommatie__PRODUCTIE.html").read_text(encoding="utf-8")
    print("\n" + "=" * 70)
    print("SOMMATIE — PRODUCTIE RENDERING")
    print("=" * 70)

    # Dubbel symbool check
    dubbel = extract(html, r"€\s*EUR|EUR\s*€")
    print(f"\n[#] Dubbel valutasymbool: {len(dubbel)}x")

    # EUR vs €
    eur_text = len(extract(html, r"EUR\s*\d"))
    print(f"[#6] 'EUR 1.234,56' formaat: {eur_text}x")


def check_all():
    print("\n" + "=" * 70)
    print("AUDIT BEWIJSSTUKKEN — uit gerendererde brieven")
    print("=" * 70)
    print(f"\nScenario: Bakkerij Van Dijk VOF (niet-BTW-plichtig) eist €3.500 van")
    print(f"Jan de Vries. 6 mnd verzuim. BIK = €475 excl, €574,75 incl BTW.")
    print(f"Totaal wettelijk vorderbaar = €3.500 + €93 rente + €574,75 = €4.167,75")
    print(f"Totaal in Luxis productie = €3.500 + €93 + €475 = €4.068 (€100 MINDER)")

    check_14dagenbrief()
    check_sommatie()

    print("\n" + "=" * 70)
    print("CONCLUSIE")
    print("=" * 70)
    print("Open in browser om visueel te checken:")
    print(f"  file:///{(SAMPLES / 'index.html').as_posix()}")
    print()


if __name__ == "__main__":
    check_all()
