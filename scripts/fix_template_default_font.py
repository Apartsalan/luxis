"""S221 — zet het terugval-lettertype van de DOCX-brieven van Cambria naar Calibri.

De brieftekst is expliciet Calibri, maar tekst zonder eigen opmaak (o.a. de
sectie-kopjes) viel terug op de thema-standaard Cambria → gemengd lettertype.
Deze fix zet het body-thema (minorFont) op Calibri zodat de hele brief één
lettertype heeft. Alleen de ene 'Cambria' in het thema wordt geraakt (geverifieerd
uniek + binnen <a:minorFont>); alle andere zip-onderdelen blijven byte-identiek.

Idempotent: draai je opnieuw, dan is er geen Cambria meer en verandert er niets.

Usage: python scripts/fix_template_default_font.py
"""

import glob
import io
import zipfile

THEME = "word/theme/theme1.xml"


def fix_docx(path: str) -> bool:
    with zipfile.ZipFile(path) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    changed = False
    out: list[tuple[zipfile.ZipInfo, bytes]] = []
    for info, data in items:
        if info.filename == THEME:
            text = data.decode("utf-8")
            if "Cambria" in text:
                # Alleen binnen minorFont staat Cambria (vooraf geverifieerd uniek).
                new = text.replace("Cambria", "Calibri")
                data = new.encode("utf-8")
                changed = True
        out.append((info, data))
    if not changed:
        return False
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in out:
            z.writestr(info, data)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return True


def main() -> None:
    for path in sorted(glob.glob("templates/*.docx")):
        did = fix_docx(path)
        print(f"  {'gewijzigd' if did else 'ongewijzigd':11s} {path}")


if __name__ == "__main__":
    main()
