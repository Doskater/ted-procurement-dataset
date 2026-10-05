"""Pinned, source-backed CPV and currency dictionaries."""
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from .common import digest, read_json, safe_path


@dataclass(frozen=True)
class Reference:
    cpv: dict[str, str]
    currencies: frozenset[str]
    identity: str


def load_reference(directory):
    directory = Path(directory)
    manifest_bytes = (directory / "manifest.json").read_bytes()
    manifest = read_json(directory / "manifest.json")
    for item in manifest["files"]:
        if digest(safe_path(directory, item["file"]).read_bytes()) != item["sha256"]:
            raise ValueError(f"Reference checksum mismatch: {item['file']}")
    cpv = read_json(directory / "cpv_en.json")
    currencies = frozenset(e.text for e in ET.parse(directory / "iso4217.xml").iter("Ccy") if e.text)
    # XXX means no currency, XTS is testing; neither is a procurement currency.
    return Reference(cpv, currencies - {"XXX", "XTS"}, digest(manifest_bytes))
