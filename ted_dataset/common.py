"""Small serialization and provenance primitives."""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    # Type-tag recursively so exact JSON decimals cannot collide with strings
    # or a source object that happens to use a reserved-looking dictionary key.
    def tagged(v):
        if isinstance(v, dict):
            return ["object", [[k, tagged(v[k])] for k in sorted(v)]]
        if isinstance(v, list):
            return ["array", [tagged(x) for x in v]]
        if isinstance(v, Decimal):
            return ["decimal", str(v)]
        return [type(v).__name__, v]
    return json.dumps(tagged(value), ensure_ascii=False, separators=(",", ":"))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def safe_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes snapshot")
    return path
