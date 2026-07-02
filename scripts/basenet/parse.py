"""Generieke parser voor BaseNet XML-export-bestanden.

BaseNet exporteert elke entiteit naar een eigen XML-bestand als een stroom van
achter elkaar geplakte top-level records. Het bestand als geheel is dus GEEN
well-formed XML (meerdere sibling-roots). Eén record ziet er zo uit:

    <rela.letter>
        <entityname>rela.letter</entityname>
        <systemid>529071024</systemid>
        <entrylist>
            <entry key="letterno" value="100000"/>
            ...
        </entrylist>
    </rela.letter>

Aanpak: we knippen het bestand in losse record-fragmenten (zodat één kapot
record niet het hele bestand sloopt) en parsen elk fragment apart. Attribuut-
waarden zijn in de bron XML-ge-escaped (&lt; &amp; &quot;) en worden door
ElementTree automatisch terug-vertaald.

Puur Python, geen app/DB-afhankelijkheden — zo standalone testbaar en snel.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Eerste top-level tag in het bestand = de entiteitsnaam (bv. "rela.letter").
# Een tag mag letters/cijfers/underscore/punt bevatten; moet direct sluiten met ">".
_ENTITY_RE = re.compile(r"<([A-Za-z_][\w.]*)>")


@dataclass
class BaseNetRecord:
    """Eén BaseNet-record: entiteitsnaam, systemid en alle key/value-velden."""

    entity: str
    systemid: str | None
    fields: dict[str, str]

    def get(self, key: str, default: str = "") -> str:
        """Veldwaarde (leeg-getrimd niet — precies zoals in de export)."""
        return self.fields.get(key, default)


@dataclass
class ParseResult:
    """Resultaat van het parsen van één bestand — records + telling van mislukte."""

    entity: str | None
    records: list[BaseNetRecord]
    failed: int  # aantal record-fragmenten dat niet als XML te parsen was


def detect_entity(content: str) -> str | None:
    """De entiteitsnaam = de eerste top-level tag in het bestand."""
    m = _ENTITY_RE.search(content)
    return m.group(1) if m else None


def _record_from_element(entity: str, el: ET.Element) -> BaseNetRecord:
    fields: dict[str, str] = {}
    for entry in el.iter("entry"):
        key = entry.get("key")
        if key is not None:
            fields[key] = entry.get("value", "")
    systemid = fields.get("systemid")
    if systemid is None:
        sid_el = el.find("systemid")
        systemid = sid_el.text if sid_el is not None and sid_el.text else None
    return BaseNetRecord(entity=entity, systemid=systemid, fields=fields)


def iter_records(path: str | Path) -> Iterator[BaseNetRecord]:
    """Yield elk record uit een BaseNet-XML-bestand (mislukte records worden
    stil overgeslagen — gebruik parse_file() als je de telling wilt)."""
    yield from parse_file(path).records


def parse_file(path: str | Path) -> ParseResult:
    """Parse een heel BaseNet-XML-bestand naar records + telling mislukte fragmenten."""
    content = Path(path).read_text(encoding="utf-8", errors="replace")
    entity = detect_entity(content)
    if entity is None:
        return ParseResult(entity=None, records=[], failed=0)

    # Grijp elk <entity>...</entity>-blok (non-greedy → per record).
    block_re = re.compile(
        rf"<{re.escape(entity)}\b[^>]*>.*?</{re.escape(entity)}>", re.DOTALL
    )
    records: list[BaseNetRecord] = []
    failed = 0
    for match in block_re.finditer(content):
        try:
            el = ET.fromstring(match.group(0))
        except ET.ParseError:
            failed += 1
            continue
        records.append(_record_from_element(entity, el))
    return ParseResult(entity=entity, records=records, failed=failed)


# ── Bestanden lokaliseren in een export-map ──────────────────────────────────

def find_entity_file(export_dir: str | Path, class_suffix: str) -> Path | None:
    """Vind het (eerste) XML-bestand voor een entiteit op basis van de Java-
    class-naam achteraan de bestandsnaam, bv. "Company" → *.Company.xml.
    Geeft None als er niets matcht."""
    matches = sorted(Path(export_dir).glob(f"*.{class_suffix}.xml"))
    return matches[0] if matches else None


def find_entity_files(export_dir: str | Path, class_suffix: str) -> list[Path]:
    """Alle XML-bestanden voor een entiteit (sommige zijn gechunkt, bv. Letter
    in 4 delen: *.Letter.xml). Gesorteerd op naam."""
    return sorted(Path(export_dir).glob(f"*.{class_suffix}.xml"))


def parse_entity(export_dir: str | Path, class_suffix: str) -> ParseResult:
    """Parse alle (eventueel gechunkte) bestanden van één entiteit samen."""
    files = find_entity_files(export_dir, class_suffix)
    entity: str | None = None
    records: list[BaseNetRecord] = []
    failed = 0
    for f in files:
        res = parse_file(f)
        entity = entity or res.entity
        records.extend(res.records)
        failed += res.failed
    return ParseResult(entity=entity, records=records, failed=failed)


# ── CLI: samenvatting van een export-map ─────────────────────────────────────

def _summarize(export_dir: str | Path) -> None:
    export_path = Path(export_dir)
    xml_files = sorted(export_path.glob("*.xml"))
    print(f"Export-map: {export_path}  ({len(xml_files)} XML-bestanden)\n")
    # Groepeer gechunkte bestanden op class-suffix.
    by_suffix: dict[str, list[Path]] = {}
    for f in xml_files:
        suffix = f.stem.split(".")[-1]
        by_suffix.setdefault(suffix, []).append(f)
    total_records = 0
    total_failed = 0
    for suffix in sorted(by_suffix):
        res = parse_entity(export_path, suffix)
        total_records += len(res.records)
        total_failed += res.failed
        flag = f"  [LET OP] {res.failed} mislukt" if res.failed else ""
        print(f"  {len(res.records):7d}  {res.entity or suffix}{flag}")
    print(f"\n  Totaal: {total_records} records, {total_failed} mislukte fragmenten")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Gebruik: python -m scripts.basenet.parse <export-map>")
        sys.exit(1)
    _summarize(sys.argv[1])
