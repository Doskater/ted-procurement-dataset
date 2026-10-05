"""Run the entire offline test suite and record evidence for report generation."""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ted_dataset.common import digest, utc_now, write_json
from ted_dataset.evidence import code_digest

out = ROOT / "verification"
out.mkdir(exist_ok=True)
before = code_digest()
command = [sys.executable, "-m", "pytest", "-q", "--junitxml=verification/pytest.xml"]
result = subprocess.run(command, cwd=ROOT)
tests = failures = errors = 0
if (out/"pytest.xml").exists():
    report_tree = ET.parse(out/"pytest.xml")
    for suite in report_tree.getroot().iter("testsuite"):
        suite.attrib.pop("hostname", None)
        tests += int(suite.get("tests", "0"))
        failures += int(suite.get("failures", "0"))
        errors += int(suite.get("errors", "0"))
    report_tree.write(out/"pytest.xml", encoding="utf-8", xml_declaration=True)
passed = result.returncode == 0 and tests > 0 and failures == errors == 0 and before == code_digest()
write_json(out/"evidence.json", dict(status="passed" if passed else "failed", tests=tests, failures=failures,
                                    errors=errors, code_sha256=before, completed_at=utc_now(),
                                    command=["python", *command[1:]], exit_code=result.returncode, junit_file="pytest.xml",
                                    junit_sha256=digest((out/"pytest.xml").read_bytes())))
sys.exit(0 if passed else 1)
