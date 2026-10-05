"""Build the pinned English CPV lookup from the official downloaded XML.

Input: data/reference/cpv_2008.xml (unzip -p cpv_2008_xml.zip cpv_2008.xml)
and the official SIX ISO 4217 list-one.xml saved as iso4217.xml.
Run from the project root after downloading those source files.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1] / "data/reference"
lookup = {}
for entry in ET.parse(root / "cpv_2008.xml").getroot().findall("CPV"):
    code = entry.attrib["CODE"].split("-")[0]
    label = entry.find("TEXT[@LANG='EN']")
    if label is not None and label.text:
        lookup[code] = label.text
(root / "cpv_en.json").write_text(json.dumps(lookup, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
sources = {
    "cpv_2008_xml.zip": "https://ted.europa.eu/documents/d/ted/cpv_2008_xml",
    "cpv_2008.xml": "https://ted.europa.eu/documents/d/ted/cpv_2008_xml",
    "cpv_en.json": "https://ted.europa.eu/documents/d/ted/cpv_2008_xml",
    "iso4217.xml": "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml",
}
manifest = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "cpv_version": "2008",
            "derivation": "CPV/@CODE without check digit -> TEXT[@LANG=EN]; tools/build_reference.py",
            "files": [{"file": name, "source_url": url, "sha256": hashlib.sha256((root/name).read_bytes()).hexdigest()}
                      for name, url in sources.items()]}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Built {len(lookup)} official CPV descriptions")
