"""Bind automated test evidence to the code and fixtures that were tested."""
from pathlib import Path

from .common import digest, read_json

ROOT = Path(__file__).resolve().parents[1]


def processing_digest(root=ROOT):
    files = sorted(root.glob("ted_dataset/*.py")) + [root/"requirements.txt"]
    return digest(b"".join(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() + b"\0" for p in files))


def code_digest(root=ROOT):
    files = sorted([*root.glob("ted_dataset/*.py"), *root.glob("tests/*.py"),
                    *root.glob("tests/fixtures/*.json"), *root.glob("tools/*.py"),
                    root/"pyproject.toml", root/"requirements.txt", root/"data/reference/manifest.json"])
    payload = b"".join(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() + b"\0" for p in files)
    return digest(payload)


def test_evidence(path=None):
    path = Path(path) if path else ROOT / "verification/evidence.json"
    if not path.exists():
        return {"status": "not recorded"}
    evidence = read_json(path)
    if evidence.get("code_sha256") != code_digest():
        return {"status": "stale: code or fixtures changed"}
    log = path.parent / evidence["junit_file"]
    if not log.exists() or digest(log.read_bytes()) != evidence["junit_sha256"]:
        return {"status": "invalid: test report checksum mismatch"}
    return {k: evidence[k] for k in ("status", "tests", "failures", "errors")}
